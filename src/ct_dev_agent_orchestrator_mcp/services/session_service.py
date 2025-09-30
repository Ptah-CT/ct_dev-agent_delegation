"""
Session Service for Agent Orchestrator V2 Migration.

Provides high-level Session-based Agent Management API that replaces 
the DelegationService architecture. Implements 6 core methods for
session lifecycle management with OpenCode integration.

Author: Agent Orchestrator V2 Migration - Phase 2
Dependencies: OpenCodeSessionManager, OpenCodeAPIClient, AgentManager
"""

import asyncio
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
import logfire

from ..models.session import (
    SpawnAgentRequest, 
    SessionInfo, 
    AgentOutput, 
    SessionStatus
)
from ..models.agent import AgentStatus
from .session_manager import OpenCodeSessionManager
from .opencode_api_client import OpenCodeAPIClient
from .agent_manager import AgentManager
from .opencode_service import OpenCodeService


class SessionService:
    """
    High-level Session-based Agent Management Service.
    
    Provides 6 core methods for session lifecycle management:
    - spawn_agent: Create new agent session
    - query_session: Get session status
    - send_to_agent: Send follow-up messages
    - get_agent_output: Retrieve session results
    - stop_agent: Terminate session
    - list_active_sessions: List all active sessions
    """
    
    def __init__(self, opencode_service: Optional[OpenCodeService] = None):
        """Initialize SessionService with required dependencies."""
        self.api_client = OpenCodeAPIClient()
        self.session_manager = OpenCodeSessionManager(self.api_client)
        
        # Initialize OpenCodeService if not provided
        if opencode_service is None:
            from .opencode_service import OpenCodeService
            opencode_service = OpenCodeService(base_port=8000, max_agents=5)
        
        self.agent_manager = AgentManager(opencode_service)
        self._semaphore = asyncio.Semaphore(5)  # Max 5 concurrent operations
        logfire.info("SessionService initialized", extra={"service": "session_service"})
    
    async def spawn_agent(self, request: SpawnAgentRequest) -> SessionInfo:
        """
        Spawn new OpenCode Server and create Session.
        
        Args:
            request: SpawnAgentRequest with role, task_id, instructions, context, model
            
        Returns:
            SessionInfo: Created session with session_id for tracking
            
        Raises:
            Exception: If session creation fails
        """
        async with self._semaphore:
            try:
                logfire.info("Spawning agent session", extra={
                    "role": request.role,
                    "task_id": request.task_id,
                    "model": request.model
                })
                
                # Step 1: Create agent via agent_manager
                agent = await self.agent_manager.create_agent(request.role)
                
                if agent.status == AgentStatus.ERROR or not agent.port:
                    raise RuntimeError(f"Failed to create agent: {agent.status}")
                
                # Step 2: Create session via session_manager
                server_url = f"http://localhost:{agent.port}"
                session_info_dict = await self.session_manager.create_session(
                    server_url=server_url,
                    agent_name=request.role.value,
                    model=request.model,
                    metadata={
                        "task_id": request.task_id,
                        "instructions": request.instructions,
                        "context": request.context,
                        "agent_id": agent.agent_id
                    }
                )
                
                # Convert to SessionInfo
                from ..models.session import SessionInfo, SessionStatus
                session_info = SessionInfo(
                    session_id=session_info_dict["session_id"],
                    agent_role=request.role,
                    status=SessionStatus.ACTIVE,
                    started_at=session_info_dict["created_at"],
                    server_url=server_url,
                    progress={},
                    messages=[]
                )
                
                logfire.info("Agent session spawned successfully", extra={
                    "session_id": session_info.session_id,
                    "server_url": session_info.server_url,
                    "status": session_info.status
                })
                
                return session_info
                
            except asyncio.TimeoutError as e:
                logfire.error("Session spawn timeout", extra={"error": str(e)})
                # Generate a fallback session_id for error response
                fallback_session_id = str(uuid.uuid4())
                return SessionInfo(
                    session_id=fallback_session_id,
                    agent_role=request.role,
                    status=SessionStatus.FAILED,
                    started_at=datetime.utcnow().isoformat(),
                    server_url="",
                    progress={},
                    messages=[]
                )
            except Exception as e:
                logfire.error("Session spawn failed", extra={"error": str(e)})
                raise
    
    async def query_session(self, session_id: str) -> SessionInfo:
        """
        Get current status of a session.
        
        Non-blocking operation that returns current state.
        
        Args:
            session_id: Unique session UUID
            
        Returns:
            SessionInfo: Current session state
            
        Raises:
            Exception: If session not found or query fails
        """
        async with self._semaphore:
            try:
                logfire.debug("Querying session status", extra={"session_id": session_id})
                
                # Query session via session_manager
                session_info = await self.session_manager.get_session(session_id)
                
                logfire.debug("Session status retrieved", extra={
                    "session_id": session_id,
                    "status": session_info.status
                })
                
                return session_info
                
            except Exception as e:
                logfire.error("Session query failed", extra={
                    "session_id": session_id,
                    "error": str(e)
                })
                raise
    
    async def send_to_agent(self, session_id: str, message: str) -> bool:
        """
        Send follow-up message to running session.
        
        Used for clarifications, adjustments, additional instructions.
        
        Args:
            session_id: Target session UUID
            message: Message to send to agent
            
        Returns:
            bool: True if message sent successfully
            
        Raises:
            Exception: If message sending fails
        """
        async with self._semaphore:
            try:
                logfire.info("Sending message to agent", extra={
                    "session_id": session_id,
                    "message_length": len(message)
                })
                
                # Send message via session_manager
                response = await self.session_manager.send_message(session_id, message)
                
                # Consider successful if we got a response without exception
                success = response is not None
                
                if success:
                    logfire.info("Message sent successfully", extra={"session_id": session_id})
                else:
                    logfire.warning("Message sending failed", extra={"session_id": session_id})
                
                return success
                
            except Exception as e:
                logfire.error("Message sending failed", extra={
                    "session_id": session_id,
                    "error": str(e)
                })
                raise
    
    async def get_agent_output(self, session_id: str) -> AgentOutput:
        """
        Get final output from completed session.
        
        Args:
            session_id: Session UUID
            
        Returns:
            AgentOutput: Final session results and artifacts
            
        Raises:
            Exception: If session not completed or output retrieval fails
        """
        async with self._semaphore:
            try:
                logfire.info("Getting agent output", extra={"session_id": session_id})
                
                # First check session status
                session_info = await self.session_manager.get_session(session_id)
                
                if session_info.status not in [SessionStatus.COMPLETED, SessionStatus.FAILED]:
                    raise ValueError(f"Session {session_id} not completed (status: {session_info.status})")
                
                # Get messages to extract final output
                messages = await self.session_manager.get_messages(session_id)
                
                # Calculate duration
                started_at = datetime.fromisoformat(session_info.started_at.replace('Z', '+00:00'))
                completed_at = datetime.utcnow()
                duration = (completed_at - started_at).total_seconds()
                
                # Extract artifacts and summary from messages
                artifacts = {}
                summary = "Session completed"
                
                if messages:
                    # Get last message as summary
                    last_message = messages[-1]
                    if isinstance(last_message, dict) and 'content' in last_message:
                        summary = last_message['content'][:500]  # Truncate for summary
                    
                    # Extract artifacts from session progress
                    artifacts = session_info.progress.get('artifacts', {})
                
                agent_output = AgentOutput(
                    session_id=session_id,
                    status=session_info.status,
                    artifacts=artifacts,
                    summary=summary,
                    duration_seconds=duration,
                    completed_at=completed_at.isoformat()
                )
                
                logfire.info("Agent output retrieved", extra={
                    "session_id": session_id,
                    "status": agent_output.status,
                    "duration": duration
                })
                
                return agent_output
                
            except Exception as e:
                logfire.error("Agent output retrieval failed", extra={
                    "session_id": session_id,
                    "error": str(e)
                })
                raise
    
    async def stop_agent(self, session_id: str) -> bool:
        """
        Stop session and clean up resources.
        
        Args:
            session_id: Session UUID to stop
            
        Returns:
            bool: True if session stopped successfully
            
        Raises:
            Exception: If session stopping fails
        """
        async with self._semaphore:
            try:
                logfire.info("Stopping agent session", extra={"session_id": session_id})
                
                # Stop session via session_manager
                success = await self.session_manager.abort_session(session_id)
                
                if success:
                    logfire.info("Agent session stopped", extra={"session_id": session_id})
                else:
                    logfire.warning("Agent session stop failed", extra={"session_id": session_id})
                
                return success
                
            except Exception as e:
                logfire.error("Agent session stop failed", extra={
                    "session_id": session_id,
                    "error": str(e)
                })
                raise
    
    async def list_active_sessions(self) -> List[SessionInfo]:
        """
        List all active sessions.
        
        Returns:
            List[SessionInfo]: All currently active sessions
            
        Raises:
            Exception: If session listing fails
        """
        async with self._semaphore:
            try:
                logfire.debug("Listing active sessions")
                
                # Get all sessions via session_manager
                all_sessions = await self.session_manager.list_sessions()
                
                # Filter for active sessions only
                active_sessions = [
                    session for session in all_sessions 
                    if session.status in [SessionStatus.RUNNING, SessionStatus.STARTING]
                ]
                
                logfire.info("Active sessions listed", extra={
                    "total_sessions": len(all_sessions),
                    "active_sessions": len(active_sessions)
                })
                
                return active_sessions
                
            except Exception as e:
                logfire.error("Session listing failed", extra={"error": str(e)})
                raise
    
    async def cleanup(self) -> None:
        """Clean up resources and shutdown service."""
        try:
            logfire.info("Cleaning up SessionService")
            
            # Cleanup session manager
            await self.session_manager.cleanup()
            
            # Cleanup API client
            await self.api_client.cleanup()
            
            logfire.info("SessionService cleanup completed")
            
        except Exception as e:
            logfire.error("SessionService cleanup failed", extra={"error": str(e)})
            raise