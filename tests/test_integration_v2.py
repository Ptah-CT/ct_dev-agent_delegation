"""
Comprehensive Integration Tests for V2 Session-based Agent Orchestrator.

Tests end-to-end functionality of the V2 architecture including:
- Complete session lifecycle flows
- MCP tools integration with real session management
- Concurrency and performance under load
- Error scenarios and recovery mechanisms

Author: Agent Orchestrator V2 Migration - Phase 4
Coverage Target: >80% integration test coverage
"""

import pytest
import asyncio
import uuid
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch, Mock

import httpx
from mcp.types import TextContent

from src.ct_dev_agent_orchestrator_mcp.services.session_service import SessionService
from src.ct_dev_agent_orchestrator_mcp.models.session import (
    SpawnAgentRequest,
    SessionInfo,
    AgentOutput,
    SessionStatus
)
from src.ct_dev_agent_orchestrator_mcp.models.agent import AgentRole
from ct_dev_agent_orchestrator_mcp.server import call_tool


class MockOpenCodeAPI:
    """Mock OpenCode API for integration testing."""
    
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.messages: Dict[str, List[Dict[str, Any]]] = {}
        self.fail_operations = set()
        self.delay_operations = {}
        
    async def create_session(self, session_id: str, agent_role: str, instructions: str, context: Dict, model: str) -> SessionInfo:
        """Mock session creation."""
        if "create_session" in self.fail_operations:
            raise httpx.HTTPError("API connection failed")
            
        if "create_session" in self.delay_operations:
            await asyncio.sleep(self.delay_operations["create_session"])
            
        session_data = {
            "session_id": session_id,
            "agent_role": agent_role,
            "status": SessionStatus.STARTING,
            "started_at": datetime.now().isoformat(),
            "server_url": f"http://localhost:800{len(self.sessions) + 1}",
            "progress": {},
            "messages": []
        }
        
        self.sessions[session_id] = session_data
        self.messages[session_id] = []
        
        # Simulate transition to RUNNING after brief delay
        await asyncio.sleep(0.1)
        session_data["status"] = SessionStatus.RUNNING
        
        return SessionInfo(**session_data)
    
    async def get_session(self, session_id: str) -> SessionInfo:
        """Mock session retrieval."""
        if "get_session" in self.fail_operations:
            raise httpx.HTTPError("Session not found")
            
        if session_id not in self.sessions:
            raise httpx.HTTPError("Session not found")
            
        session_data = self.sessions[session_id].copy()
        session_data["messages"] = self.messages[session_id].copy()
        
        return SessionInfo(**session_data)
    
    async def send_message(self, session_id: str, message: str) -> bool:
        """Mock message sending."""
        if "send_message" in self.fail_operations:
            raise httpx.HTTPError("Failed to send message")
            
        if session_id not in self.sessions:
            return False
            
        self.messages[session_id].append({
            "timestamp": datetime.now().isoformat(),
            "content": message,
            "type": "user"
        })
        
        # Simulate agent response
        await asyncio.sleep(0.05)
        self.messages[session_id].append({
            "timestamp": datetime.now().isoformat(),
            "content": f"Agent response to: {message[:50]}...",
            "type": "assistant"
        })
        
        return True
    
    async def abort_session(self, session_id: str) -> bool:
        """Mock session abortion."""
        if session_id not in self.sessions:
            return False
            
        self.sessions[session_id]["status"] = SessionStatus.CANCELLED
        return True
    
    async def get_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """Mock message retrieval."""
        if session_id not in self.messages:
            return []
        return self.messages[session_id]
    
    async def list_sessions(self) -> List[SessionInfo]:
        """Mock session listing."""
        return [SessionInfo(**data) for data in self.sessions.values()]
    
    def set_failure_mode(self, operation: str, should_fail: bool = True):
        """Set specific operations to fail for testing."""
        if should_fail:
            self.fail_operations.add(operation)
        else:
            self.fail_operations.discard(operation)
    
    def set_delay(self, operation: str, delay_seconds: float):
        """Set delays for operations to test timeouts."""
        self.delay_operations[operation] = delay_seconds


@pytest.fixture
def mock_api():
    """Create mock API instance."""
    return MockOpenCodeAPI()


@pytest.fixture
async def integration_session_service(mock_api):
    """Create SessionService with mocked OpenCode API for integration testing."""
    with patch('src.ct_dev_agent_orchestrator_mcp.services.session_service.OpenCodeSessionManager') as mock_session_manager:
        # Configure the mock to use our mock API
        mock_session_manager.return_value.create_session = mock_api.create_session
        mock_session_manager.return_value.get_session = mock_api.get_session
        mock_session_manager.return_value.send_message = mock_api.send_message
        mock_session_manager.return_value.abort_session = mock_api.abort_session
        mock_session_manager.return_value.get_messages = mock_api.get_messages
        mock_session_manager.return_value.list_sessions = mock_api.list_sessions
        
        service = SessionService()
        service.session_manager = mock_session_manager.return_value
        
        yield service


