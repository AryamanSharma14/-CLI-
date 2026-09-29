"""
Network port scanning and socket listener inspection module.
Inspects active TCP listeners, identifies the bound process, working directory,
command line, and detects orphaned/zombie states.
"""

from typing import List, Optional, Tuple
import os
import psutil

from .models import PortInfo
from .security import is_system_process, validate_port
from .catalog import lookup_port_context


DEV_PROCESS_NAMES = {
    "python.exe", "python", "python3.exe", "python3",
    "node.exe", "node",
    "uvicorn.exe", "uvicorn",
    "vite.exe", "vite",
    "esbuild.exe", "esbuild",
    "next.exe", "next",
    "flask.exe", "flask",
    "cargo.exe", "cargo",
    "go.exe", "go",
}


def _is_zombie_dev_process(proc: psutil.Process) -> bool:
    """
    Determines if a process is a lingering orphaned development process.
    Criteria:
    - Matches a known dev runtime (python, node, uvicorn, etc.)
    - Its parent PID no longer exists, or is an OS root (PID 0, 1, 4), or has exited.
    """
    try:
        proc_name = proc.name().lower()
        is_dev = any(dev in proc_name for dev in DEV_PROCESS_NAMES)
        if not is_dev:
            return False

        ppid = proc.ppid()
        if ppid <= 4:
            return True
        if not psutil.pid_exists(ppid):
            return True
        parent = psutil.Process(ppid)
        if not parent.is_running():
            return True
        return False
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return True


def scan_listening_ports(port_filter: Optional[int] = None, dev_only: bool = False) -> List[PortInfo]:
    """
    Scan all active listening TCP ports and gather rich process metadata.
    If dev_only is True, filters out high Windows ephemeral RPC ports (>49000)
    owned by system processes like svchost/lsass to reduce noise.
    """
    if port_filter is not None:
        port_filter = validate_port(port_filter)

    results: List[PortInfo] = []
    seen_ports = set()

    try:
        connections = psutil.net_connections(kind="inet")
    except (psutil.AccessDenied, PermissionError):
        # On some restricted platforms, fallback to tcp4/tcp6
        try:
            connections = psutil.net_connections(kind="tcp4")
        except Exception:
            connections = []

    for conn in connections:
        if conn.status != psutil.CONN_LISTEN:
            continue

        laddr = conn.laddr
        if not laddr:
            continue

        port = laddr.port
        if port_filter is not None and port != port_filter:
            continue

        if port in seen_ports:
            continue
        seen_ports.add(port)

        pid = conn.pid
        info = PortInfo(
            port=port,
            protocol="tcp",
            status="LISTEN",
            pid=pid,
        )

        if pid is not None:
            try:
                proc = psutil.Process(pid)
                info.process_name = proc.name()
                info.create_time = proc.create_time()
                info.memory_mb = round(proc.memory_info().rss / (1024 * 1024), 1)

                try:
                    cmdline = proc.cmdline()
                    info.cmdline = " ".join(cmdline) if cmdline else info.process_name
                except (psutil.AccessDenied, psutil.ZombieProcess):
                    info.cmdline = info.process_name

                try:
                    info.cwd = proc.cwd()
                except (psutil.AccessDenied, psutil.ZombieProcess):
                    info.cwd = ""

                info.is_system = is_system_process(pid, info.process_name)
                info.is_zombie = _is_zombie_dev_process(proc)

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                info.process_name = "System/Protected" if pid <= 4 else "Exited/Zombie"
                info.is_system = is_system_process(pid, info.process_name)

        # Contextual intelligence lookup
        ctx = lookup_port_context(port, info.process_name, info.cmdline, pid=info.pid)
        info.category = ctx.category
        info.purpose = ctx.purpose

        if dev_only and info.is_system and port >= 49152:
            # Skip Windows dynamic RPC ephemeral ports for system daemons
            continue

        results.append(info)

    # Sort results by port ascending
    results.sort(key=lambda x: x.port)
    return results


