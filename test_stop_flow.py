"""End-to-end smoke test for spawn and stop delegation flow."""

import asyncio
from datetime import datetime, timezone

from ct_dev_agent_delegation_mcp.services.delegation_service import DelegationService
from ct_dev_agent_delegation_mcp.models.delegation import SpawnDelegationRequest


def build_request() -> SpawnDelegationRequest:
    now = datetime.now(timezone.utc).isoformat()
    return SpawnDelegationRequest(
        role="backend_specialist",
        task_id="stop-flow",
        instructions="Remain idle until stop request is issued.",
        project_directory="/tmp",
        expected_output="Confirmation of stop",
        context={},
        model="claude-sonnet-4",
        original_task={
            "task_id": "stop-origin",
            "title": "Delegation stop flow test",
            "description": "Ensure stop_agent terminates OpenCode session cleanly.",
            "requester": "Auctor",
            "requested_at": now
        },
        cap_origin={
            "ultimate_authority": "Auctor",
            "original_scope": "Delegation infrastructure validation",
            "granted_at": now,
            "grant_context": "Stop flow smoke test"
        },
        delegation_context={
            "delegator": "Project Manager",
            "delegator_cap": f"Stop command authority (Auctor, {now})",
            "delegated_to": "backend_specialist",
            "delegated_cap": "Hold session until stop command",
            "constraints": ["No additional work"],
            "phantom_level": "Delegation/Cap",
            "delegated_at": now
        }
    )


async def main() -> None:
    service = DelegationService()

    try:
        print("Spawning delegation session")
        session_info = await service.spawn_agent(build_request())
        print(f"Session spawned: {session_info.session_id}")
        print(f"Status: {session_info.status}")

        await asyncio.sleep(2)

        print("Stopping session")
        stopped = await service.stop_agent(session_info.session_id)
        print(f"Stop result: {stopped}")
    finally:
        await service.cleanup()
        print("Cleanup complete")


if __name__ == "__main__":
    asyncio.run(main())
