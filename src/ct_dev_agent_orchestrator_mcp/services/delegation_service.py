"""Delegation service for managing agent work assignments."""

import asyncio
import json
from typing import Dict, Optional
from datetime import datetime, timezone
import uuid
import logfire

from ..models.delegation import (
    DelegationRequest,
    DelegationResponse,
    DelegationResult,
    DelegationStatus
)
from ..models.agent import AgentRole
from .agent_manager import AgentManager
from .opencode_service import OpenCodeService
from ..storage.database import get_database
from ..utils.constitution_gate import get_constitution_gate


class DelegationService:
    """Manages work delegation to agents."""
    
    def __init__(self, agent_manager: AgentManager, opencode_service: OpenCodeService):
        """Initialize delegation service.
        
        Args:
            agent_manager: Agent manager instance
            opencode_service: OpenCode service instance
        """
        self.agent_manager = agent_manager
        self.opencode_service = opencode_service
        self.delegations: Dict[str, Dict] = {}
        self._tasks: Dict[str, asyncio.Task] = {}
        self.db = get_database()
        self.constitution_gate = get_constitution_gate()
        
    async def delegate(self, request: DelegationRequest) -> DelegationResponse:
        """Delegate work to an agent (fire-and-forget).
        
        Args:
            request: Delegation request
            
        Returns:
            Delegation response with tracking ID
        """
        delegation_id = str(uuid.uuid4())
        
        try:
            # Constitution gate check
            approved, violations = self.constitution_gate.check_delegation(
                task_id=request.task_id,
                instructions=request.instructions,
                delegator="Main Agent"  # TODO: Get from context
            )
            
            if not approved:
                error_msg = "; ".join([v.description for v in violations])
                raise ValueError(f"Delegation rejected by constitution gate: {error_msg}")
            
            # Parse role
            role = AgentRole(request.agent_role)
            
            # Get or create agent
            agent = await self.agent_manager.get_or_create_agent(role)
            
            # Mark agent as busy
            await self.agent_manager.mark_busy(agent.agent_id, delegation_id)
            
            # Store delegation
            created_at = datetime.now(timezone.utc).isoformat()
            self.delegations[delegation_id] = {
                "id": delegation_id,
                "agent_id": agent.agent_id,
                "task_id": request.task_id,
                "status": DelegationStatus.PENDING,
                "request": request,
                "created_at": created_at,
                "started_at": None,
                "completed_at": None,
                "result": None
            }
            
            # Persist to database
            self.db.execute("""
                INSERT INTO delegations 
                (delegation_id, agent_id, task_id, status, created_at, 
                 instructions, context, timeout_seconds)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                delegation_id,
                agent.agent_id,
                request.task_id,
                DelegationStatus.PENDING.value,
                created_at,
                request.instructions,
                json.dumps(request.context),
                request.timeout_seconds
            ))
            
            # Log delegation event
            self.db.execute("""
                INSERT INTO delegation_events 
                (delegation_id, timestamp, event_type, delegator, 
                 delegatee_agent_id, responsibility_chain)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                delegation_id,
                created_at,
                "DELEGATED",
                "Main Agent",
                agent.agent_id,
                json.dumps(["Main Agent", agent.role.value])
            ))
            
            # Start execution in background
            task = asyncio.create_task(
                self._execute_delegation(delegation_id, agent.agent_id, request)
            )
            self._tasks[delegation_id] = task
            
            logfire.info(
                f"Delegation {delegation_id} created",
                agent_id=agent.agent_id,
                task_id=request.task_id,
                role=role.value
            )
            
            # Return immediately (fire-and-forget)
            return DelegationResponse(
                delegation_id=delegation_id,
                agent_id=agent.agent_id,
                status=DelegationStatus.PENDING,
                message=f"Work delegated to {role.value} agent",
                estimated_completion=None  # TODO: Calculate based on timeout
            )
            
        except Exception as e:
            logfire.error(f"Delegation failed", error=str(e))
            raise
    
    async def _execute_delegation(
        self,
        delegation_id: str,
        agent_id: str,
        request: DelegationRequest
    ):
        """Execute delegation work (background task).
        
        Args:
            delegation_id: Delegation UUID
            agent_id: Agent UUID
            request: Delegation request
        """
        delegation = self.delegations[delegation_id]
        
        try:
            # Update status
            delegation["status"] = DelegationStatus.RUNNING
            delegation["started_at"] = datetime.now(timezone.utc).isoformat()
            
            agent = await self.agent_manager.get_agent(agent_id)
            if not agent:
                raise RuntimeError(f"Agent {agent_id} not found")
            
            logfire.info(f"Executing delegation {delegation_id}")
            
            # Send work to agent via OpenCode API
            payload = {
                "task_id": request.task_id,
                "instructions": request.instructions,
                "context": request.context,
                "timeout": request.timeout_seconds
            }
            
            # Execute with timeout
            try:
                result_data = await asyncio.wait_for(
                    self.opencode_service.send_request(
                        agent,
                        "/execute",
                        payload
                    ),
                    timeout=request.timeout_seconds
                )
                
                # Create result
                completed_at = datetime.now(timezone.utc).isoformat()
                started_at = datetime.fromisoformat(delegation["started_at"])
                duration = (
                    datetime.fromisoformat(completed_at) - started_at
                ).total_seconds()
                
                result = DelegationResult(
                    delegation_id=delegation_id,
                    status=DelegationStatus.COMPLETED,
                    success=True,
                    output=result_data.get("output"),
                    error=None,
                    scope_deviation=result_data.get("scope_deviation"),
                    artifacts=result_data.get("artifacts", {}),
                    duration_seconds=duration,
                    completed_at=completed_at
                )
                
                delegation["status"] = DelegationStatus.COMPLETED
                delegation["result"] = result
                delegation["completed_at"] = completed_at
                
                logfire.info(
                    f"Delegation {delegation_id} completed",
                    duration=duration
                )
                
            except asyncio.TimeoutError:
                logfire.error(f"Delegation {delegation_id} timed out")
                delegation["status"] = DelegationStatus.FAILED
                delegation["completed_at"] = datetime.now(timezone.utc).isoformat()
                
                result = DelegationResult(
                    delegation_id=delegation_id,
                    status=DelegationStatus.FAILED,
                    success=False,
                    output=None,
                    error="Execution timeout",
                    scope_deviation=None,
                    artifacts={},
                    duration_seconds=request.timeout_seconds,
                    completed_at=delegation["completed_at"]
                )
                delegation["result"] = result
                
        except Exception as e:
            logfire.error(f"Delegation {delegation_id} failed", error=str(e))
            
            delegation["status"] = DelegationStatus.FAILED
            delegation["completed_at"] = datetime.now(timezone.utc).isoformat()
            
            duration = 0
            if delegation.get("started_at"):
                started_at = datetime.fromisoformat(delegation["started_at"])
                duration = (
                    datetime.fromisoformat(delegation["completed_at"]) - started_at
                ).total_seconds()
            
            result = DelegationResult(
                delegation_id=delegation_id,
                status=DelegationStatus.FAILED,
                success=False,
                output=None,
                error=str(e),
                scope_deviation=None,
                artifacts={},
                duration_seconds=duration,
                completed_at=delegation["completed_at"]
            )
            delegation["result"] = result
            
        finally:
            # Mark agent as idle
            await self.agent_manager.mark_idle(agent_id)
            
            # Clean up task
            if delegation_id in self._tasks:
                del self._tasks[delegation_id]
    
    async def get_status(self, delegation_id: str) -> Optional[Dict]:
        """Get delegation status.
        
        Args:
            delegation_id: Delegation UUID
            
        Returns:
            Delegation details or None
        """
        return self.delegations.get(delegation_id)
    
    async def get_result(self, delegation_id: str) -> Optional[DelegationResult]:
        """Get delegation result.
        
        Args:
            delegation_id: Delegation UUID
            
        Returns:
            Delegation result or None
        """
        delegation = self.delegations.get(delegation_id)
        if not delegation:
            return None
        
        return delegation.get("result")
    
    async def cancel_delegation(self, delegation_id: str) -> bool:
        """Cancel a running delegation.
        
        Args:
            delegation_id: Delegation UUID
            
        Returns:
            True if cancelled
        """
        delegation = self.delegations.get(delegation_id)
        if not delegation:
            return False
        
        if delegation["status"] not in [DelegationStatus.PENDING, DelegationStatus.RUNNING]:
            return False
        
        # Cancel task
        task = self._tasks.get(delegation_id)
        if task:
            task.cancel()
        
        # Update status
        delegation["status"] = DelegationStatus.FAILED
        delegation["completed_at"] = datetime.now(timezone.utc).isoformat()
        
        # Mark agent as idle
        agent_id = delegation["agent_id"]
        await self.agent_manager.mark_idle(agent_id)
        
        logfire.info(f"Delegation {delegation_id} cancelled")
        return True
    
    async def list_delegations(self) -> list:
        """List all delegations.
        
        Returns:
            List of delegation details
        """
        return list(self.delegations.values())
