#!/usr/bin/env python3
"""Test complete spawn -> stop agent flow."""

import asyncio
from src.ct_dev_agent_orchestrator_mcp.services.session_service import SessionService
from src.ct_dev_agent_orchestrator_mcp.models.session import SpawnAgentRequest

async def main():
    session_service = SessionService()

    try:
        print("Step 1: Spawning agent session...")
        request = SpawnAgentRequest(
            role="backend_specialist",
            task_id="test-task-stop-flow",
            instructions="Test task for stop flow",
            context={},
            model="claude-sonnet-4"
        )

        session_info = await session_service.spawn_agent(request)
        print(f"Session spawned: {session_info.session_id}")
        print(f"Status: {session_info.status}")
        print(f"Server URL: {session_info.server_url}")

        # Wait a moment for session to be fully established
        await asyncio.sleep(2)

        print("\nStep 2: Stopping agent session...")
        success = await session_service.stop_agent(session_info.session_id)
        print(f"Stop result: {success}")
        print(f"Stop result type: {type(success)}")

        if success:
            print("\nTest PASSED: Session stopped successfully")
        else:
            print("\nTest FAILED: Session stop returned False")

    except Exception as e:
        print(f"\nTest FAILED with exception: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        await session_service.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
