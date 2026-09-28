from typer.testing import CliRunner
from devctl.main import app

runner = CliRunner()


def test_cli_help():
    """devctl --help should return code 0 and show all main commands."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "ports" in result.output
    assert "free" in result.output
    assert "doctor" in result.output
    assert "zombies" in result.output
    assert "py" in result.output
    assert "run" in result.output
    assert "add" in result.output


def test_cli_doctor():
    """devctl doctor should run and display the diagnosis panel."""
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "Environment Doctor" in result.output
    assert "PROJECT ENVIRONMENT" in result.output


def test_cli_py():
    """devctl py should run and display the runtimes table."""
    result = runner.invoke(app, ["py"])
    assert result.exit_code == 0
    assert "Installed Python Runtimes" in result.output


def test_cli_ports():
    """devctl ports should run cleanly without crashing."""
    result = runner.invoke(app, ["ports"])
    assert result.exit_code == 0


def test_cli_ports_invalid_filter():
    """devctl ports -p 999999 should return non-zero exit code due to validation."""
    result = runner.invoke(app, ["ports", "-p", "999999"])
    assert result.exit_code != 0
    assert "out of valid range" in result.output


def test_cli_free_already_free_port():
    """devctl free on an empty port should report free cleanly."""
    result = runner.invoke(app, ["free", "59986", "-y"])
    assert result.exit_code == 0
    assert "already free" in result.output
