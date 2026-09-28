"""
Rich table and panel formatters for devctl.
High-density, professional developer aesthetics with zero cartoonish emojis.
"""

from typing import List, Optional
from rich.table import Table
from rich.panel import Panel
from rich import box

from ..core.models import PortInfo, PythonRuntime, EnvDiagnosis
from ..core.catalog import PortContext
from .theme import (
    BADGE_ACTIVE,
    BADGE_ZOMBIE,
    BADGE_SYSTEM,
    CAT_SYSTEM,
    CAT_DATABASE,
    CAT_AI_LLM,
    CAT_VECTOR_DB,
    CAT_AI_UI,
    CAT_IDE,
    CAT_DEV_SERVER,
    CAT_BACKGROUND,
    CAT_REMOTE,
    ICON_SUCCESS,
    ICON_ERROR,
    ICON_WARN,
    MARK_BULLET,
)


def _format_category(cat: str) -> str:
    """Format category with clean terminal styling."""
    c = cat.upper()
    if c == "SYSTEM":
        return CAT_SYSTEM
    if c == "DATABASE":
        return CAT_DATABASE
    if c in ("AI_LLM", "AI/LLM"):
        return CAT_AI_LLM
    if c == "VECTOR_DB":
        return CAT_VECTOR_DB
    if c in ("AI_UI", "AI_IMAGE"):
        return CAT_AI_UI
    if c in ("IDE", "IDE/LSP", "LSP"):
        return CAT_IDE
    if c == "DEV_SERVER":
        return CAT_DEV_SERVER
    if c == "BACKGROUND":
        return CAT_BACKGROUND
    if c == "REMOTE":
        return CAT_REMOTE
    return f"[dim]{cat}[/dim]"


def _truncate_str(val: str, max_len: int = 36) -> str:
    """Compact string truncation."""
    if not val or len(val) <= max_len:
        return val or "-"
    return val[: max_len - 3] + "..."


def render_ports_table(ports: List[PortInfo]) -> Table:
    """Renders a clean, context-rich table of active ports with category and purpose."""
    table = Table(
        title="[bold cyan]Active Listening Ports & Runtime Processes[/bold cyan]",
        box=box.ROUNDED,
        header_style="bold white on #1a1a2e",
        show_lines=False,
        expand=False,
    )

    table.add_column("PORT", style="bold cyan", justify="right", min_width=6, no_wrap=True)
    table.add_column("STATUS", justify="center", min_width=8, no_wrap=True)
    table.add_column("CATEGORY", justify="center", min_width=11, no_wrap=True)
    table.add_column("PID", style="yellow", justify="right", min_width=6, no_wrap=True)
    table.add_column("PROCESS", style="bold white", min_width=13, max_width=18, overflow="ellipsis", no_wrap=True)
    table.add_column("PURPOSE / CONTEXT", style="white", min_width=24, max_width=38, overflow="ellipsis", no_wrap=True)
    table.add_column("RAM", justify="right", style="green", min_width=8, no_wrap=True)

    for p in ports:
        if p.is_system:
            badge = BADGE_SYSTEM
        elif p.is_zombie:
            badge = BADGE_ZOMBIE
        else:
            badge = BADGE_ACTIVE

        pid_str = str(p.pid) if p.pid is not None else "-"
        mem_str = f"{p.memory_mb:.1f} MB" if p.memory_mb > 0 else "-"
        cat_badge = _format_category(p.category)
        purpose_str = p.purpose or p.cmdline or p.process_name

        table.add_row(
            str(p.port),
            badge,
            cat_badge,
            pid_str,
            p.process_name,
            _truncate_str(purpose_str, max_len=38),
            mem_str,
        )

    return table


def render_explain_panel(ctx: PortContext, info: Optional[PortInfo] = None) -> Panel:
    """Renders in-depth technical explanation and safety advice for a target port."""
    lines = []

    lines.append(f"[bold cyan]PORT {ctx.port}[/bold cyan] :: {_format_category(ctx.category)}")
    if info and info.pid:
        lines.append(f"  {MARK_BULLET} Process       : [bold white]{info.process_name}[/bold white] (PID {info.pid})")
        if info.memory_mb > 0:
            lines.append(f"  {MARK_BULLET} Memory Footprint: [green]{info.memory_mb:.1f} MB[/green]")
        if info.cwd:
            lines.append(f"  {MARK_BULLET} Working Dir   : [dim]{info.cwd}[/dim]")
        if info.cmdline:
            lines.append(f"  {MARK_BULLET} Command       : [dim]{info.cmdline}[/dim]")

    lines.append("")
    lines.append(f"[bold white]TECHNICAL PURPOSE:[/bold white]")
    lines.append(f"  {ctx.purpose}")

    lines.append("")
    lines.append(f"[bold white]SAFETY VERDICT:[/bold white]")
    if ctx.safety_verdict == "PROTECTED":
        verdict_str = "[bold red][PROTECTED - DO NOT TERMINATE][/bold red]"
    elif ctx.safety_verdict == "SAFE_TO_KILL":
        verdict_str = "[bold green][SAFE TO TERMINATE][/bold green]"
    elif ctx.safety_verdict == "DEV_TARGET":
        verdict_str = "[bold yellow][ACTIVE DEV SERVER - TARGET ON CONFLICT][/bold yellow]"
    else:
        verdict_str = "[bold cyan][CONDITIONAL - KEEP IF USING][/bold cyan]"

    lines.append(f"  {verdict_str}")
    lines.append(f"  {ctx.recommendation}")

    return Panel(
        "\n".join(lines),
        title=f"[bold cyan]devctl explain · Port {ctx.port}[/bold cyan]",
        border_style="cyan",
        box=box.ROUNDED,
    )


