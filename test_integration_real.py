"""Integration test for ct_dev-agent_delegation-mcp with a real OpenCode agent."""

import asyncio
from datetime import datetime, timezone

from ct_dev_agent_delegation_mcp.services.delegation_service import DelegationService
from ct_dev_agent_delegation_mcp.models.delegation import SpawnDelegationRequest


def build_request() -> SpawnDelegationRequest:
    now = datetime.now(timezone.utc).isoformat()
    return SpawnDelegationRequest(
        role="backend_specialist",
        task_id="integration-real",
        instructions="Reply with a simple acknowledgement and list working files.",
        project_directory="/tmp",
        expected_output="Completion summary",
        context={"test": "integration"},
        model="claude-sonnet-4",
        original_task={
            "task_id": "integration-origin",
            "title": "Real agent integration test",
            "description": "Verify end-to-end flow against a live OpenCode agent.",
            "requester": "Auctor",
            "requested_at": now
        },
        cap_origin={
            "ultimate_authority": "Auctor",
            "original_scope": "Delegation platform validation",
            "granted_at": now,
            "grant_context": "Integration smoke test"
        },
        delegation_context={
            "delegator": "Project Manager",
            "delegator_cap": f"Integration validation authority (Auctor, {now})",
            "delegated_to": "backend_specialist",
            "delegated_cap": "Complete acknowledgement workflow",
            "constraints": ["No external network calls"],
            "phantom_level": "Delegation/Cap",
            "delegated_at": now
        }
    )


async def test_real_agent_lifecycle() -> None:
    print("=== Integration Test: Real Agent Instance ===")
    service = DelegationService()
    session_info = None

    try:
        request = build_request()
        session_info = await service.spawn_agent(request)
        session_id = session_info.session_id
        print(f"Session ID: {session_id}")
        print(f"Server URL: {session_info.server_url}")

        await asyncio.sleep(5)
        status = await service.query_session(session_id)
        print(f"Status after spawn: {status.status} (messages={len(status.messages)})")

        await service.send_to_agent(session_id, "Please confirm receipt and list the current directory contents.")
        print("Follow-up message sent")

        await asyncio.sleep(5)
        status = await service.query_session(session_id)
        print(f"Status after follow-up: {status.status} (messages={len(status.messages)})")
        if status.messages:
            print(f"Last message snippet: {status.messages[-1]}")

        output = await service.get_agent_output(session_id)
        print(f"Final status: {output.status}")
        print(f"Duration: {output.duration_seconds:.2f}s")
        print(f"Summary snippet: {output.summary[:200]}")

    finally:
        if session_info:
            await service.stop_agent(session_info.session_id)
        await service.cleanup()
        print("Cleanup complete")


if __name__ == "__main__":
    asyncio.run(test_real_agent_lifecycle())
