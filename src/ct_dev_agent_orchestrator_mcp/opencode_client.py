"""
OpenCode API Client
Handles communication with OpenCode server via REST API and SSE.
"""
import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime, timedelta

import httpx
from httpx_sse import aconnect_sse

logger = logging.getLogger(__name__)


@dataclass
class OpenCodeAgent:
    """OpenCode Agent definition."""
    name: str
    description: str
    mode: str  # "subagent" | "primary" | "all"
    built_in: bool
    model: Dict[str, str]  # {"modelID": str, "providerID": str}
    permission: Dict[str, Any]
    tools: Dict[str, bool]
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    prompt: Optional[str] = None
    options: Optional[Dict[str, Any]] = None


@dataclass
class OpenCodeModel:
    """OpenCode Model definition."""
    id: str
    name: str
    provider_id: str
    release_date: str
    attachment: bool
    reasoning: bool
    temperature: bool
    tool_call: bool
    cost: Dict[str, float]  # {input, output, cache_read?, cache_write?}
    limit: Dict[str, int]  # {context, output}
    experimental: bool = False
    options: Optional[Dict[str, Any]] = None


@dataclass
class OpenCodeSession:
    """OpenCode Session."""
    id: str
    project_id: str
    directory: str
    title: str
    version: str
    time: Dict[str, float]  # {created, updated, compacting?}
    parent_id: Optional[str] = None
    share: Optional[Dict[str, str]] = None  # {url}
    revert: Optional[Dict[str, Any]] = None


@dataclass
class OpenCodeMessage:
    """OpenCode Message."""
    id: str
    session_id: str
    role: str  # "user" | "assistant"
    time: Dict[str, float]
    
    # Assistant message fields
    model_id: Optional[str] = None
    provider_id: Optional[str] = None
    mode: Optional[str] = None
    cost: Optional[float] = None
    tokens: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None


@dataclass
class OpenCodePart:
    """Message Part."""
    id: str
    session_id: str
    message_id: str
    type: str  # text, reasoning, file, tool, step-start, step-finish, snapshot, patch, agent
    
    # Type-specific fields
    text: Optional[str] = None
    tool: Optional[str] = None
    call_id: Optional[str] = None
    state: Optional[Dict[str, Any]] = None
    cost: Optional[float] = None
    tokens: Optional[Dict[str, Any]] = None


