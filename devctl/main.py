"""
devctl CLI entrypoint.
Defines commands: ports, explain, free, zombies, heavy, ai, ctx, doctor, py, run, and add.
"""

from typing import List, Optional
import sys
import shutil
import platform
import psutil

if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import typer
from rich.console import Console

from .core.ports import scan_listening_ports, get_port_info, is_port_in_use, DEV_PROCESS_NAMES
from .core.process import free_port, prune_zombies
from .core.catalog import lookup_port_context
from .core.env import diagnose_environment, discover_system_pythons
from .core.runner import run_in_venv, safe_add_package
from .core.security import validate_port, is_privileged_port, is_system_process
from .ui.formatters import (
    render_ports_table,
    render_explain_panel,
    render_heavy_table,
    render_ai_status,
    render_doctor_panel,
    render_pythons_table,
)
from .ui.theme import ICON_SUCCESS, ICON_ERROR, ICON_WARN, MARK_BULLET

app = typer.Typer(
    name="devctl",
    help="devctl: The local dev runtime, port collision & Python environment guardian.",
    add_completion=False,
)

term_width = max(115, shutil.get_terminal_size((115, 24)).columns)
console = Console(legacy_windows=False, width=term_width)


@app.command("ports", help="Inspect active listening TCP ports with process category and technical context.")
def list_ports(
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Filter for a specific port number"),
    all_ports: bool = typer.Option(False, "--all", "-a", help="Show all system and ephemeral RPC ports"),
):
    """Scan and list listening ports with PID, process name, category, purpose, and memory."""
    try:
        ports = scan_listening_ports(port_filter=port, dev_only=not all_ports)
        if not ports:
            if port:
                console.print(f"[green][{ICON_SUCCESS}] Port {port} is completely free.[/green]")
            else:
                console.print(f"[green][{ICON_SUCCESS}] No active listening development ports found.[/green]")
            return

        table = render_ports_table(ports)
        console.print(table)

        zombie_count = sum(1 for p in ports if p.is_zombie and not p.is_system)
        summary = f"\n[dim]Found {len(ports)} active listening port(s)"
        if zombie_count > 0:
            summary += f" · [bold yellow]{zombie_count} orphaned zombie(s) detected![/bold yellow] (Run `devctl zombies` to clean)"
        summary += " · Run `devctl explain <port>` for in-depth advice.[/dim]"
        console.print(summary)

    except ValueError as ve:
        console.print(f"[bold red][{ICON_ERROR}] {str(ve)}[/bold red]")
        raise typer.Exit(code=1)


@app.command("explain", help="Analyze what a specific port does, its category, and whether it is safe to terminate.")
def explain_port_cmd(
    port: int = typer.Argument(..., help="Port number to inspect (e.g. 5432, 8000, 7768)"),
):
    """Provides technical explanation, safety verdict, and recommendation for any port."""
    try:
        port_num = validate_port(port)
    except ValueError as ve:
        console.print(f"[bold red][{ICON_ERROR}] {str(ve)}[/bold red]")
        raise typer.Exit(code=1)

    info = get_port_info(port_num)
    proc_name = info.process_name if info else ""
    cmdline = info.cmdline if info else ""

    ctx = lookup_port_context(port_num, proc_name, cmdline)
    panel = render_explain_panel(ctx, info)
    console.print(panel)


