"""Agent data model."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    """Agent status states."""
    IDLE = "idle"
    BUSY = "busy"
    STARTING = "starting"
    ERROR = "error"
    UNKNOWN = "unknown"


class AgentRole(str, Enum):
    """Available agent roles matching ~/.claude/agents/."""
    BACKEND_SPECIALIST = "backend_specialist"
    BUG_HUNTER = "bug_hunter"
    CODE_REVIEWER = "code_reviewer"
    DATABASE_ARCHITECT = "database_architect"
    DEVOPS_ENGINEER = "devops_engineer"
    DOCUMENTATION_SPECIALIST = "documentation_specialist"
    FRONTEND_SPECIALIST = "frontend_specialist"
    GENERIC_ENGINEER = "generic_engineer"
    INTEGRATION_SPECIALIST = "integration_specialist"
    PERFORMANCE_ENGINEER = "performance_engineer"
    PRODUCT_MANAGER = "product_manager"
    PROJECT_ARCHITECT = "project_architect"
    QUALITY_ASSURANCE = "quality_assurance"
    REFACTORING_SPECIALIST = "refactoring_specialist"
    RESEARCH_SPECIALIST = "research_specialist"
    SECURITY_EXPERT = "security_expert"
    SYSTEM_ARCHITECT = "system_architect"
    TECHNICAL_WRITER = "technical_writer"


class Agent(BaseModel):
    """Agent instance representation."""
    
    agent_id: str = Field(..., description="Unique agent identifier (UUID)")
    role: AgentRole = Field(..., description="Agent role")
    status: AgentStatus = Field(default=AgentStatus.IDLE, description="Current status")
    port: Optional[int] = Field(None, description="OpenCode server port")
    pid: Optional[int] = Field(None, description="Process ID of opencode serve")
    health_check_url: Optional[str] = Field(None, description="Health check endpoint")
    created_at: str = Field(..., description="ISO 8601 creation timestamp")
    last_health_check: Optional[str] = Field(None, description="ISO 8601 last health check")
    current_delegation_id: Optional[str] = Field(None, description="Current delegation UUID if busy")
