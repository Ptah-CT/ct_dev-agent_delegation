"""Basic tests for agent orchestrator."""

import pytest
from pathlib import Path

def test_imports():
    """Test that core modules can be imported."""
    from ct_dev_agent_delegation_mcp.models.agent import Agent, AgentRole, AgentStatus
    from ct_dev_agent_delegation_mcp.models.delegation import (
        DelegationRequest,
        DelegationResponse,
        DelegationResult,
        DelegationStatus
    )
    from ct_dev_agent_delegation_mcp.services.agent_manager import AgentManager
    from ct_dev_agent_delegation_mcp.services.delegation_service import DelegationService
    from ct_dev_agent_delegation_mcp.storage.database import Database
    
    assert Agent is not None
    assert AgentManager is not None


def test_agent_roles():
    """Test agent roles are defined."""
    from ct_dev_agent_delegation_mcp.models.agent import AgentRole
    
    # Check some key roles exist
    assert hasattr(AgentRole, 'BACKEND_SPECIALIST')
    assert hasattr(AgentRole, 'SYSTEM_ARCHITECT')
    assert hasattr(AgentRole, 'PROJECT_ARCHITECT')
    
    # Test value conversion
    role = AgentRole.BACKEND_SPECIALIST
    assert role.value == "backend_specialist"


def test_database_creation():
    """Test database can be created."""
    from ct_dev_agent_delegation_mcp.storage.database import Database
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))
        
        assert db_path.exists()
        
        # Test a simple query
        result = db.fetchall("SELECT name FROM sqlite_master WHERE type='table'")
        table_names = [r['name'] for r in result]
        
        # Check required tables exist
        assert 'agents' in table_names
        assert 'delegations' in table_names
        assert 'delegation_events' in table_names


@pytest.mark.asyncio
async def test_agent_model():
    """Test agent model creation."""
    from ct_dev_agent_delegation_mcp.models.agent import Agent, AgentRole, AgentStatus
    from datetime import datetime, timezone
    
    agent = Agent(
        agent_id="test-123",
        role=AgentRole.BACKEND_SPECIALIST,
        status=AgentStatus.IDLE,
        created_at=datetime.now(timezone.utc).isoformat()
    )
    
    assert agent.agent_id == "test-123"
    assert agent.role == AgentRole.BACKEND_SPECIALIST
    assert agent.status == AgentStatus.IDLE


@pytest.mark.asyncio  
async def test_delegation_request():
    """Test delegation request model."""
    from ct_dev_agent_delegation_mcp.models.delegation import DelegationRequest
    
    request = DelegationRequest(
        task_id="task-123",
        agent_role="backend_specialist",
        instructions="Implement API endpoints"
    )
    
    assert request.task_id == "task-123"
    assert request.agent_role == "backend_specialist"
    assert request.timeout_seconds == 3600  # default


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