@pytest.fixture
def sample_spawn_request():
    """Sample SpawnAgentRequest for integration testing."""
    return SpawnAgentRequest(
        role=AgentRole.BACKEND_SPECIALIST,
        task_id=str(uuid.uuid4()),
        instructions="Implement OAuth2 authentication with JWT tokens",
        context={
            "framework": "FastAPI",
            "database": "PostgreSQL", 
            "requirements": ["security", "scalability"]
        },
        model="claude-sonnet-4"
    )


class TestEndToEndSessionLifecycle:
    """Test complete session lifecycle flows."""
    
    @pytest.mark.asyncio
    async def test_complete_session_lifecycle_success(self, integration_session_service, sample_spawn_request, mock_api):
        """Test successful complete lifecycle: spawn → query → send → output → stop."""
        service = integration_session_service
        
        # 1. Spawn agent
        session_info = await service.spawn_agent(sample_spawn_request)
        assert session_info.session_id is not None
        assert session_info.status == SessionStatus.RUNNING
        assert session_info.server_url is not None
        
        session_id = session_info.session_id
        
        # 2. Query session status
        queried_session = await service.query_session(session_id)
        assert queried_session.session_id == session_id
        assert queried_session.status == SessionStatus.RUNNING
        
        # 3. Send message to agent
        message_sent = await service.send_to_agent(session_id, "Implement user registration endpoint")
        assert message_sent is True
        
        # 4. Get agent output (first mark session as completed)
        mock_api.sessions[session_id]["status"] = SessionStatus.COMPLETED
        agent_output = await service.get_agent_output(session_id)
        assert agent_output is not None
        assert agent_output.status == SessionStatus.COMPLETED
        assert agent_output.duration_seconds > 0
        
        # 5. Stop agent
        stopped = await service.stop_agent(session_id)
        assert stopped is True
        
        # Verify session is stopped
        final_session = await service.query_session(session_id)
        assert final_session.status == SessionStatus.CANCELLED
    
    @pytest.mark.asyncio
    async def test_multiple_message_exchange(self, integration_session_service, sample_spawn_request, mock_api):
        """Test multiple message exchanges in a session."""
        service = integration_session_service
        
        # Spawn agent
        session_info = await service.spawn_agent(sample_spawn_request)
        session_id = session_info.session_id
        
        # Send multiple messages
        messages = [
            "Create the user model with email and password fields",
            "Add password hashing with bcrypt", 
            "Implement login endpoint with JWT generation",
            "Add refresh token mechanism"
        ]
        
        for message in messages:
            sent = await service.send_to_agent(session_id, message)
            assert sent is True
            
            # Small delay to allow processing
            await asyncio.sleep(0.1)
        
        # Get final output (mark session as completed first)
        mock_api.sessions[session_id]["status"] = SessionStatus.COMPLETED
        output = await service.get_agent_output(session_id)
        assert output.status == SessionStatus.COMPLETED
        
        # Stop session
        await service.stop_agent(session_id)
    
    @pytest.mark.asyncio
    async def test_session_lifecycle_with_different_agents(self, integration_session_service, mock_api):
        """Test lifecycle with different agent types."""
        service = integration_session_service
        
        # Test different agent roles
        agent_configs = [
            (AgentRole.BACKEND_SPECIALIST, "Implement REST API"),
            (AgentRole.FRONTEND_SPECIALIST, "Create user interface"),
            (AgentRole.CODE_REVIEWER, "Review code quality"),
            (AgentRole.SYSTEM_ARCHITECT, "Design system architecture")
        ]
        
        sessions = []
        
        for role, instructions in agent_configs:
            request = SpawnAgentRequest(
                role=role,
                task_id=str(uuid.uuid4()),
                instructions=instructions,
                context={"project": "oauth_system"},
                model="claude-sonnet-4"
            )
            
            session_info = await service.spawn_agent(request)
            assert session_info.agent_role == role.value
            sessions.append(session_info.session_id)
        
        # Interact with all sessions
        for session_id in sessions:
            sent = await service.send_to_agent(session_id, "What should I focus on first?")
            assert sent is True
            
            # Mark session as completed and get output
            mock_api.sessions[session_id]["status"] = SessionStatus.COMPLETED
            output = await service.get_agent_output(session_id)
            assert output is not None
            assert output.status == SessionStatus.COMPLETED
        
        # Clean up all sessions
        for session_id in sessions:
            stopped = await service.stop_agent(session_id)
            assert stopped is True


