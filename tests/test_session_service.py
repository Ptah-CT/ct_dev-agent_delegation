"""
Comprehensive unit tests for SessionService.

Tests all 6 core methods with mocked dependencies to ensure
proper functionality and error handling without external dependencies.

Author: Agent Orchestrator V2 Migration - Phase 2
Coverage Target: >80% for session_service.py
"""

import pytest
import asyncio
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from src.ct_dev_agent_orchestrator_mcp.services.session_service import SessionService
from src.ct_dev_agent_orchestrator_mcp.models.session import (
    SpawnAgentRequest,
    SessionInfo, 
    AgentOutput,
    SessionStatus
)


@pytest.fixture
def session_service():
    """Create SessionService instance with mocked dependencies."""
    with patch('src.ct_dev_agent_orchestrator_mcp.services.session_service.OpenCodeSessionManager') as mock_session_manager, \
         patch('src.ct_dev_agent_orchestrator_mcp.services.session_service.OpenCodeAPIClient') as mock_api_client, \
         patch('src.ct_dev_agent_orchestrator_mcp.services.session_service.AgentManager') as mock_agent_manager:
        
        service = SessionService()
        service.session_manager = AsyncMock()
        service.api_client = AsyncMock()
        service.agent_manager = AsyncMock()
        
        return service


@pytest.fixture
def sample_spawn_request():
    """Sample SpawnAgentRequest for testing."""
    return SpawnAgentRequest(
        role="backend_specialist",
        task_id="550e8400-e29b-41d4-a716-446655440000",
        instructions="Implement OAuth2 authentication endpoints",
        context={"framework": "FastAPI", "db": "PostgreSQL"},
        model="claude-sonnet-4"
    )


@pytest.fixture
def sample_session_info():
    """Sample SessionInfo for testing."""
    return SessionInfo(
        session_id="test-session-id",
        agent_role="backend_specialist",
        status=SessionStatus.RUNNING,
        started_at="2025-09-30T10:00:00Z",
        server_url="http://localhost:8000",
        progress={"step": "initializing"},
        messages=[]
    )


@pytest.fixture
def sample_agent_output():
    """Sample AgentOutput for testing."""
    return AgentOutput(
        session_id="test-session-id",
        status=SessionStatus.COMPLETED,
        artifacts={"code": "implementation.py", "tests": "test_implementation.py"},
        summary="OAuth2 authentication implemented successfully",
        duration_seconds=1800.0,
        completed_at="2025-09-30T10:30:00Z"
    )


class TestSpawnAgent:
    """Test spawn_agent method."""
    
    @pytest.mark.asyncio
    async def test_spawn_agent_success(self, session_service, sample_spawn_request, sample_session_info):
        """Test successful agent spawning."""
        # Setup mocks - create mock agent with port
        from src.ct_dev_agent_orchestrator_mcp.models.agent import Agent, AgentRole, AgentStatus
        mock_agent = Agent(
            agent_id="test-agent-id",
            role=AgentRole.BACKEND_SPECIALIST,
            status=AgentStatus.IDLE,
            port=8000,
            created_at="2025-09-30T10:00:00Z"
        )
        session_service.agent_manager.create_agent.return_value = mock_agent
        
        # create_session should return a dict, not SessionInfo
        session_dict = {
            "session_id": sample_session_info.session_id,
            "created_at": sample_session_info.started_at,
            "status": "running"
        }
        session_service.session_manager.create_session.return_value = session_dict
        
        # Execute
        result = await session_service.spawn_agent(sample_spawn_request)
        
        # Verify
        assert isinstance(result, SessionInfo)
        assert result.agent_role == "backend_specialist"
        assert result.status == SessionStatus.RUNNING
        assert result.server_url == "http://localhost:8000"
        
        # Verify session manager was called correctly
        session_service.session_manager.create_session.assert_called_once()
        call_args = session_service.session_manager.create_session.call_args
        assert call_args.kwargs['agent_name'] == sample_spawn_request.role
        assert call_args.kwargs['model'] == sample_spawn_request.model
    
    @pytest.mark.asyncio
    async def test_spawn_agent_timeout(self, session_service, sample_spawn_request):
        """Test agent spawning with timeout."""
        # Setup mocks
        session_service.session_manager.create_session.side_effect = asyncio.TimeoutError("Timeout")
        
        # Execute
        result = await session_service.spawn_agent(sample_spawn_request)
        
        # Verify failure handling
        assert isinstance(result, SessionInfo)
        assert result.status == SessionStatus.FAILED
        assert result.agent_role == "backend_specialist"
        assert result.server_url == ""
    
    @pytest.mark.asyncio
    async def test_spawn_agent_exception(self, session_service, sample_spawn_request):
        """Test agent spawning with unexpected exception."""
        # Setup mocks
        session_service.session_manager.create_session.side_effect = Exception("Unexpected error")
        
        # Execute & Verify
        with pytest.raises(Exception, match="Unexpected error"):
            await session_service.spawn_agent(sample_spawn_request)


