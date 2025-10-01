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
        title: Optional[str] = None,
        directory: Optional[str] = None,
        parent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create new agent session via OpenCode API.
        
        NOTE: OpenCode 0.13.5+ uses session-based architecture.
        Agent and model are specified PER MESSAGE, not at session creation.
        
        Args:
            server_url: OpenCode server URL
            title: Session title
            directory: Working directory
            parent_id: Parent session ID for nested sessions
            metadata: Additional metadata
            
        Returns:
            Session info dict with:
            - session_id: Session ID (format: ses_...)
            - server_url: OpenCode server URL  
            - directory: Working directory
            - status: Session status
            - created_at: Creation timestamp
        """
        try:
            # Prepare request payload (API spec)
            payload: Dict[str, Any] = {}
            
            if title:
                payload["title"] = title
            if parent_id:
                payload["parentID"] = parent_id
                
            # Query parameter for directory
            params = {}
            if directory:
                params["directory"] = directory
            
            # Create session via API
            import httpx
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{server_url}/session",
                    json=payload,
                    params=params
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
                "title": title,
                "directory": session_data.get("directory"),
                "parent_id": parent_id,
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
                title=title,
                server_url=server_url
            )
            
            return session_info
            
        except Exception as e:
            logfire.error(
                "Failed to create session",
                server_url=server_url,
                title=title,
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
        agent_name: Optional[str] = None,
        provider_id: Optional[str] = None,
        model_id: Optional[str] = None,
        files: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Send message to agent session with OpenCode 0.13.5+ API.
        
        NOTE: Agent and model are specified PER MESSAGE, not per session.
        This allows dynamic agent/model switching within a session.
        
        Args:
            session_id: Session ID
            message: Message text
            agent_name: Optional agent to use (from GET /agent)
            provider_id: Provider ID (e.g., "mistral", "openrouter")
            model_id: Model ID (e.g., "devstral-medium-2507")
            files: Optional list of file paths
            
        Returns:
            Response dict from OpenCode with structure:
            {
                "info": {
                    "id": "msg_...",
                    "role": "assistant",
                    ...
                },
                "parts": [
                    {
                        "type": "text",
                        "text": "AI response..."
                    }
                ]
            }
        """
        server_url = self._server_mapping.get(session_id)
        if not server_url:
            raise ValueError(f"Unknown session: {session_id}")
        
        try:
            # Build payload according to API spec
            payload: Dict[str, Any] = {
                "parts": [
                    {
                        "type": "text",
                        "text": message
                    }
                ]
            }
            
            # Add agent if specified
            if agent_name:
                payload["agent"] = agent_name
            
            # Add model if specified (requires both provider and model)
            if provider_id and model_id:
                payload["model"] = {
                    "providerID": provider_id,
                    "modelID": model_id
                }
            
            # Add file parts if specified
            if files:
                for file_path in files:
                    payload["parts"].append({
                        "type": "file",
                        "path": file_path
                    })
            
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
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
                agent=agent_name,
                provider=provider_id,
                model=model_id,
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
    
    async def get_available_providers(self, server_url: str) -> Dict[str, Any]:
        """Get available AI providers and models from OpenCode server.
        
        Args:
            server_url: OpenCode server URL
            
        Returns:
            Dict with structure:
            {
                "providers": [
                    {
                        "id": "mistral",
                        "name": "Mistral",
                        "models": {
                            "devstral-medium-2507": {
                                "id": "devstral-medium-2507",
                                "name": "Devstral Medium",
                                ...
                            }
                        }
                    }
                ]
            }
        """
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{server_url}/config/providers")
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logfire.error(
                "Failed to get providers",
                server_url=server_url,
                error=str(e)
            )
            raise
    
    async def get_available_agents(self, server_url: str) -> List[Dict[str, Any]]:
        """Get available agents from OpenCode server.
        
        Args:
            server_url: OpenCode server URL
            
        Returns:
            List of agent dicts with structure:
            {
                "name": str,
                "description": str,
                "mode": "subagent" | "primary" | "all",
                "builtIn": bool,
                ...
            }
        """
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{server_url}/agent")
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logfire.error(
                "Failed to get agents",
                server_url=server_url,
                error=str(e)
            )
            raise
    
    async def abort_session(self, session_id: str, server_url: Optional[str] = None) -> bool:
        """Abort a running session.
        
        Args:
            session_id: Session ID
            server_url: Optional server URL. If not provided, looks up in _server_mapping
            
        Returns:
            bool: True if abort succeeded, False otherwise
        """
        # If server_url not provided, look up in _server_mapping (backward compatibility)
        if not server_url:
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
            
            # Parse boolean result from API
            success = result if isinstance(result, bool) else bool(result)
            
            if success and session_id in self._sessions:
                self._sessions[session_id]["status"] = "aborted"
            
            logfire.info("Aborted session", session_id=session_id, success=success)
            return success
            
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
