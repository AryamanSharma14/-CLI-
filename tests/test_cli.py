import json
from typer.testing import CliRunner
from portscope.main import app

runner = CliRunner()


def test_cli_help():
    """portscope --help should return code 0 and show the consolidated primary commands."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "ports" in result.output
    assert "explain" in result.output
    assert "free" in result.output
    assert "doctor" in result.output
    assert "run" in result.output
    assert "add" in result.output
    assert "mcp" in result.output


def test_cli_doctor():
    """portscope doctor should run and display the diagnosis panel."""
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "Environment Audit" in result.output
    assert "PROJECT ENVIRONMENT" in result.output


def test_cli_py():
    """portscope py should run and display the runtimes table."""
    result = runner.invoke(app, ["py"])
    assert result.exit_code == 0
    assert "Installed Python Runtimes" in result.output


def test_cli_ports():
    """portscope ports should run cleanly without crashing."""
    result = runner.invoke(app, ["ports"])
    assert result.exit_code == 0


def test_cli_explain():
    """portscope explain 5432 should explain Postgres port."""
    result = runner.invoke(app, ["explain", "5432"])
    assert result.exit_code == 0
    assert "DATABASE" in result.output
    assert "PostgreSQL" in result.output


def test_cli_heavy():
    """portscope heavy should display resource consumption table."""
    result = runner.invoke(app, ["heavy"])
    assert result.exit_code == 0


def test_cli_ai():
    """portscope ai should display AI runtime status panel."""
    result = runner.invoke(app, ["ai"])
    assert result.exit_code == 0
    assert "Ollama" in result.output


def test_cli_ctx():
    """portscope ctx should output markdown environment context."""
    result = runner.invoke(app, ["ctx"])
    assert result.exit_code == 0
    assert "Local Environment Context" in result.output


def test_cli_ports_invalid_filter():
    """portscope ports -p 999999 should return non-zero exit code due to validation."""
    result = runner.invoke(app, ["ports", "-p", "999999"])
    assert result.exit_code != 0
    assert "out of valid range" in result.output


def test_cli_free_already_free_port():
    """portscope free on an empty port should report free cleanly."""
    result = runner.invoke(app, ["free", "59986", "-y"])
    assert result.exit_code == 0
    assert "already free" in result.output


def test_cli_explain_process_name():
    """portscope explain spotify should explain Spotify process context in plain English."""
    result = runner.invoke(app, ["explain", "spotify"])
    assert result.exit_code == 0
    assert "WHAT IS THIS?" in result.output
    assert "CAN I KILL IT?" in result.output
    assert "WHAT HAPPENS IF I KILL IT?" in result.output


def test_cli_explain_pid():
    """portscope explain <current_process_pid> should identify the running process."""
    import os
    pid = str(os.getpid())
    result = runner.invoke(app, ["explain", pid])
    assert result.exit_code == 0
    assert "PID " in result.output
    assert "WHAT IS THIS?" in result.output


def test_cli_summary():
    """portscope summary should output smart intelligence panel without errors."""
    result = runner.invoke(app, ["summary"])
    assert result.exit_code == 0
    assert "SMART PORT INTELLIGENCE" in result.output


def test_cli_ports_bloat_flag():
    """portscope ports -b should run cleanly."""
    result = runner.invoke(app, ["ports", "-b"])
    assert result.exit_code == 0


def test_cli_doctor_py_flag():
    """portscope doctor -p should catalog installed Python runtimes."""
    result = runner.invoke(app, ["doctor", "-p"])
    assert result.exit_code == 0
    assert "Installed Python Runtimes" in result.output


def test_cli_free_zombies_flag():
    """portscope free -z should safely check zombies."""
    result = runner.invoke(app, ["free", "-z", "-y"])
    assert result.exit_code == 0


def test_cli_ports_json_flag():
    """portscope ports --json should output a valid JSON array."""
    result = runner.invoke(app, ["ports", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)


def test_cli_explain_json_flag():
    """portscope explain <target> --json should output a valid JSON object."""
    result = runner.invoke(app, ["explain", "3306", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "target" in data
    assert "context" in data
    assert data["context"]["category"] == "DATABASE"


def test_cli_doctor_json_flag():
    """portscope doctor --json should output a valid JSON diagnostic report."""
    result = runner.invoke(app, ["doctor", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "project_dir" in data
    assert "issues" in data


def test_cli_free_dev_flag():
    """portscope free --dev -y should run without error."""
    result = runner.invoke(app, ["free", "--dev", "-y"])
    assert result.exit_code == 0


def test_cli_run_free_port_flag():
    """portscope run --free-port on an unoccupied port should run target command and exit 0."""
    result = runner.invoke(app, ["run", "--free-port", "64899", "python", "-c", "import sys; sys.exit(0)"])
    assert result.exit_code == 0



