"""MCP Server for ct_dev-agents orchestration - V2 Session-based."""

import asyncio
import os
from typing import Dict, Any
import logfire
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .models.agent import AgentRole
from .models.session import SpawnAgentRequest, SessionInfo, AgentOutput, SessionStatus
from .services.agent_manager import AgentManager
from .services.session_service import SessionService
from .services.opencode_service import OpenCodeService


# Initialize logfire (optional for development)
try:
    if os.getenv("LOGFIRE_TOKEN") or os.path.exists(os.path.expanduser("~/.logfire")):
        logfire.configure()
    else:
        # Disable logfire if not configured
        logfire.configure(send_to_logfire=False)
except Exception:
    # Fallback: disable logfire
    logfire.configure(send_to_logfire=False)

# Create services
opencode_service = OpenCodeService(base_port=8000, max_agents=5)
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
                "Spawns a specialized agent session for interactive work. "
                "Returns session_id for tracking and follow-up communication."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "role": {
                        "type": "string",
                        "enum": [role.value for role in AgentRole],
                        "description": "Agent role (e.g., 'backend_specialist')"
                    },
                    "task_id": {
                        "type": "string",
                        "description": "Task UUID from task_orchestrator"
                    },
                    "instructions": {
                        "type": "string",
                        "description": "Detailed work instructions"
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
                    }
                },
                "required": ["role", "task_id", "instructions"]
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
                     f"Server URL: {session_info.server_url}\n\n"
                     f"Use query_session to check progress."
            )]
        
        elif name == "query_session":
            session_id = arguments["session_id"]
            session_info = await session_service.query_session(session_id)
            
            return [TextContent(
                type="text",
                text=f"Session Status:\n\n"
                     f"ID: {session_info.session_id}\n"
                     f"Agent Role: {session_info.agent_role}\n"
                     f"Status: {session_info.status.value if hasattr(session_info.status, 'value') else session_info.status}\n"
                     f"Started: {session_info.started_at}\n"
                     f"Server URL: {session_info.server_url}\n"
                     f"Messages: {len(session_info.messages)}"
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
            capabilities = []
            for role in AgentRole:
                capabilities.append(f"• {role.value}")
            
            return [TextContent(
                type="text",
                text=f"Available Agent Roles:\n\n" + "\n".join(capabilities) + 
                     f"\n\nTotal: {len(AgentRole)} specialized roles available"
            )]
        

        

            
            return [TextContent(
                type="text",
                text=warning_text + f"Delegation Status:\n\n"
                     f"ID: {status['id']}\n"
                     f"Agent: {status['agent_id']}\n"
                     f"Task: {status['task_id']}\n"
                     f"Status: {status['status']}\n"
                     f"Created: {status['created_at']}\n"
                     f"Started: {status.get('started_at', 'N/A')}\n"
                     f"Completed: {status.get('completed_at', 'N/A')}"
            )]
        

            
            return [TextContent(
                type="text",
                text=warning_text + f"Delegation Result:\n\n"
                     f"Success: {result.success}\n"
                     f"Status: {result.status}\n"
                     f"Duration: {result.duration_seconds:.2f}s\n"
                     f"Output: {result.output or 'N/A'}\n"
                     f"Error: {result.error or 'None'}\n"
                     f"Scope Deviation: {result.scope_deviation or 'None'}"
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
            total = await agent_manager.get_agent_count()
            by_status = await agent_manager.get_agent_count_by_status()
            
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