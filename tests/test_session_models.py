"""Tests for session models."""

import pytest
from typing import Dict, Any
from datetime import datetime, timezone

from ct_dev_agent_orchestrator_mcp.models.session import (
    SessionStatus,
    SpawnAgentRequest,
    SessionInfo,
    AgentOutput
)


class TestSessionStatus:
    """Test SessionStatus enum."""
    
    def test_session_status_values(self):
        """Test enum values."""
        assert SessionStatus.STARTING == "starting"
        assert SessionStatus.RUNNING == "running"
        assert SessionStatus.COMPLETED == "completed"
        assert SessionStatus.FAILED == "failed"
        assert SessionStatus.CANCELLED == "cancelled"
    
    def test_session_status_all_values(self):
        """Test all expected values are present."""
        expected_values = {"starting", "running", "completed", "failed", "cancelled"}
        actual_values = {status.value for status in SessionStatus}
        assert actual_values == expected_values


class TestSpawnAgentRequest:
    """Test SpawnAgentRequest model."""
    
    def test_spawn_agent_request_creation(self):
        """Test basic model creation."""
        request = SpawnAgentRequest(
            role="backend_specialist",
            task_id="550e8400-e29b-41d4-a716-446655440000",
            instructions="Implement OAuth2 authentication"
        )
        
        assert request.role == "backend_specialist"
        assert request.task_id == "550e8400-e29b-41d4-a716-446655440000"
        assert request.instructions == "Implement OAuth2 authentication"
        assert request.context == {}
        assert request.model == "claude-sonnet-4"
    
    def test_spawn_agent_request_with_context(self):
        """Test model creation with context."""
        context = {"framework": "FastAPI", "db": "PostgreSQL"}
        request = SpawnAgentRequest(
            role="backend_specialist",
            task_id="550e8400-e29b-41d4-a716-446655440000",
            instructions="Implement OAuth2 authentication",
            context=context,
            model="claude-opus-4"
        )
        
        assert request.context == context
        assert request.model == "claude-opus-4"
    
    def test_spawn_agent_request_validation_required_fields(self):
        """Test validation of required fields."""
        with pytest.raises(ValueError):
            SpawnAgentRequest()
            
        with pytest.raises(ValueError):
            SpawnAgentRequest(role="backend_specialist")
            
        with pytest.raises(ValueError):
            SpawnAgentRequest(
                role="backend_specialist",
                task_id="550e8400-e29b-41d4-a716-446655440000"
            )
    
    def test_spawn_agent_request_json_serialization(self):
        """Test JSON serialization."""
        request = SpawnAgentRequest(
            role="backend_specialist",
            task_id="550e8400-e29b-41d4-a716-446655440000",
            instructions="Implement OAuth2 authentication",
            context={"test": "value"}
        )
        
        json_data = request.model_dump()
        
        assert json_data["role"] == "backend_specialist"
        assert json_data["task_id"] == "550e8400-e29b-41d4-a716-446655440000"
        assert json_data["instructions"] == "Implement OAuth2 authentication"
        assert json_data["context"] == {"test": "value"}
        assert json_data["model"] == "claude-sonnet-4"
    
    def test_spawn_agent_request_from_dict(self):
        """Test model creation from dictionary."""
        data = {
            "role": "frontend_specialist",
            "task_id": "123e4567-e89b-12d3-a456-426614174000",
            "instructions": "Build React components",
            "context": {"library": "React"},
            "model": "claude-haiku-4"
        }
        
        request = SpawnAgentRequest(**data)
        
        assert request.role == "frontend_specialist"
        assert request.task_id == "123e4567-e89b-12d3-a456-426614174000"
        assert request.instructions == "Build React components"
        assert request.context == {"library": "React"}
        assert request.model == "claude-haiku-4"


