"""Task context and scope models."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class TaskScope(BaseModel):
    """Defined scope for a task."""
    
    allowed_operations: List[str] = Field(
        default_factory=list,
        description="Allowed operations (e.g., 'read', 'write', 'execute')"
    )
    file_patterns: List[str] = Field(
        default_factory=list,
        description="File patterns agent can access (glob patterns)"
    )
    tool_restrictions: Dict[str, bool] = Field(
        default_factory=dict,
        description="Tool availability map"
    )
    max_files_modified: int = Field(default=50, description="Max files to modify")
    max_lines_changed: int = Field(default=5000, description="Max lines to change")
    
    class Config:
        json_schema_extra = {
            "example": {
                "allowed_operations": ["read", "write"],
                "file_patterns": ["src/**/*.py", "tests/**/*.py"],
                "tool_restrictions": {"git": True, "bash": False},
                "max_files_modified": 10,
                "max_lines_changed": 500
            }
        }


class TaskContext(BaseModel):
    """Context information for task execution."""
    
    task_id: str = Field(..., description="Task UUID from task_orchestrator")
    scope: TaskScope = Field(..., description="Task scope definition")
    environment: Dict[str, str] = Field(
        default_factory=dict,
        description="Environment variables"
    )
    working_directory: str = Field(..., description="Working directory path")
    git_branch: Optional[str] = Field(None, description="Git branch to work on")
    related_tasks: List[str] = Field(
        default_factory=list,
        description="Related task UUIDs"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "550e8400-e29b-41d4-a716-446655440000",
                "scope": {
                    "allowed_operations": ["read", "write"],
                    "file_patterns": ["src/**/*.py"],
                    "tool_restrictions": {"git": True},
                    "max_files_modified": 10,
                    "max_lines_changed": 500
                },
                "environment": {"DEBUG": "false"},
                "working_directory": "/home/auctor/dev/project",
                "git_branch": "feature/oauth2",
                "related_tasks": []
            }
        }
