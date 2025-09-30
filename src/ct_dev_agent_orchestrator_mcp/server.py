"""MCP Server for ct_dev-agents orchestration."""

import asyncio
from typing import Dict, Any
import logfire
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .models.agent import AgentRole
from .models.delegation import DelegationRequest
from .services.agent_manager import AgentManager
from .services.delegation_service import DelegationService
from .services.opencode_service import OpenCodeService


# Initialize logfire
logfire.configure()

# Create services
opencode_service = OpenCodeService(base_port=8000, max_agents=5)
agent_manager = AgentManager(opencode_service)
delegation_service = DelegationService(agent_manager, opencode_service)

# Create MCP server
app = Server("ct_dev-agent_orchestrator")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools."""
    return [
        Tool(
            name="delegate_work",
            description=(
                "Delegate work to a specialized ct_dev-agent. "
                "Fire-and-forget async delegation (returns immediately). "
                "Use get_delegation_status to check progress."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "Task UUID from task_orchestrator"
                    },
                    "agent_role": {
                        "type": "string",
                        "enum": [role.value for role in AgentRole],
                        "description": "Required agent role/specialization"
                    },
                    "instructions": {
                        "type": "string",
                        "description": "Detailed work instructions for the agent"
                    },
                    "context": {
                        "type": "object",
                        "description": "Additional context (optional)",
                        "default": {}
                    },
                    "timeout_seconds": {
                        "type": "integer",
                        "description": "Max execution time in seconds",
                        "default": 3600
                    }
                },
                "required": ["task_id", "agent_role", "instructions"]
            }
        ),
        Tool(
            name="get_delegation_status",
            description="Get the status of a delegated work item.",
            inputSchema={
                "type": "object",
                "properties": {
                    "delegation_id": {
                        "type": "string",
                        "description": "Delegation UUID returned from delegate_work"
                    }
                },
                "required": ["delegation_id"]
            }
        ),
        Tool(
            name="get_delegation_result",
            description="Get the result of a completed delegation.",
            inputSchema={
                "type": "object",
                "properties": {
                    "delegation_id": {
                        "type": "string",
                        "description": "Delegation UUID"
                    }
                },
                "required": ["delegation_id"]
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
            name="list_delegations",
            description="List all delegations (past and present).",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="cancel_delegation",
            description="Cancel a running delegation.",
            inputSchema={
                "type": "object",
                "properties": {
                    "delegation_id": {
                        "type": "string",
                        "description": "Delegation UUID to cancel"
                    }
                },
                "required": ["delegation_id"]
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
        if name == "delegate_work":
            request = DelegationRequest(**arguments)
            response = await delegation_service.delegate(request)
            
            result = {
                "success": True,
                "delegation_id": response.delegation_id,
                "agent_id": response.agent_id,
                "status": response.status,
                "message": response.message
            }
            
            return [TextContent(
                type="text",
                text=f"✓ Work delegated successfully\n\n"
                     f"Delegation ID: {response.delegation_id}\n"
                     f"Agent ID: {response.agent_id}\n"
                     f"Status: {response.status}\n\n"
                     f"Use get_delegation_status to check progress."
            )]
        
        elif name == "get_delegation_status":
            delegation_id = arguments["delegation_id"]
            status = await delegation_service.get_status(delegation_id)
            
            if not status:
                return [TextContent(
                    type="text",
                    text=f"✗ Delegation {delegation_id} not found"
                )]
            
            return [TextContent(
                type="text",
                text=f"Delegation Status:\n\n"
                     f"ID: {status['id']}\n"
                     f"Agent: {status['agent_id']}\n"
                     f"Task: {status['task_id']}\n"
                     f"Status: {status['status']}\n"
                     f"Created: {status['created_at']}\n"
                     f"Started: {status.get('started_at', 'N/A')}\n"
                     f"Completed: {status.get('completed_at', 'N/A')}"
            )]
        
        elif name == "get_delegation_result":
            delegation_id = arguments["delegation_id"]
            result = await delegation_service.get_result(delegation_id)
            
            if not result:
                return [TextContent(
                    type="text",
                    text=f"✗ Result not available for {delegation_id}"
                )]
            
            return [TextContent(
                type="text",
                text=f"Delegation Result:\n\n"
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
        
        elif name == "list_delegations":
            delegations = await delegation_service.list_delegations()
            
            if not delegations:
                return [TextContent(
                    type="text",
                    text="No delegations found."
                )]
            
            delegation_list = []
            for d in delegations:
                delegation_list.append(
                    f"• {d['id']}\n"
                    f"  Task: {d['task_id']}\n"
                    f"  Agent: {d['agent_id']}\n"
                    f"  Status: {d['status']}\n"
                    f"  Created: {d['created_at']}"
                )
            
            return [TextContent(
                type="text",
                text=f"Delegations ({len(delegations)}):\n\n" + "\n\n".join(delegation_list)
            )]
        
        elif name == "cancel_delegation":
            delegation_id = arguments["delegation_id"]
            success = await delegation_service.cancel_delegation(delegation_id)
            
            if success:
                return [TextContent(
                    type="text",
                    text=f"✓ Delegation {delegation_id} cancelled"
                )]
            else:
                return [TextContent(
                    type="text",
                    text=f"✗ Failed to cancel delegation {delegation_id}"
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
    logfire.info("Starting ct_dev-agent_orchestrator MCP server")
    
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
        logfire.info("ct_dev-agent_orchestrator MCP server stopped")


if __name__ == "__main__":
    asyncio.run(main())