def filter_visible_ports(
    ports: List[PortInfo],
    include_all: bool = False,
    bloat_only: bool = False,
) -> Tuple[List[PortInfo], int]:
    """
    Filters out noise like internal IDE/editor loopback IPC sockets (> 1024)
    and ephemeral Windows RPC system sockets to keep the CLI clean and focused.
    Returns (visible_ports, hidden_count).
    """
    if bloat_only:
        bloat_ports = [
            p for p in ports
            if p.category == "BACKGROUND"
            or "spotify" in (p.process_name or "").lower()
            or "onedrive" in (p.process_name or "").lower()
        ]
        return bloat_ports, max(0, len(ports) - len(bloat_ports))

    if include_all:
        return ports, 0

    visible = []
    hidden_count = 0
    for p in ports:
        # Hide internal IDE/editor loopback sockets (VS Code, Antigravity, language servers on ephemeral ports)
        if p.category == "IDE" and p.port >= 1024:
            hidden_count += 1
        elif p.is_system and p.port >= 49152:
            hidden_count += 1
        else:
            visible.append(p)

    return visible, hidden_count


def get_port_info(port: int) -> Optional[PortInfo]:
    """Retrieve process information for a specific port, if listening."""
    ports = scan_listening_ports(port_filter=port)
    return ports[0] if ports else None


def is_port_in_use(port: int) -> bool:
    """Returns True if the specified port currently has an active listener."""
    return get_port_info(port) is not None


DEV_SERVER_KEYWORDS = {
    "node", "vite", "next", "webpack", "esbuild", "nodemon",
    "astro", "remix", "tsx", "ts-node", "uvicorn", "gunicorn",
    "flask", "fastapi", "django", "streamlit", "gradio",
    "celery", "air", "cargo-watch"
}

DATABASE_KEYWORDS = {
    "postgres", "mysqld", "mongod", "redis", "clickhouse", "mariadb", "cockroach"
}

IDE_KEYWORDS = {
    "antigravity", "code", "cursor", "windsurf", "pycharm", "idea", "sublime", "fleet", "zed"
}


def is_ancestor_or_self_process(pid: Optional[int]) -> bool:
    """Returns True if the pid belongs to current process or any of its parent processes."""
    if pid is None or pid <= 0:
        return True
    try:
        curr = psutil.Process(os.getpid())
        if curr.pid == pid:
            return True
        for p in curr.parents():
            if p.pid == pid:
                return True
    except Exception:
        pass
    return False


def find_dev_servers(ports: Optional[List[PortInfo]] = None) -> List[PortInfo]:
    """
    Finds active listening ports running development servers (Node, Vite, Next, Uvicorn, Flask, etc.)
    Strictly shields system processes, databases, and code editors/IDEs.
    """
    if ports is None:
        ports = scan_listening_ports()

    dev_servers: List[PortInfo] = []

    for p in ports:
        if p.is_system or not p.pid:
            continue
        if is_ancestor_or_self_process(p.pid):
            continue

        p_name = (p.process_name or "").lower()
        cmd = (p.cmdline or "").lower()
        category = (p.category or "").upper()

        # Hard exclusions
        if category in ("SYSTEM", "DATABASE", "IDE"):
            continue
        if any(db in p_name for db in DATABASE_KEYWORDS):
            continue
        if any(ide in p_name for ide in IDE_KEYWORDS):
            continue

        # Inclusion criteria:
        is_dev = (
            category == "DEV"
            or any(kw in p_name for kw in DEV_SERVER_KEYWORDS)
            or any(kw in cmd for kw in DEV_SERVER_KEYWORDS)
            or "runserver" in cmd
            or "app.py" in cmd
            or "server.py" in cmd
            or "main.py" in cmd
        )

        if is_dev:
            dev_servers.append(p)

    return dev_servers

