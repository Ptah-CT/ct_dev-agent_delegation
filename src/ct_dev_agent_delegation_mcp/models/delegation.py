"""Session data models for V2 Agent Orchestrator."""

from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class DelegationStatus(str, Enum):
    """Session lifecycle status."""
    STARTING = "starting"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SpawnDelegationRequest(BaseModel):
    """Request to spawn a new agent session."""
    
    role: str = Field(..., description="Agent role (e.g., 'backend_specialist')")
    task_id: str = Field(..., description="Task UUID from task_orchestrator")
    instructions: str = Field(..., description="Detailed work instructions")
    project_directory: str = Field(..., description="Absolute path to project working directory")
    expected_output: str = Field(..., description="Expected work output/deliverable (e.g., 'Report', 'Implementation', 'Analysis')")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")
    model: str = Field(default="claude-sonnet-4", description="Model to use")
    
    # X^∞ Responsibility & Cap Tracking Fields
    original_task: Dict[str, Any] = Field(
        ...,
        description="Original task that started this work (task_id, title, description, requester, requested_at)"
    )
    cap_origin: Dict[str, Any] = Field(
        ...,
        description="Cap origin - ultimate authority source (ultimate_authority, original_scope, granted_at, grant_context)"
    )
    delegation_context: Dict[str, Any] = Field(
        ...,
        description="Current delegation context (delegator, delegator_cap, delegated_to, delegated_cap, constraints, phantom_level, delegated_at)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "role": "backend_specialist",
                "task_id": "550e8400-e29b-41d4-a716-446655440000",
                "instructions": "Implement OAuth2 authentication endpoints with JWT tokens",
                "project_directory": "/home/auctor/dev/my-project",
                "expected_output": "Report",
                "context": {"framework": "FastAPI", "db": "PostgreSQL"},
                "model": "claude-sonnet-4",
                "original_task": {
                    "task_id": "a86d0e77-a8b8-4dcc-b854-cc27fe474c76",
                    "title": "Add OAuth Authentication",
                    "description": "Implement OAuth2 authentication system with JWT tokens",
                    "requester": "Auctor",
                    "requested_at": "2025-10-02T04:00:00Z"
                },
                "cap_origin": {
                    "ultimate_authority": "Auctor",
                    "original_scope": "Full system development authority",
                    "granted_at": "2025-10-01T00:00:00Z",
                    "grant_context": "Initial project authorization"
                },
                "delegation_context": {
                    "delegator": "Project Manager",
                    "delegator_cap": "Implementation coordination (from Auctor on 2025-10-02T03:00:00Z)",
                    "delegated_to": "Backend Specialist",
                    "delegated_cap": "OAuth implementation with tests",
                    "constraints": ["Follow patterns", "Tests required"],
                    "phantom_level": "Delegation/Cap",
                    "delegated_at": "2025-10-02T04:30:00Z"
                }
            }
        }


class DelegationInfo(BaseModel):
    """Information about an active agent session."""
    
    session_id: str = Field(..., description="Unique session UUID")
    agent_role: str = Field(..., description="Agent role")
    status: DelegationStatus = Field(..., description="Current session status")
    started_at: str = Field(..., description="ISO 8601 start timestamp")
    progress: Dict[str, Any] = Field(default_factory=dict, description="Progress information")
    messages: List[Dict] = Field(default_factory=list, description="Session messages")
    server_url: str = Field(..., description="Agent server URL")
    scope_deviation: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Scope deviation detection data. Structure: {detected: bool, type: str, severity: str, message: str, timestamp: str}"
    )
    
    # X^∞ Responsibility & Cap Tracking Fields
    original_task: Dict[str, Any] = Field(
        ...,
        description="Original task that started this work (task_id, title, description, requester, requested_at)"
    )
    cap_origin: Dict[str, Any] = Field(
        ...,
        description="Cap origin - ultimate authority source (ultimate_authority, original_scope, granted_at, grant_context)"
    )
    delegation_context: Dict[str, Any] = Field(
        ...,
        description="Current delegation context (delegator, delegator_cap, delegated_to, delegated_cap, constraints, phantom_level, delegated_at)"
    )


class AgentOutput(BaseModel):
    """Output from a completed agent session."""
    
    session_id: str = Field(..., description="Session UUID")
    status: DelegationStatus = Field(..., description="Final session status")
    artifacts: Dict[str, Any] = Field(default_factory=dict, description="Generated artifacts")
    summary: str = Field(..., description="Session summary")
    duration_seconds: float = Field(..., description="Session duration in seconds")
    completed_at: str = Field(..., description="ISO 8601 completion timestamp")