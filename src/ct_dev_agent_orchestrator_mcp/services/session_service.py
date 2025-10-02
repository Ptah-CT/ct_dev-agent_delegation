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
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import logfire

# Configure logfire with token from environment or disable
try:
    token = os.getenv("LOGFIRE_TOKEN")
    if token:
        logfire.configure(token=token)
    else:
        logfire.configure(send_to_logfire=False)
except Exception:
    logfire.configure(send_to_logfire=False)

from ..models.session import (
    SpawnAgentRequest,
    SessionInfo,
    AgentOutput,
    SessionStatus
)
from ..models.agent import AgentRole
from .session_manager import OpenCodeSessionManager
from .opencode_api_client import OpenCodeAPIClient
from .agent_manager import AgentManager
from .opencode_service import OpenCodeService
from ..utils.scope_deviation import ScopeDeviationDetector


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
        # Port allocation is now handled dynamically by OpenCode
        if opencode_service is None:
            from .opencode_service import OpenCodeService
            opencode_service = OpenCodeService(max_agents=5)
        
        self.agent_manager = AgentManager(opencode_service)
        self._semaphore = asyncio.Semaphore(5)  # Max 5 concurrent operations
        
        # Session registry: session_id -> server_url mapping
        self._sessions: Dict[str, str] = {}
        
        logfire.info("SessionService initialized", extra={"service": "session_service"})
    
    async def spawn_agent(self, request: SpawnAgentRequest) -> SessionInfo:
        """
        Create agent via AgentManager and establish OpenCode session.
        
        This method orchestrates the agent lifecycle:
        1. Creates agent instance via AgentManager (which starts OpenCode server)
        2. Creates session via SessionManager with the agent's server
        
        Args:
            request: SpawnAgentRequest with role, task_id, instructions, context, model
            
        Returns:
            SessionInfo: Created session with session_id for tracking
            
        Raises:
            Exception: If agent creation or session creation fails
        """
        async with self._semaphore:
            try:
                logfire.info("Spawning agent session", extra={
                    "role": request.role,
                    "task_id": request.task_id,
                    "model": request.model
                })
                
                # Step 1: Create agent via agent_manager (convert str to AgentRole enum)
                agent = await self.agent_manager.create_agent(AgentRole(request.role))
                
                # Step 2: Create session via session_manager
                server_url = f"http://localhost:{agent.port}"
                session_info_dict = await self.session_manager.create_session(
                    server_url=server_url,
                    title=f"Agent {request.role} - Task {request.task_id}",
                    directory=request.project_directory,
                    metadata={
                        "task_id": request.task_id,
                        "instructions": request.instructions,
                        "expected_output": request.expected_output,
                        "context": request.context,
                        "agent_id": agent.agent_id,
                        "agent_role": request.role
                    }
                )
                
                # Convert dict to SessionInfo
                session_info = SessionInfo(
                    session_id=session_info_dict["session_id"],
                    agent_role=request.role,
                    status=SessionStatus.RUNNING,
                    started_at=session_info_dict["created_at"],
                    server_url=server_url,
                    progress={},
                    messages=[]
                )
                
                # Add to session registry for tracking
                self._sessions[session_info.session_id] = server_url

                # Step 3: Queue initial instructions in background (fire-and-forget)
                # Don't wait for AI response - return immediately so spawn_agent is fast
                import asyncio
                asyncio.create_task(self._send_initial_instructions(
                    session_id=session_info.session_id,
                    instructions=request.instructions,
                    model=request.model
                ))

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

    def _check_and_update_scope_deviation(
        self,
        session_id: str,
        response: Dict[str, Any]
    ) -> None:
        """
        Check agent response for scope deviation and update session metadata.

        Args:
            session_id: Session UUID
            response: Agent response dict with 'parts' list
        """
        try:
            # Extract text from response parts
            parts = response.get("parts", [])
            for part in parts:
                if part.get("type") == "text":
                    text = part.get("text", "")
                    deviation = ScopeDeviationDetector.detect_scope_keywords(text)

                    if deviation:
                        # Update session metadata with deviation info
                        session_info = self.session_manager._sessions.get(session_id)
                        if session_info:
                            session_info["scope_deviation"] = deviation

                            # Log and potentially escalate
                            if ScopeDeviationDetector.should_escalate(deviation):
                                logfire.error(
                                    "SCOPE DEVIATION DETECTED - ESCALATION REQUIRED",
                                    session_id=session_id,
                                    deviation_type=deviation["type"],
                                    severity=deviation["severity"],
                                    message=deviation["message"]
                                )
                            else:
                                logfire.warn(
                                    "Scope deviation detected",
                                    session_id=session_id,
                                    deviation_type=deviation["type"],
                                    severity=deviation["severity"]
                                )

                        # Stop after first deviation detected
                        break

        except Exception as e:
            logfire.error(
                "Failed to check scope deviation",
                session_id=session_id,
                error=str(e)
            )

    async def _send_initial_instructions(
        self,
        session_id: str,
        instructions: str,
        model: Optional[str] = None
    ) -> None:
        """
        Send initial instructions to agent in background (fire-and-forget).
        This runs as a background task and doesn't block spawn_agent.
        """
        try:
            response = await self.session_manager.send_message(
                session_id=session_id,
                message=instructions,
                agent_name=None,
                provider_id=None,
                model_id=model
            )

            # Check for scope deviation in initial response
            if response:
                self._check_and_update_scope_deviation(session_id, response)

            logfire.info("Initial instructions sent", extra={
                "session_id": session_id
            })
        except Exception as e:
            logfire.error("Failed to send initial instructions", extra={
                "session_id": session_id,
                "error": str(e)
            })

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
                
                # Get server URL from registry
                if session_id not in self._sessions:
                    raise ValueError(f"Session {session_id} not found in registry")
                
                server_url = self._sessions[session_id]
                
                # Get local session info from session_manager (contains metadata)
                local_session_info = self.session_manager._sessions.get(session_id)
                if not local_session_info:
                    raise ValueError(f"Session {session_id} not found in session manager")

                # Query OpenCode API for current status (optional, for live status)
                try:
                    await self.session_manager.get_session(session_id)
                except Exception:
                    pass

                # Get messages to populate message list
                try:
                    messages_data = await self.session_manager.get_messages(session_id)
                    messages = []
                    for msg in messages_data:
                        info = msg.get('info', {})
                        parts = msg.get('parts', [])
                        # Build message dict
                        message_dict = {
                            "id": info.get('id', ''),
                            "role": info.get('role', 'unknown'),
                            "parts": parts
                        }
                        messages.append(message_dict)
                except Exception as e:
                    logfire.warning("Failed to fetch messages", extra={
                        "session_id": session_id,
                        "error": str(e)
                    })
                    messages = []

                # Use local metadata as primary source (OpenCode API doesn't preserve custom metadata)
                local_metadata = local_session_info.get("metadata", {})

                # Get scope deviation if detected
                scope_deviation = local_session_info.get("scope_deviation")

                session_info = SessionInfo(
                    session_id=session_id,
                    agent_role=local_metadata.get("agent_role", "unknown"),
                    status=SessionStatus.RUNNING,
                    started_at=local_session_info.get("created_at", ""),
                    server_url=server_url,
                    progress=local_metadata.get("progress", {}),
                    messages=messages,
                    scope_deviation=scope_deviation
                )
                
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

                # Check for scope deviation in agent response
                if response:
                    self._check_and_update_scope_deviation(session_id, response)

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
                session_data = await self.session_manager.get_session(session_id)
                
                # Get server URL from registry
                if session_id not in self._sessions:
                    raise ValueError(f"Session {session_id} not found in registry")
                
                server_url = self._sessions[session_id]
                
                # Map OpenCode fields to SessionInfo fields
                session_info = SessionInfo(
                    session_id=session_data.get("id", session_id),
                    agent_role=session_data.get("metadata", {}).get("agent_role", "unknown"),
                    status=SessionStatus.RUNNING,
                    started_at=session_data.get("created", ""),
                    server_url=server_url,
                    progress=session_data.get("metadata", {}).get("progress", {}),
                    messages=[]
                )
                
                if session_info.status not in (SessionStatus.COMPLETED, SessionStatus.FAILED):
                    raise ValueError(f"Session {session_id} not completed (status: {session_info.status})")
                
                # Get messages to extract final output
                messages = await self.session_manager.get_messages(session_id)
                
                # Calculate duration with timezone-aware datetime
                from datetime import timezone
                started_at = datetime.fromisoformat(session_info.started_at.replace('Z', '+00:00'))
                completed_at = datetime.now(timezone.utc)
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
                
                # Get server_url from own registry
                server_url = self._sessions.get(session_id)
                if not server_url:
                    raise ValueError(f"Session {session_id} not found in registry")
                
                # Stop session via session_manager with explicit server_url
                success = await self.session_manager.abort_session(session_id, server_url)
                
                # Remove from registry on successful stop
                if success and session_id in self._sessions:
                    del self._sessions[session_id]
                    logfire.debug("Session removed from registry", extra={"session_id": session_id})
                
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
                
                # Get unique server URLs from registry
                unique_servers = set(self._sessions.values())
                
                if not unique_servers:
                    logfire.info("No sessions in registry")
                    return []
                
                # Collect sessions from all servers
                all_sessions = []
                for server_url in unique_servers:
                    try:
                        server_sessions = await self.session_manager.list_sessions(server_url)
                        all_sessions.extend(server_sessions)
                    except Exception as e:
                        logfire.warning(f"Failed to list sessions from {server_url}", extra={"error": str(e)})
                        continue
                
                # Filter for active sessions only (those in our registry) and deduplicate
                seen_ids = set()
                active_sessions = []
                for session in all_sessions:
                    session_id = session.get("id")
                    if session_id in self._sessions and session_id not in seen_ids:
                        active_sessions.append(session)
                        seen_ids.add(session_id)

                # Convert to SessionInfo objects using local metadata
                session_infos = []
                for session_dict in active_sessions:
                    try:
                        session_id = session_dict.get("id", "")
                        # Get local session info for accurate metadata
                        local_session_info = self.session_manager._sessions.get(session_id, {})
                        local_metadata = local_session_info.get("metadata", {})

                        # Get scope deviation if detected
                        scope_deviation = local_session_info.get("scope_deviation")

                        session_info = SessionInfo(
                            session_id=session_id,
                            agent_role=local_metadata.get("agent_role", "unknown"),
                            status=SessionStatus.RUNNING,
                            started_at=local_session_info.get("created_at", ""),
                            server_url=self._sessions[session_id],
                            progress=local_metadata.get("progress", {}),
                            messages=[],
                            scope_deviation=scope_deviation
                        )
                        session_infos.append(session_info)
                    except Exception as e:
                        logfire.warning(f"Failed to parse session {session_dict.get('id')}", extra={"error": str(e)})
                        continue
                
                logfire.info("Active sessions listed", extra={
                    "total_servers": len(unique_servers),
                    "active_sessions": len(session_infos)
                })
                
                return session_infos
                
            except Exception as e:
                logfire.error("Session listing failed", extra={"error": str(e)})
                raise
    
    async def cleanup(self) -> None:
        """Clean up resources and shutdown service."""
        try:
            logfire.info("Cleaning up SessionService")
            
            # Stop AgentManager and underlying agents first
            try:
                if hasattr(self.agent_manager, 'stop_all_agents'):
                    await self.agent_manager.stop_all_agents()
                    logfire.info("All agents stopped successfully")
            except Exception as e:
                logfire.error("Failed to stop agents during cleanup", extra={"error": str(e)})
            
            # Cleanup session manager
            await self.session_manager.cleanup()
            
            # Cleanup API client
            await self.api_client.cleanup()
            
            logfire.info("SessionService cleanup completed")
            
        except Exception as e:
            logfire.error("SessionService cleanup failed", extra={"error": str(e)})
            raise