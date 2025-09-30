"""Delegation data models."""

from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class DelegationStatus(str, Enum):
    """Delegation lifecycle status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SCOPE_DEVIATION = "scope_deviation"


class DelegationRequest(BaseModel):
    """Request to delegate work to an agent."""
    
    task_id: str = Field(..., description="Task UUID from task_orchestrator")
    agent_role: str = Field(..., description="Required agent role")
    instructions: str = Field(..., description="Work instructions for agent")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")
    timeout_seconds: int = Field(default=3600, description="Max execution time")
    
    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "550e8400-e29b-41d4-a716-446655440000",
                "agent_role": "backend_specialist",
                "instructions": "Implement OAuth2 authentication endpoints",
                "context": {"framework": "FastAPI", "db": "PostgreSQL"},
                "timeout_seconds": 7200
            }
        }


class DelegationResponse(BaseModel):
    """Response from delegation request."""
    
    delegation_id: str = Field(..., description="Unique delegation UUID")
    agent_id: str = Field(..., description="Assigned agent UUID")
    status: DelegationStatus = Field(..., description="Initial status (pending)")
    message: str = Field(..., description="Human-readable status message")
    estimated_completion: Optional[str] = Field(None, description="ISO 8601 estimated completion")
    
    class Config:
        use_enum_values = True


class DelegationResult(BaseModel):
    """Result of completed delegation."""
    
    delegation_id: str = Field(..., description="Delegation UUID")
    status: DelegationStatus = Field(..., description="Final status")
    success: bool = Field(..., description="Overall success indicator")
    output: Optional[str] = Field(None, description="Agent output/summary")
    error: Optional[str] = Field(None, description="Error message if failed")
    scope_deviation: Optional[str] = Field(None, description="Scope deviation details")
    artifacts: Dict[str, Any] = Field(default_factory=dict, description="Generated artifacts")
    duration_seconds: float = Field(..., description="Actual execution time")
    completed_at: str = Field(..., description="ISO 8601 completion timestamp")
    
    class Config:
        use_enum_values = True
