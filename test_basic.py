"""Smoke tests for ct_dev-agent_delegation-mcp service layer."""

import asyncio
from datetime import datetime, timezone
from pathlib import Path

from ct_dev_agent_delegation_mcp.services.delegation_service import DelegationService
from ct_dev_agent_delegation_mcp.services.agent_manager import AgentManager
from ct_dev_agent_delegation_mcp.services.opencode_service import OpenCodeService
from ct_dev_agent_delegation_mcp.models.agent import AgentRole
from ct_dev_agent_delegation_mcp.models.delegation import SpawnDelegationRequest

PROJECT_DIR = Path(__file__).parent


def build_spawn_request(role: str) -> SpawnDelegationRequest:
    """Return a SpawnDelegationRequest with baseline responsibility context."""
    timestamp = datetime.now(timezone.utc).isoformat()
    return SpawnDelegationRequest(
        role=role,
        task_id="test-task-001",
        instructions="Please confirm receipt and report working directory contents.",
        project_directory=str(PROJECT_DIR),
        expected_output="Acknowledgement plus directory listing",
        context={"purpose": "smoke-test"},
        model="claude-sonnet-4",
        original_task={
            "task_id": "test-origin-001",
            "title": "Delegation smoke test",
            "description": "Verify spawn_agent and follow-up interactions in a controlled environment.",
            "requester": "Auctor",
            "requested_at": timestamp
        },
        cap_origin={
            "ultimate_authority": "Auctor",
            "original_scope": "Delegation platform maintenance",
            "granted_at": timestamp,
            "grant_context": "Routine infrastructure validation"
        },
        delegation_context={
            "delegator": "Project Manager",
            "delegator_cap": "Delegation oversight (Auctor, {})".format(timestamp),
            "delegated_to": role,
            "delegated_cap": "Execute smoke test instructions",
            "constraints": ["Use Serena tools", "Report deviations immediately"],
            "phantom_level": "Delegation/Cap",
            "delegated_at": timestamp
        }
    )


async def smoke_test_agent_manager() -> None:
    """Start an agent, probe health, and tear down."""
    print("[agent-manager] starting smoke test")
    opencode_service = OpenCodeService(max_agents=1)
    agent_manager = AgentManager(opencode_service)

    await agent_manager.start()
    try:
        agent = await agent_manager.create_agent(AgentRole.GENERIC_ENGINEER)
        print(f"[agent-manager] agent created: {agent.agent_id} port={agent.port}")

        healthy = await opencode_service.check_health(agent)
        print(f"[agent-manager] health check result: {healthy}")

        await agent_manager.remove_agent(agent.agent_id)
        print("[agent-manager] agent removed")
    finally:
        await agent_manager.stop()
        print("[agent-manager] manager stopped")


async def smoke_test_delegation_flow() -> None:
    """Run spawn/query/stop flow through DelegationService."""
    print("[delegation] starting delegation flow smoke test")
    service = DelegationService()
    session_info = await service.spawn_agent(build_spawn_request("backend_specialist"))
    session_id = session_info.session_id
    print(f"[delegation] session spawned: {session_id} status={session_info.status}")

    await asyncio.sleep(2)
    status = await service.query_session(session_id)
    print(f"[delegation] session status: {status.status} messages={len(status.messages)}")

    await service.send_to_agent(session_id, "Confirm working directory and files present.")
    print("[delegation] follow-up message sent")

    await asyncio.sleep(2)
    output = await service.get_agent_output(session_id)
    print(f"[delegation] output status={output.status} duration={output.duration_seconds:.2f}s")

    await service.stop_agent(session_id)
    print("[delegation] session stopped")

    await service.cleanup()
    print("[delegation] cleanup complete")


async def main() -> None:
    """Execute smoke tests sequentially."""
    await smoke_test_agent_manager()
    await smoke_test_delegation_flow()


if __name__ == "__main__":
    asyncio.run(main())
