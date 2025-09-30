#!/usr/bin/env python3
"""
Quick integration test for adapted service layer.

Tests adapted services against real OpenCode 0.13.5 API.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ct_dev_agent_orchestrator_mcp.services.opencode_api_client import OpenCodeAPIClient
from ct_dev_agent_orchestrator_mcp.services.session_manager import OpenCodeSessionManager
from ct_dev_agent_orchestrator_mcp.models.agent import Agent, AgentRole, AgentStatus


async def test_adapted_services():
    """Test adapted service layer with real OpenCode API."""
    
    print("=" * 70)
    print(" " * 15 + "Service Layer Integration Test")
    print("=" * 70)
    
    # Initialize services
    api_client = OpenCodeAPIClient(base_port=9900, max_agents=5)
    session_manager = OpenCodeSessionManager(api_client)
    
    # Create test agent
    from datetime import datetime, timezone
    agent = Agent(
        agent_id="test-agent-001",
        role=AgentRole.BACKEND_SPECIALIST,
        status=AgentStatus.IDLE,
        created_at=datetime.now(timezone.utc).isoformat()
    )
    
    try:
        # Test 1: Start OpenCode server
        print("\n[1/6] Starting OpenCode server...")
        server_info = await api_client.start_agent_server(agent)
        server_url = server_info["url"]
        port = server_info["port"]
        print(f"✓ Server started: {server_url}")
        print(f"  PID: {server_info['pid']}, Port: {port}")
        
        # Test 2: Check health
        print("\n[2/6] Checking server health...")
        healthy = await api_client.check_health(server_url)
        if healthy:
            print("✓ Server healthy")
        else:
            print("✗ Server not healthy")
            return False
        
        # Test 3: Get available agents
        print("\n[3/6] Fetching available agents...")
        agents = await session_manager.get_available_agents(server_url)
        print(f"✓ Found {len(agents)} agents")
        print(f"  First 3: {', '.join([a['name'] for a in agents[:3]])}")
        
        # Test 4: Get available providers
        print("\n[4/6] Fetching available providers...")
        providers_data = await session_manager.get_available_providers(server_url)
        providers = providers_data.get("providers", [])
        print(f"✓ Found {len(providers)} providers")
        
        if not providers:
            print("✗ No providers available")
            return False
        
        # Get first provider with models
        provider = providers[0]
        provider_id = provider["id"]
        models = provider.get("models", {})
        if not models:
            print("✗ Provider has no models")
            return False
        
        model_id = list(models.keys())[0]
        print(f"  Using: {provider_id}/{model_id}")
        
        # Test 5: Create session
        print("\n[5/6] Creating session...")
        session = await session_manager.create_session(
            server_url=server_url,
            title="Service Layer Test Session"
        )
        session_id = session["session_id"]
        print(f"✓ Session created: {session_id}")
        
        # Test 6: Send message
        print("\n[6/6] Sending message to AI...")
        response = await session_manager.send_message(
            session_id=session_id,
            message="Please respond with exactly: 'Service layer test successful'",
            agent_name=agents[0]["name"],  # Use first available agent
            provider_id=provider_id,
            model_id=model_id
        )
        
        print("✓ Message sent and response received")
        
        # Extract response text
        if "parts" in response:
            for part in response["parts"]:
                if part.get("type") == "text":
                    text = part.get("text", "")[:100]
                    print(f"  Response: {text}...")
                    break
        
        print("\n" + "=" * 70)
        print(" " * 20 + "✓ ALL TESTS PASSED")
        print("=" * 70)
        return True
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup
        print("\n[CLEANUP] Stopping server...")
        try:
            await api_client.stop_agent_server(port)
            print("✓ Server stopped")
        except Exception as e:
            print(f"✗ Cleanup error: {e}")


if __name__ == "__main__":
    success = asyncio.run(test_adapted_services())
    exit(0 if success else 1)
