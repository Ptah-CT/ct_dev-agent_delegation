#!/usr/bin/env python3
"""
Integration test for Agent Orchestrator MCP with real agent instances.

This script tests:
1. Spawning real agent with OpenCode
2. Sending messages to agent
3. Querying session status
4. Stopping agent
5. Cleanup

Author: Claude
Constitution-compliant: Phase 3 Überprüfung
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ct_dev_agent_delegation_mcp.services.delegation_service import DelegationService
from ct_dev_agent_delegation_mcp.models.delegation import SpawnDelegationRequest


async def test_real_agent_lifecycle():
    """Test complete agent lifecycle with real OpenCode instance."""
    
    print("=" * 60)
    print("INTEGRATION TEST: Real Agent Instance")
    print("=" * 60)
    
    service = DelegationService()
    session_id = None
    
    try:
        # Step 1: Spawn agent
        print("\n[1/5] Spawning backend_specialist agent...")
        request = SpawnDelegationRequest(
            role="backend_specialist",
            task_id="test-task-001",
            instructions="You are a test agent. Please respond with 'Hello from backend specialist!'",
            context={"test": "integration"},
            model="claude-sonnet-4"
        )
        
        session_info = await service.spawn_agent(request)
        session_id = session_info.session_id
        
        print(f"✓ Agent spawned successfully")
        print(f"  Session ID: {session_id}")
        print(f"  Status: {session_info.status}")
        print(f"  Server URL: {session_info.server_url}")
        
        # Wait for agent to be ready
        await asyncio.sleep(5)
        
        # Step 2: Query session
        print("\n[2/5] Querying session status...")
        session_status = await service.query_session(session_id)
        print(f"✓ Session status retrieved")
        print(f"  Status: {session_status.status}")
        print(f"  Messages: {len(session_status.messages)}")
        
        # Step 3: Send message
        print("\n[3/5] Sending message to agent...")
        success = await service.send_to_agent(session_id, "Hello, agent! Please confirm you received this.")
        print(f"✓ Message sent: {success}")
        
        # Wait for response
        await asyncio.sleep(3)
        
        # Step 4: Query again
        print("\n[4/5] Querying session after message...")
        session_status = await service.query_session(session_id)
        print(f"✓ Session status retrieved")
        print(f"  Status: {session_status.status}")
        print(f"  Messages: {len(session_status.messages)}")
        if session_status.messages:
            print(f"  Last message: {session_status.messages[-1]}")
        
        # Step 5: List active sessions
        print("\n[5/5] Listing active sessions...")
        active_sessions = await service.list_active_sessions()
        print(f"✓ Found {len(active_sessions)} active session(s)")
        for sess in active_sessions:
            print(f"  - {sess.session_id}: {sess.agent_role} ({sess.status})")
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup
        if session_id:
            try:
                print("\n[CLEANUP] Stopping agent...")
                await service.stop_agent(session_id)
                print("✓ Agent stopped")
            except Exception as e:
                print(f"✗ Cleanup error: {e}")
        
        try:
            await service.cleanup()
        except Exception as e:
            print(f"✗ Service cleanup error: {e}")
    
    print("\n" + "=" * 60)
    print("INTEGRATION TEST COMPLETED SUCCESSFULLY")
    print("=" * 60)
    return True


async def test_concurrent_agents():
    """Test spawning multiple agents concurrently."""
    
    print("\n" + "=" * 60)
    print("CONCURRENT AGENTS TEST")
    print("=" * 60)
    
    service = DelegationService()
    session_ids = []
    
    try:
        # Spawn 2 agents concurrently
        print("\n[1/3] Spawning 2 agents concurrently...")
        
        requests = [
            SpawnDelegationRequest(
                role="backend_specialist",
                task_id=f"test-task-{i}",
                instructions=f"Test agent {i}",
                context={"index": i},
                model="claude-sonnet-4"
            )
            for i in range(1, 3)
        ]
        
        sessions = await asyncio.gather(*[
            service.spawn_agent(req) for req in requests
        ])
        
        session_ids = [s.session_id for s in sessions]
        
        print(f"✓ Spawned {len(sessions)} agents")
        for sess in sessions:
            print(f"  - {sess.session_id}: {sess.agent_role}")
        
        # Wait for agents to be ready
        await asyncio.sleep(5)
        
        # Step 2: List all active
        print("\n[2/3] Listing all active sessions...")
        active = await service.list_active_sessions()
        print(f"✓ Found {len(active)} active session(s)")
        
        # Step 3: Query each
        print("\n[3/3] Querying each session...")
        for session_id in session_ids:
            status = await service.query_session(session_id)
            print(f"✓ {session_id}: {status.status}")
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup all
        print("\n[CLEANUP] Stopping all agents...")
        for session_id in session_ids:
            try:
                await service.stop_agent(session_id)
                print(f"✓ Stopped {session_id}")
            except Exception as e:
                print(f"✗ Error stopping {session_id}: {e}")
        
        try:
            await service.cleanup()
        except:
            pass
    
    print("\n" + "=" * 60)
    print("CONCURRENT TEST COMPLETED")
    print("=" * 60)
    return True


async def main():
    """Run all integration tests."""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 8 + "Agent Orchestrator MCP - Integration Tests" + " " * 7 + "║")
    print("╚" + "═" * 58 + "╝")
    
    # Test 1: Basic lifecycle
    result1 = await test_real_agent_lifecycle()
    
    # Wait between tests
    await asyncio.sleep(2)
    
    # Test 2: Concurrent agents
    result2 = await test_concurrent_agents()
    
    # Summary
    print("\n\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Basic Lifecycle Test: {'✓ PASSED' if result1 else '✗ FAILED'}")
    print(f"Concurrent Agents Test: {'✓ PASSED' if result2 else '✗ FAILED'}")
    print("=" * 60)
    
    if result1 and result2:
        print("\n✅ ALL INTEGRATION TESTS PASSED")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
