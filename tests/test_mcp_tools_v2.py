"""
Tests for V2 Session-based MCP Tools.

Tests the new session-based MCP tools that replace the delegation-based tools.
Tests both new tools and deprecated tools (with warnings).

Author: Agent Orchestrator V2 Migration - Phase 3
"""

import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from mcp.types import TextContent

from ct_dev_agent_delegation_mcp.server import call_tool
from ct_dev_agent_delegation_mcp.models.delegation import (
    SpawnDelegationRequest, DelegationInfo, AgentOutput, DelegationStatus
)
from ct_dev_agent_delegation_mcp.models.agent import AgentRole

# Test helper data for Cap fields
TEST_CAP_FIELDS = {
    "original_task": {
        "task_id": "test-task-123",
        "title": "Test Task",
        "description": "Test Description",
        "requester": "Test User",
        "requested_at": "2025-01-15T10:00:00Z"
    },
    "cap_origin": {
        "ultimate_authority": "Auctor",
        "original_scope": "Test Scope",
        "granted_at": "2025-01-15T10:00:00Z",
        "grant_context": "Test Context"
    },
    "delegation_context": {
        "delegator": "Test Delegator",
        "delegator_cap": "Test Cap",
        "delegated_to": "backend_specialist",
        "delegated_cap": "Test Delegated Cap",
        "constraints": [],
        "phantom_level": "Test Level",
        "delegated_at": "2025-01-15T10:00:00Z"
    }
}