class TestQuerySession:
    """Test query_session method."""
    
    @pytest.mark.asyncio
    async def test_query_session_success(self, session_service, sample_session_info):
        """Test successful session query."""
        # Setup mocks - get_session should return a dict, not SessionInfo
        session_dict = {
            "session_id": sample_session_info.session_id,
            "agent_role": sample_session_info.agent_role,
            "status": sample_session_info.status,
            "started_at": sample_session_info.started_at,
            "progress": sample_session_info.progress,
            "messages": sample_session_info.messages,
            "server_url": sample_session_info.server_url
        }
        session_service.session_manager.get_session.return_value = session_dict
        
        # Execute
        result = await session_service.query_session("test-session-id")
        
        # Verify
        assert isinstance(result, SessionInfo)
        assert result.session_id == "test-session-id"
        assert result.status == SessionStatus.RUNNING
        
        # Verify session manager was called
        session_service.session_manager.get_session.assert_called_once_with("test-session-id")
    
    @pytest.mark.asyncio
    async def test_query_session_not_found(self, session_service):
        """Test session query for non-existent session."""
        # Setup mocks
        session_service.session_manager.get_session.side_effect = Exception("Session not found")
        
        # Execute & Verify
        with pytest.raises(Exception, match="Session not found"):
            await session_service.query_session("non-existent-id")


class TestSendToAgent:
    """Test send_to_agent method."""
    
    @pytest.mark.asyncio
    async def test_send_to_agent_success(self, session_service):
        """Test successful message sending."""
        # Setup mocks
        session_service.session_manager.send_message.return_value = True
        
        # Execute
        result = await session_service.send_to_agent("test-session-id", "Additional instructions")
        
        # Verify
        assert result is True
        
        # Verify session manager was called
        session_service.session_manager.send_message.assert_called_once_with(
            "test-session-id", "Additional instructions"
        )
    
    @pytest.mark.asyncio
    async def test_send_to_agent_failure(self, session_service):
        """Test message sending failure."""
        # Setup mocks - return None to trigger failure
        session_service.session_manager.send_message.return_value = None
        
        # Execute
        result = await session_service.send_to_agent("test-session-id", "Message")
        
        # Verify - send_message returns False when response is None
        assert result is False
    
    @pytest.mark.asyncio
    async def test_send_to_agent_exception(self, session_service):
        """Test message sending with exception."""
        # Setup mocks
        session_service.session_manager.send_message.side_effect = Exception("Send failed")
        
        # Execute & Verify
        with pytest.raises(Exception, match="Send failed"):
            await session_service.send_to_agent("test-session-id", "Message")