class TestMCPToolsIntegration:
    """Test MCP tools integration with session management."""
    
    @pytest.mark.asyncio
    async def test_spawn_agent_mcp_tool(self, mock_api):
        """Test spawn_agent MCP tool integration."""
        with patch('ct_dev_agent_orchestrator_mcp.server.session_service') as mock_service:
            # Setup mock session service
            mock_session_info = SessionInfo(
                session_id="test-session-123",
                agent_role=AgentRole.BACKEND_SPECIALIST.value,
                status=SessionStatus.RUNNING,
                started_at=datetime.now().isoformat(),
                server_url="http://localhost:8001",
                progress={},
                messages=[]
            )
            mock_service.spawn_agent = AsyncMock(return_value=mock_session_info)
            
            # Call MCP tool
            result = await call_tool("spawn_agent", {
                "role": "backend_specialist",
                "task_id": "550e8400-e29b-41d4-a716-446655440000",
                "instructions": "Implement OAuth2 endpoints",
                "context": {"framework": "FastAPI"},
                "model": "claude-sonnet-4"
            })
            
            # Verify result
            assert len(result) == 1
            assert isinstance(result[0], TextContent)
            assert "Agent session spawned successfully" in result[0].text
            assert "test-session-123" in result[0].text
    
    @pytest.mark.asyncio
    async def test_full_mcp_workflow(self, mock_api):
        """Test complete workflow through MCP tools."""
        session_id = None
        
        with patch('ct_dev_agent_orchestrator_mcp.server.session_service') as mock_service:
            # Mock all session service methods
            mock_session_info = SessionInfo(
                session_id="integration-test-session",
                agent_role=AgentRole.BACKEND_SPECIALIST.value,
                status=SessionStatus.RUNNING,
                started_at=datetime.now().isoformat(),
                server_url="http://localhost:8001",
                progress={},
                messages=[]
            )
            
            mock_service.spawn_agent = AsyncMock(return_value=mock_session_info)
            mock_service.query_session = AsyncMock(return_value=mock_session_info)
            mock_service.send_to_agent = AsyncMock(return_value=True)
            mock_service.get_agent_output = AsyncMock(return_value=AgentOutput(
                session_id="integration-test-session",
                status=SessionStatus.COMPLETED,
                artifacts={},
                summary="Session completed successfully",
                duration_seconds=0.15,
                completed_at=datetime.now().isoformat()
            ))
            mock_service.stop_agent = AsyncMock(return_value=True)
            mock_service.list_active_sessions = AsyncMock(return_value=[mock_session_info])
            
            # 1. Spawn agent
            spawn_result = await call_tool("spawn_agent", {
                "role": "backend_specialist",
                "task_id": str(uuid.uuid4()),
                "instructions": "Build API endpoints"
            })
            assert "Agent session spawned successfully" in spawn_result[0].text
            session_id = "integration-test-session"
            
            # 2. Query session
            query_result = await call_tool("query_session", {
                "session_id": session_id
            })
            assert "Status: running" in query_result[0].text
            
            # 3. Send message
            send_result = await call_tool("send_to_agent", {
                "session_id": session_id,
                "message": "Create user authentication endpoints"
            })
            assert "Message sent to agent session" in send_result[0].text
            
            # 4. Get output
            output_result = await call_tool("get_agent_output", {
                "session_id": session_id
            })
            assert "Agent Output" in output_result[0].text
            assert "Duration:" in output_result[0].text
            
            # 5. List sessions
            list_result = await call_tool("list_active_sessions", {})
            assert "Active Sessions (1)" in list_result[0].text
            
            # 6. Stop agent
            stop_result = await call_tool("stop_agent", {
                "session_id": session_id
            })
            assert "stopped successfully" in stop_result[0].text


