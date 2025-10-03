"""MCP Server for ct_dev-agents orchestration - V2 Session-based."""

import asyncio
import os
import sys
from typing import Dict, Any
import json
import logfire
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .models.session import SpawnAgentRequest
from .services.agent_manager import AgentManager
from .services.session_service import SessionService
from .services.opencode_service import OpenCodeService


# Initialize logfire (optional for development)
try:
    # Check for logfire token
    token = os.getenv("LOGFIRE_TOKEN")
    if token:
        logfire.configure(token=token)
        print("Logfire configured with token", file=sys.stderr)
    elif os.path.exists(os.path.expanduser("~/.logfire")):
        logfire.configure()
        print("Logfire configured from ~/.logfire", file=sys.stderr)
    else:
        # Disable logfire if not configured
        logfire.configure(send_to_logfire=False)
        print("Logfire disabled - no token found", file=sys.stderr)
except Exception as e:
    # Fallback: disable logfire
    logfire.configure(send_to_logfire=False)
    print(f"Logfire configuration failed: {e}", file=sys.stderr)

# Create services
opencode_service = OpenCodeService(max_agents=5)
agent_manager = AgentManager(opencode_service)
session_service = SessionService()

# Create MCP server
app = Server("ct_dev-agent_orchestrator")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools."""
    return [
        # NEW V2 SESSION-BASED TOOLS
        Tool(
            name="spawn_agent",
            description=(
                "Spawns a specialized agent session for interactive work with complete X^∞ responsibility tracking. "
                "Returns session_id for tracking and follow-up communication. "
                "REQUIRED: All X^∞ responsibility fields (original_task, cap_origin, delegation_context) must be provided "
                "to ensure full traceability of authority and delegation chains."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "role": {
                        "type": "string",
                        "description": "Agent role/name from OpenCode (e.g., 'backend_specialist', 'plan', 'build'). Use list_opencode_agents to discover available agents."
                    },
                    "task_id": {
                        "type": "string",
                        "description": "Task UUID from task_orchestrator"
                    },
                    "instructions": {
                        "type": "string",
                        "description": "Detailed work instructions"
                    },
                    "project_directory": {
                        "type": "string",
                        "description": "Absolute path to project working directory"
                    },
                    "expected_output": {
                        "type": "string",
                        "description": "Expected work output/deliverable (e.g., 'Report', 'Implementation', 'Analysis')"
                    },
                    "context": {
                        "type": "object",
                        "description": "Additional context",
                        "default": {}
                    },
                    "model": {
                        "type": "string",
                        "description": "Model to use",
                        "default": "claude-sonnet-4"
                    },
                    "original_task": {
                        "type": "object",
                        "description": "Original task that started this work",
                        "properties": {
                            "task_id": {"type": "string", "description": "Original task UUID"},
                            "title": {"type": "string", "description": "Original task title"},
                            "description": {"type": "string", "description": "Complete original task description"},
                            "requester": {"type": "string", "description": "Who originally requested the task"},
                            "requested_at": {"type": "string", "description": "ISO 8601 timestamp of original request"}
                        },
                        "required": ["task_id", "title", "description", "requester", "requested_at"]
                    },
                    "cap_origin": {
                        "type": "object",
                        "description": "Origin of the capability/authority",
                        "properties": {
                            "ultimate_authority": {"type": "string", "description": "Ultimate authority (e.g., 'Auctor')"},
                            "original_scope": {"type": "string", "description": "Scope of original authority"},
                            "granted_at": {"type": "string", "description": "ISO 8601 timestamp when authority was granted"},
                            "grant_context": {"type": "string", "description": "Context of authority grant"}
                        },
                        "required": ["ultimate_authority", "original_scope", "granted_at", "grant_context"]
                    },
                    "delegation_context": {
                        "type": "object",
                        "description": "Current delegation context - who delegates NOW with what cap",
                        "properties": {
                            "delegator": {"type": "string", "description": "Who is delegating NOW"},
                            "delegator_cap": {"type": "string", "description": "What cap the delegator has (with reference to source)"},
                            "delegated_to": {"type": "string", "description": "Agent role receiving delegation"},
                            "delegated_cap": {"type": "string", "description": "What capability is being delegated"},
                            "constraints": {"type": "array", "items": {"type": "string"}, "description": "Constraints for this delegation"},
                            "phantom_level": {"type": "string", "description": "Phantom level (e.g., 'Delegation/Cap')"},
                            "delegated_at": {"type": "string", "description": "ISO 8601 timestamp of delegation"}
                        },
                        "required": ["delegator", "delegator_cap", "delegated_to", "delegated_cap", "constraints", "phantom_level", "delegated_at"]
                    }
                },
                "required": ["role", "task_id", "instructions", "project_directory", "expected_output", "original_task", "cap_origin", "delegation_context"]
            }
        ),
        Tool(
            name="query_session",
            description="Gets current status of an agent session",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Session UUID"
                    }
                },
                "required": ["session_id"]
            }
        ),
        Tool(
            name="get_agent_output",
            description="Gets final output from completed agent session",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Session UUID"
                    }
                },
                "required": ["session_id"]
            }
        ),
        Tool(
            name="list_active_sessions",
            description="Lists all active agent sessions",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_agent_capabilities",
            description=(
                "Gets information about available agent roles and capabilities from OpenCode Server. "
                "Returns list of agents with their names, descriptions, and configurations."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="stop_agent",
            description="Stops an agent session and cleans up resources",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Session UUID to stop"
                    }
                },
                "required": ["session_id"]
            }
        ),
        Tool(
            name="send_to_agent",
            description="Sends follow-up message to running agent session",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Session UUID"
                    },
                    "message": {
                        "type": "string",
                        "description": "Follow-up message"
                    }
                },
                "required": ["session_id", "message"]
            }
        ),
        Tool(
            name="get_agent_capabilities",
            description="Gets information about available agent roles and capabilities",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="list_opencode_agents",
            description=(
                "List all available agents from OpenCode server with their configurations. "
                "Returns agent names, descriptions, modes, models, tools, and permissions. "
                "Use this before spawn_agent to discover available agent roles."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "force_refresh": {
                        "type": "boolean",
                        "description": "Force refresh of cached data",
                        "default": False
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="list_opencode_models",
            description=(
                "List all available models from OpenCode server with their providers and capabilities. "
                "Returns model names, provider IDs, costs, limits, and features (reasoning, tool_call, etc). "
                "Use this to select appropriate models for spawn_agent."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "force_refresh": {
                        "type": "boolean",
                        "description": "Force refresh of cached data",
                        "default": False
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="list_agents",
            description="List all active agent instances.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),


        Tool(
            name="get_agent_stats",
            description="Get agent statistics (count by status, etc).",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    
    try:
        # NEW V2 SESSION-BASED TOOLS
        if name == "spawn_agent":
            request = SpawnAgentRequest(**arguments)
            session_info = await session_service.spawn_agent(request)
            
            return [TextContent(
                type="text",
                text=f"✓ Agent session spawned successfully\n\n"
                     f"Session ID: {session_info.session_id}\n"
                     f"Agent Role: {session_info.agent_role}\n"
                     f"Status: {session_info.status.value if hasattr(session_info.status, 'value') else session_info.status}\n"
                     f"Server URL: {session_info.server_url}\n"
                     f"Delegator: {session_info.delegation_context.get('delegator')}\n"
                     f"Delegated Cap: {session_info.delegation_context.get('delegated_cap')[:80]}...\n\n"
                     f"Use query_session to check progress."
            )]
        
        elif name == "query_session":
            session_id = arguments["session_id"]
            session_info = await session_service.query_session(session_id)

            # Build message output
            messages_text = ""
            if session_info.messages:
                messages_text = "\n\nMessages:\n"
                for idx, msg in enumerate(session_info.messages, 1):
                    role = msg.get('role', 'unknown')
                    parts = msg.get('parts', [])
                    messages_text += f"\n{idx}. [{role}]:\n"
                    for part in parts:
                        if part.get('type') == 'text':
                            text = part.get('text', '')
                            # Truncate very long messages
                            if len(text) > 500:
                                text = text[:500] + "... (truncated)"
                            messages_text += f"   {text}\n"

            return [TextContent(
                type="text",
                text=f"Session Status:\n\n"
                     f"ID: {session_info.session_id}\n"
                     f"Agent Role: {session_info.agent_role}\n"
                     f"Status: {session_info.status.value if hasattr(session_info.status, 'value') else session_info.status}\n"
                     f"Started: {session_info.started_at}\n"
                     f"Server URL: {session_info.server_url}\n"
                     f"Message Count: {len(session_info.messages)}"
                     f"{messages_text}"
            )]
        
        elif name == "get_agent_output":
            session_id = arguments["session_id"]
            output = await session_service.get_agent_output(session_id)
            
            return [TextContent(
                type="text",
                text=f"Agent Output:\n\n"
                     f"Session ID: {output.session_id}\n"
                     f"Status: {output.status.value if hasattr(output.status, 'value') else output.status}\n"
                     f"Duration: {output.duration_seconds:.2f}s\n"
                     f"Completed: {output.completed_at}\n\n"
                     f"Summary:\n{output.summary}\n\n"
                     f"Artifacts: {len(output.artifacts)} items"
            )]
        
        elif name == "list_active_sessions":
            sessions = await session_service.list_active_sessions()
            
            if not sessions:
                return [TextContent(
                    type="text",
                    text="No active sessions found."
                )]
            
            session_list = []
            for session in sessions:
                session_list.append(
                    f"• {session.session_id}\n"
                    f"  Role: {session.agent_role}\n"
                    f"  Status: {session.status.value if hasattr(session.status, 'value') else session.status}\n"
                    f"  Started: {session.started_at}\n"
                    f"  Messages: {len(session.messages)}"
                )
            
            return [TextContent(
                type="text",
                text=f"Active Sessions ({len(sessions)}):\n\n" + "\n\n".join(session_list)
            )]
        
        elif name == "stop_agent":
            session_id = arguments["session_id"]
            success = await session_service.stop_agent(session_id)
            
            if success:
                return [TextContent(
                    type="text",
                    text=f"✓ Agent session {session_id} stopped successfully"
                )]
            else:
                return [TextContent(
                    type="text",
                    text=f"✗ Failed to stop agent session {session_id}"
                )]
        
        elif name == "send_to_agent":
            session_id = arguments["session_id"]
            message = arguments["message"]
            success = await session_service.send_to_agent(session_id, message)
            
            if success:
                return [TextContent(
                    type="text",
                    text=f"✓ Message sent to agent session {session_id}"
                )]
            else:
                return [TextContent(
                    type="text",
                    text=f"✗ Failed to send message to session {session_id}"
                )]
        
        elif name == "get_agent_capabilities":
            try:
                # Default OpenCode server URL
                server_url = os.getenv("OPENCODE_SERVER_URL", "http://localhost:8000")
                
                # Fetch agents via API
                agents = await opencode_service.api_client.fetch_available_agents(server_url)
                
                # Format for response
                capabilities = {
                    "agents": [
                        {
                            "name": agent.get("name"),
                            "description": agent.get("description", "No description available"),
                            "mode": agent.get("mode", "unknown"),
                            "builtIn": agent.get("builtIn", False),
                            "tools": list(agent.get("tools", {}).keys()) if agent.get("tools") else []
                        }
                        for agent in agents
                    ],
                    "count": len(agents),
                    "server_url": server_url
                }
                
                return [TextContent(
                    type="text",
                    text=json.dumps(capabilities, indent=2)
                )]
                
            except Exception as e:
                logfire.error("Error fetching agent capabilities", error=str(e))
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "success": False,
                        "error": str(e),
                        "message": "Failed to fetch agent capabilities from OpenCode Server"
                    }, indent=2)
                )]
        
        
        elif name == "list_opencode_agents":
            try:
                force_refresh = arguments.get("force_refresh", False)
                
                # Use OpenCodeClient to fetch agents
                client = opencode_service.process_manager.opencode_client
                agents = await client.list_agents(force_refresh=force_refresh)
                
                # Format for response
                agents_info = {
                    "agents": [
                        {
                            "name": agent.name,
                            "description": agent.description,
                            "mode": agent.mode,
                            "built_in": agent.built_in,
                            "model": agent.model,
                            "temperature": agent.temperature,
                            "top_p": agent.top_p,
                            "tools": list(agent.tools.keys()) if agent.tools else [],
                            "permission": agent.permission
                        }
                        for agent in agents
                    ],
                    "count": len(agents),
                    "cached": not force_refresh
                }
                
                return [TextContent(
                    type="text",
                    text=json.dumps(agents_info, indent=2)
                )]
                
            except Exception as e:
                logfire.error("Error listing OpenCode agents", error=str(e))
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "success": False,
                        "error": str(e),
                        "message": "Failed to list agents from OpenCode Server"
                    }, indent=2)
                )]
        
        elif name == "list_opencode_models":
            try:
                force_refresh = arguments.get("force_refresh", False)
                
                # Use OpenCodeClient to fetch models
                client = opencode_service.process_manager.opencode_client
                providers_dict = await client.list_providers(force_refresh=force_refresh)
                
                # Flatten providers dictionary into list
                models_info = {
                    "models": [],
                    "providers": []
                }
                
                for provider_id, models in providers_dict.items():
                    models_info["providers"].append(provider_id)
                    for model in models:
                        models_info["models"].append({
                            "id": model.id,
                            "name": model.name,
                            "provider_id": model.provider_id,
                            "release_date": model.release_date,
                            "attachment": model.attachment,
                            "reasoning": model.reasoning,
                            "temperature": model.temperature,
                            "tool_call": model.tool_call,
                            "experimental": model.experimental,
                            "cost": model.cost,
                            "limit": model.limit
                        })
                
                models_info["count"] = len(models_info["models"])
                models_info["provider_count"] = len(models_info["providers"])
                models_info["cached"] = not force_refresh
                
                return [TextContent(
                    type="text",
                    text=json.dumps(models_info, indent=2)
                )]
                
            except Exception as e:
                logfire.error("Error listing OpenCode models", error=str(e))
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "success": False,
                        "error": str(e),
                        "message": "Failed to list models from OpenCode Server"
                    }, indent=2)
                )]
        
        elif name == "list_agents":
            agents = await agent_manager.list_agents()
            
            if not agents:
                return [TextContent(
                    type="text",
                    text="No agents currently running."
                )]
            
            agent_list = []
            for agent in agents:
                agent_list.append(
                    f"• {agent.agent_id}\n"
                    f"  Role: {agent.role}\n"
                    f"  Status: {agent.status}\n"
                    f"  Port: {agent.port}\n"
                    f"  PID: {agent.pid}"
                )
            
            return [TextContent(
                type="text",
                text=f"Active Agents ({len(agents)}):\n\n" + "\n\n".join(agent_list)
            )]
        
        elif name == "get_agent_stats":
            # Use session_service for V2 consistency - count active sessions not agents
            sessions = await session_service.list_active_sessions()
            total = len(sessions)

            # Group by status
            by_status = {}
            for session in sessions:
                status_str = session.status.value if hasattr(session.status, 'value') else str(session.status)
                by_status[status_str] = by_status.get(status_str, 0) + 1

            stats = [f"Total Agents: {total}\n"]
            stats.append("By Status:")
            for status, count in by_status.items():
                if count > 0:
                    stats.append(f"  • {status}: {count}")

            return [TextContent(
                type="text",
                text="\n".join(stats)
            )]
        
        else:
            return [TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]
            
    except Exception as e:
        logfire.error(f"Tool call failed: {name}", error=str(e))
        return [TextContent(
            type="text",
            text=f"✗ Error: {str(e)}"
        )]


async def main():
    """Run MCP server."""
    logfire.info("Starting ct_dev-agent_orchestrator MCP server v2")
    
    # Start agent manager
    await agent_manager.start()
    
    try:
        # Run server
        async with stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )
    finally:
        # Stop agent manager
        await agent_manager.stop()
        logfire.info("ct_dev-agent_orchestrator MCP server v2 stopped")


if __name__ == "__main__":
    asyncio.run(main())