class TestGetAgentOutput:
    """Test get_agent_output method."""
    
    @pytest.mark.asyncio
    async def test_get_agent_output_success(self, session_service):
        """Test successful agent output retrieval."""
        # Setup mocks - get_session should return dict
        completed_session_dict = {
            "session_id": "test-session-id",
            "agent_role": "backend_specialist",
            "status": SessionStatus.COMPLETED,
            "started_at": "2025-09-30T10:00:00Z",
            "server_url": "http://localhost:8000",
            "progress": {"artifacts": {"code": "implementation.py"}},
            "messages": []
        }
        
        messages = [
            {"role": "assistant", "content": "Task completed successfully"}
        ]
        
        session_service.session_manager.get_session.return_value = completed_session_dict
        session_service.session_manager.get_messages.return_value = messages
        
        # Execute with proper datetime mocking
        from datetime import timezone
        with patch('src.ct_dev_agent_orchestrator_mcp.services.session_service.datetime') as mock_datetime_class:
            # Mock datetime.fromisoformat
            started_dt = datetime(2025, 9, 30, 10, 0, 0, tzinfo=timezone.utc)
            mock_datetime_class.fromisoformat.return_value = started_dt
            
            # Mock datetime.now(timezone.utc)
            completed_dt = datetime(2025, 9, 30, 10, 30, 0, tzinfo=timezone.utc)
            mock_datetime_class.now.return_value = completed_dt
            
            result = await session_service.get_agent_output("test-session-id")
        
        # Verify
        assert isinstance(result, AgentOutput)
        assert result.session_id == "test-session-id"
        assert result.status == SessionStatus.COMPLETED
        assert result.artifacts == {"code": "implementation.py"}
        assert "Task completed successfully" in result.summary
        assert result.duration_seconds == 1800.0
    
    @pytest.mark.asyncio
    async def test_get_agent_output_not_completed(self, session_service, sample_session_info):
        """Test agent output retrieval for non-completed session."""
        # Setup mocks - convert SessionInfo to dict
        session_dict = {
            "session_id": sample_session_info.session_id,
            "agent_role": sample_session_info.agent_role,
            "status": sample_session_info.status,
            "started_at": sample_session_info.started_at,
            "progress": sample_session_info.progress,
            "messages": sample_session_info.messages,
            "server_url": sample_session_info.server_url
        }
        session_service.session_manager.get_session.return_value = session_dict
        
        # Execute & Verify
        with pytest.raises(ValueError, match="Session test-session-id not completed"):
            await session_service.get_agent_output("test-session-id")
    
    @pytest.mark.asyncio
    async def test_get_agent_output_failed_session(self, session_service):
        """Test agent output retrieval for failed session."""
        # Setup mocks - use dict
        failed_session_dict = {
            "session_id": "test-session-id",
            "agent_role": "backend_specialist",
            "status": SessionStatus.FAILED,
            "started_at": "2025-09-30T10:00:00Z",
            "server_url": "http://localhost:8000",
            "progress": {},
            "messages": []
        }
        
        session_service.session_manager.get_session.return_value = failed_session_dict
        session_service.session_manager.get_messages.return_value = []
        
        # Execute with proper datetime mocking
        from datetime import timezone
        with patch('src.ct_dev_agent_orchestrator_mcp.services.session_service.datetime') as mock_datetime_class:
            # Mock datetime.fromisoformat
            started_dt = datetime(2025, 9, 30, 10, 0, 0, tzinfo=timezone.utc)
            mock_datetime_class.fromisoformat.return_value = started_dt
            
            # Mock datetime.now(timezone.utc)
            completed_dt = datetime(2025, 9, 30, 10, 30, 0, tzinfo=timezone.utc)
            mock_datetime_class.now.return_value = completed_dt
            
            result = await session_service.get_agent_output("test-session-id")
        
        # Verify
        assert result.status == SessionStatus.FAILED
        assert result.summary == "Session completed"


class TestStopAgent:
    """Test stop_agent method."""
    
    @pytest.mark.asyncio
    async def test_stop_agent_success(self, session_service):
        """Test successful agent stopping."""
        # Setup mocks
        session_service.session_manager.abort_session.return_value = True
        
        # Execute
        result = await session_service.stop_agent("test-session-id")
        
        # Verify
        assert result is True
        
        # Verify session manager was called
        session_service.session_manager.abort_session.assert_called_once_with("test-session-id")
    
    @pytest.mark.asyncio
    async def test_stop_agent_failure(self, session_service):
        """Test agent stopping failure."""
        # Setup mocks
        session_service.session_manager.abort_session.return_value = False
        
        # Execute
        result = await session_service.stop_agent("test-session-id")
        
        # Verify
        assert result is False
    
    @pytest.mark.asyncio
    async def test_stop_agent_exception(self, session_service):
        """Test agent stopping with exception."""
        # Setup mocks
        session_service.session_manager.abort_session.side_effect = Exception("Stop failed")
        
        # Execute & Verify
        with pytest.raises(Exception, match="Stop failed"):
            await session_service.stop_agent("test-session-id")