@app.command("free", help="Safely free one or more occupied ports by terminating their listener.")
def free_ports_cmd(
    ports: List[int] = typer.Argument(..., help="One or more port numbers to free (e.g. 8000 or 3000 8000)"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
    force: bool = typer.Option(False, "--force", "-f", help="Force termination on privileged ports (<1024)"),
):
    """Frees ports using two-stage termination with TOCTOU race protection."""
    for p in ports:
        try:
            port_num = validate_port(p)
        except ValueError as ve:
            console.print(f"[bold red][{ICON_ERROR}] {str(ve)}[/bold red]")
            continue

        info = get_port_info(port_num)
        if not info:
            console.print(f"[green][{ICON_SUCCESS}] Port {port_num} is already free.[/green]")
            continue

        if info.is_system:
            console.print(
                f"[bold red][{ICON_ERROR}] Cannot free port {port_num}: Occupied by protected system process '{info.process_name}' (PID {info.pid}).[/bold red]"
            )
            continue

        if is_privileged_port(port_num) and not force:
            console.print(
                f"[bold yellow][{ICON_WARN}] Port {port_num} is a privileged system port (< 1024). Use --force to proceed.[/bold yellow]"
            )
            continue

        # Target details
        console.print(f"\n[bold cyan]Target on Port {port_num}:[/bold cyan]")
        console.print(f"  {MARK_BULLET} Process  : [bold white]{info.process_name}[/bold white] (PID {info.pid})")
        if info.purpose:
            console.print(f"  {MARK_BULLET} Context  : [white]{info.purpose}[/white]")
        if info.cwd:
            console.print(f"  {MARK_BULLET} Folder   : [dim]{info.cwd}[/dim]")
        if info.cmdline:
            console.print(f"  {MARK_BULLET} Command  : [dim]{info.cmdline}[/dim]")
        if info.memory_mb > 0:
            console.print(f"  {MARK_BULLET} Memory   : [green]{info.memory_mb:.1f} MB[/green]")

        if not yes:
            confirm = typer.confirm(f"Terminate process '{info.process_name}' to free port {port_num}?", default=True)
            if not confirm:
                console.print("[dim]Operation cancelled.[/dim]")
                continue

        success, msg, _ = free_port(port_num)
        if success:
            console.print(f"[bold green][{ICON_SUCCESS}] {msg}[/bold green]")
        else:
            console.print(f"[bold red][{ICON_ERROR}] {msg}[/bold red]")


@app.command("heavy", help="Scan and rank the heaviest development, AI, and background processes by RAM usage.")
def heavy_cmd(
    limit: int = typer.Option(10, "--limit", "-n", help="Number of processes to display"),
):
    """Finds top memory-consuming dev and background processes."""
    candidates = []

    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            pid = proc.info["pid"]
            name = proc.info["name"] or ""
            if pid <= 4 or is_system_process(pid, name):
                continue

            # Target dev processes, python, node, AI models, electron apps, media
            name_lower = name.lower()
            is_relevant = (
                any(dev in name_lower for dev in DEV_PROCESS_NAMES)
                or "code" in name_lower
                or "spotify" in name_lower
                or "antigravity" in name_lower
                or "postgres" in name_lower
                or "mysql" in name_lower
                or "ollama" in name_lower
                or "qdrant" in name_lower
                or "torch" in name_lower
            )

            if not is_relevant:
                continue

            mem_mb = proc.memory_info().rss / (1024 * 1024)
            if mem_mb < 20.0:
                continue

            ctx = lookup_port_context(0, name, " ".join(proc.info.get("cmdline") or []))

            # Check if zombie
            is_zomb = False
            try:
                ppid = proc.ppid()
                if ppid <= 4 or not psutil.pid_exists(ppid):
                    is_zomb = True
            except Exception:
                pass

            candidates.append({
                "pid": pid,
                "name": name,
                "category": ctx.category,
                "memory_mb": mem_mb,
                "cpu_percent": proc.cpu_percent(interval=0),
                "is_zombie": is_zomb,
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    candidates.sort(key=lambda x: x["memory_mb"], reverse=True)
    top_candidates = candidates[:limit]

    if not top_candidates:
        console.print(f"[green][{ICON_SUCCESS}] No heavy development processes detected.[/green]")
        return

    table = render_heavy_table(top_candidates)
    console.print(table)


@app.command("ai", help="Status check for local AI stack (Ollama, Vector DBs, Gradio, Streamlit).")
def ai_status_cmd():
    """Inspects status of local AI inference engines and vector databases."""
    ai_checks = [
        {"name": "Ollama LLM Server", "port": 11434, "expected_proc": "ollama"},
        {"name": "LM Studio Inference", "port": 1234, "expected_proc": "lmstudio"},
        {"name": "Qdrant Vector DB", "port": 6333, "expected_proc": "qdrant"},
        {"name": "ChromaDB Vector Store", "port": 8000, "expected_proc": "chroma"},
        {"name": "Gradio UI Server", "port": 7860, "expected_proc": "python"},
        {"name": "Streamlit App", "port": 8501, "expected_proc": "streamlit"},
        {"name": "ComfyUI Pipeline", "port": 8188, "expected_proc": "comfyui"},
    ]

    services = []
    for check in ai_checks:
        port = check["port"]
        running = is_port_in_use(port)
        info = get_port_info(port) if running else None
        details = ""
        if info:
            details = f"PID {info.pid} ({info.process_name}) · {info.memory_mb:.1f} MB"
        services.append({
            "name": check["name"],
            "port": port,
            "running": running,
            "details": details,
        })

    panel = render_ai_status(services)
    console.print(panel)


@app.command("ctx", help="Generate a clean markdown context snapshot for AI coding agents (Claude, Antigravity).")
def export_context_cmd():
    """Outputs ground-truth environment context to paste into an AI agent prompt."""
    diag = diagnose_environment()
    ports = scan_listening_ports(dev_only=True)

    lines = []
    lines.append("### Local Environment Context (via devctl)")
    lines.append(f"- **OS**: {platform.system()} {platform.release()} ({platform.machine()})")
    lines.append(f"- **Project Directory**: `{diag.project_dir}`")
    lines.append(f"- **Virtualenv**: `{diag.venv_path or 'None'}` (Python {diag.venv_version or 'N/A'})")
    lines.append(f"- **Active Shell Python**: `{diag.shell_python or 'None'}`")

    if diag.issues:
        lines.append("- **Detected Environment Issues**:")
        for iss in diag.issues:
            lines.append(f"  - {iss}")
    else:
        lines.append("- **Environment Health**: Fully aligned (no PATH mismatches)")

    lines.append("- **Active Development Ports**:")
    dev_ports = [p for p in ports if not p.is_system]
    if dev_ports:
        for p in dev_ports[:8]:
            lines.append(f"  - Port {p.port}: {p.process_name} (PID {p.pid}) [{p.category}] - {p.purpose}")
    else:
        lines.append("  - No active dev ports listening.")

    console.print("\n".join(lines))


@app.command("zombies", help="Scan and prune lingering/orphaned development processes.")
def handle_zombies(
    prune: bool = typer.Option(False, "--prune", "-p", help="Immediately prune all detected zombies without prompting"),
):
    """Finds dev processes whose parent PID has died and cleans them up."""
    all_ports = scan_listening_ports()
    zombies = [p for p in all_ports if p.is_zombie and not p.is_system and p.pid is not None]

    if not zombies:
        console.print(f"[bold green][{ICON_SUCCESS}] Clean system: No orphaned zombie dev processes detected.[/bold green]")
        return

    console.print(f"[bold yellow][{ICON_WARN}] Detected {len(zombies)} orphaned zombie dev process(es):[/bold yellow]")
    for z in zombies:
        console.print(f"  {MARK_BULLET} Port [bold cyan]{z.port}[/bold cyan] · PID [yellow]{z.pid}[/yellow] ({z.process_name}) · {z.memory_mb} MB")

    if not prune:
        confirm = typer.confirm(f"Terminate all {len(zombies)} zombie process(es)?", default=True)
        if not confirm:
            console.print("[dim]Aborted.[/dim]")
            return

    pruned = prune_zombies()
    console.print(f"[bold green][{ICON_SUCCESS}] Successfully cleaned up {len(pruned)} zombie process(es).[/bold green]")


@app.command("doctor", help="Run 5-point environment health audit on local Python and virtualenv.")
def doctor_cmd():
    """Diagnoses PATH desyncs, missing virtualenvs, and pip/python alignment."""
    diag = diagnose_environment()
    panel = render_doctor_panel(diag)
    console.print(panel)


@app.command("py", help="Catalog all Python runtimes installed across your machine.")
def catalog_pythons():
    """Lists Windows py launcher runtimes, MSYS2, PATH pythons, and local venvs."""
    runtimes = discover_system_pythons()
    if not runtimes:
        console.print("[yellow]No Python runtimes could be automatically discovered.[/yellow]")
        return

    table = render_pythons_table(runtimes)
    console.print(table)


@app.command("run", context_settings={"allow_extra_args": True, "ignore_unknown_options": True}, help="Execute a command directly inside the local project .venv without activation.")
def run_cmd(
    ctx: typer.Context,
):
    """Auto-routes any command into the local virtual environment."""
    args = ctx.args
    if not args:
        console.print("[yellow]Usage: devctl run <command> [args...][/yellow]")
        console.print("Example: `devctl run uvicorn dummy_api:app --reload` or `devctl run pytest`")
        raise typer.Exit(code=1)

    exit_code = run_in_venv(args)
    raise typer.Exit(code=exit_code)


@app.command("add", help="Safely install a Python package into the project's .venv and record in requirements.txt.")
def add_package_cmd(
    package: str = typer.Argument(..., help="Package name to install (e.g. 'requests' or 'fastapi>=0.110')"),
):
    """Guarantees pip installs directly to the local .venv, never polluting global Python."""
    console.print(f"[dim]Installing '{package}' into local virtual environment...[/dim]")
    success, msg = safe_add_package(package)
    if success:
        console.print(f"[bold green][{ICON_SUCCESS}] {msg}[/bold green]")
    else:
        console.print(f"[bold red][{ICON_ERROR}] {msg}[/bold red]")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
