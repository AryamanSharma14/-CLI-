"""
Network port scanning and socket listener inspection module.
Inspects active TCP listeners, identifies the bound process, working directory,
command line, and detects orphaned/zombie states.
"""

from typing import List, Optional
import os
import psutil

from .models import PortInfo
from .security import is_system_process, validate_port


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

        if dev_only and info.is_system and port >= 49152:
            # Skip Windows dynamic RPC ephemeral ports for system daemons
            continue

        results.append(info)

    # Sort results by port ascending
    results.sort(key=lambda x: x.port)
    return results


def get_port_info(port: int) -> Optional[PortInfo]:
    """Retrieve process information for a specific port, if listening."""
    ports = scan_listening_ports(port_filter=port)
    return ports[0] if ports else None


def is_port_in_use(port: int) -> bool:
    """Returns True if the specified port currently has an active listener."""
    return get_port_info(port) is not None
