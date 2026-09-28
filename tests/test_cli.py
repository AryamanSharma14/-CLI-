from typer.testing import CliRunner
from devctl.main import app

runner = CliRunner()


def test_cli_help():
    """devctl --help should return code 0 and show the consolidated primary commands."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "ports" in result.output
    assert "explain" in result.output
    assert "free" in result.output
    assert "doctor" in result.output
    assert "run" in result.output
    assert "add" in result.output


def test_cli_doctor():
    """devctl doctor should run and display the diagnosis panel."""
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "Environment Audit" in result.output
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


def test_cli_explain():
    """devctl explain 5432 should explain Postgres port."""
    result = runner.invoke(app, ["explain", "5432"])
    assert result.exit_code == 0
    assert "DATABASE" in result.output
    assert "PostgreSQL" in result.output


def test_cli_heavy():
    """devctl heavy should display resource consumption table."""
    result = runner.invoke(app, ["heavy"])
    assert result.exit_code == 0


def test_cli_ai():
    """devctl ai should display AI runtime status panel."""
    result = runner.invoke(app, ["ai"])
    assert result.exit_code == 0
    assert "Ollama" in result.output


def test_cli_ctx():
    """devctl ctx should output markdown environment context."""
    result = runner.invoke(app, ["ctx"])
    assert result.exit_code == 0
    assert "Local Environment Context" in result.output


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


def test_cli_explain_process_name():
    """devctl explain spotify should explain Spotify process context in plain English."""
    result = runner.invoke(app, ["explain", "spotify"])
    assert result.exit_code == 0
    assert "WHAT IS THIS?" in result.output
    assert "CAN I KILL IT?" in result.output
    assert "WHAT HAPPENS IF I KILL IT?" in result.output


def test_cli_explain_pid():
    """devctl explain <current_process_pid> should identify the running process."""
    import os
    pid = str(os.getpid())
    result = runner.invoke(app, ["explain", pid])
    assert result.exit_code == 0
    assert "PID " in result.output
    assert "WHAT IS THIS?" in result.output


def test_cli_summary():
    """devctl summary should output smart intelligence panel without errors."""
    result = runner.invoke(app, ["summary"])
    assert result.exit_code == 0
    assert "SMART PORT INTELLIGENCE" in result.output


def test_cli_ports_bloat_flag():
    """devctl ports -b should run cleanly."""
    result = runner.invoke(app, ["ports", "-b"])
    assert result.exit_code == 0


def test_cli_doctor_py_flag():
    """devctl doctor -p should catalog installed Python runtimes."""
    result = runner.invoke(app, ["doctor", "-p"])
    assert result.exit_code == 0
    assert "Installed Python Runtimes" in result.output


def test_cli_free_zombies_flag():
    """devctl free -z should safely check zombies."""
    result = runner.invoke(app, ["free", "-z", "-y"])
    assert result.exit_code == 0