class OpenCodeClient:
    """Client for OpenCode REST API."""
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        socket_path: Optional[str] = None,
        timeout: float = 300.0,
    ):
        """
        Initialize OpenCode client.
        
        Args:
            base_url: HTTP base URL (e.g., "http://localhost:8080")
            socket_path: Unix socket path (e.g., "~/.opencode/server.sock")
            timeout: Request timeout in seconds
        """
        self.base_url = base_url
        self.socket_path = Path(socket_path).expanduser() if socket_path else None
        self.timeout = timeout
        
        # Cache
        self._agents_cache: Optional[List[OpenCodeAgent]] = None
        self._agents_cache_time: Optional[datetime] = None
        self._models_cache: Optional[Dict[str, List[OpenCodeModel]]] = None
        self._models_cache_time: Optional[datetime] = None
        self._cache_ttl = timedelta(minutes=5)
        
        # HTTP client
        self._client: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_client()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def _ensure_client(self):
        """Ensure HTTP client is initialized."""
        if self._client is not None:
            return
        
        # Discover connection
        if not self.base_url and not self.socket_path:
            self._discover_connection()
        
        # Create client
        if self.socket_path and self.socket_path.exists():
            # Unix socket
            transport = httpx.AsyncHTTPTransport(uds=str(self.socket_path))
            self._client = httpx.AsyncClient(
                transport=transport,
                base_url="http://opencode",
                timeout=self.timeout,
            )
            logger.info(f"Connected to OpenCode via Unix socket: {self.socket_path}")
        elif self.base_url:
            # HTTP URL
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
            )
            logger.info(f"Connected to OpenCode via HTTP: {self.base_url}")
        else:
            raise ValueError("No OpenCode server connection available")
    
    def _discover_connection(self):
        """Discover OpenCode server connection."""
        # Try Unix socket
        default_socket = Path.home() / ".opencode" / "server.sock"
        if default_socket.exists():
            self.socket_path = default_socket
            return
        
        # Try environment
        if url := os.getenv("OPENCODE_SERVER_URL"):
            self.base_url = url
            return
        
        # Try config file
        config_file = Path.home() / ".opencode" / "config.json"
        if config_file.exists():
            try:
                config = json.loads(config_file.read_text())
                # Config might have server URL
                # (structure depends on actual config format)
                pass
            except Exception as e:
                logger.warning(f"Failed to parse OpenCode config: {e}")
        
        # Default to localhost
        self.base_url = "http://localhost:8080"
    
    async def _get(self, path: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make GET request."""
        await self._ensure_client()
        response = await self._client.get(path, params=params or {})
        response.raise_for_status()
        return response.json()
    
    async def _post(
        self,
        path: str,
        json_data: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Make POST request."""
        await self._ensure_client()
        response = await self._client.post(
            path,
            json=json_data,
            params=params or {},
        )
        response.raise_for_status()
        return response.json()
    
    async def _patch(
        self,
        path: str,
        json_data: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Make PATCH request."""
        await self._ensure_client()
        response = await self._client.patch(
            path,
            json=json_data,
            params=params or {},
        )
        response.raise_for_status()
        return response.json()
    
    async def _delete(self, path: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make DELETE request."""
        await self._ensure_client()
        response = await self._client.delete(path, params=params or {})
        response.raise_for_status()
        return response.json()
    
    # Agent Management
    
    async def list_agents(
        self,
        force_refresh: bool = False,
    ) -> List[OpenCodeAgent]:
        """
        List all available agents.
        
        Args:
            force_refresh: Force refresh of cache
            
        Returns:
            List of OpenCodeAgent objects
        """
        # Check cache
        if not force_refresh and self._agents_cache:
            if self._agents_cache_time:
                age = datetime.now() - self._agents_cache_time
                if age < self._cache_ttl:
                    return self._agents_cache
        
        # Fetch from API
        data = await self._get("/agent")
        
        agents = []
        for agent_data in data:
            agents.append(OpenCodeAgent(
                name=agent_data["name"],
                description=agent_data.get("description", ""),
                mode=agent_data["mode"],
                built_in=agent_data["builtIn"],
                model=agent_data["model"],
                permission=agent_data["permission"],
                tools=agent_data["tools"],
                temperature=agent_data.get("temperature"),
                top_p=agent_data.get("topP"),
                prompt=agent_data.get("prompt"),
                options=agent_data.get("options"),
            ))
        
        # Update cache
        self._agents_cache = agents
        self._agents_cache_time = datetime.now()
        
        logger.info(f"Loaded {len(agents)} agents from OpenCode")
        return agents
    
    async def get_agent(self, name: str) -> Optional[OpenCodeAgent]:
        """Get agent by name."""
        agents = await self.list_agents()
        for agent in agents:
            if agent.name == name:
                return agent
        return None
    
    # Model/Provider Management
    
    async def list_providers(
        self,
        force_refresh: bool = False,
    ) -> Dict[str, List[OpenCodeModel]]:
        """
        List all providers and their models.
        
        Args:
            force_refresh: Force refresh of cache
            
        Returns:
            Dict mapping provider_id to list of models
        """
        # Check cache
        if not force_refresh and self._models_cache:
            if self._models_cache_time:
                age = datetime.now() - self._models_cache_time
                if age < self._cache_ttl:
                    return self._models_cache
        
        # Fetch from API
        data = await self._get("/config/providers")
        
        providers = {}
        for provider_data in data["providers"]:
            provider_id = provider_data["id"]
            models = []
            
            for model_id, model_data in provider_data.get("models", {}).items():
                models.append(OpenCodeModel(
                    id=model_data["id"],
                    name=model_data["name"],
                    provider_id=provider_id,
                    release_date=model_data["release_date"],
                    attachment=model_data["attachment"],
                    reasoning=model_data["reasoning"],
                    temperature=model_data["temperature"],
                    tool_call=model_data["tool_call"],
                    cost=model_data["cost"],
                    limit=model_data["limit"],
                    experimental=model_data.get("experimental", False),
                    options=model_data.get("options"),
                ))
            
            providers[provider_id] = models
        
        # Update cache
        self._models_cache = providers
        self._models_cache_time = datetime.now()
        
        total_models = sum(len(models) for models in providers.values())
        logger.info(f"Loaded {total_models} models from {len(providers)} providers")
        return providers
    
    async def get_model(
        self,
        provider_id: str,
        model_id: str,
    ) -> Optional[OpenCodeModel]:
        """Get specific model."""
        providers = await self.list_providers()
        for model in providers.get(provider_id, []):
            if model.id == model_id:
                return model
        return None
    
    # Session Management
    
    async def list_sessions(self) -> List[OpenCodeSession]:
        """List all sessions."""
        data = await self._get("/session")
        
        sessions = []
        for session_data in data:
            sessions.append(OpenCodeSession(
                id=session_data["id"],
                project_id=session_data["projectID"],
                directory=session_data["directory"],
                title=session_data["title"],
                version=session_data["version"],
                time=session_data["time"],
                parent_id=session_data.get("parentID"),
                share=session_data.get("share"),
                revert=session_data.get("revert"),
            ))
        
        return sessions
    
    async def create_session(
        self,
        title: Optional[str] = None,
        parent_id: Optional[str] = None,
    ) -> OpenCodeSession:
        """
        Create new session.
        
        Args:
            title: Session title
            parent_id: Parent session ID for sub-sessions
            
        Returns:
            Created session
        """
        payload = {}
        if title:
            payload["title"] = title
        if parent_id:
            payload["parentID"] = parent_id
        
        data = await self._post("/session", json_data=payload)
        
        return OpenCodeSession(
            id=data["id"],
            project_id=data["projectID"],
            directory=data["directory"],
            title=data["title"],
            version=data["version"],
            time=data["time"],
            parent_id=data.get("parentID"),
        )
    
    async def get_session(self, session_id: str) -> OpenCodeSession:
        """Get session details."""
        data = await self._get(f"/session/{session_id}")
        
        return OpenCodeSession(
            id=data["id"],
            project_id=data["projectID"],
            directory=data["directory"],
            title=data["title"],
            version=data["version"],
            time=data["time"],
            parent_id=data.get("parentID"),
            share=data.get("share"),
            revert=data.get("revert"),
        )
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete session."""
        result = await self._delete(f"/session/{session_id}")
        return result
    
    async def abort_session(self, session_id: str) -> bool:
        """Abort running session."""
        result = await self._post(f"/session/{session_id}/abort")
        return result
    
    # Message Management
    
    async def list_messages(
        self,
        session_id: str,
    ) -> List[tuple[OpenCodeMessage, List[OpenCodePart]]]:
        """
        List all messages in session.
        
        Returns:
            List of (message, parts) tuples
        """
        data = await self._get(f"/session/{session_id}/message")
        
        results = []
        for item in data:
            msg_data = item["info"]
            parts_data = item["parts"]
            
            # Parse message
            message = OpenCodeMessage(
                id=msg_data["id"],
                session_id=msg_data["sessionID"],
                role=msg_data["role"],
                time=msg_data["time"],
                model_id=msg_data.get("modelID"),
                provider_id=msg_data.get("providerID"),
                mode=msg_data.get("mode"),
                cost=msg_data.get("cost"),
                tokens=msg_data.get("tokens"),
                error=msg_data.get("error"),
            )
            
            # Parse parts
            parts = []
            for part_data in parts_data:
                parts.append(OpenCodePart(
                    id=part_data["id"],
                    session_id=part_data["sessionID"],
                    message_id=part_data["messageID"],
                    type=part_data["type"],
                    text=part_data.get("text"),
                    tool=part_data.get("tool"),
                    call_id=part_data.get("callID"),
                    state=part_data.get("state"),
                    cost=part_data.get("cost"),
                    tokens=part_data.get("tokens"),
                ))
            
            results.append((message, parts))
        
        return results
    
    async def send_message(
        self,
        session_id: str,
        text: str,
        agent: Optional[str] = None,
        provider_id: Optional[str] = None,
        model_id: Optional[str] = None,
        message_id: Optional[str] = None,
    ) -> tuple[OpenCodeMessage, List[OpenCodePart]]:
        """
        Send message to session.
        
        Args:
            session_id: Session ID
            text: Message text
            agent: Agent name to use
            provider_id: Provider ID
            model_id: Model ID
            message_id: Optional message ID (for tracking)
            
        Returns:
            (message, parts) tuple with response
        """
        payload: Dict[str, Any] = {
            "parts": [
                {
                    "type": "text",
                    "text": text,
                }
            ]
        }
        
        if message_id:
            payload["messageID"] = message_id
        
        if agent:
            payload["agent"] = agent
        
        if provider_id and model_id:
            payload["model"] = {
                "providerID": provider_id,
                "modelID": model_id,
            }
        
        data = await self._post(
            f"/session/{session_id}/message",
            json_data=payload,
        )
        
        # Parse response
        msg_data = data["info"]
        parts_data = data["parts"]
        
        message = OpenCodeMessage(
            id=msg_data["id"],
            session_id=msg_data["sessionID"],
            role=msg_data["role"],
            time=msg_data["time"],
            model_id=msg_data.get("modelID"),
            provider_id=msg_data.get("providerID"),
            mode=msg_data.get("mode"),
            cost=msg_data.get("cost"),
            tokens=msg_data.get("tokens"),
            error=msg_data.get("error"),
        )
        
        parts = []
        for part_data in parts_data:
            parts.append(OpenCodePart(
                id=part_data["id"],
                session_id=part_data["sessionID"],
                message_id=part_data["messageID"],
                type=part_data["type"],
                text=part_data.get("text"),
                tool=part_data.get("tool"),
                call_id=part_data.get("callID"),
                state=part_data.get("state"),
                cost=part_data.get("cost"),
                tokens=part_data.get("tokens"),
            ))
        
        return message, parts
    
    # Event Stream
    
    async def event_stream(self) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Connect to event stream (Server-Sent Events).
        
        Yields:
            Event dictionaries
        """
        await self._ensure_client()
        
        url = f"{self._client.base_url}/event"
        
        async with aconnect_sse(
            self._client,
            "GET",
            url,
        ) as event_source:
            async for sse in event_source.aiter_sse():
                try:
                    event = json.loads(sse.data)
                    yield event
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse SSE event: {e}")
                    continue
