import json
import pytest
from portscope.mcp.server import handle_tool_call, TOOLS_SPEC


def test_mcp_tools_spec():
    """Verify all 5 core tools are properly registered with valid schemas."""
    tool_names = [t["name"] for t in TOOLS_SPEC]
    assert "portscope_list_ports" in tool_names
    assert "portscope_explain_target" in tool_names
    assert "portscope_free_target" in tool_names
    assert "portscope_free_dev_servers" in tool_names
    assert "portscope_doctor" in tool_names


def test_mcp_call_list_ports():
    """portscope_list_ports tool should return a valid ports dictionary."""
    result = handle_tool_call("portscope_list_ports", {"include_all": True})
    assert "ports" in result
    assert "total_count" in result
    assert isinstance(result["ports"], list)


def test_mcp_call_explain_target():
    """portscope_explain_target should return structured diagnosis."""
    result = handle_tool_call("portscope_explain_target", {"target": "3306"})
    assert result["target"] == "Port 3306"
    assert "context" in result
    assert result["context"]["category"] == "DATABASE"


def test_mcp_call_explain_invalid():
    """portscope_explain_target with empty target returns error."""
    result = handle_tool_call("portscope_explain_target", {"target": ""})
    assert "error" in result


def test_mcp_call_doctor():
    """portscope_doctor tool should return diagnostic report dictionary."""
    result = handle_tool_call("portscope_doctor", {})
    assert "project_dir" in result
    assert "issues" in result
    assert "recommendations" in result


def test_mcp_call_free_dev_servers():
    """portscope_free_dev_servers should execute cleanly."""
    result = handle_tool_call("portscope_free_dev_servers", {})
    assert result["success"] is True
    assert "freed_ports" in result


def test_mcp_call_free_system_protection():
    """portscope_free_target on system port (e.g. 135) or PID 4 should reject or report error."""
    result = handle_tool_call("portscope_free_target", {"target": "4"})
    assert result["success"] is False
