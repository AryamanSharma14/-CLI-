import pytest
import psutil
from devctl.core.security import (
    is_system_process,
    validate_port,
    is_privileged_port,
    verify_process_identity,
    SecurityError,
)


def test_system_process_protection_by_pid():
    """PIDs 0, 1, and 4 must always be identified as protected system processes."""
    assert is_system_process(0, "System Idle") is True
    assert is_system_process(4, "System") is True
    assert is_system_process(1, "init") is True


def test_system_process_protection_by_name():
    """Critical OS executables must be blocked regardless of PID."""
    assert is_system_process(99999, "svchost.exe") is True
    assert is_system_process(99999, "lsass.exe") is True
    assert is_system_process(99999, "csrss.exe") is True
    assert is_system_process(99999, "explorer.exe") is True
    assert is_system_process(99999, r"C:\Windows\System32\svchost.exe") is True


def test_dev_process_not_system():
    """Development and user processes should not be blocked."""
    assert is_system_process(10050, "python.exe") is False
    assert is_system_process(10051, "node.exe") is False
    assert is_system_process(10052, "uvicorn.exe") is False
    assert is_system_process(10053, "vite.exe") is False


def test_validate_port_valid():
    """Valid ports should return as integers."""
    assert validate_port(80) == 80
    assert validate_port("8000") == 8000
    assert validate_port(65535) == 65535


def test_validate_port_out_of_range():
    """Ports outside 1-65535 must raise ValueError."""
    with pytest.raises(ValueError):
        validate_port(0)
    with pytest.raises(ValueError):
        validate_port(-1)
    with pytest.raises(ValueError):
        validate_port(65536)
    with pytest.raises(ValueError):
        validate_port("not_a_port")


def test_privileged_port():
    """Ports under 1024 are privileged; >= 1024 are unprivileged."""
    assert is_privileged_port(80) is True
    assert is_privileged_port(443) is True
    assert is_privileged_port(22) is True
    assert is_privileged_port(8000) is False
    assert is_privileged_port(3000) is False


def test_toctou_process_identity():
    """Verify process identity matching and mismatch detection."""
    current_proc = psutil.Process()
    real_time = current_proc.create_time()
    real_name = current_proc.name()

    # Exact match passes
    assert verify_process_identity(current_proc, real_time, real_name) is True

    # Fake create time (mismatch) fails
    assert verify_process_identity(current_proc, real_time + 1000.0, real_name) is False

    # Fake name fails
    assert verify_process_identity(current_proc, real_time, "definitely_not_python_9999") is False