class TestListActiveSessions:
    """Test list_active_sessions method."""
    
    @pytest.mark.asyncio
    async def test_list_active_sessions_success(self, session_service):
        """Test successful active sessions listing."""
        # Setup mocks
        all_sessions = [
            SessionInfo(
                session_id="session-1",
                agent_role="backend_specialist",
                status=SessionStatus.RUNNING,
                started_at="2025-09-30T10:00:00Z",
                server_url="http://localhost:8000",
                progress={},
                messages=[]
            ),
            SessionInfo(
                session_id="session-2",
                agent_role="frontend_specialist", 
                status=SessionStatus.COMPLETED,
                started_at="2025-09-30T09:00:00Z",
                server_url="http://localhost:8001",
                progress={},
                messages=[]
            ),
            SessionInfo(
                session_id="session-3",
                agent_role="security_expert",
                status=SessionStatus.STARTING,
                started_at="2025-09-30T10:30:00Z",
                server_url="http://localhost:8002",
                progress={},
                messages=[]
            )
        ]
        
        session_service.session_manager.list_sessions.return_value = all_sessions
        
        # Execute
        result = await session_service.list_active_sessions()
        
        # Verify
        assert len(result) == 2  # Only RUNNING and STARTING sessions
        assert all(session.status in [SessionStatus.RUNNING, SessionStatus.STARTING] for session in result)
        assert any(session.session_id == "session-1" for session in result)
        assert any(session.session_id == "session-3" for session in result)
        assert not any(session.session_id == "session-2" for session in result)  # COMPLETED should be filtered out
    
    @pytest.mark.asyncio
    async def test_list_active_sessions_empty(self, session_service):
        """Test active sessions listing when no sessions exist."""
        # Setup mocks
        session_service.session_manager.list_sessions.return_value = []
        
        # Execute
        result = await session_service.list_active_sessions()
        
        # Verify
        assert result == []
    
    @pytest.mark.asyncio
    async def test_list_active_sessions_exception(self, session_service):
        """Test active sessions listing with exception."""
        # Setup mocks
        session_service.session_manager.list_sessions.side_effect = Exception("List failed")
        
        # Execute & Verify
        with pytest.raises(Exception, match="List failed"):
            await session_service.list_active_sessions()


class TestCleanup:
    """Test cleanup method."""
    
    @pytest.mark.asyncio
    async def test_cleanup_success(self, session_service):
        """Test successful cleanup."""
        # Setup mocks
        session_service.session_manager.cleanup.return_value = None
        session_service.api_client.cleanup.return_value = None
        
        # Execute
        await session_service.cleanup()
        
        # Verify
        session_service.session_manager.cleanup.assert_called_once()
        session_service.api_client.cleanup.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cleanup_exception(self, session_service):
        """Test cleanup with exception."""
        # Setup mocks
        session_service.session_manager.cleanup.side_effect = Exception("Cleanup failed")
        
        # Execute & Verify
        with pytest.raises(Exception, match="Cleanup failed"):
            await session_service.cleanup()


class TestConcurrency:
    """Test concurrency and semaphore behavior."""
    
    @pytest.mark.asyncio
    async def test_semaphore_limiting(self, session_service, sample_spawn_request, sample_session_info):
        """Test that semaphore limits concurrent operations."""
        # Setup mocks - create mock agent
        from src.ct_dev_agent_orchestrator_mcp.models.agent import Agent, AgentRole, AgentStatus
        mock_agent = Agent(
            agent_id="test-agent-id",
            role=AgentRole.BACKEND_SPECIALIST,
            status=AgentStatus.IDLE,
            port=8000,
            created_at="2025-09-30T10:00:00Z"
        )
        session_service.agent_manager.create_agent.return_value = mock_agent
        
        # Setup slow mock that takes time and returns dict
        async def slow_create_session(*args, **kwargs):
            await asyncio.sleep(0.1)
            return {
                "session_id": sample_session_info.session_id,
                "created_at": sample_session_info.started_at,
                "status": "running"
            }
        
        session_service.session_manager.create_session.side_effect = slow_create_session
        
        # Execute multiple operations concurrently
        tasks = [
            session_service.spawn_agent(sample_spawn_request)
            for _ in range(10)
        ]
        
        start_time = asyncio.get_event_loop().time()
        results = await asyncio.gather(*tasks)
        end_time = asyncio.get_event_loop().time()
        
        # Verify
        assert len(results) == 10
        assert all(isinstance(result, SessionInfo) for result in results)
        
        # With semaphore limit of 5, execution should take at least 0.2 seconds
        # (2 batches of 5 concurrent operations, each taking 0.1 seconds)
        assert end_time - start_time >= 0.15  # Allow some margin for timing