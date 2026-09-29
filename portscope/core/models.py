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
    category: str = "DEV"
    purpose: str = ""
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

    def to_dict(self) -> dict:
        return {
            "port": self.port,
            "protocol": self.protocol,
            "status": self.status,
            "pid": self.pid,
            "process_name": self.process_name,
            "cmdline": self.cmdline,
            "cwd": self.cwd,
            "category": self.category,
            "purpose": self.purpose,
            "memory_mb": self.memory_mb,
            "cpu_percent": self.cpu_percent,
            "is_zombie": self.is_zombie,
            "is_system": self.is_system,
        }


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

    def to_dict(self) -> dict:
        return {
            "tag": self.tag,
            "version": self.version,
            "executable_path": self.executable_path,
            "source": self.source,
            "is_default": self.is_default,
        }


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

    def to_dict(self) -> dict:
        return {
            "project_dir": self.project_dir,
            "venv_path": self.venv_path,
            "venv_python": self.venv_python,
            "venv_version": self.venv_version,
            "shell_python": self.shell_python,
            "shell_pip": self.shell_pip,
            "is_shell_in_venv": self.is_shell_in_venv,
            "path_mismatch": self.path_mismatch,
            "issues": self.issues,
            "recommendations": self.recommendations,
        }

