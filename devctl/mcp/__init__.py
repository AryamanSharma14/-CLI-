"""
Model Context Protocol (MCP) server integration for devctl.
Enables AI coding agents (Cursor, Claude Desktop, Antigravity)
to autonomously inspect ports, free hung dev servers, and diagnose environments.
"""

from .server import run_mcp_server

__all__ = ["run_mcp_server"]