class TestSessionInfo:
    """Test SessionInfo model."""
    
    def test_session_info_creation(self):
        """Test basic model creation."""
        timestamp = datetime.now(timezone.utc).isoformat()
        session = SessionInfo(
            session_id="session-123",
            agent_role="backend_specialist",
            status=SessionStatus.RUNNING,
            started_at=timestamp,
            server_url="http://localhost:8080"
        )
        
        assert session.session_id == "session-123"
        assert session.agent_role == "backend_specialist"
        assert session.status == SessionStatus.RUNNING
        assert session.started_at == timestamp
        assert session.progress == {}
        assert session.messages == []
        assert session.server_url == "http://localhost:8080"
    
    def test_session_info_with_progress_and_messages(self):
        """Test model creation with progress and messages."""
        timestamp = datetime.now(timezone.utc).isoformat()
        progress = {"completed_steps": 3, "total_steps": 10}
        messages = [
            {"type": "info", "content": "Starting task"},
            {"type": "progress", "content": "Step 1 completed"}
        ]
        
        session = SessionInfo(
            session_id="session-456",
            agent_role="system_architect",
            status=SessionStatus.RUNNING,
            started_at=timestamp,
            progress=progress,
            messages=messages,
            server_url="http://localhost:8081"
        )
        
        assert session.progress == progress
        assert session.messages == messages
    
    def test_session_info_status_enum_serialization(self):
        """Test enum serialization."""
        timestamp = datetime.now(timezone.utc).isoformat()
        session = SessionInfo(
            session_id="session-789",
            agent_role="database_architect",
            status=SessionStatus.COMPLETED,
            started_at=timestamp,
            server_url="http://localhost:8082"
        )
        
        json_data = session.model_dump()
        assert json_data["status"] == "completed"
    
    def test_session_info_validation_required_fields(self):
        """Test validation of required fields."""
        with pytest.raises(ValueError):
            SessionInfo()
            
        with pytest.raises(ValueError):
            SessionInfo(session_id="session-123")
    
    def test_session_info_from_dict(self):
        """Test model creation from dictionary."""
        timestamp = datetime.now(timezone.utc).isoformat()
        data = {
            "session_id": "session-999",
            "agent_role": "security_expert",
            "status": "starting",
            "started_at": timestamp,
            "progress": {"initialization": True},
            "messages": [{"type": "system", "content": "Session initialized"}],
            "server_url": "http://localhost:8083"
        }
        
        session = SessionInfo(**data)
        
        assert session.session_id == "session-999"
        assert session.agent_role == "security_expert"
        assert session.status == SessionStatus.STARTING
        assert session.started_at == timestamp
        assert session.progress == {"initialization": True}
        assert len(session.messages) == 1
        assert session.server_url == "http://localhost:8083"


class TestAgentOutput:
    """Test AgentOutput model."""
    
    def test_agent_output_creation(self):
        """Test basic model creation."""
        timestamp = datetime.now(timezone.utc).isoformat()
        output = AgentOutput(
            session_id="session-abc",
            status=SessionStatus.COMPLETED,
            summary="Task completed successfully",
            duration_seconds=300.5,
            completed_at=timestamp
        )
        
        assert output.session_id == "session-abc"
        assert output.status == SessionStatus.COMPLETED
        assert output.artifacts == {}
        assert output.summary == "Task completed successfully"
        assert output.duration_seconds == 300.5
        assert output.completed_at == timestamp
    
    def test_agent_output_with_artifacts(self):
        """Test model creation with artifacts."""
        timestamp = datetime.now(timezone.utc).isoformat()
        artifacts = {
            "files_created": ["auth.py", "models.py"],
            "tests_run": 15,
            "coverage": 98.5
        }
        
        output = AgentOutput(
            session_id="session-def",
            status=SessionStatus.COMPLETED,
            artifacts=artifacts,
            summary="API implementation completed",
            duration_seconds=1800.0,
            completed_at=timestamp
        )
        
        assert output.artifacts == artifacts
    
    def test_agent_output_failed_status(self):
        """Test output with failed status."""
        timestamp = datetime.now(timezone.utc).isoformat()
        output = AgentOutput(
            session_id="session-xyz",
            status=SessionStatus.FAILED,
            summary="Task failed due to compilation errors",
            duration_seconds=120.0,
            completed_at=timestamp
        )
        
        assert output.status == SessionStatus.FAILED
        assert "failed" in output.summary
    
    def test_agent_output_validation_required_fields(self):
        """Test validation of required fields."""
        with pytest.raises(ValueError):
            AgentOutput()
            
        with pytest.raises(ValueError):
            AgentOutput(session_id="session-123")
    
    def test_agent_output_json_serialization(self):
        """Test JSON serialization."""
        timestamp = datetime.now(timezone.utc).isoformat()
        artifacts = {"result": "success"}
        
        output = AgentOutput(
            session_id="session-json",
            status=SessionStatus.COMPLETED,
            artifacts=artifacts,
            summary="Serialization test",
            duration_seconds=45.2,
            completed_at=timestamp
        )
        
        json_data = output.model_dump()
        
        assert json_data["session_id"] == "session-json"
        assert json_data["status"] == "completed"
        assert json_data["artifacts"] == artifacts
        assert json_data["summary"] == "Serialization test"
        assert json_data["duration_seconds"] == 45.2
        assert json_data["completed_at"] == timestamp
    
    def test_agent_output_from_dict(self):
        """Test model creation from dictionary."""
        timestamp = datetime.now(timezone.utc).isoformat()
        data = {
            "session_id": "session-from-dict",
            "status": "cancelled",
            "artifacts": {"reason": "user_cancelled"},
            "summary": "Session was cancelled by user",
            "duration_seconds": 75.3,
            "completed_at": timestamp
        }
        
        output = AgentOutput(**data)
        
        assert output.session_id == "session-from-dict"
        assert output.status == SessionStatus.CANCELLED
        assert output.artifacts == {"reason": "user_cancelled"}
        assert output.summary == "Session was cancelled by user"
        assert output.duration_seconds == 75.3
        assert output.completed_at == timestamp


