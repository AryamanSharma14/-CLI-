"""
Safe process termination engine.
Implements two-stage graceful shutdown (SIGTERM -> timeout -> SIGKILL),
system process safety enforcement, and child process tree cleanup.
"""

from typing import Tuple, List, Optional
import time
import psutil

from .models import PortInfo
from .security import (
    is_system_process,
    verify_process_identity,
    SecurityError,
    validate_port,
)
from .ports import get_port_info, scan_listening_ports


def terminate_process(
    pid: int,
    timeout_seconds: float = 1.5,
    expected_name: Optional[str] = None,
    expected_create_time: Optional[float] = None,
) -> bool:
    """
    Safely terminates a process and its children.
    Enforces security guards:
    1. Rejects protected system PIDs and OS components.
    2. Verifies process identity to prevent TOCTOU PID recycling.
    3. Attempts graceful termination first, escalating to SIGKILL only if needed.
    """
    if not psutil.pid_exists(pid):
        return True

    try:
        proc = psutil.Process(pid)
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return True

    proc_name = proc.name()

    # 1. System process check
    if is_system_process(pid, proc_name):
        raise SecurityError(
            f"Cannot terminate process '{proc_name}' (PID {pid}): It is a protected system component."
        )

    # 2. TOCTOU identity check
    if expected_create_time is not None and expected_name is not None:
        if not verify_process_identity(proc, expected_create_time, expected_name):
            raise SecurityError(
                f"Process identity mismatch for PID {pid}. The original process may have exited and the PID was recycled."
            )

    # Collect children first so we don't leave orphans behind
    try:
        children = proc.children(recursive=True)
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        children = []

    # 3. Stage 1: Graceful termination
    try:
        proc.terminate()
        for child in children:
            try:
                child.terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return True

    # Wait for clean exit
    gone, alive = psutil.wait_procs([proc] + children, timeout=timeout_seconds)

    # 4. Stage 2: Force kill if any process is still alive
    if alive:
        for p in alive:
            try:
                p.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        psutil.wait_procs(alive, timeout=1.0)

    return not proc.is_running()


def free_port(
    port: int,
    timeout_seconds: float = 1.5,
) -> Tuple[bool, str, Optional[PortInfo]]:
    """
    Frees a network port by safely terminating its listening process.
    Returns (success: bool, message: str, port_info: Optional[PortInfo]).
    """
    port = validate_port(port)
    info = get_port_info(port)

    if not info:
        return True, f"Port {port} is already free.", None

    if info.pid is None:
        return False, f"Port {port} is occupied, but no process ID could be determined.", info

    if info.is_system:
        return (
            False,
            f"Port {port} is occupied by protected system process '{info.process_name}' (PID {info.pid}). Operation blocked.",
            info,
        )

    try:
        terminated = terminate_process(
            pid=info.pid,
            timeout_seconds=timeout_seconds,
            expected_name=info.process_name,
            expected_create_time=info.create_time if info.create_time > 0 else None,
        )

        # Brief pause to verify socket release
        time.sleep(0.2)
        remaining = get_port_info(port)
        if remaining is None:
            return True, f"Successfully freed port {port} (stopped {info.process_name}, PID {info.pid}).", info
        else:
            return False, f"Process stopped but port {port} is still in TIME_WAIT or occupied by another listener.", info

    except SecurityError as se:
        return False, str(se), info
    except Exception as e:
        return False, f"Failed to free port {port}: {str(e)}", info


def prune_zombies() -> List[PortInfo]:
    """
    Scans all active listening ports, identifies zombie/orphaned dev processes,
    and terminates them. Returns the list of cleaned up PortInfo objects.
    """
    all_ports = scan_listening_ports()
    zombies = [p for p in all_ports if p.is_zombie and not p.is_system and p.pid is not None]

    pruned: List[PortInfo] = []
    for z in zombies:
        try:
            if z.pid and terminate_process(z.pid, expected_name=z.process_name, expected_create_time=z.create_time):
                pruned.append(z)
        except Exception:
            continue

    return pruned
