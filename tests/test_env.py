import pathlib
import pytest
from portscope.core.env import (
    find_local_venv,
    get_venv_python_executable,
    diagnose_environment,
    discover_system_pythons,
)


def test_find_local_venv():
    """devctl should discover the local .venv directory in the current repo."""
    venv = find_local_venv()
    assert venv is not None
    assert venv.name == ".venv"


def test_get_venv_python_executable():
    """Should return a valid existing executable inside .venv."""
    venv = find_local_venv()
    assert venv is not None
    exe = get_venv_python_executable(venv)
    assert exe is not None
    assert exe.is_file()
    assert "python" in exe.name.lower()


def test_diagnose_environment():
    """Environment audit should return a comprehensive structured diagnosis."""
    diag = diagnose_environment()
    assert diag.project_dir is not None
    assert diag.venv_path is not None
    assert diag.shell_python is not None
    assert isinstance(diag.issues, list)
    assert isinstance(diag.recommendations, list)


def test_discover_system_pythons():
    """Should discover at least one installed Python interpreter on the system."""
    runtimes = discover_system_pythons()
    assert len(runtimes) >= 1
    for r in runtimes:
        assert hasattr(r, "tag")
        assert hasattr(r, "executable_path")
        assert pathlib.Path(r.executable_path).is_file()