def render_heavy_table(processes: List[dict]) -> Table:
    """Renders table of top RAM/CPU-heavy processes."""
    table = Table(
        title="[bold cyan]Heavy Development & Background Processes[/bold cyan]",
        box=box.ROUNDED,
        header_style="bold white on #1a1a2e",
    )

    table.add_column("PID", style="yellow", justify="right", width=8)
    table.add_column("PROCESS", style="bold white", width=18)
    table.add_column("CATEGORY", justify="center", width=12)
    table.add_column("RAM USAGE", justify="right", style="green", width=12)
    table.add_column("CPU %", justify="right", style="cyan", width=8)
    table.add_column("STATUS", justify="center", width=10)

    for p in processes:
        table.add_row(
            str(p["pid"]),
            p["name"],
            _format_category(p.get("category", "DEV")),
            f"{p['memory_mb']:.1f} MB",
            f"{p.get('cpu_percent', 0.0):.1f}%",
            BADGE_ZOMBIE if p.get("is_zombie") else BADGE_ACTIVE,
        )

    return table


def render_ai_status(services: List[dict]) -> Panel:
    """Renders status check for local LLM, vector DB, and ML runtimes."""
    lines = []
    lines.append("[bold cyan]LOCAL AI & ML RUNTIME STATUS[/bold cyan]")
    lines.append("")

    for s in services:
        name = s["name"]
        port = s["port"]
        running = s["running"]
        details = s.get("details", "")

        status_str = "[bold green]ONLINE[/bold green]" if running else "[dim]OFFLINE[/dim]"
        desc = f"[white]{name}[/white] (Port {port})"
        if details:
            desc += f" [dim]· {details}[/dim]"

        lines.append(f"  [{status_str:^7}] {desc}")

    lines.append("")
    lines.append("[dim]Run `devctl ports -p <port>` to view process details or `devctl free <port>` to release.[/dim]")

    return Panel(
        "\n".join(lines),
        title="[bold cyan]devctl ai · Local AI Stack[/bold cyan]",
        border_style="cyan",
        box=box.ROUNDED,
    )


def render_pythons_table(runtimes: List[PythonRuntime]) -> Table:
    """Renders catalog table of all installed Python interpreters on the host."""
    table = Table(
        title="[bold cyan]Installed Python Runtimes Catalog[/bold cyan]",
        box=box.ROUNDED,
        header_style="bold white on #1a1a2e",
    )

    table.add_column("TAG", style="bold cyan", width=14)
    table.add_column("VERSION", style="bold white", width=10)
    table.add_column("SOURCE", style="dim", width=22)
    table.add_column("EXECUTABLE PATH", style="green")

    for r in runtimes:
        tag_display = f"* {r.tag}" if r.is_default else f"  {r.tag}"
        table.add_row(
            tag_display,
            r.version,
            r.source,
            r.executable_path,
        )

    return table


def render_doctor_panel(diag: EnvDiagnosis) -> Panel:
    """Renders 5-point environment health audit panel without emojis."""
    lines = []

    # Project Section
    lines.append("[bold cyan]PROJECT ENVIRONMENT[/bold cyan]")
    lines.append(f"  {MARK_BULLET} Directory    : [white]{diag.project_dir}[/white]")
    if diag.venv_path:
        lines.append(
            f"  {MARK_BULLET} Virtualenv   : [{ICON_SUCCESS}] Found [white]({diag.venv_path})[/white] · Python {diag.venv_version or 'Unknown'}"
        )
    else:
        lines.append(f"  {MARK_BULLET} Virtualenv   : [{ICON_WARN}] [bold yellow]No local .venv found[/bold yellow]")

    lines.append("")

    # Shell Section
    lines.append("[bold cyan]CURRENT TERMINAL SHELL[/bold cyan]")
    if diag.is_shell_in_venv:
        lines.append(f"  {MARK_BULLET} Shell State  : [{ICON_SUCCESS}] [bold green]Active in project .venv[/bold green]")
    else:
        lines.append(
            f"  {MARK_BULLET} Shell State  : [{ICON_WARN}] [bold yellow]NOT inside project .venv (running in global environment)[/bold yellow]"
        )

    lines.append(f"  {MARK_BULLET} `python` bin : [dim]{diag.shell_python or 'None'}[/dim]")
    lines.append(f"  {MARK_BULLET} `pip` bin    : [dim]{diag.shell_pip or 'None'}[/dim]")

    # Diagnosis Section
    lines.append("")
    lines.append("[bold cyan]────────────────────────────────────────────────────────────────────────[/bold cyan]")
    if diag.issues:
        lines.append(f"[bold red][{ICON_ERROR}] DIAGNOSIS: {len(diag.issues)} Issue(s) Detected[/bold red]")
        for issue in diag.issues:
            lines.append(f"  {MARK_BULLET} [red]{issue}[/red]")
    else:
        lines.append(f"[bold green][{ICON_SUCCESS}] DIAGNOSIS: Everything looks healthy and aligned.[/bold green]")

    # Recommendations Section
    if diag.recommendations:
        lines.append("")
        lines.append("[bold yellow]RECOMMENDED ACTIONS:[/bold yellow]")
        for rec in diag.recommendations:
            lines.append(f"  {MARK_BULLET} [yellow]{rec}[/yellow]")

    content = "\n".join(lines)
    return Panel(
        content,
        title="[bold cyan]devctl doctor · Environment Audit[/bold cyan]",
        border_style="cyan" if not diag.issues else "yellow",
        box=box.ROUNDED,
    )
