"""
Python environment, interpreter, and virtualenv audit module.
Performs 5-point parity checks, detects PATH mismatches, and catalogs
all installed Python runtimes on the system.
"""

from typing import List, Optional
import os
import sys
import shutil
import subprocess
import pathlib

from .models import PythonRuntime, EnvDiagnosis


def find_local_venv(start_dir: Optional[pathlib.Path] = None) -> Optional[pathlib.Path]:
    """
    Search start_dir and its parent directories for a standard virtual environment
    (.venv, venv, env).
    """
    current = (start_dir or pathlib.Path.cwd()).resolve()

    for directory in [current] + list(current.parents):
        for candidate in [".venv", "venv", "env"]:
            venv_path = directory / candidate
            if venv_path.is_dir():
                # Check for python binary inside
                if sys.platform == "win32":
                    py_exe = venv_path / "Scripts" / "python.exe"
                else:
                    py_exe = venv_path / "bin" / "python"

                if py_exe.is_file():
                    return venv_path

        # Stop if we hit a git root or filesystem root
        if (directory / ".git").is_dir():
            break

    return None


def get_venv_python_executable(venv_path: pathlib.Path) -> Optional[pathlib.Path]:
    """Return the absolute path to the Python executable inside a venv."""
    if sys.platform == "win32":
        exe = venv_path / "Scripts" / "python.exe"
    else:
        exe = venv_path / "bin" / "python"
    return exe if exe.is_file() else None


def get_python_version_from_cfg(venv_path: pathlib.Path) -> Optional[str]:
    """Read Python version from pyvenv.cfg if present."""
    cfg_file = venv_path / "pyvenv.cfg"
    if cfg_file.is_file():
        try:
            with open(cfg_file, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if line.startswith("version =") or line.startswith("version_info ="):
                        return line.split("=", 1)[1].strip()
        except Exception:
            pass
    return None


def discover_system_pythons() -> List[PythonRuntime]:
    """
    Discover all installed Python runtimes on the host machine.
    Uses Windows `py -0p` if available, and scans PATH and common directories.
    """
    runtimes: List[PythonRuntime] = []
    seen_paths = set()

    # 1. Try Windows Python Launcher: `py -0p`
    if sys.platform == "win32":
        py_launcher = shutil.which("py")
        if py_launcher:
            try:
                result = subprocess.run(
                    [py_launcher, "-0p"],
                    capture_output=True,
                    text=True,
                    timeout=3,
                    check=False,
                )
                for line in result.stdout.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    # Format: " -V:3.13 * C:\Path\to\python.exe"
                    is_def = "*" in line
                    parts = line.replace("*", "").split()
                    if len(parts) >= 2:
                        tag = parts[0].replace("-V:", "").strip()
                        exe_path = parts[1].strip()
                        resolved = str(pathlib.Path(exe_path).resolve())
                        if resolved not in seen_paths and os.path.isfile(resolved):
                            seen_paths.add(resolved)
                            runtimes.append(
                                PythonRuntime(
                                    tag=tag,
                                    version=tag,
                                    executable_path=resolved,
                                    source="Windows py launcher",
                                    is_default=is_def,
                                )
                            )
            except Exception:
                pass

    # 2. Check active shell executables (python, python3)
    for name in ["python", "python3"]:
        exe = shutil.which(name)
        if exe:
            resolved = str(pathlib.Path(exe).resolve())
            if resolved not in seen_paths:
                seen_paths.add(resolved)
                tag = "shell"
                source = "System PATH"
                if "msys" in resolved.lower() or "mingw" in resolved.lower():
                    tag = "msys"
                    source = "MSYS2 MinGW"
                elif ".venv" in resolved.lower() or "venv" in resolved.lower():
                    tag = "local-venv"
                    source = "Virtual Environment"
                runtimes.append(
                    PythonRuntime(
                        tag=tag,
                        version=sys.version.split()[0],
                        executable_path=resolved,
                        source=source,
                        is_default=False,
                    )
                )

    # 3. Check local project .venv if available
    local_venv = find_local_venv()
    if local_venv:
        venv_exe = get_venv_python_executable(local_venv)
        if venv_exe:
            resolved = str(venv_exe.resolve())
            if resolved not in seen_paths:
                seen_paths.add(resolved)
                version_str = get_python_version_from_cfg(local_venv) or "Unknown"
                runtimes.append(
                    PythonRuntime(
                        tag="project-venv",
                        version=version_str,
                        executable_path=resolved,
                        source=f"Project ({local_venv.name})",
                        is_default=False,
                    )
                )

    return runtimes


def diagnose_environment(target_dir: Optional[pathlib.Path] = None) -> EnvDiagnosis:
    """
    Performs a 5-point environment health audit on the current workspace.
    Detects PATH mismatches, unactivated virtualenvs, and pip/python desyncs.
    """
    cwd = (target_dir or pathlib.Path.cwd()).resolve()
    shell_py = shutil.which("python") or shutil.which("python3") or sys.executable
    shell_pip = shutil.which("pip") or shutil.which("pip3")

    shell_py_resolved = str(pathlib.Path(shell_py).resolve()) if shell_py else ""
    shell_pip_resolved = str(pathlib.Path(shell_pip).resolve()) if shell_pip else None

    local_venv = find_local_venv(cwd)
    venv_str = str(local_venv) if local_venv else None
    venv_py_str = None
    venv_version = None

    if local_venv:
        venv_py = get_venv_python_executable(local_venv)
        if venv_py:
            venv_py_str = str(venv_py.resolve())
            venv_version = get_python_version_from_cfg(local_venv)

    is_shell_in_venv = False
    if local_venv and venv_py_str:
        # Check if active shell python matches local venv python
        is_shell_in_venv = shell_py_resolved.lower() == venv_py_str.lower()

    # Detect pip / python mismatch
    path_mismatch = False
    if shell_py_resolved and shell_pip_resolved:
        py_parent = str(pathlib.Path(shell_py_resolved).parent).lower()
        pip_parent = str(pathlib.Path(shell_pip_resolved).parent).lower()
        # On Windows, python.exe is in root or Scripts, pip is in Scripts
        # They should share parent or parent's parent
        if py_parent != pip_parent and not pip_parent.startswith(py_parent):
            path_mismatch = True

    issues: List[str] = []
    recommendations: List[str] = []

    if local_venv:
        if not is_shell_in_venv:
            issues.append(
                f"Local virtualenv found at '{local_venv.name}', but current terminal is running global Python ({shell_py_resolved})."
            )
            recommendations.append("Use `devctl run <cmd>` to automatically execute inside the project's .venv.")
            recommendations.append("Or activate the virtualenv in your shell.")
    else:
        issues.append("No virtual environment (.venv) detected in this project directory.")
        recommendations.append("Create a virtualenv with `python -m venv .venv`.")

    if path_mismatch:
        issues.append(
            f"PATH Mismatch: `python` points to '{shell_py_resolved}', but `pip` points to '{shell_pip_resolved}'. Packages installed via `pip` will NOT be available to your `python` command!"
        )
        recommendations.append("Use `python -m pip install <package>` instead of plain `pip install`.")
        recommendations.append("Or use `devctl add <package>` to guarantee installation into the project's .venv.")

    return EnvDiagnosis(
        project_dir=str(cwd),
        venv_path=venv_str,
        venv_python=venv_py_str,
        venv_version=venv_version,
        shell_python=shell_py_resolved,
        shell_pip=shell_pip_resolved,
        is_shell_in_venv=is_shell_in_venv,
        path_mismatch=path_mismatch,
        issues=issues,
        recommendations=recommendations,
    )