class TestSessionBasedTools:
    """Test new V2 session-based MCP tools."""
    
    @pytest.mark.asyncio
    async def test_spawn_agent_success(self):
        """Test successful agent spawning."""
        # Mock session_service.spawn_agent
        mock_session_info = DelegationInfo(
            **TEST_CAP_FIELDS,
            session_id="test-session-123",
            agent_role="backend_specialist",
            status=DelegationStatus.STARTING,
            started_at="2025-01-15T10:00:00Z",
            server_url="http://localhost:8001",
            progress={},
            messages=[]
        )
        
        with patch('ct_dev_agent_delegation_mcp.server.session_service') as mock_service:
            mock_service.spawn_agent = AsyncMock(return_value=mock_session_info)
            
            # Test spawn_agent call
            result = await call_tool("spawn_agent", {
                "role": "backend_specialist",
                "task_id": "550e8400-e29b-41d4-a716-446655440000",
                "instructions": "Implement OAuth2 endpoints",
                "project_directory": "/test/dir",
                "expected_output": "OAuth2 endpoints implemented",
                **TEST_CAP_FIELDS
            })
            
            # Verify result
            assert len(result) == 1
            assert isinstance(result[0], TextContent)
            assert "✓ Agent session spawned successfully" in result[0].text
            assert "test-session-123" in result[0].text
            assert "backend_specialist" in result[0].text
            assert "starting" in result[0].text
            
            # Verify service was called correctly
            mock_service.spawn_agent.assert_called_once()
            call_args = mock_service.spawn_agent.call_args[0][0]
            assert isinstance(call_args, SpawnDelegationRequest)
            assert call_args.role == "backend_specialist"
            assert call_args.task_id == "550e8400-e29b-41d4-a716-446655440000"
            assert call_args.instructions == "Implement OAuth2 endpoints"
    
    @pytest.mark.asyncio
    async def test_query_session_success(self):
        """Test successful session status query."""
        mock_session_info = DelegationInfo(
            **TEST_CAP_FIELDS,
            session_id="test-session-123",
            agent_role="backend_specialist",
            status=DelegationStatus.RUNNING,
            started_at="2025-01-15T10:00:00Z",
            server_url="http://localhost:8001",
            progress={"completion": 0.5},
            messages=[{"role": "user", "content": "Starting work"}]
        )
        
        with patch('ct_dev_agent_delegation_mcp.server.session_service') as mock_service:
            mock_service.query_session = AsyncMock(return_value=mock_session_info)
            
            result = await call_tool("query_session", {
                "session_id": "test-session-123"
            })
            
            assert len(result) == 1
            assert "Session Status:" in result[0].text
            assert "test-session-123" in result[0].text
            assert "backend_specialist" in result[0].text
            assert "running" in result[0].text
            assert "Message Count: 1" in result[0].text
            
            mock_service.query_session.assert_called_once_with("test-session-123")
    
    @pytest.mark.asyncio
    async def test_get_agent_output_success(self):
        """Test successful agent output retrieval."""
        mock_output = AgentOutput(
            session_id="test-session-123",
            status=DelegationStatus.COMPLETED,
            artifacts={"files": ["test.py"], "changes": 3},
            summary="Successfully implemented OAuth2 endpoints with JWT tokens",
            duration_seconds=450.5,
            completed_at="2025-01-15T10:30:00Z"
        )
        
        with patch('ct_dev_agent_delegation_mcp.server.session_service') as mock_service:
            mock_service.get_agent_output = AsyncMock(return_value=mock_output)
            
            result = await call_tool("get_agent_output", {
                "session_id": "test-session-123"
            })
            
            assert len(result) == 1
            assert "Agent Output:" in result[0].text
            assert "test-session-123" in result[0].text
            assert "completed" in result[0].text
            assert "450.50s" in result[0].text
            assert "OAuth2 endpoints" in result[0].text
            assert "Artifacts: 2 items" in result[0].text
            
            mock_service.get_agent_output.assert_called_once_with("test-session-123")
    
    @pytest.mark.asyncio
    async def test_list_active_sessions_success(self):
        """Test successful active sessions listing."""
        mock_sessions = [
            DelegationInfo(
                **TEST_CAP_FIELDS,
                session_id="session-1",
                agent_role="backend_specialist",
                status=DelegationStatus.RUNNING,
                started_at="2025-01-15T10:00:00Z",
                server_url="http://localhost:8001",
                progress={},
                messages=[]
            ),
            DelegationInfo(
                **TEST_CAP_FIELDS,
                session_id="session-2", 
                agent_role="frontend_specialist",
                status=DelegationStatus.STARTING,
                started_at="2025-01-15T10:05:00Z",
                server_url="http://localhost:8002",
                progress={},
                messages=[{"role": "user", "content": "test"}]
            )
        ]
        
        with patch('ct_dev_agent_delegation_mcp.server.session_service') as mock_service:
            mock_service.list_active_sessions = AsyncMock(return_value=mock_sessions)
            
            result = await call_tool("list_active_sessions", {})
            
            assert len(result) == 1
            assert "Active Sessions (2):" in result[0].text
            assert "session-1" in result[0].text
            assert "session-2" in result[0].text
            assert "backend_specialist" in result[0].text
            assert "frontend_specialist" in result[0].text
            assert "Messages: 0" in result[0].text
            assert "Messages: 1" in result[0].text
            
            mock_service.list_active_sessions.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_list_active_sessions_empty(self):
        """Test active sessions listing when no sessions exist."""
        with patch('ct_dev_agent_delegation_mcp.server.session_service') as mock_service:
            mock_service.list_active_sessions = AsyncMock(return_value=[])
            
            result = await call_tool("list_active_sessions", {})
            
            assert len(result) == 1
            assert "No active sessions found." in result[0].text
    
    @pytest.mark.asyncio
    async def test_stop_agent_success(self):
        """Test successful agent stopping."""
        with patch('ct_dev_agent_delegation_mcp.server.session_service') as mock_service:
            mock_service.stop_agent = AsyncMock(return_value=True)
            
            result = await call_tool("stop_agent", {
                "session_id": "test-session-123"
            })
            
            assert len(result) == 1
            assert "✓ Agent session test-session-123 stopped successfully" in result[0].text
            
            mock_service.stop_agent.assert_called_once_with("test-session-123")
    
    @pytest.mark.asyncio
    async def test_stop_agent_failure(self):
        """Test agent stopping failure."""
        with patch('ct_dev_agent_delegation_mcp.server.session_service') as mock_service:
            mock_service.stop_agent = AsyncMock(return_value=False)
            
            result = await call_tool("stop_agent", {
                "session_id": "test-session-123"
            })
            
            assert len(result) == 1
            assert "✗ Failed to stop agent session test-session-123" in result[0].text
    
    @pytest.mark.asyncio
    async def test_send_to_agent_success(self):
        """Test successful message sending to agent."""
        with patch('ct_dev_agent_delegation_mcp.server.session_service') as mock_service:
            mock_service.send_to_agent = AsyncMock(return_value=True)
            
            result = await call_tool("send_to_agent", {
                "session_id": "test-session-123",
                "message": "Please add error handling to the endpoints"
            })
            
            assert len(result) == 1
            assert "✓ Message sent to agent session test-session-123" in result[0].text
            
            mock_service.send_to_agent.assert_called_once_with(
                "test-session-123", 
                "Please add error handling to the endpoints"
            )
    
    @pytest.mark.asyncio
    async def test_send_to_agent_failure(self):
        """Test message sending failure."""
        with patch('ct_dev_agent_delegation_mcp.server.session_service') as mock_service:
            mock_service.send_to_agent = AsyncMock(return_value=False)
            
            result = await call_tool("send_to_agent", {
                "session_id": "test-session-123",
                "message": "Test message"
            })
            
            assert len(result) == 1
            assert "✗ Failed to send message to session test-session-123" in result[0].text
    
    @pytest.mark.asyncio
    async def test_get_agent_capabilities(self):
        """Test agent capabilities listing."""
        mock_agents = [
            {
                "name": "backend_specialist",
                "description": "Backend development specialist",
                "mode": "code",
                "builtIn": True,
                "tools": {"read_file": {}, "write_file": {}}
            },
            {
                "name": "frontend_specialist",
                "description": "Frontend development specialist",
                "mode": "code",
                "builtIn": True,
                "tools": {"read_file": {}, "write_file": {}}
            }
        ]
        
        with patch('ct_dev_agent_delegation_mcp.server.opencode_service') as mock_service:
            mock_service.api_client.fetch_available_agents = AsyncMock(return_value=mock_agents)
            
            result = await call_tool("get_agent_capabilities", {})
            
            assert len(result) == 1
            response = json.loads(result[0].text)
            assert response["count"] == 2
            assert any(agent["name"] == "backend_specialist" for agent in response["agents"])
            assert any(agent["name"] == "frontend_specialist" for agent in response["agents"])



