#!/usr/bin/env python3
"""Test OpenCode abort API directly to check response."""

import asyncio
import httpx
from src.ct_dev_agent_orchestrator_mcp.services.session_service import SessionService
from src.ct_dev_agent_orchestrator_mcp.models.session import SpawnAgentRequest

async def main():
    session_service = SessionService()

    try:
        print("Creating session...")
        request = SpawnAgentRequest(
            role="backend_specialist",
            task_id="test-abort-api",
            instructions="Test abort API",
            context={},
            model="claude-sonnet-4"
        )

        session_info = await session_service.spawn_agent(request)
        print(f"Session created: {session_info.session_id}")
        print(f"Server URL: {session_info.server_url}")

        await asyncio.sleep(2)

        # Test abort API directly
        print(f"\nCalling POST {session_info.server_url}/session/{session_info.session_id}/abort")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{session_info.server_url}/session/{session_info.session_id}/abort"
            )

            print(f"Response status: {response.status_code}")
            print(f"Response headers: {response.headers}")
            print(f"Response text: '{response.text}'")
            print(f"Response json(): {response.json()}")
            print(f"Type: {type(response.json())}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await session_service.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
