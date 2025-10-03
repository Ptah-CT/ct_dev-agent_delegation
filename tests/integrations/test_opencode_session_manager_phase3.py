"""Tests for OpenCode Session Manager Phase 3 Features.

Tests the new features added in Phase 3:
- create_session with agent/model parameters
- get_config
- update_config
- list_commands
- execute_command
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from ct_dev_agent_orchestrator_mcp.services.session_manager import OpenCodeSessionManager


@pytest.fixture
def session_manager():
    """Create session manager instance with mocked API client."""
    mock_api_client = MagicMock()
    return OpenCodeSessionManager(api_client=mock_api_client)


@pytest.mark.asyncio
async def test_create_session_with_agent(session_manager):
    """Test creating session with agent parameter."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "id": "session-123",
        "title": "Test Session",
        "agent": "backend_specialist"
    }
    mock_response.raise_for_status = MagicMock()
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=mock_response
        )
        
        result = await session_manager.create_session(
            server_url="http://localhost:8000",
            agent="backend_specialist",
            title="Test Session"
        )
        
        assert result["session_id"] == "session-123"
        # Agent is stored in raw_data, not at top level
        assert result["raw_data"]["agent"] == "backend_specialist"


@pytest.mark.asyncio
async def test_create_session_with_model(session_manager):
    """Test creating session with model parameter."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "id": "session-456",
        "title": "Test Session",
        "model": "anthropic/claude-sonnet-4"
    }
    mock_response.raise_for_status = MagicMock()
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=mock_response
        )
        
        result = await session_manager.create_session(
            server_url="http://localhost:8000",
            model="anthropic/claude-sonnet-4",
            title="Test Session"
        )
        
        assert result["session_id"] == "session-456"
        # Model is stored in raw_data, not at top level
        assert result["raw_data"]["model"] == "anthropic/claude-sonnet-4"


@pytest.mark.asyncio
async def test_create_session_with_agent_and_model(session_manager):
    """Test creating session with both agent and model parameters."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "id": "session-789",
        "title": "Test Session",
        "agent": "backend_specialist",
        "model": "anthropic/claude-sonnet-4"
    }
    mock_response.raise_for_status = MagicMock()
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=mock_response
        )
        
        result = await session_manager.create_session(
            server_url="http://localhost:8000",
            agent="backend_specialist",
            model="anthropic/claude-sonnet-4",
            title="Test Session"
        )
        
        assert result["session_id"] == "session-789"
        assert result["raw_data"]["agent"] == "backend_specialist"
        assert result["raw_data"]["model"] == "anthropic/claude-sonnet-4"


@pytest.mark.asyncio
async def test_get_config_success(session_manager):
    """Test getting OpenCode configuration."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "theme": "dark",
        "model": {
            "modelID": "claude-sonnet-4",
            "providerID": "anthropic"
        },
        "agents": []
    }
    mock_response.raise_for_status = MagicMock()
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=mock_response
        )
        
        result = await session_manager.get_config(
            server_url="http://localhost:8000"
        )
        
        assert result["theme"] == "dark"
        assert result["model"]["modelID"] == "claude-sonnet-4"


@pytest.mark.asyncio
async def test_update_config_success(session_manager):
    """Test updating OpenCode configuration."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "theme": "light",
        "model": {
            "modelID": "claude-opus-4",
            "providerID": "anthropic"
        }
    }
    mock_response.raise_for_status = MagicMock()
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.patch = AsyncMock(
            return_value=mock_response
        )
        
        result = await session_manager.update_config(
            server_url="http://localhost:8000",
            config_update={"theme": "light"}
        )
        
        assert result["theme"] == "light"


@pytest.mark.asyncio
async def test_list_commands_success(session_manager):
    """Test listing available commands."""
    mock_response = MagicMock()
    mock_response.json.return_value = [
        {
            "name": "commit",
            "description": "Create a git commit"
        },
        {
            "name": "test",
            "description": "Run tests"
        }
    ]
    mock_response.raise_for_status = MagicMock()
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=mock_response
        )
        
        result = await session_manager.list_commands(
            server_url="http://localhost:8000"
        )
        
        assert len(result) == 2
        assert result[0]["name"] == "commit"
        assert result[1]["name"] == "test"


@pytest.mark.asyncio
async def test_execute_command_success(session_manager):
    """Test executing a command."""
    # Setup session mapping
    session_manager._server_mapping["session-123"] = "http://localhost:8000"
    
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "status": "success",
        "output": "Command executed successfully"
    }
    mock_response.raise_for_status = MagicMock()
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=mock_response
        )
        
        result = await session_manager.execute_command(
            session_id="session-123",
            command="commit",
            arguments={"message": "Test commit"}
        )
        
        assert result["status"] == "success"
        assert "successfully" in result["output"]


@pytest.mark.asyncio
async def test_get_config_error(session_manager):
    """Test get_config error handling."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            side_effect=httpx.HTTPError("Connection failed")
        )
        
        with pytest.raises(httpx.HTTPError):
            await session_manager.get_config(
                server_url="http://localhost:8000"
            )


@pytest.mark.asyncio
async def test_update_config_error(session_manager):
    """Test update_config error handling."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.patch = AsyncMock(
            side_effect=httpx.HTTPError("Connection failed")
        )
        
        with pytest.raises(httpx.HTTPError):
            await session_manager.update_config(
                server_url="http://localhost:8000",
                config_update={"theme": "dark"}
            )


@pytest.mark.asyncio
async def test_execute_command_unknown_session(session_manager):
    """Test execute_command with unknown session ID."""
    with pytest.raises(ValueError, match="Unknown session"):
        await session_manager.execute_command(
            session_id="unknown-session",
            command="test",
            arguments={}
        )
