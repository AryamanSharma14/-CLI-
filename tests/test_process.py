import sys
import subprocess
import time
import pytest
from portscope.core.process import terminate_process, free_port
from portscope.core.security import SecurityError


def test_terminate_system_process_blocked():
    """Attempting to terminate PID 4 must be blocked and raise SecurityError."""
    with pytest.raises(SecurityError) as exc_info:
        terminate_process(4)
    assert "protected system component" in str(exc_info.value)


def test_terminate_user_process_success():
    """Spawn a disposable child process and verify portscope terminates it cleanly."""
    child = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(60)"],
    )
    pid = child.pid

    try:
        # Give it a moment to initialize
        time.sleep(0.1)
        assert child.poll() is None  # Still running

        success = terminate_process(pid)
        assert success is True
        assert child.poll() is not None or not subprocess.run(f"tasklist /FI \"PID eq {pid}\"", capture_output=True, text=True).stdout.find(str(pid)) != -1
    finally:
        # Cleanup in case of failure
        if child.poll() is None:
            child.kill()


def test_free_port_on_already_free_port():
    """Freeing an unoccupied high port should report success idempotently."""
    # Use a port in 59990+ range that is highly unlikely to be bound
    free_test_port = 59987
    success, msg, info = free_port(free_test_port)
    assert success is True
    assert "already free" in msg
