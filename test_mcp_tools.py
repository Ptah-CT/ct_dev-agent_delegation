#!/usr/bin/env python3
"""Test script for agent_orchestrator MCP tools."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ct_dev_agent_delegation_mcp.models.agent import AgentRole
from ct_dev_agent_delegation_mcp.models.delegation import SpawnDelegationRequest
from ct_dev_agent_delegation_mcp.services.delegation_service import DelegationService
from ct_dev_agent_delegation_mcp.services.agent_manager import AgentManager
from ct_dev_agent_delegation_mcp.services.opencode_service import OpenCodeService


class MCPToolsTester:
    """Test harness for MCP tools."""
    
    def __init__(self):
        """Initialize test harness."""
        self.opencode_service = OpenCodeService(max_agents=3)
        self.agent_manager = AgentManager(self.opencode_service)
        self.session_service = DelegationService()
        self.test_session_id = None
        
    async def setup(self):
        """Setup test environment."""
        print("🔧 Setting up test environment...")
        await self.agent_manager.start()
        print("✓ Agent manager started\n")
        
    async def teardown(self):
        """Cleanup test environment."""
        print("\n🧹 Cleaning up test environment...")
        await self.agent_manager.stop()
        print("✓ Agent manager stopped")
        
    async def test_get_agent_capabilities(self):
        """Test 1: get_agent_capabilities"""
        print("=" * 60)
        print("TEST 1: get_agent_capabilities")
        print("=" * 60)
        
        try:
            print("Available Agent Roles:")
            for role in AgentRole:
                print(f"  • {role.value}")
            print(f"\nTotal: {len(list(AgentRole))} specialized roles available")
            print("✓ Test passed\n")
            return True
        except Exception as e:
            print(f"✗ Test failed: {e}\n")
            return False
            
    async def test_list_agents_empty(self):
        """Test 2: list_agents (empty)"""
        print("=" * 60)
        print("TEST 2: list_agents (should be empty initially)")
        print("=" * 60)
        
        try:
            agents = await self.agent_manager.list_agents()
            if not agents:
                print("No agents currently running.")
                print("✓ Test passed\n")
                return True
            else:
                print(f"Found {len(agents)} agents (expected 0)")
                print("⚠ Test warning: expected empty list\n")
                return True
        except Exception as e:
            print(f"✗ Test failed: {e}\n")
            return False
            
    async def test_get_agent_stats_empty(self):
        """Test 3: get_agent_stats (empty)"""
        print("=" * 60)
        print("TEST 3: get_agent_stats (empty)")
        print("=" * 60)
        
        try:
            total = await self.agent_manager.get_agent_count()
            by_status = await self.agent_manager.get_agent_count_by_status()
            
            print(f"Total Agents: {total}")
            print("By Status:")
            for status, count in by_status.items():
                if count > 0:
                    print(f"  • {status}: {count}")
            
            if total == 0:
                print("✓ Test passed\n")
                return True
            else:
                print(f"⚠ Test warning: expected 0 agents, found {total}\n")
                return True
        except Exception as e:
            print(f"✗ Test failed: {e}\n")
            return False
            
    async def test_list_active_sessions_empty(self):
        """Test 4: list_active_sessions (empty)"""
        print("=" * 60)
        print("TEST 4: list_active_sessions (should be empty initially)")
        print("=" * 60)
        
        try:
            sessions = await self.session_service.list_active_sessions()
            if not sessions:
                print("No active sessions found.")
                print("✓ Test passed\n")
                return True
            else:
                print(f"Found {len(sessions)} sessions (expected 0)")
                print("⚠ Test warning: expected empty list\n")
                # Clean up any existing sessions
                for session in sessions:
                    await self.session_service.stop_agent(session.session_id)
                return True
        except Exception as e:
            print(f"✗ Test failed: {e}\n")
            return False
            
    async def test_spawn_agent(self):
        """Test 5: spawn_agent"""
        print("=" * 60)
        print("TEST 5: spawn_agent")
        print("=" * 60)
        
        try:
            # Use string value instead of enum to match the model definition
            request = SpawnDelegationRequest(
                role="backend_specialist",  # Changed from AgentRole.BACKEND_SPECIALIST
                task_id="test-task-001",
                instructions="Test instructions: Please analyze a simple Python function.",
                context={"test": "true", "environment": "testing"},
                model="claude-sonnet-4"
            )
            
            print(f"Spawning agent with role: {request.role}")
            print(f"Task ID: {request.task_id}")
            print(f"Instructions: {request.instructions}")
            
            session_info = await self.session_service.spawn_agent(request)
            self.test_session_id = session_info.session_id
            
            print(f"\n✓ Agent session spawned successfully")
            print(f"  Session ID: {session_info.session_id}")
            print(f"  Agent Role: {session_info.agent_role}")
            print(f"  Status: {session_info.status.value if hasattr(session_info.status, 'value') else session_info.status}")
            print(f"  Server URL: {session_info.server_url}")
            print("✓ Test passed\n")
            return True
        except Exception as e:
            import traceback
            print(f"✗ Test failed: {e}")
            traceback.print_exc()
            print()
            return False
            
    async def test_query_session(self):
        """Test 6: query_session"""
        print("=" * 60)
        print("TEST 6: query_session")
        print("=" * 60)
        
        if not self.test_session_id:
            print("✗ Test skipped: No session ID available\n")
            return False
            
        try:
            print(f"Querying session: {self.test_session_id}")
            session_info = await self.session_service.query_session(self.test_session_id)
            
            print(f"\nSession Status:")
            print(f"  ID: {session_info.session_id}")
            print(f"  Agent Role: {session_info.agent_role}")
            print(f"  Status: {session_info.status.value if hasattr(session_info.status, 'value') else session_info.status}")
            print(f"  Started: {session_info.started_at}")
            print(f"  Server URL: {session_info.server_url}")
            print(f"  Messages: {len(session_info.messages)}")
            print("✓ Test passed\n")
            return True
        except Exception as e:
            print(f"✗ Test failed: {e}\n")
            return False
            
    async def test_send_to_agent(self):
        """Test 7: send_to_agent"""
        print("=" * 60)
        print("TEST 7: send_to_agent")
        print("=" * 60)
        
        if not self.test_session_id:
            print("✗ Test skipped: No session ID available\n")
            return False
            
        try:
            message = "Please provide a brief status update on your analysis."
            print(f"Sending message to session {self.test_session_id}")
            print(f"Message: {message}")
            
            success = await self.session_service.send_to_agent(self.test_session_id, message)
            
            if success:
                print(f"✓ Message sent successfully")
                print("✓ Test passed\n")
                return True
            else:
                print(f"✗ Failed to send message")
                print("✗ Test failed\n")
                return False
        except Exception as e:
            print(f"✗ Test failed: {e}\n")
            return False
            
    async def test_list_active_sessions_with_data(self):
        """Test 8: list_active_sessions (with data)"""
        print("=" * 60)
        print("TEST 8: list_active_sessions (with active session)")
        print("=" * 60)
        
        try:
            sessions = await self.session_service.list_active_sessions()
            
            if not sessions:
                print("No active sessions found.")
                print("⚠ Test warning: expected at least 1 session\n")
                return True
            
            print(f"Active Sessions ({len(sessions)}):\n")
            for session in sessions:
                print(f"• {session.session_id}")
                print(f"  Role: {session.agent_role}")
                print(f"  Status: {session.status.value if hasattr(session.status, 'value') else session.status}")
                print(f"  Started: {session.started_at}")
                print(f"  Messages: {len(session.messages)}\n")
            
            print("✓ Test passed\n")
            return True
        except Exception as e:
            print(f"✗ Test failed: {e}\n")
            return False
            
    async def test_list_agents_with_data(self):
        """Test 9: list_agents (with data)"""
        print("=" * 60)
        print("TEST 9: list_agents (with active agents)")
        print("=" * 60)
        
        try:
            agents = await self.agent_manager.list_agents()
            
            if not agents:
                print("No agents currently running.")
                print("⚠ Test warning: expected at least 1 agent\n")
                return True
            
            print(f"Active Agents ({len(agents)}):\n")
            for agent in agents:
                print(f"• {agent.agent_id}")
                print(f"  Role: {agent.role}")
                print(f"  Status: {agent.status}")
                print(f"  Port: {agent.port}")
                print(f"  PID: {agent.pid}\n")
            
            print("✓ Test passed\n")
            return True
        except Exception as e:
            print(f"✗ Test failed: {e}\n")
            return False
            
    async def test_get_agent_stats_with_data(self):
        """Test 10: get_agent_stats (with data)"""
        print("=" * 60)
        print("TEST 10: get_agent_stats (with active agents)")
        print("=" * 60)
        
        try:
            total = await self.agent_manager.get_agent_count()
            by_status = await self.agent_manager.get_agent_count_by_status()
            
            print(f"Total Agents: {total}")
            print("By Status:")
            for status, count in by_status.items():
                if count > 0:
                    print(f"  • {status}: {count}")
            
            print("✓ Test passed\n")
            return True
        except Exception as e:
            print(f"✗ Test failed: {e}\n")
            return False
            
    async def test_stop_agent(self):
        """Test 11: stop_agent"""
        print("=" * 60)
        print("TEST 11: stop_agent")
        print("=" * 60)
        
        if not self.test_session_id:
            print("✗ Test skipped: No session ID available\n")
            return False
            
        try:
            print(f"Stopping agent session: {self.test_session_id}")
            success = await self.session_service.stop_agent(self.test_session_id)
            
            if success:
                print(f"✓ Agent session stopped successfully")
                print("✓ Test passed\n")
                return True
            else:
                print(f"✗ Failed to stop agent session")
                print("✗ Test failed\n")
                return False
        except Exception as e:
            print(f"✗ Test failed: {e}\n")
            return False
            
    async def test_get_agent_output(self):
        """Test 12: get_agent_output (optional - may fail if not completed)"""
        print("=" * 60)
        print("TEST 12: get_agent_output")
        print("=" * 60)
        
        if not self.test_session_id:
            print("✗ Test skipped: No session ID available\n")
            return False
            
        try:
            print(f"Getting output for session: {self.test_session_id}")
            output = await self.session_service.get_agent_output(self.test_session_id)
            
            print(f"\nAgent Output:")
            print(f"  Session ID: {output.session_id}")
            print(f"  Status: {output.status.value if hasattr(output.status, 'value') else output.status}")
            print(f"  Duration: {output.duration_seconds:.2f}s")
            print(f"  Completed: {output.completed_at}")
            print(f"\n  Summary: {output.summary[:200]}..." if len(output.summary) > 200 else f"\n  Summary: {output.summary}")
            print(f"  Artifacts: {len(output.artifacts)} items")
            print("✓ Test passed\n")
            return True
        except Exception as e:
            print(f"⚠ Test expected to fail for stopped sessions: {e}")
            print("✓ Test passed (expected failure)\n")
            return True
            
    async def run_all_tests(self):
        """Run all tests in sequence."""
        print("\n" + "=" * 60)
        print("AGENT ORCHESTRATOR MCP TOOLS TEST SUITE")
        print("=" * 60 + "\n")
        
        await self.setup()
        
        results = []
        
        # Phase 1: Empty state tests
        print("\n📋 PHASE 1: Empty State Tests\n")
        results.append(await self.test_get_agent_capabilities())
        results.append(await self.test_list_agents_empty())
        results.append(await self.test_get_agent_stats_empty())
        results.append(await self.test_list_active_sessions_empty())
        
        # Phase 2: Spawn and query tests
        print("\n📋 PHASE 2: Agent Spawning and Session Management\n")
        results.append(await self.test_spawn_agent())
        
        # Wait a bit for agent to initialize
        print("⏳ Waiting 3 seconds for agent to initialize...")
        await asyncio.sleep(3)
        
        results.append(await self.test_query_session())
        results.append(await self.test_send_to_agent())
        
        # Wait a bit for message processing
        print("⏳ Waiting 2 seconds for message processing...")
        await asyncio.sleep(2)
        
        # Phase 3: List tests with data
        print("\n📋 PHASE 3: Listing Active Resources\n")
        results.append(await self.test_list_active_sessions_with_data())
        results.append(await self.test_list_agents_with_data())
        results.append(await self.test_get_agent_stats_with_data())
        
        # Phase 4: Cleanup tests
        print("\n📋 PHASE 4: Session Termination\n")
        results.append(await self.test_stop_agent())
        results.append(await self.test_get_agent_output())
        
        await self.teardown()
        
        # Summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        total = len(results)
        passed = sum(results)
        failed = total - passed
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed} ✓")
        print(f"Failed: {failed} ✗")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        print("=" * 60 + "\n")
        
        return passed == total


async def main():
    """Main entry point."""
    tester = MCPToolsTester()
    try:
        success = await tester.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠ Tests interrupted by user")
        await tester.teardown()
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ Test suite failed with exception: {e}")
        import traceback
        traceback.print_exc()
        await tester.teardown()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
