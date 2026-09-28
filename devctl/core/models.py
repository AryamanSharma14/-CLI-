from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class PortInfo:
    """Represents a network port and the process bound to it."""
    port: int
    protocol: str = "tcp"
    status: str = "LISTEN"
    pid: Optional[int] = None
    process_name: str = "Unknown"
    cmdline: str = ""
    cwd: str = ""
    memory_mb: float = 0.0
    cpu_percent: float = 0.0
    create_time: float = 0.0
    is_zombie: bool = False
    is_system: bool = False

    @property
    def display_cmd(self) -> str:
        """Compact command line representation."""
        if self.cmdline:
            # Take only the first few words or executable base
            parts = self.cmdline.split()
            if len(parts) > 4:
                return " ".join(parts[:4]) + "..."
            return self.cmdline
        return self.process_name


@dataclass
class ProcessTarget:
    """Target process identified for termination."""
    pid: int
    name: str
    create_time: float
    ports: List[int] = field(default_factory=list)
    cmdline: str = ""


@dataclass
class PythonRuntime:
    """An installed Python runtime discovered on the system."""
    tag: str
    version: str
    executable_path: str
    source: str
    is_default: bool = False


@dataclass
class EnvDiagnosis:
    """Complete diagnostic report for the local Python environment."""
    project_dir: str
    venv_path: Optional[str] = None
    venv_python: Optional[str] = None
    venv_version: Optional[str] = None
    shell_python: str = ""
    shell_pip: Optional[str] = None
    is_shell_in_venv: bool = False
    path_mismatch: bool = False
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
