"""
Rich table and panel formatting for devctl CLI commands.
"""

from typing import List
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

from ..core.models import PortInfo, PythonRuntime, EnvDiagnosis
from .theme import (
    BADGE_ACTIVE,
    BADGE_ZOMBIE,
    BADGE_SYSTEM,
    ICON_SUCCESS,
    ICON_ERROR,
    ICON_WARN,
    ICON_DOCTOR,
)


def _truncate_path(path_str: str, max_len: int = 40) -> str:
    """Smartly truncate long file paths with ellipsis in the middle or prefix."""
    if not path_str or len(path_str) <= max_len:
        return path_str or "-"
    parts = path_str.replace("\\", "/").split("/")
    if len(parts) > 3:
        return f".../{parts[-2]}/{parts[-1]}"
    return f"...{path_str[-(max_len - 3):]}"


def render_ports_table(ports: List[PortInfo]) -> Table:
    """Renders a clean, scan-friendly table of active listening ports."""
    table = Table(
        title="[bold cyan]🔌 Active Listening Ports & Development Processes[/bold cyan]",
        box=box.ROUNDED,
        header_style="bold white on #1a1a2e",
        show_lines=False,
        expand=False,
    )

    table.add_column("PORT", style="bold cyan", justify="right", min_width=7, no_wrap=True)
    table.add_column("STATUS", justify="center", min_width=10, no_wrap=True)
    table.add_column("PID", style="yellow", justify="right", min_width=7, no_wrap=True)
    table.add_column("PROCESS", style="bold white", min_width=14, max_width=18, overflow="ellipsis", no_wrap=True)
    table.add_column("LOCATION / CMD", style="dim", max_width=26, overflow="ellipsis", no_wrap=True)
    table.add_column("MEMORY", justify="right", style="green", min_width=9, no_wrap=True)

    for p in ports:
        if p.is_system:
            badge = BADGE_SYSTEM
        elif p.is_zombie:
            badge = BADGE_ZOMBIE
        else:
            badge = BADGE_ACTIVE

        pid_str = str(p.pid) if p.pid is not None else "-"
        mem_str = f"{p.memory_mb:.1f} MB" if p.memory_mb > 0 else "-"

        # Prefer showing cwd or cmd
        display_location = _truncate_path(p.cwd or p.cmdline)

        table.add_row(
            str(p.port),
            badge,
            pid_str,
            p.process_name,
            display_location,
            mem_str,
        )

    return table


def render_pythons_table(runtimes: List[PythonRuntime]) -> Table:
    """Renders a catalog table of all installed Python interpreters on the host."""
    table = Table(
        title="[bold cyan]🐍 Installed Python Runtimes Catalog[/bold cyan]",
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
    """Renders the comprehensive 5-point environment health audit panel."""
    lines = []

    # Project Section
    lines.append("[bold cyan]PROJECT ENVIRONMENT[/bold cyan]")
    lines.append(f"  • Directory    : [white]{diag.project_dir}[/white]")
    if diag.venv_path:
        lines.append(
            f"  • Virtualenv   : {ICON_SUCCESS} Found [white]({diag.venv_path})[/white] · Python {diag.venv_version or 'Unknown'}"
        )
    else:
        lines.append(f"  • Virtualenv   : {ICON_WARN} [bold yellow]No local .venv found[/bold yellow]")

    lines.append("")

    # Shell Section
    lines.append("[bold cyan]CURRENT TERMINAL SHELL[/bold cyan]")
    if diag.is_shell_in_venv:
        lines.append(f"  • Shell State  : {ICON_SUCCESS} [bold green]Active in project .venv[/bold green]")
    else:
        lines.append(
            f"  • Shell State  : {ICON_WARN} [bold yellow]NOT inside project .venv (running in global environment)[/bold yellow]"
        )

    lines.append(f"  • `python` bin : [dim]{diag.shell_python or 'None'}[/dim]")
    lines.append(f"  • `pip` bin    : [dim]{diag.shell_pip or 'None'}[/dim]")

    # Diagnosis Section
    lines.append("")
    lines.append("[bold cyan]────────────────────────────────────────────────────────────────────────[/bold cyan]")
    if diag.issues:
        lines.append(f"[bold red]{ICON_ERROR} DIAGNOSIS: {len(diag.issues)} Issue(s) Detected[/bold red]")
        for issue in diag.issues:
            lines.append(f"  [red]• {issue}[/red]")
    else:
        lines.append(f"[bold green]{ICON_SUCCESS} DIAGNOSIS: Everything looks healthy and aligned![/bold green]")

    # Recommendations Section
    if diag.recommendations:
        lines.append("")
        lines.append("[bold yellow]💡 RECOMMENDED ACTIONS:[/bold yellow]")
        for rec in diag.recommendations:
            lines.append(f"  • [yellow]{rec}[/yellow]")

    content = "\n".join(lines)
    return Panel(
        content,
        title=f"[bold cyan]{ICON_DOCTOR} devctl · Environment Doctor[/bold cyan]",
        border_style="cyan" if not diag.issues else "yellow",
        box=box.ROUNDED,
    )