class TestErrorHandling:
    """Test error handling for V2 tools."""
    
    
    @pytest.mark.asyncio
    async def test_spawn_agent_validation_error(self):
        """Test spawn_agent with invalid input."""
        result = await call_tool("spawn_agent", {
            "role": "invalid_role",
            "task_id": "task-123",
            "instructions": "Test"
        })
        
        assert len(result) == 1
        assert "✗ Error:" in result[0].text
    
    @pytest.mark.asyncio
    async def test_query_session_service_error(self):
        """Test query_session when service raises exception."""
        with patch('ct_dev_agent_delegation_mcp.server.session_service') as mock_service:
            mock_service.query_session = AsyncMock(side_effect=Exception("Session not found"))
            
            result = await call_tool("query_session", {
                "session_id": "nonexistent-session"
            })
            
            assert len(result) == 1
            assert "✗ Error:" in result[0].text
            assert "Session not found" in result[0].text
    
    @pytest.mark.asyncio
    async def test_get_agent_output_incomplete_session(self):
        """Test get_agent_output when session not completed."""
        with patch('ct_dev_agent_delegation_mcp.server.session_service') as mock_service:
            mock_service.get_agent_output = AsyncMock(
                side_effect=ValueError("Session not completed")
            )
            
            result = await call_tool("get_agent_output", {
                "session_id": "running-session"
            })
            
            assert len(result) == 1
            assert "✗ Error:" in result[0].text
            assert "Session not completed" in result[0].text
    
    @pytest.mark.asyncio
    async def test_unknown_tool(self):
        """Test unknown tool handling."""
        result = await call_tool("unknown_tool", {})
        
        assert len(result) == 1
        assert "Unknown tool: unknown_tool" in result[0].text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])