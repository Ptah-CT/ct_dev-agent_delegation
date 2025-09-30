"""OpenCode Session Manager - Manages agent sessions via OpenCode API.

This module provides session-based agent management using OpenCode Server API.
Each session represents a running agent task.
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import logfire

from .opencode_api_client import OpenCodeAPIClient


class OpenCodeSessionManager:
    """Manages agent sessions via OpenCode Server API.
    
    A session is a running agent instance handling a specific task.
    All operations go through OpenCode Server API.
    """
    
    def __init__(self, api_client: OpenCodeAPIClient):
        """Initialize session manager.
        
        Args:
            api_client: OpenCode API client instance
        """
        self.api_client = api_client
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._server_mapping: Dict[str, str] = {}  # session_id -> server_url
        
    async def create_session(
        self,
        server_url: str,
        agent_name: Optional[str] = None,
        model: Optional[str] = None,
        directory: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create new agent session via OpenCode API.
        
        Args:
            server_url: OpenCode server URL
            agent_name: Agent to use (from GET /agent)
            model: Model to use
            directory: Working directory
            metadata: Additional metadata
            
        Returns:
            Session info dict with:
            - session_id: Session ID
            - server_url: OpenCode server URL  
            - agent_name: Agent name
            - model: Model name
            - status: Session status
            - created_at: Creation timestamp
        """
        try:
            # Prepare request payload
            payload: Dict[str, Any] = {}
            
            if agent_name:
                payload["agent"] = agent_name
            if model:
                payload["model"] = model
            if directory:
                payload["directory"] = directory
                
            # Create session via API
            import httpx
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{server_url}/session",
                    json=payload
                )
                response.raise_for_status()
                session_data = response.json()
            
            session_id = session_data.get("id")
            if not session_id:
                raise ValueError("No session ID in response")
            
            # Store session info
            session_info = {
                "session_id": session_id,
                "server_url": server_url,
                "agent_name": agent_name,
                "model": model,
                "directory": directory,
                "status": "created",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "metadata": metadata or {},
                "raw_data": session_data
            }
            
            self._sessions[session_id] = session_info
            self._server_mapping[session_id] = server_url
            
            logfire.info(
                "Created OpenCode session",
                session_id=session_id,
                agent_name=agent_name,
                model=model,
                server_url=server_url
            )
            
            return session_info
            
        except Exception as e:
            logfire.error(
                "Failed to create session",
                server_url=server_url,
                agent_name=agent_name,
                error=str(e)
            )
            raise
    
    async def get_session(self, session_id: str) -> Dict[str, Any]:
        """Get session details from OpenCode API.
        
        Args:
            session_id: Session ID
            
        Returns:
            Session details dict
        """
        server_url = self._server_mapping.get(session_id)
        if not server_url:
            raise ValueError(f"Unknown session: {session_id}")
        
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{server_url}/session/{session_id}"
                )
                response.raise_for_status()
                session_data = response.json()
            
            # Update cached info
            if session_id in self._sessions:
                self._sessions[session_id]["raw_data"] = session_data
                self._sessions[session_id]["status"] = session_data.get("status", "unknown")
            
            return session_data
            
        except Exception as e:
            logfire.error(
                "Failed to get session",
                session_id=session_id,
                error=str(e)
            )
            raise
    
    async def list_sessions(self, server_url: str) -> List[Dict[str, Any]]:
        """List all sessions on a server.
        
        Args:
            server_url: OpenCode server URL
            
        Returns:
            List of session dicts
        """
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{server_url}/session")
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logfire.error(
                "Failed to list sessions",
                server_url=server_url,
                error=str(e)
            )
            raise
    
    async def send_message(
        self,
        session_id: str,
        message: str,
        files: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Send message to agent session.
        
        Args:
            session_id: Session ID
            message: Message text
            files: Optional list of file paths
            
        Returns:
            Response dict from OpenCode
        """
        server_url = self._server_mapping.get(session_id)
        if not server_url:
            raise ValueError(f"Unknown session: {session_id}")
        
        try:
            payload: Dict[str, Any] = {"message": message}
            
            if files:
                payload["files"] = files
            
            import httpx
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(
                    f"{server_url}/session/{session_id}/message",
                    json=payload
                )
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logfire.error(
                "Failed to send message",
                session_id=session_id,
                error=str(e)
            )
            raise
    
    async def get_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all messages from a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            List of message dicts
        """
        server_url = self._server_mapping.get(session_id)
        if not server_url:
            raise ValueError(f"Unknown session: {session_id}")
        
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{server_url}/session/{session_id}/message"
                )
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logfire.error(
                "Failed to get messages",
                session_id=session_id,
                error=str(e)
            )
            raise
    
    async def abort_session(self, session_id: str) -> Dict[str, Any]:
        """Abort a running session.
        
        Args:
            session_id: Session ID
            
        Returns:
            Response dict
        """
        server_url = self._server_mapping.get(session_id)
        if not server_url:
            raise ValueError(f"Unknown session: {session_id}")
        
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{server_url}/session/{session_id}/abort"
                )
                response.raise_for_status()
                result = response.json()
            
            if session_id in self._sessions:
                self._sessions[session_id]["status"] = "aborted"
            
            logfire.info("Aborted session", session_id=session_id)
            return result
            
        except Exception as e:
            logfire.error(
                "Failed to abort session",
                session_id=session_id,
                error=str(e)
            )
            raise
    
    async def delete_session(self, session_id: str) -> None:
        """Delete a session.
        
        Args:
            session_id: Session ID
        """
        server_url = self._server_mapping.get(session_id)
        if not server_url:
            raise ValueError(f"Unknown session: {session_id}")
        
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.delete(
                    f"{server_url}/session/{session_id}"
                )
                response.raise_for_status()
            
            # Clean up local state
            if session_id in self._sessions:
                del self._sessions[session_id]
            if session_id in self._server_mapping:
                del self._server_mapping[session_id]
            
            logfire.info("Deleted session", session_id=session_id)
            
        except Exception as e:
            logfire.error(
                "Failed to delete session",
                session_id=session_id,
                error=str(e)
            )
            raise
    
    def get_local_sessions(self) -> List[Dict[str, Any]]:
        """Get all locally tracked sessions.
        
        Returns:
            List of session info dicts
        """
        return list(self._sessions.values())
    
    async def cleanup(self):
        """Clean up all sessions."""
        session_ids = list(self._sessions.keys())
        for session_id in session_ids:
            try:
                await self.delete_session(session_id)
            except Exception as e:
                logfire.error(
                    "Error cleaning up session",
                    session_id=session_id,
                    error=str(e)
                )
        
        logfire.info("Cleaned up all sessions")
