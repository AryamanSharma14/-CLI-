"""
Model Context Protocol (MCP) JSON-RPC 2.0 stdio server implementation.
Allows external AI coding tools (Cursor, Claude Desktop, Antigravity)
to autonomously query ports, free stuck development processes, and check environment health.
"""

from typing import Any, Dict, List, Optional
import json
import os
import sys
import psutil

from ..core.ports import scan_listening_ports, filter_visible_ports, get_port_info, find_dev_servers
from ..core.catalog import lookup_port_context
from ..core.process import free_port, terminate_process
from ..core.security import is_system_process, validate_port
from ..core.env import diagnose_environment
from ..core.models import PortInfo


TOOLS_SPEC = [
    {
        "name": "devctl_list_ports",
        "description": "Inspect active listening TCP ports with process details, RAM consumption, and bloat classifications.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "include_all": {
                    "type": "boolean",
                    "description": "If true, includes internal IDE IPC sockets and system ephemeral ports."
                },
                "bloat_only": {
                    "type": "boolean",
                    "description": "If true, returns only useless background bloat (Spotify, OneDrive, etc.)."
                }
            }
        }
    },
    {
        "name": "devctl_explain_target",
        "description": "Analyze what a port number, PID, or process name does in plain English, with safety ratings and kill impact.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "Port number (e.g. '3000'), PID (e.g. '14210'), or process name ('spotify', 'node')."
                }
            },
            "required": ["target"]
        }
    },
    {
        "name": "devctl_free_target",
        "description": "Safely free an occupied port or terminate a process with system protections and TOCTOU checks.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "Port number, PID, or process name to free."
                },
                "force": {
                    "type": "boolean",
                    "description": "Force termination for privileged ports (<1024)."
                }
            },
            "required": ["target"]
        }
    },
    {
        "name": "devctl_free_dev_servers",
        "description": "Sweep and safely terminate lingering Node, Vite, Next.js, Uvicorn, and Flask dev servers holding ports, while strictly protecting databases and editors.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "devctl_doctor",
        "description": "Audit Python virtualenv status, interpreter parity, and PATH desync between pip and python.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    }
]


