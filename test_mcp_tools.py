"""Interactive check for ct_dev-agent_delegation-mcp MCP tools."""

import asyncio
from datetime import datetime, timezone
from pathlib import Path

from ct_dev_agent_delegation_mcp.server import call_tool
from ct_dev_agent_delegation_mcp.models.delegation import SpawnDelegationRequest

PROJECT_DIR = Path(__file__).parent


def build_request(role: str) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    return SpawnDelegationRequest(
        role=role,
        task_id="mcp-tools-smoke",
        instructions="Report readiness and wait for follow-up instructions.",
        project_directory=str(PROJECT_DIR),
        expected_output="Acknowledgement message",
        context={},
        model="claude-sonnet-4",
        original_task={
            "task_id": "mcp-tools-origin",
            "title": "MCP tool smoke test",
            "description": "Verify spawn/list/stop MCP tools under delegation naming.",
            "requester": "Auctor",
            "requested_at": now
        },
        cap_origin={
            "ultimate_authority": "Auctor",
            "original_scope": "Delegation platform quality assurance",
            "granted_at": now,
            "grant_context": "Manual MCP smoke test"
        },
        delegation_context={
            "delegator": "Project Manager",
            "delegator_cap": f"Tool verification authority (Auctor, {now})",
            "delegated_to": role,
            "delegated_cap": "Acknowledge spawn and await instructions",
            "constraints": ["No external side effects"],
            "phantom_level": "Delegation/Cap",
            "delegated_at": now
        }
    ).model_dump()


async def list_tools() -> None:
    response = await call_tool("list_active_sessions", {})
    print("Current active sessions:")
    print(response[0].text)


async def spawn_and_stop() -> None:
    print("Spawning backend_specialist session via MCP tool")
    request_payload = build_request("backend_specialist")
    spawn_response = await call_tool("spawn_agent", request_payload)
    spawn_text = spawn_response[0].text
    print(spawn_text)

    session_id = None
    for line in spawn_text.splitlines():
        line = line.strip()
        if line.lower().startswith("session id"):
            session_id = line.split(":", 1)[1].strip()
            break
    if not session_id:
        print("Could not extract session identifier from spawn output")
        await list_tools()
        return

    await list_tools()

    print(f"Stopping session {session_id}")
    stop_response = await call_tool("stop_agent", {"session_id": session_id})
    print(stop_response[0].text)

    await list_tools()
    session_id = request_payload.get("task_id")
    # The call_tool response includes session id text; parse simple fallback by re-querying list_active_sessions
    active = await call_tool("list_active_sessions", {})
    text = active[0].text
    session_id_line = next((line for line in text.splitlines() if "Session ID" in line or "session_id" in line.lower()), "")
    session_id = session_id_line.split(":")[-1].strip() if session_id_line else None

    if session_id:
        print(f"Stopping session {session_id}")
        stop_response = await call_tool("stop_agent", {"session_id": session_id})
        print(stop_response[0].text)
    else:
        print("Unable to parse session identifier from list_active_sessions output")

    await list_tools()


async def main() -> None:
    print("Running MCP tool smoke test")
    await spawn_and_stop()


if __name__ == "__main__":
    asyncio.run(main())
