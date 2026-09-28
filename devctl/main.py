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
from .core.process import free_port, prune_zombies, terminate_process
from .core.catalog import lookup_port_context
from .core.env import diagnose_environment, discover_system_pythons
from .core.runner import run_in_venv, safe_add_package
from .core.security import validate_port, is_privileged_port, is_system_process
from .core.models import PortInfo
from .ui.formatters import (
    render_ports_table,
    render_explain_panel,
    render_suggestions_panel,
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

        # Smart action suggestions
        suggestions = render_suggestions_panel(ports)
        console.print(suggestions)

        zombie_count = sum(1 for p in ports if p.is_zombie and not p.is_system)
        summary = f"\n[dim]Found {len(ports)} active listening port(s)"
        if zombie_count > 0:
            summary += f" · [bold yellow]{zombie_count} orphaned zombie(s) detected![/bold yellow] (Run `devctl zombies` to clean)"
        summary += " · Run `devctl explain <target>` for in-depth advice.[/dim]"
        console.print(summary)

    except ValueError as ve:
        console.print(f"[bold red][{ICON_ERROR}] {str(ve)}[/bold red]")
        raise typer.Exit(code=1)


@app.command("explain", help="Analyze what a specific port, PID, or process does in plain English.")
def explain_port_cmd(
    target: str = typer.Argument(..., help="Port number (e.g. 3000), PID (e.g. 30828), or process name (e.g. 'spotify')"),
):
    """Provides plain English explanation, safety verdict, and recommendation for any port or process."""
    target_clean = target.strip()

    if target_clean.isdigit():
        num = int(target_clean)
        # 1. Check if active listening port
        port_info = get_port_info(num) if (1 <= num <= 65535) else None

        # 2. Check if active running PID
        pid_proc = None
        if psutil.pid_exists(num):
            try:
                pid_proc = psutil.Process(num)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pid_proc = None

        if port_info is not None:
            ctx = lookup_port_context(num, port_info.process_name, port_info.cmdline, pid=port_info.pid)
            panel = render_explain_panel(ctx, port_info, target_label=f"Port {num}")
            console.print(panel)
            return
        elif pid_proc is not None:
            try:
                p_name = pid_proc.name()
                cmdline = " ".join(pid_proc.cmdline())
                cwd = pid_proc.cwd()
                mem_mb = round(pid_proc.memory_info().rss / (1024 * 1024), 1)
            except Exception:
                p_name = "Unknown"
                cmdline = ""
                cwd = ""
                mem_mb = 0.0

            all_ports = scan_listening_ports()
            bound_ports = [p.port for p in all_ports if p.pid == num]
            primary_port = bound_ports[0] if bound_ports else 0

            info = PortInfo(
                port=primary_port,
                protocol="tcp" if primary_port > 0 else "-",
                status="LISTEN" if primary_port > 0 else "RUNNING",
                pid=num,
                process_name=p_name,
                cmdline=cmdline,
                cwd=cwd,
                memory_mb=mem_mb,
            )
            ctx = lookup_port_context(primary_port, p_name, cmdline, pid=num)
            panel = render_explain_panel(ctx, info, target_label=f"PID {num} ({p_name})")
            console.print(panel)
            return
        elif 1 <= num <= 65535:
            ctx = lookup_port_context(num, "", "")
            panel = render_explain_panel(ctx, None, target_label=f"Port {num} (Inactive)")
            console.print(panel)
            return
        else:
            console.print(f"[bold red][{ICON_ERROR}] '{num}' is neither a running PID nor a valid port (1-65535).[/bold red]")
            raise typer.Exit(code=1)

    # Process name target (e.g. "spotify", "antigravity", "postgres", "node")
    target_lower = target_clean.lower()
    matching_procs = []
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            name = (proc.info["name"] or "").lower()
            if target_lower in name:
                matching_procs.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if matching_procs:
        main_proc = matching_procs[0]
        try:
            p_name = main_proc.name()
            p_pid = main_proc.pid
            p_cmdline = " ".join(main_proc.cmdline())
            p_cwd = main_proc.cwd()
            p_mem = sum(p.memory_info().rss / (1024 * 1024) for p in matching_procs)
        except Exception:
            p_name = target_clean
            p_pid = matching_procs[0].pid
            p_cmdline = ""
            p_cwd = ""
            p_mem = 0.0

        all_ports = scan_listening_ports()
        pids_set = {p.pid for p in matching_procs}
        bound_ports = [p.port for p in all_ports if p.pid in pids_set]
        primary_port = bound_ports[0] if bound_ports else 0

        info = PortInfo(
            port=primary_port,
            protocol="tcp" if primary_port > 0 else "-",
            status="LISTEN" if primary_port > 0 else "RUNNING",
            pid=p_pid,
            process_name=p_name,
            cmdline=p_cmdline,
            cwd=p_cwd,
            memory_mb=round(p_mem, 1),
        )
        ctx = lookup_port_context(primary_port, p_name, p_cmdline, pid=p_pid)
        count_desc = f" ({len(matching_procs)} instances, primary PID {p_pid})" if len(matching_procs) > 1 else f" (PID {p_pid})"
        panel = render_explain_panel(ctx, info, target_label=f"{p_name}{count_desc}")
        console.print(panel)
    else:
        ctx = lookup_port_context(0, target_clean, "")
        info = PortInfo(
            port=0,
            protocol="-",
            status="NOT_RUNNING",
            process_name=target_clean,
        )
        panel = render_explain_panel(ctx, info, target_label=f"{target_clean} (Not Currently Running)")
        console.print(panel)


@app.command("free", help="Safely free one or more occupied ports, PIDs, or process names.")
def free_ports_cmd(
    targets: List[str] = typer.Argument(..., help="One or more ports, PIDs, or process names (e.g. 8000, 30828, or spotify)"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
    force: bool = typer.Option(False, "--force", "-f", help="Force termination on privileged ports (<1024)"),
):
    """Frees ports or terminates processes using two-stage termination with TOCTOU race protection."""
    for target in targets:
        target_clean = target.strip()
        if target_clean.isdigit():
            num = int(target_clean)
            if 1 <= num <= 65535 and is_port_in_use(num):
                info = get_port_info(num)
                if not info:
                    console.print(f"[green][{ICON_SUCCESS}] Port {num} is already free.[/green]")
                    continue

                if info.is_system:
                    console.print(
                        f"[bold red][{ICON_ERROR}] Cannot free port {num}: Occupied by protected system process '{info.process_name}' (PID {info.pid}).[/bold red]"
                    )
                    continue

                if is_privileged_port(num) and not force:
                    console.print(
                        f"[bold yellow][{ICON_WARN}] Port {num} is a privileged system port (< 1024). Use --force to proceed.[/bold yellow]"
                    )
                    continue

                console.print(f"\n[bold cyan]Target on Port {num}:[/bold cyan]")
                console.print(f"  {MARK_BULLET} Process  : [bold white]{info.process_name}[/bold white] (PID {info.pid})")
                if info.purpose:
                    console.print(f"  {MARK_BULLET} Context  : [white]{info.purpose}[/white]")
                if info.memory_mb > 0:
                    console.print(f"  {MARK_BULLET} Memory   : [green]{info.memory_mb:.1f} MB[/green]")

                if not yes:
                    confirm = typer.confirm(f"Terminate process '{info.process_name}' to free port {num}?", default=True)
                    if not confirm:
                        console.print("[dim]Operation cancelled.[/dim]")
                        continue

                success, msg, _ = free_port(num)
                if success:
                    console.print(f"[bold green][{ICON_SUCCESS}] {msg}[/bold green]")
                else:
                    console.print(f"[bold red][{ICON_ERROR}] {msg}[/bold red]")
                continue

            elif psutil.pid_exists(num):
                # Free by PID
                try:
                    p = psutil.Process(num)
                    p_name = p.name()
                    p_mem = round(p.memory_info().rss / (1024 * 1024), 1)
                except Exception:
                    p_name = "Unknown"
                    p_mem = 0.0

                if is_system_process(num, p_name):
                    console.print(f"[bold red][{ICON_ERROR}] Cannot terminate PID {num}: Protected system component '{p_name}'.[/bold red]")
                    continue

                if "antigravity" in p_name.lower() and not force:
                    console.print(f"[bold red][{ICON_ERROR}] Process '{p_name}' (PID {num}) is your active code editor! Use --force if you genuinely want to close it.[/bold red]")
                    continue

                console.print(f"\n[bold cyan]Target Process PID {num}:[/bold cyan]")
                console.print(f"  {MARK_BULLET} Process  : [bold white]{p_name}[/bold white]")
                if p_mem > 0:
                    console.print(f"  {MARK_BULLET} Memory   : [green]{p_mem:.1f} MB[/green]")

                if not yes:
                    confirm = typer.confirm(f"Terminate process '{p_name}' (PID {num})?", default=True)
                    if not confirm:
                        console.print("[dim]Operation cancelled.[/dim]")
                        continue

                try:
                    terminate_process(num)
                    console.print(f"[bold green][{ICON_SUCCESS}] Successfully terminated process '{p_name}' (PID {num}). Freeing {p_mem:.1f} MB RAM.[/bold green]")
                except Exception as e:
                    console.print(f"[bold red][{ICON_ERROR}] Failed to terminate PID {num}: {str(e)}[/bold red]")
                continue

            elif 1 <= num <= 65535:
                console.print(f"[green][{ICON_SUCCESS}] Port {num} is already free.[/green]")
                continue
            else:
                console.print(f"[bold red][{ICON_ERROR}] '{num}' is neither an active port nor a running PID.[/bold red]")
                continue

        # Target by process name (e.g. "spotify", "onedrive")
        target_lower = target_clean.lower()
        matching_procs = []
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                name = (proc.info["name"] or "").lower()
                if target_lower in name:
                    if not is_system_process(proc.info["pid"], name):
                        matching_procs.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        if not matching_procs:
            console.print(f"[yellow]No non-system running processes found matching '{target_clean}'.[/yellow]")
            continue

        total_mem = 0.0
        pids = []
        for proc in matching_procs:
            try:
                total_mem += proc.memory_info().rss / (1024 * 1024)
                pids.append(proc.pid)
            except Exception:
                pass

        proc_label = matching_procs[0].name()
        console.print(f"\n[bold cyan]Target Process '{target_clean}':[/bold cyan]")
        console.print(f"  {MARK_BULLET} Instances : {len(matching_procs)} process(es) (PIDs: {', '.join(map(str, pids[:5]))}{'...' if len(pids) > 5 else ''})")
        console.print(f"  {MARK_BULLET} Reclaim   : [green]~{total_mem:.1f} MB RAM[/green]")

        if not yes:
            confirm = typer.confirm(f"Terminate all {len(matching_procs)} '{proc_label}' process(es)?", default=True)
            if not confirm:
                console.print("[dim]Operation cancelled.[/dim]")
                continue

        killed = 0
        for pid in pids:
            try:
                if terminate_process(pid):
                    killed += 1
            except Exception:
                pass

        console.print(f"[bold green][{ICON_SUCCESS}] Successfully terminated {killed}/{len(pids)} process(es) for '{target_clean}'. Reclaimed ~{total_mem:.1f} MB RAM.[/bold green]")


@app.command("summary", help="Quick executive summary of RAM usage, active dev servers, and safe-to-kill bloat.")
@app.command("digest", hidden=True)
def summary_cmd():
    """Generates an instant high-level digest for vibe coders and developers."""
    all_ports = scan_listening_ports(dev_only=False)
    panel = render_suggestions_panel(all_ports)
    console.print(panel)


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
