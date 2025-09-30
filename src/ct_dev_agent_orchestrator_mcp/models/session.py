"""Session data models for V2 Agent Orchestrator."""

from enum import Enum
from typing import Dict, Any, List
from pydantic import BaseModel, Field


class SessionStatus(str, Enum):
    """Session lifecycle status."""
    STARTING = "starting"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SpawnAgentRequest(BaseModel):
    """Request to spawn a new agent session."""
    
    role: str = Field(..., description="Agent role (e.g., 'backend_specialist')")
    task_id: str = Field(..., description="Task UUID from task_orchestrator")
    instructions: str = Field(..., description="Detailed work instructions")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")
    model: str = Field(default="claude-sonnet-4", description="Model to use")
    
    class Config:
        json_schema_extra = {
            "example": {
                "role": "backend_specialist",
                "task_id": "550e8400-e29b-41d4-a716-446655440000",
                "instructions": "Implement OAuth2 authentication endpoints with JWT tokens",
                "context": {"framework": "FastAPI", "db": "PostgreSQL"},
                "model": "claude-sonnet-4"
            }
        }


class SessionInfo(BaseModel):
    """Information about an active agent session."""
    
    session_id: str = Field(..., description="Unique session UUID")
    agent_role: str = Field(..., description="Agent role")
    status: SessionStatus = Field(..., description="Current session status")
    started_at: str = Field(..., description="ISO 8601 start timestamp")
    progress: Dict[str, Any] = Field(default_factory=dict, description="Progress information")
    messages: List[Dict] = Field(default_factory=list, description="Session messages")
    server_url: str = Field(..., description="Agent server URL")


class AgentOutput(BaseModel):
    """Output from a completed agent session."""
    
    session_id: str = Field(..., description="Session UUID")
    status: SessionStatus = Field(..., description="Final session status")
    artifacts: Dict[str, Any] = Field(default_factory=dict, description="Generated artifacts")
    summary: str = Field(..., description="Session summary")
    duration_seconds: float = Field(..., description="Session duration in seconds")
    completed_at: str = Field(..., description="ISO 8601 completion timestamp")