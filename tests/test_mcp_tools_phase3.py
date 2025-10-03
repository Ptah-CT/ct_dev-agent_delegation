"""Tests for MCP Tools Phase 3 Features.

Tests the new MCP tools added in Phase 3:
- list_opencode_agents
- list_opencode_models
- get_agent_capabilities (OpenCode integration)
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from ct_dev_agent_orchestrator_mcp.server import call_tool


@pytest.mark.asyncio
async def test_list_opencode_agents_success():
    """Test list_opencode_agents tool returns agents from OpenCode."""
    from ct_dev_agent_orchestrator_mcp.opencode_client import OpenCodeAgent
    
    mock_agents = [
        OpenCodeAgent(
            name="backend_specialist",
            description="Backend development expert",
            mode="subagent",
            built_in=True,
            model={"modelID": "claude-sonnet-4", "providerID": "anthropic"},
            permission={},
            tools={},
            temperature=1.0
        ),
        OpenCodeAgent(
            name="frontend_specialist",
            description="Frontend development expert",
            mode="subagent",
            built_in=True,
            model={"modelID": "claude-sonnet-4", "providerID": "anthropic"},
            permission={},
            tools={},
            temperature=1.0
        )
    ]
    
    with patch("ct_dev_agent_orchestrator_mcp.server.opencode_service") as mock_service:
        mock_client = MagicMock()
        mock_client.list_agents = AsyncMock(return_value=mock_agents)
        mock_service.process_manager.opencode_client = mock_client
        
        result = await call_tool("list_opencode_agents", {"force_refresh": False})
        
        assert len(result) == 1
        assert "backend_specialist" in result[0].text
        assert "frontend_specialist" in result[0].text
        assert "Backend development expert" in result[0].text


@pytest.mark.asyncio
async def test_list_opencode_agents_force_refresh():
    """Test list_opencode_agents with force_refresh parameter."""
    from ct_dev_agent_orchestrator_mcp.opencode_client import OpenCodeAgent
    
    mock_agents = [
        OpenCodeAgent(
            name="test_agent",
            description="Test agent",
            mode="primary",
            built_in=True,
            model={"modelID": "test-model", "providerID": "test"},
            permission={},
            tools={}
        )
    ]
    
    with patch("ct_dev_agent_orchestrator_mcp.server.opencode_service") as mock_service:
        mock_client = MagicMock()
        mock_client.list_agents = AsyncMock(return_value=mock_agents)
        mock_service.process_manager.opencode_client = mock_client
        
        result = await call_tool("list_opencode_agents", {"force_refresh": True})
        
        assert len(result) == 1
        assert "test_agent" in result[0].text
        
        # Verify force_refresh was passed to client
        mock_client.list_agents.assert_called_once_with(force_refresh=True)


@pytest.mark.asyncio
async def test_list_opencode_agents_error():
    """Test list_opencode_agents error handling."""
    with patch("ct_dev_agent_orchestrator_mcp.server.opencode_service") as mock_service:
        mock_client = MagicMock()
        mock_client.list_agents = AsyncMock(side_effect=Exception("Connection failed"))
        mock_service.process_manager.opencode_client = mock_client
        
        result = await call_tool("list_opencode_agents", {})
        
        assert len(result) == 1
        assert "success" in result[0].text
        assert "false" in result[0].text
        assert "Connection failed" in result[0].text


@pytest.mark.asyncio
async def test_list_opencode_models_success():
    """Test list_opencode_models tool returns models from OpenCode."""
    from ct_dev_agent_orchestrator_mcp.opencode_client import OpenCodeModel
    
    mock_models = [
        OpenCodeModel(
            id="claude-sonnet-4",
            name="Claude Sonnet 4",
            provider_id="anthropic",
            release_date="2025-01-01",
            attachment=True,
            reasoning=True,
            temperature=True,
            tool_call=True,
            cost={"input": 0.003, "output": 0.015},
            limit={"context": 200000, "output": 8096}
        ),
        OpenCodeModel(
            id="gpt-4",
            name="GPT-4",
            provider_id="openai",
            release_date="2023-03-14",
            attachment=True,
            reasoning=False,
            temperature=True,
            tool_call=True,
            cost={"input": 0.01, "output": 0.03},
            limit={"context": 128000, "output": 4096}
        )
    ]
    
    # Mock providers dict structure
    mock_providers = {
        "anthropic": [mock_models[0]],
        "openai": [mock_models[1]]
    }
    
    with patch("ct_dev_agent_orchestrator_mcp.server.opencode_service") as mock_service:
        mock_client = MagicMock()
        mock_client.list_providers = AsyncMock(return_value=mock_providers)
        mock_service.process_manager.opencode_client = mock_client
        
        result = await call_tool("list_opencode_models", {"force_refresh": False})
        
        assert len(result) == 1
        assert "claude-sonnet-4" in result[0].text
        assert "gpt-4" in result[0].text
        assert "anthropic" in result[0].text


@pytest.mark.asyncio
async def test_list_opencode_models_force_refresh():
    """Test list_opencode_models with force_refresh parameter."""
    from ct_dev_agent_orchestrator_mcp.opencode_client import OpenCodeModel
    
    mock_model = OpenCodeModel(
        id="test-model",
        name="Test Model",
        provider_id="test",
        release_date="2025-01-01",
        attachment=True,
        reasoning=False,
        temperature=True,
        tool_call=True,
        cost={"input": 0.001, "output": 0.002},
        limit={"context": 100000, "output": 4096}
    )
    
    mock_providers = {"test": [mock_model]}
    
    with patch("ct_dev_agent_orchestrator_mcp.server.opencode_service") as mock_service:
        mock_client = MagicMock()
        mock_client.list_providers = AsyncMock(return_value=mock_providers)
        mock_service.process_manager.opencode_client = mock_client
        
        result = await call_tool("list_opencode_models", {"force_refresh": True})
        
        # Verify force_refresh was passed to client
        mock_client.list_providers.assert_called_once_with(force_refresh=True)
        assert len(result) == 1
        assert "test-model" in result[0].text


@pytest.mark.asyncio
async def test_list_opencode_models_error():
    """Test list_opencode_models error handling."""
    with patch("ct_dev_agent_orchestrator_mcp.server.opencode_service") as mock_service:
        mock_client = MagicMock()
        mock_client.list_providers = AsyncMock(side_effect=Exception("Failed to fetch models"))
        mock_service.process_manager.opencode_client = mock_client
        
        result = await call_tool("list_opencode_models", {})
        
        assert len(result) == 1
        assert "success" in result[0].text
        assert "false" in result[0].text
        assert "Failed to fetch models" in result[0].text


@pytest.mark.asyncio
async def test_get_agent_capabilities_opencode():
    """Test get_agent_capabilities uses OpenCode agent list."""
    mock_agents = [
        {
            "name": "backend_specialist",
            "description": "Backend expert",
            "mode": "subagent"
        },
        {
            "name": "plan",
            "description": "Planning agent",
            "mode": "primary"
        }
    ]
    
    with patch("ct_dev_agent_orchestrator_mcp.server.opencode_service") as mock_service:
        mock_service.api_client.fetch_available_agents = AsyncMock(return_value=mock_agents)
        
        result = await call_tool("get_agent_capabilities", {})
        
        assert len(result) == 1
        assert "backend_specialist" in result[0].text
        assert "plan" in result[0].text
        assert "Backend expert" in result[0].text
        assert "Planning agent" in result[0].text


@pytest.mark.asyncio
async def test_spawn_agent_with_opencode_role():
    """Test spawn_agent accepts dynamic OpenCode agent role."""
    # This test verifies that spawn_agent now accepts any string role
    # instead of being restricted to AgentRole enum
    
    # Create mock SessionInfo object
    mock_session_info = MagicMock()
    mock_session_info.session_id = "session-123"
    mock_session_info.agent_role = "custom_opencode_agent"
    mock_session_info.status = "running"
    mock_session_info.server_url = "http://localhost:8000"
    mock_session_info.delegation_context = {
        "delegator": "Test Delegator",
        "delegated_cap": "Test Delegated Cap"
    }
    
    with patch("ct_dev_agent_orchestrator_mcp.server.session_service") as mock_service:
        mock_service.spawn_agent = AsyncMock(return_value=mock_session_info)
        
        # Use a custom OpenCode agent role (not in original AgentRole enum)
        result = await call_tool("spawn_agent", {
            "role": "custom_opencode_agent",
            "task_id": "task-123",
            "instructions": "Test instructions",
            "project_directory": "/test/dir",
            "expected_output": "Test output",
            "original_task": {
                "task_id": "task-123",
                "title": "Test Task",
                "description": "Test Description",
                "requester": "Test User",
                "requested_at": "2025-10-03T00:00:00Z"
            },
            "cap_origin": {
                "ultimate_authority": "Auctor",
                "original_scope": "Test Scope",
                "granted_at": "2025-10-03T00:00:00Z",
                "grant_context": "Test Context"
            },
            "delegation_context": {
                "delegator": "Test Delegator",
                "delegator_cap": "Test Cap",
                "delegated_to": "custom_opencode_agent",
                "delegated_cap": "Test Delegated Cap",
                "constraints": [],
                "phantom_level": "Test Level",
                "delegated_at": "2025-10-03T00:00:00Z"
            }
        })
        
        assert len(result) == 1
        assert "session-123" in result[0].text
        assert "custom_opencode_agent" in result[0].text
        # Verify custom role was accepted
        mock_service.spawn_agent.assert_called_once()


@pytest.mark.asyncio
async def test_list_opencode_agents_empty():
    """Test list_opencode_agents with no agents available."""
    with patch("ct_dev_agent_orchestrator_mcp.server.opencode_service") as mock_service:
        mock_client = MagicMock()
        mock_client.list_agents = AsyncMock(return_value=[])
        mock_service.process_manager.opencode_client = mock_client
        
        result = await call_tool("list_opencode_agents", {})
        
        assert len(result) == 1
        # Check for JSON structure with count: 0
        assert '"count": 0' in result[0].text or '"agents": []' in result[0].text


@pytest.mark.asyncio
async def test_list_opencode_models_empty():
    """Test list_opencode_models with no models available."""
    with patch("ct_dev_agent_orchestrator_mcp.server.opencode_service") as mock_service:
        mock_client = MagicMock()
        mock_client.list_providers = AsyncMock(return_value={})
        mock_service.process_manager.opencode_client = mock_client
        
        result = await call_tool("list_opencode_models", {})
        
        assert len(result) == 1
        # Check for JSON structure with empty providers or models
        assert '"providers": []' in result[0].text or '"models": []' in result[0].text