class TestConcurrencyAndPerformance:
    """Test concurrency handling and performance characteristics."""
    
    @pytest.mark.asyncio
    async def test_concurrent_session_spawning(self, integration_session_service, mock_api):
        """Test concurrent session spawning up to semaphore limit."""
        service = integration_session_service
        
        # Add delay to create_session to test semaphore behavior
        mock_api.set_delay("create_session", 0.2)
        
        # Create multiple spawn requests
        requests = [
            SpawnAgentRequest(
                role=AgentRole.BACKEND_SPECIALIST,
                task_id=str(uuid.uuid4()),
                instructions=f"Task {i}",
                context={"task_num": i},
                model="claude-sonnet-4"
            )
            for i in range(8)  # More than semaphore limit of 5
        ]
        
        # Execute concurrently
        start_time = time.time()
        tasks = [service.spawn_agent(req) for req in requests]
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        # Verify all succeeded
        assert len(results) == 8
        assert all(isinstance(result, SessionInfo) for result in results)
        assert all(result.status == SessionStatus.RUNNING for result in results)
        
        # Should take at least 0.4 seconds (2 batches of 5 with 0.2s delay each)
        # but less than 1.6 seconds (8 sequential operations)
        duration = end_time - start_time
        assert 0.3 < duration < 1.0, f"Duration {duration} not in expected range"
        
        # Clean up
        for result in results:
            await service.stop_agent(result.session_id)
    
    @pytest.mark.asyncio
    async def test_concurrent_message_sending(self, integration_session_service, sample_spawn_request, mock_api):
        """Test concurrent message sending to multiple sessions."""
        service = integration_session_service
        
        # Create multiple sessions
        sessions = []
        for i in range(3):
            request = SpawnAgentRequest(
                role=AgentRole.BACKEND_SPECIALIST,
                task_id=str(uuid.uuid4()),
                instructions=f"Session {i} task",
                context={"session_num": i},
                model="claude-sonnet-4"
            )
            session_info = await service.spawn_agent(request)
            sessions.append(session_info.session_id)
        
        # Send messages concurrently to all sessions
        messages = [f"Task for session {i}" for i in range(len(sessions))]
        send_tasks = [
            service.send_to_agent(session_id, message)
            for session_id, message in zip(sessions, messages)
        ]
        
        send_results = await asyncio.gather(*send_tasks)
        assert all(result is True for result in send_results)
        
        # Mark sessions as completed and get outputs concurrently
        for session_id in sessions:
            mock_api.sessions[session_id]["status"] = SessionStatus.COMPLETED
            
        output_tasks = [service.get_agent_output(session_id) for session_id in sessions]
        outputs = await asyncio.gather(*output_tasks)
        
        assert len(outputs) == 3
        assert all(output is not None for output in outputs)
        assert all(output.status == SessionStatus.COMPLETED for output in outputs)
        
        # Clean up
        for session_id in sessions:
            await service.stop_agent(session_id)
    
    @pytest.mark.asyncio
    async def test_session_timeout_handling(self, integration_session_service, sample_spawn_request, mock_api):
        """Test handling of slow operations and timeouts."""
        service = integration_session_service
        
        # Set a very long delay for create_session
        mock_api.set_delay("create_session", 2.0)
        
        # Test that operations complete despite delays
        start_time = time.time()
        session_info = await service.spawn_agent(sample_spawn_request)
        end_time = time.time()
        
        assert session_info is not None
        assert end_time - start_time >= 2.0  # Should respect the delay
        
        await service.stop_agent(session_info.session_id)