def handle_tool_call(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Executes the requested tool and returns the result dictionary."""
    if name == "devctl_list_ports":
        include_all = bool(arguments.get("include_all", False))
        bloat_only = bool(arguments.get("bloat_only", False))
        all_ports = scan_listening_ports()
        visible, hidden = filter_visible_ports(all_ports, include_all=include_all, bloat_only=bloat_only)
        return {
            "ports": [p.to_dict() for p in visible],
            "total_count": len(visible),
            "hidden_count": hidden,
        }

    elif name == "devctl_explain_target":
        target = str(arguments.get("target", "")).strip()
        if not target:
            return {"error": "Missing 'target' parameter."}

        if target.isdigit():
            num = int(target)
            port_info = get_port_info(num) if (1 <= num <= 65535) else None
            if port_info:
                ctx = lookup_port_context(num, port_info.process_name, port_info.cmdline, pid=port_info.pid)
                return {
                    "target": f"Port {num}",
                    "context": ctx.to_dict(),
                    "process": port_info.to_dict(),
                }
            elif 1 <= num <= 65535:
                ctx = lookup_port_context(num, "", "")
                return {
                    "target": f"Port {num}",
                    "status": "INACTIVE",
                    "context": ctx.to_dict(),
                }
            else:
                return {"error": f"Invalid port or PID number: {num}"}
        else:
            ctx = lookup_port_context(0, target, "")
            return {
                "target": target,
                "context": ctx.to_dict(),
            }

    elif name == "devctl_free_target":
        target = str(arguments.get("target", "")).strip()
        force = bool(arguments.get("force", False))
        if not target:
            return {"success": False, "error": "Missing 'target' parameter."}

        if target.isdigit():
            num = int(target)
            # Check system protection first
            if num <= 4 or is_system_process(num, ""):
                return {
                    "success": False,
                    "error": f"Target {num} is a protected system component. Operation blocked by devctl security guard."
                }

            # Check if active listening port
            if 1 <= num <= 65535 and is_port_in_use(num):
                port_info = get_port_info(num)
                if port_info and port_info.is_system:
                    return {
                        "success": False,
                        "error": f"Port {num} is occupied by protected system process '{port_info.process_name}' (PID {port_info.pid}). Operation blocked."
                    }
                ok, msg, info = free_port(num)
                return {
                    "success": ok,
                    "message": msg,
                    "target": f"Port {num}",
                    "freed_process": info.to_dict() if info else None,
                }
            elif psutil.pid_exists(num):
                try:
                    p = psutil.Process(num)
                    p_name = p.name()
                    c_time = p.create_time()
                    if is_system_process(num, p_name):
                        return {
                            "success": False,
                            "error": f"PID {num} ({p_name}) is a protected system process. Operation blocked."
                        }
                    ok = terminate_process(num, expected_name=p_name, expected_create_time=c_time)
                    return {
                        "success": ok,
                        "message": f"Successfully terminated PID {num} ({p_name})." if ok else f"Failed to terminate PID {num}.",
                        "target": f"PID {num}",
                    }
                except Exception as e:
                    return {"success": False, "error": str(e)}
            else:
                return {"success": False, "error": f"No active listening port or running process matches {num}."}
        else:
            # By process name
            matching = []
            for proc in psutil.process_iter(["pid", "name"]):
                try:
                    if target.lower() in (proc.info["name"] or "").lower():
                        matching.append(proc)
                except Exception:
                    continue

            if not matching:
                return {"success": True, "message": f"No active processes found matching '{target}'."}

            terminated_count = 0
            for proc in matching:
                try:
                    if not is_system_process(proc.pid, proc.name()):
                        if terminate_process(proc.pid, expected_name=proc.name(), expected_create_time=proc.create_time()):
                            terminated_count += 1
                except Exception:
                    continue

            return {
                "success": terminated_count > 0,
                "message": f"Terminated {terminated_count}/{len(matching)} process(es) matching '{target}'.",
                "matching_count": len(matching),
                "terminated_count": terminated_count,
            }

    elif name == "devctl_free_dev_servers":
        dev_servers = find_dev_servers()
        if not dev_servers:
            return {"success": True, "message": "No active development servers found holding ports.", "freed_ports": []}

        freed_ports = []
        total_ram = 0.0
        for s in dev_servers:
            if s.port:
                ok, msg, _ = free_port(s.port)
                if ok:
                    freed_ports.append({"port": s.port, "process": s.process_name, "pid": s.pid, "ram_mb": s.memory_mb})
                    total_ram += s.memory_mb

        return {
            "success": True,
            "message": f"Swept and freed {len(freed_ports)} dev server port(s), reclaiming ~{total_ram:.1f} MB RAM.",
            "freed_ports": freed_ports,
            "reclaimed_ram_mb": round(total_ram, 1),
        }

    elif name == "devctl_doctor":
        diag = diagnose_environment()
        return diag.to_dict()

    else:
        return {"error": f"Unknown tool: {name}"}


def run_mcp_server():
    """Runs the stdio JSON-RPC 2.0 loop for MCP clients."""
    # Ensure stdout/stderr are using utf-8
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue

        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue

        req_id = req.get("id")
        method = req.get("method", "")

        # Notifications don't require responses
        if req_id is None:
            continue

        if method == "initialize":
            resp = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "devctl-mcp",
                        "version": "0.2.0"
                    }
                }
            }
        elif method == "ping":
            resp = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {}
            }
        elif method == "tools/list":
            resp = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "tools": TOOLS_SPEC
                }
            }
        elif method == "tools/call":
            params = req.get("params", {})
            tool_name = params.get("name", "")
            args = params.get("arguments", {})
            try:
                tool_output = handle_tool_call(tool_name, args)
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(tool_output, indent=2)
                            }
                        ]
                    }
                }
            except Exception as e:
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": -32603,
                        "message": str(e)
                    }
                }
        else:
            resp = {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32601,
                    "message": f"Method '{method}' not found."
                }
            }

        sys.stdout.write(json.dumps(resp) + "\n")
        sys.stdout.flush()
