"""
Security and system safety guards for devctl.
Prevents accidental termination of OS processes, TOCTOU PID reuse race conditions,
and command injection.
"""

from typing import Set
import psutil

# Immutable set of protected operating system process names (case-insensitive)
PROTECTED_PROCESS_NAMES: Set[str] = {
    # Windows core subsystems
    "system",
    "system idle process",
    "registry",
    "smss.exe",
    "csrss.exe",
    "wininit.exe",
    "services.exe",
    "lsass.exe",
    "svchost.exe",
    "fontdrvhost.exe",
    "dwm.exe",
    "explorer.exe",
    "spoolsv.exe",
    "conhost.exe",
    "winlogon.exe",
    "sihost.exe",
    "taskhostw.exe",
    "searchindexer.exe",
    "securityhealthservice.exe",
    
    # Unix/macOS core subsystems
    "systemd",
    "init",
    "kthreadd",
    "launchd",
    "sshd",
    "dockerd",
    "containerd",
}

# Critical system PIDs that can never be terminated
PROTECTED_PIDS: Set[int] = {0, 1, 4}


class SecurityError(Exception):
    """Raised when an operation violates security or system safety policies."""
    pass


def is_system_process(pid: int, name: str) -> bool:
    """
    Check if a process is a protected operating system component.
    """
    if pid in PROTECTED_PIDS or pid <= 4:
        return True
    
    clean_name = (name or "").lower().strip()
    if clean_name in PROTECTED_PROCESS_NAMES:
        return True
    
    # Also check if name ends with any protected name (e.g. C:\Windows\System32\svchost.exe)
    for protected in PROTECTED_PROCESS_NAMES:
        if clean_name == protected or clean_name.endswith("\\" + protected) or clean_name.endswith("/" + protected):
            return True
            
    return False


def validate_port(port: int) -> int:
    """
    Validate that a port number is within the legitimate TCP/UDP range (1-65535).
    Raises ValueError on invalid input.
    """
    if not isinstance(port, int):
        try:
            port = int(port)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid port value '{port}'. Port must be an integer between 1 and 65535.")
            
    if port < 1 or port > 65535:
        raise ValueError(f"Port {port} is out of valid range (1 - 65535).")
        
    return port


def is_privileged_port(port: int) -> bool:
    """Returns True if the port is in the system privileged range (< 1024)."""
    return 1 <= port < 1024


def verify_process_identity(
    proc: psutil.Process, 
    expected_create_time: float, 
    expected_name: str,
    time_tolerance_seconds: float = 1.0
) -> bool:
    """
    Guards against TOCTOU (Time-of-Check to Time-of-Use) PID recycling.
    Verifies that the process currently occupying the PID is the EXACT same process
    that was inspected originally by comparing creation time and executable name.
    """
    try:
        if not proc.is_running():
            return False
            
        current_create_time = proc.create_time()
        if abs(current_create_time - expected_create_time) > time_tolerance_seconds:
            return False
            
        current_name = proc.name().lower()
        clean_expected = expected_name.lower()
        if current_name != clean_expected and not current_name.startswith(clean_expected):
            return False
            
        return True
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return False