class TestErrorScenarios:
    """Test error scenarios and recovery mechanisms."""
    
    @pytest.mark.asyncio
    async def test_api_connection_failure(self, integration_session_service, sample_spawn_request, mock_api):
        """Test handling of API connection failures."""
        service = integration_session_service
        
        # Set API to fail
        mock_api.set_failure_mode("create_session", True)
        
        # Should raise exception on spawn failure
        with pytest.raises(Exception):  # Should be HTTPError or similar
            await service.spawn_agent(sample_spawn_request)
    
    @pytest.mark.asyncio
    async def test_invalid_session_operations(self, integration_session_service):
        """Test operations on non-existent sessions."""
        service = integration_session_service
        
        fake_session_id = "non-existent-session-123"
        
        # All operations on non-existent session should fail gracefully
        with pytest.raises(Exception):
            await service.query_session(fake_session_id)
        
        send_result = await service.send_to_agent(fake_session_id, "test message")
        assert send_result is False
        
        stop_result = await service.stop_agent(fake_session_id)
        assert stop_result is False
    
    @pytest.mark.asyncio
    async def test_message_sending_failure(self, integration_session_service, sample_spawn_request, mock_api):
        """Test handling of message sending failures."""
        service = integration_session_service
        
        # Create session successfully
        session_info = await service.spawn_agent(sample_spawn_request)
        session_id = session_info.session_id
        
        # Set message sending to fail
        mock_api.set_failure_mode("send_message", True)
        
        # Message sending should fail
        with pytest.raises(Exception):
            await service.send_to_agent(session_id, "test message")
        
        # Clean up
        mock_api.set_failure_mode("send_message", False)
        await service.stop_agent(session_id)
    
    @pytest.mark.asyncio
    async def test_session_recovery_after_failure(self, integration_session_service, sample_spawn_request, mock_api):
        """Test system recovery after temporary failures."""
        service = integration_session_service
        
        # Create a session successfully
        session_info = await service.spawn_agent(sample_spawn_request)
        session_id = session_info.session_id
        
        # Simulate temporary API failure
        mock_api.set_failure_mode("get_session", True)
        
        with pytest.raises(Exception):
            await service.query_session(session_id)
        
        # Restore API functionality
        mock_api.set_failure_mode("get_session", False)
        
        # Should work again
        recovered_session = await service.query_session(session_id)
        assert recovered_session.session_id == session_id
        
        # Clean up
        await service.stop_agent(session_id)
    
    @pytest.mark.asyncio 
    async def test_resource_exhaustion_scenario(self, integration_session_service, mock_api):
        """Test behavior when approaching resource limits."""
        service = integration_session_service
        
        # Create many sessions to test resource limits
        sessions = []
        max_sessions = 10  # Test with more than semaphore limit
        
        requests = [
            SpawnAgentRequest(
                role=AgentRole.BACKEND_SPECIALIST,
                task_id=str(uuid.uuid4()),
                instructions=f"Resource test {i}",
                context={"test": "resource_exhaustion"},
                model="claude-sonnet-4"
            )
            for i in range(max_sessions)
        ]
        
        # Should handle all requests even if they need to queue
        for request in requests:
            try:
                session_info = await service.spawn_agent(request)
                sessions.append(session_info.session_id)
            except Exception as e:
                # Some may fail due to resource limits, that's acceptable
                print(f"Session creation failed: {e}")
        
        # Should have created at least some sessions
        assert len(sessions) > 0
        print(f"Created {len(sessions)} out of {max_sessions} sessions")
        
        # Clean up all created sessions
        for session_id in sessions:
            try:
                await service.stop_agent(session_id)
            except Exception:
                pass  # Clean up best effort


class TestPerformanceMetrics:
    """Test performance characteristics and metrics."""
    
    @pytest.mark.asyncio
    async def test_session_creation_performance(self, integration_session_service, mock_api):
        """Test session creation performance metrics."""
        service = integration_session_service
        
        # Measure single session creation
        request = SpawnAgentRequest(
            role=AgentRole.BACKEND_SPECIALIST,
            task_id=str(uuid.uuid4()),
            instructions="Performance test",
            context={"test": "performance"},
            model="claude-sonnet-4"
        )
        
        start_time = time.time()
        session_info = await service.spawn_agent(request)
        end_time = time.time()
        
        creation_time = end_time - start_time
        assert creation_time < 1.0, f"Session creation took {creation_time}s, expected < 1.0s"
        
        # Test message response time
        start_time = time.time()
        sent = await service.send_to_agent(session_info.session_id, "Quick test message")
        end_time = time.time()
        
        assert sent is True
        message_time = end_time - start_time
        assert message_time < 0.5, f"Message sending took {message_time}s, expected < 0.5s"
        
        # Clean up
        await service.stop_agent(session_info.session_id)
    
    @pytest.mark.asyncio
    async def test_throughput_under_load(self, integration_session_service):
        """Test system throughput under concurrent load."""
        service = integration_session_service
        
        # Create multiple sessions and send messages concurrently
        num_sessions = 5
        messages_per_session = 3
        
        # Setup sessions
        sessions = []
        for i in range(num_sessions):
            request = SpawnAgentRequest(
                role=AgentRole.BACKEND_SPECIALIST,
                task_id=str(uuid.uuid4()),
                instructions=f"Throughput test session {i}",
                context={"session": i},
                model="claude-sonnet-4"
            )
            session_info = await service.spawn_agent(request)
            sessions.append(session_info.session_id)
        
        # Send messages concurrently
        start_time = time.time()
        
        all_tasks = []
        for session_id in sessions:
            for msg_num in range(messages_per_session):
                task = service.send_to_agent(session_id, f"Message {msg_num}")
                all_tasks.append(task)
        
        results = await asyncio.gather(*all_tasks)
        end_time = time.time()
        
        # Verify all messages sent successfully
        assert all(result is True for result in results)
        
        total_messages = num_sessions * messages_per_session
        total_time = end_time - start_time
        throughput = total_messages / total_time
        
        print(f"Sent {total_messages} messages in {total_time:.2f}s, throughput: {throughput:.2f} msg/s")
        assert throughput > 5.0, f"Throughput {throughput} msg/s too low"
        
        # Clean up
        for session_id in sessions:
            await service.stop_agent(session_id)


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "--tb=short"])