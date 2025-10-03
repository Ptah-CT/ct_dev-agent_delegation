"""Probe the OpenCode abort endpoint against a live delegation session."""

import asyncio
import httpx
from datetime import datetime, timezone

from ct_dev_agent_delegation_mcp.services.delegation_service import DelegationService
from ct_dev_agent_delegation_mcp.models.delegation import SpawnDelegationRequest


def build_request() -> SpawnDelegationRequest:
    now = datetime.now(timezone.utc).isoformat()
    return SpawnDelegationRequest(
        role="backend_specialist",
        task_id="abort-test",
        instructions="Wait idle for abort verification.",
        project_directory="/tmp",
        expected_output="Abort acknowledgement",
        context={},
        model="claude-sonnet-4",
        original_task={
            "task_id": "abort-origin",
            "title": "Abort API test",
            "description": "Validate abort endpoint behaviour for delegation sessions.",
            "requester": "Auctor",
            "requested_at": now
        },
        cap_origin={
            "ultimate_authority": "Auctor",
            "original_scope": "Delegation infrastructure validation",
            "granted_at": now,
            "grant_context": "Abort API smoke test"
        },
        delegation_context={
            "delegator": "Project Manager",
            "delegator_cap": f"Abort validation authority (Auctor, {now})",
            "delegated_to": "backend_specialist",
            "delegated_cap": "Respond to abort request",
            "constraints": ["Do not perform extra actions"],
            "phantom_level": "Delegation/Cap",
            "delegated_at": now
        }
    )


async def main() -> None:
    service = DelegationService()

    try:
        print("Creating delegation session for abort test")
        request = build_request()
        session_info = await service.spawn_agent(request)
        session_id = session_info.session_id
        print(f"Session created: {session_id}")
        print(f"Server URL: {session_info.server_url}")

        await asyncio.sleep(2)

        url = f"{session_info.server_url}/session/{session_id}/abort"
        print(f"Invoking abort endpoint: {url}")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url)
            print(f"Status: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            print(f"Body: {response.text}")

    finally:
        await service.cleanup()
        print("Session cleanup complete")


if __name__ == "__main__":
    asyncio.run(main())
