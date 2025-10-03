#!/usr/bin/env python3
"""Quick test script for ct_dev-agent_orchestrator-mcp."""

import asyncio
from ct_dev_agent_delegation_mcp.services.opencode_service import OpenCodeService
from ct_dev_agent_delegation_mcp.services.agent_manager import AgentManager
from ct_dev_agent_delegation_mcp.services.delegation_service import DelegationService
from ct_dev_agent_delegation_mcp.models.agent import AgentRole
from ct_dev_agent_delegation_mcp.models.delegation import DelegationRequest


async def test_agent_creation():
    """Test creating an agent."""
    print("🧪 Testing Agent Creation...")
    
    opencode_service = OpenCodeService(base_port=8100, max_agents=3)
    agent_manager = AgentManager(opencode_service)
    
    try:
        await agent_manager.start()
        print("✓ Agent manager started")
        
        # Create an agent
        agent = await agent_manager.create_agent(AgentRole.GENERIC_ENGINEER)
        print(f"✓ Agent created: {agent.agent_id}")
        print(f"  Role: {agent.role}")
        print(f"  Status: {agent.status}")
        print(f"  Port: {agent.port}")
        print(f"  PID: {agent.pid}")
        
        # Check health
        is_healthy = await opencode_service.check_health(agent)
        print(f"  Health: {'✓ Healthy' if is_healthy else '✗ Unhealthy'}")
        
        # List agents
        agents = await agent_manager.list_agents()
        print(f"\n✓ Total agents: {len(agents)}")
        
        # Stop agent
        await agent_manager.remove_agent(agent.agent_id)
        print(f"✓ Agent removed: {agent.agent_id}")
        
    finally:
        await agent_manager.stop()
        print("✓ Agent manager stopped")


async def test_delegation_flow():
    """Test delegation flow."""
    print("\n🧪 Testing Delegation Flow...")
    
    opencode_service = OpenCodeService(base_port=8100, max_agents=3)
    agent_manager = AgentManager(opencode_service)
    delegation_service = DelegationService(agent_manager, opencode_service)
    
    try:
        await agent_manager.start()
        
        # Create delegation request
        request = DelegationRequest(
            task_id="test-task-123",
            agent_role="generic_engineer",
            instructions="This is a test delegation",
            context={"test": True},
            timeout_seconds=30
        )
        
        # Delegate work
        response = await delegation_service.delegate(request)
        print(f"✓ Work delegated")
        print(f"  Delegation ID: {response.delegation_id}")
        print(f"  Agent ID: {response.agent_id}")
        print(f"  Status: {response.status}")
        
        # Check status
        status = await delegation_service.get_status(response.delegation_id)
        print(f"\n✓ Delegation status retrieved")
        print(f"  Status: {status['status']}")
        print(f"  Created: {status['created_at']}")
        
        # Wait a bit
        await asyncio.sleep(2)
        
        # Check status again
        status = await delegation_service.get_status(response.delegation_id)
        print(f"\n✓ Updated status: {status['status']}")
        
    finally:
        await agent_manager.stop()


async def main():
    """Run tests."""
    print("=" * 60)
    print("ct_dev-agent_orchestrator-mcp Test Suite")
    print("=" * 60)
    
    try:
        # Test 1: Agent Creation
        await test_agent_creation()
        
        # Test 2: Delegation Flow (commented out as it requires actual opencode)
        # await test_delegation_flow()
        
        print("\n" + "=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
