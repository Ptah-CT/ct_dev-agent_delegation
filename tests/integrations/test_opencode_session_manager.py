"""
Tests for OpenCode Session Manager

🜄 Verantwortung: Test coverage for OpenCode REST API integration
🜄 Autor: Claude (Agent Orchestrator MCP)
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from src.integrations.opencode_session_manager import (
    OpencodeSessionManager,
    OpencodeAgent,
    OpencodeModel,
    OpencodeSession,
    OpencodeMessage,
    SessionStatus
)


@pytest.fixture
async def session_manager():
    """Create test session manager"""
    manager = OpencodeSessionManager(
        base_url="http://localhost:7777",
        project_directory="/test/project"
    )
    yield manager
    await manager.close()


@pytest.fixture
def mock_agents_response():
    """Mock agents list response"""
    return [
        {
            "name": "test-agent",
            "description": "Test agent description",
            "mode": "primary",
            "builtIn": True,
            "temperature": 0.7,
            "topP": 0.9,
            "model": {
                "providerID": "anthropic",
                "modelID": "claude-sonnet-4"
            },
            "tools": {
                "bash": True,
                "edit": True
            }
        }
    ]


@pytest.fixture
def mock_providers_response():
    """Mock providers response"""
    return {
        "providers": [
            {
                "id": "anthropic",
                "name": "Anthropic",
                "models": {
                    "claude-sonnet-4": {
                        "id": "claude-sonnet-4",
                        "name": "Claude Sonnet 4",
                        "attachment": True,
                        "reasoning": True,
                        "temperature": True,
                        "tool_call": True,
                        "experimental": False,
                        "cost": {
                            "input": 0.003,
                            "output": 0.015
                        },
                        "limit": {
                            "context": 200000,
                            "output": 8192
                        }
                    }
                }
            }
        ],
        "default": {
            "anthropic": "claude-sonnet-4"
        }
    }


@pytest.fixture
def mock_session_response():
    """Mock session response"""
    return {
        "id": "ses_test123",
        "projectID": "proj_test",
        "directory": "/test/project",
        "title": "Test Session",
        "version": "1.0.0",
        "time": {
            "created": 1234567890,
            "updated": 1234567890
        }
    }


@pytest.fixture
def mock_message_response():
    """Mock message response"""
    return {
        "info": {
            "id": "msg_test123",
            "sessionID": "ses_test123",
            "role": "assistant",
            "time": {
                "created": 1234567890,
                "completed": 1234567891
            },
            "modelID": "claude-sonnet-4",
            "providerID": "anthropic",
            "cost": 0.05,
            "tokens": {
                "input": 1000,
                "output": 500,
                "reasoning": 0,
                "cache": {
                    "read": 0,
                    "write": 100
                }
            }
        },
        "parts": [
            {
                "id": "prt_test123",
                "type": "text",
                "text": "Test response"
            }
        ]
    }


# ========================
# Agent Discovery Tests
# ========================


@pytest.mark.asyncio
async def test_list_agents_success(session_manager, mock_agents_response):
    """Test successful agent listing"""
    with patch.object(session_manager.client, 'get') as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = mock_agents_response
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        agents = await session_manager.list_agents()
        
        assert len(agents) == 1
        assert isinstance(agents[0], OpencodeAgent)
        assert agents[0].name == "test-agent"
        assert agents[0].mode == "primary"
        assert agents[0].built_in is True


@pytest.mark.asyncio
async def test_list_agents_caching(session_manager, mock_agents_response):
    """Test agent list caching"""
    with patch.object(session_manager.client, 'get') as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = mock_agents_response
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # First call
        agents1 = await session_manager.list_agents()
        assert mock_get.call_count == 1
        
        # Second call (should use cache)
        agents2 = await session_manager.list_agents()
        assert mock_get.call_count == 1
        assert agents1 == agents2
        
        # Force refresh
        agents3 = await session_manager.list_agents(force_refresh=True)
        assert mock_get.call_count == 2


@pytest.mark.asyncio
async def test_get_agent_found(session_manager, mock_agents_response):
    """Test getting specific agent"""
    with patch.object(session_manager.client, 'get') as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = mock_agents_response
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        agent = await session_manager.get_agent("test-agent")
        
        assert agent is not None
        assert agent.name == "test-agent"


@pytest.mark.asyncio
async def test_get_agent_not_found(session_manager, mock_agents_response):
    """Test getting non-existent agent"""
    with patch.object(session_manager.client, 'get') as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = mock_agents_response
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        agent = await session_manager.get_agent("nonexistent")
        
        assert agent is None


# ========================
# Model Discovery Tests
# ========================


@pytest.mark.asyncio
async def test_list_providers_success(session_manager, mock_providers_response):
    """Test successful provider listing"""
    with patch.object(session_manager.client, 'get') as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = mock_providers_response
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        providers = await session_manager.list_providers()
        
        assert 'providers' in providers
        assert len(providers['providers']) == 1
        assert providers['providers'][0]['id'] == 'anthropic'


@pytest.mark.asyncio
async def test_list_models_success(session_manager, mock_providers_response):
    """Test successful model listing"""
    with patch.object(session_manager.client, 'get') as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = mock_providers_response
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        models = await session_manager.list_models()
        
        assert len(models) == 1
        assert isinstance(models[0], OpencodeModel)
        assert models[0].id == "claude-sonnet-4"
        assert models[0].provider_id == "anthropic"


@pytest.mark.asyncio
async def test_get_model_found(session_manager, mock_providers_response):
    """Test getting specific model"""
    with patch.object(session_manager.client, 'get') as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = mock_providers_response
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        model = await session_manager.get_model("anthropic", "claude-sonnet-4")
        
        assert model is not None
        assert model.id == "claude-sonnet-4"
        assert model.provider_id == "anthropic"


# ========================
# Session Management Tests
# ========================


@pytest.mark.asyncio
async def test_create_session_success(session_manager, mock_session_response):
    """Test successful session creation"""
    with patch.object(session_manager.client, 'post') as mock_post:
        mock_response = Mock()
        mock_response.json.return_value = mock_session_response
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        session = await session_manager.create_session(title="Test Session")
        
        assert isinstance(session, OpencodeSession)
        assert session.id == "ses_test123"
        assert session.title == "Test Session"


@pytest.mark.asyncio
async def test_get_session_success(session_manager, mock_session_response):
    """Test getting session by ID"""
    with patch.object(session_manager.client, 'get') as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = mock_session_response
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        session = await session_manager.get_session("ses_test123")
        
        assert session.id == "ses_test123"
        assert session.project_id == "proj_test"


@pytest.mark.asyncio
async def test_list_sessions_success(session_manager, mock_session_response):
    """Test listing all sessions"""
    with patch.object(session_manager.client, 'get') as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = [mock_session_response]
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        sessions = await session_manager.list_sessions()
        
        assert len(sessions) == 1
        assert sessions[0].id == "ses_test123"


@pytest.mark.asyncio
async def test_delete_session_success(session_manager):
    """Test session deletion"""
    with patch.object(session_manager.client, 'delete') as mock_delete:
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_delete.return_value = mock_response
        
        result = await session_manager.delete_session("ses_test123")
        
        assert result is True


# ========================
# Message Management Tests
# ========================


@pytest.mark.asyncio
async def test_send_message_success(session_manager, mock_message_response):
    """Test sending message"""
    with patch.object(session_manager.client, 'post') as mock_post:
        mock_response = Mock()
        mock_response.json.return_value = mock_message_response
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        message = await session_manager.send_message(
            session_id="ses_test123",
            text="Test message",
            agent="test-agent"
        )
        
        assert isinstance(message, OpencodeMessage)
        assert message.id == "msg_test123"
        assert message.role == "assistant"


@pytest.mark.asyncio
async def test_send_message_with_model(session_manager, mock_message_response):
    """Test sending message with specific model"""
    with patch.object(session_manager.client, 'post') as mock_post:
        mock_response = Mock()
        mock_response.json.return_value = mock_message_response
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        message = await session_manager.send_message(
            session_id="ses_test123",
            text="Test message",
            provider_id="anthropic",
            model_id="claude-sonnet-4"
        )
        
        # Verify model was included in request
        call_kwargs = mock_post.call_args.kwargs
        assert 'json' in call_kwargs
        assert 'model' in call_kwargs['json']


@pytest.mark.asyncio
async def test_list_messages_success(session_manager, mock_message_response):
    """Test listing messages"""
    with patch.object(session_manager.client, 'get') as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = [mock_message_response]
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        messages = await session_manager.list_messages("ses_test123")
        
        assert len(messages) == 1
        assert messages[0].id == "msg_test123"


@pytest.mark.asyncio
async def test_get_message_success(session_manager, mock_message_response):
    """Test getting specific message"""
    with patch.object(session_manager.client, 'get') as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = mock_message_response
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        message = await session_manager.get_message("ses_test123", "msg_test123")
        
        assert message.id == "msg_test123"
        assert message.session_id == "ses_test123"


@pytest.mark.asyncio
async def test_abort_session_success(session_manager):
    """Test aborting session"""
    with patch.object(session_manager.client, 'post') as mock_post:
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        result = await session_manager.abort_session("ses_test123")
        
        assert result is True


# ========================
# Error Handling Tests
# ========================


@pytest.mark.asyncio
async def test_list_agents_error(session_manager):
    """Test agent listing error handling"""
    with patch.object(session_manager.client, 'get') as mock_get:
        mock_get.side_effect = Exception("API Error")
        
        agents = await session_manager.list_agents()
        
        assert agents == []


@pytest.mark.asyncio
async def test_send_message_error(session_manager):
    """Test message sending error handling"""
    with patch.object(session_manager.client, 'post') as mock_post:
        mock_post.side_effect = Exception("API Error")
        
        with pytest.raises(Exception):
            await session_manager.send_message(
                session_id="ses_test123",
                text="Test message"
            )


# ========================
# Context Manager Tests
# ========================


@pytest.mark.asyncio
async def test_context_manager():
    """Test async context manager"""
    async with OpencodeSessionManager() as manager:
        assert manager is not None
    # Should close client automatically