class TestModelIntegration:
    """Test integration between models."""
    
    def test_complete_session_workflow_models(self):
        """Test a complete workflow using all models."""
        # 1. Create spawn request
        spawn_request = SpawnAgentRequest(
            role="backend_specialist",
            task_id="workflow-test-123",
            instructions="Complete integration test workflow",
            context={"test": True}
        )
        
        # 2. Create session info (simulating session creation)
        start_time = datetime.now(timezone.utc).isoformat()
        session = SessionInfo(
            session_id="session-workflow-123",
            agent_role=spawn_request.role,
            status=SessionStatus.STARTING,
            started_at=start_time,
            server_url="http://localhost:9000"
        )
        
        # 3. Update session to running (simulating status change)
        session.status = SessionStatus.RUNNING
        session.progress = {"phase": "implementation"}
        session.messages = [{"type": "info", "content": "Implementation started"}]
        
        # 4. Create output (simulating completion)
        end_time = datetime.now(timezone.utc).isoformat()
        output = AgentOutput(
            session_id=session.session_id,
            status=SessionStatus.COMPLETED,
            artifacts={"implementation": "completed"},
            summary="Workflow test completed successfully",
            duration_seconds=600.0,
            completed_at=end_time
        )
        
        # Verify the workflow consistency
        assert session.session_id == output.session_id
        assert session.agent_role == spawn_request.role
        assert output.status == SessionStatus.COMPLETED
        assert output.duration_seconds > 0
    
    def test_model_serialization_round_trip(self):
        """Test that all models can be serialized and deserialized."""
        # Test SpawnAgentRequest
        spawn_request = SpawnAgentRequest(
            role="test_role",
            task_id="test-task-id",
            instructions="test instructions"
        )
        spawn_dict = spawn_request.model_dump()
        spawn_restored = SpawnAgentRequest(**spawn_dict)
        assert spawn_restored.role == spawn_request.role
        
        # Test SessionInfo
        timestamp = datetime.now(timezone.utc).isoformat()
        session = SessionInfo(
            session_id="test-session",
            agent_role="test_role",
            status=SessionStatus.RUNNING,
            started_at=timestamp,
            server_url="http://test.com"
        )
        session_dict = session.model_dump()
        session_restored = SessionInfo(**session_dict)
        assert session_restored.session_id == session.session_id
        
        # Test AgentOutput
        output = AgentOutput(
            session_id="test-session",
            status=SessionStatus.COMPLETED,
            summary="test summary",
            duration_seconds=100.0,
            completed_at=timestamp
        )
        output_dict = output.model_dump()
        output_restored = AgentOutput(**output_dict)
        assert output_restored.session_id == output.session_id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])