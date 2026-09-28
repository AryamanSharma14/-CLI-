import socket
import pytest
from devctl.core.ports import scan_listening_ports, get_port_info, is_port_in_use


def test_scan_listening_ports_returns_list():
    """scan_listening_ports should return a valid list of PortInfo objects."""
    ports = scan_listening_ports()
    assert isinstance(ports, list)
    if ports:
        first = ports[0]
        assert hasattr(first, "port")
        assert hasattr(first, "pid")
        assert hasattr(first, "process_name")
        assert hasattr(first, "memory_mb")


def test_mock_tcp_listener_detection():
    """Spin up an ephemeral TCP server and verify devctl detects it accurately."""
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Bind to port 0 to let OS assign an available high ephemeral port
    server_sock.bind(("127.0.0.1", 0))
    server_sock.listen(1)
    assigned_port = server_sock.getsockname()[1]

    try:
        assert is_port_in_use(assigned_port) is True
        info = get_port_info(assigned_port)
        assert info is not None
        assert info.port == assigned_port
        assert "python" in info.process_name.lower()
        assert info.is_system is False
    finally:
        server_sock.close()

    # After closing, port should eventually be free
    # Note: On some systems brief TIME_WAIT may occur, but is_port_in_use checks LISTEN status
    assert is_port_in_use(assigned_port) is False
