"""
Zero-activation subprocess runner and package installer.
Automatically routes commands into the project's local .venv without requiring
prior shell activation, and safely executes commands without shell injection risks.
"""

from typing import List, Optional, Tuple
import os
import sys
import shutil
import subprocess
import pathlib

from .env import find_local_venv, get_venv_python_executable


def build_venv_environment(venv_path: pathlib.Path) -> dict:
    """
    Constructs an isolated subprocess environment dictionary configured
    to prioritize the given virtual environment.
    """
    env = os.environ.copy()
    scripts_dir = venv_path / "Scripts" if sys.platform == "win32" else venv_path / "bin"

    # Prepend venv scripts to PATH
    current_path = env.get("PATH", "")
    env["PATH"] = str(scripts_dir) + os.pathsep + current_path
    env["VIRTUAL_ENV"] = str(venv_path)

    # Clean out PYTHONHOME to prevent library confusion
    env.pop("PYTHONHOME", None)

    return env


def resolve_command_args(args: List[str], venv_path: Optional[pathlib.Path]) -> Tuple[List[str], Optional[pathlib.Path]]:
    """
    Resolves command arguments to prioritize binaries inside the virtual environment.
    """
    if not args:
        return args, None

    if not venv_path:
        return args, None

    scripts_dir = venv_path / "Scripts" if sys.platform == "win32" else venv_path / "bin"
    first_cmd = args[0]

    # If calling python directly
    if first_cmd in ("python", "python3", "python.exe"):
        py_exe = get_venv_python_executable(venv_path)
        if py_exe:
            return [str(py_exe)] + args[1:], py_exe

    # If calling an installed tool binary (e.g. uvicorn, pytest, pip)
    candidate_names = [first_cmd]
    if sys.platform == "win32" and not first_cmd.endswith(".exe"):
        candidate_names.append(first_cmd + ".exe")

    for candidate in candidate_names:
        binary_path = scripts_dir / candidate
        if binary_path.is_file():
            return [str(binary_path)] + args[1:], binary_path

    return args, None


def run_in_venv(args: List[str], cwd: Optional[pathlib.Path] = None) -> int:
    """
    Executes a command inside the project's local virtual environment.
    Does NOT use shell=True to eliminate command injection vulnerabilities.
    Returns the exit code of the executed process.
    """
    target_dir = cwd or pathlib.Path.cwd()
    venv_path = find_local_venv(target_dir)

    env = build_venv_environment(venv_path) if venv_path else os.environ.copy()
    resolved_args, target_bin = resolve_command_args(args, venv_path)

    try:
        # Zero shell=True: pass resolved argument array directly
        process = subprocess.run(
            resolved_args,
            env=env,
            cwd=str(target_dir),
            check=False,
        )
        return process.returncode
    except FileNotFoundError:
        print(f"[devctl] Error: Executable '{args[0]}' not found.", file=sys.stderr)
        return 127
    except Exception as e:
        print(f"[devctl] Execution failed: {str(e)}", file=sys.stderr)
        return 1


def safe_add_package(package_name: str, cwd: Optional[pathlib.Path] = None) -> Tuple[bool, str]:
    """
    Installs a package directly into the local .venv using `python -m pip install`
    and optionally records it in requirements.txt.
    """
    target_dir = cwd or pathlib.Path.cwd()
    venv_path = find_local_venv(target_dir)

    if not venv_path:
        return False, "No virtual environment (.venv) found. Please create one with `python -m venv .venv` first."

    py_exe = get_venv_python_executable(venv_path)
    if not py_exe:
        return False, f"Could not find Python executable inside {venv_path}."

    try:
        cmd = [str(py_exe), "-m", "pip", "install", package_name]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(target_dir),
            check=False,
        )

        if result.returncode != 0:
            return False, f"pip install failed:\n{result.stderr.strip()}"

        # If requirements.txt exists in project root, check if we should record it
        req_file = target_dir / "requirements.txt"
        recorded = False
        if req_file.is_file():
            content = req_file.read_text(encoding="utf-8", errors="ignore")
            # Basic check if package is already mentioned
            clean_pkg = package_name.split("==")[0].split(">=")[0].split("<=")[0].strip().lower()
            lines = [line.strip().lower() for line in content.splitlines()]
            already_there = any(l.startswith(clean_pkg) for l in lines)
            if not already_there:
                with open(req_file, "a", encoding="utf-8") as f:
                    f.write(f"\n{package_name}\n")
                recorded = True

        msg = f"Successfully installed '{package_name}' into {venv_path.name}."
        if recorded:
            msg += " Added to requirements.txt."
        return True, msg

    except Exception as e:
        return False, f"Installation error: {str(e)}"
