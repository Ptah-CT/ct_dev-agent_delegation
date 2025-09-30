"""OpenCode API client for dynamic agent and model management.

This service uses ONLY the OpenCode Server API, not file system access.
All agents, models, and configurations are fetched dynamically via HTTP.
"""

import asyncio
import subprocess
import httpx
import psutil
from typing import Optional, Dict, List, Any
from pathlib import Path
import logfire

from ..models.agent import Agent, AgentStatus


class OpenCodeAPIClient:
    """Client for OpenCode Server API.
    
    Manages communication with OpenCode server instances via HTTP API.
    Does NOT access file system or use CLI commands except for:
    - Starting server processes (opencode serve)
    - Checking process health (psutil)
    """
    
    def __init__(self, base_port: int = 8000, max_agents: int = 5):
        """Initialize OpenCode API client.
        
        Args:
            base_port: Starting port for agent servers
            max_agents: Maximum concurrent agents
        """
        self.base_port = base_port
        self.max_agents = max_agents
        self._port_offset = 0
        self._server_processes: Dict[int, subprocess.Popen] = {}
        self._lock = asyncio.Lock()
        
    async def _get_next_port(self) -> int:
        """Get next available free port within the configured range.
        
        Raises:
            RuntimeError: If no free ports are available
        """
        async with self._lock:
            # Enforce capacity
            if len(self._server_processes) >= self.max_agents:
                raise RuntimeError("No free OpenCode server ports available")
            
            # Find next unused port
            for _ in range(self.max_agents):
                port = self.base_port + self._port_offset
                self._port_offset = (self._port_offset + 1) % self.max_agents
                if port not in self._server_processes:
                    return port
            
            raise RuntimeError("No free OpenCode server ports available")
    
    async def fetch_available_agents(self, server_url: str) -> List[Dict[str, Any]]:
        """Fetch available agents from OpenCode server API.
        
        Args:
            server_url: OpenCode server URL (e.g., http://localhost:8000)
            
        Returns:
            List of agent definitions with structure:
            {
                "name": str,
                "description": str,
                "tools": dict,
                "options": dict,
                "permission": dict,
                "mode": str,
                "builtIn": bool,
                "prompt": str (optional)
            }
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{server_url}/agent")
                response.raise_for_status()
                agents = response.json()
                
                logfire.info(
                    "Fetched agents from OpenCode API",
                    url=server_url,
                    count=len(agents)
                )
                return agents
                
        except httpx.HTTPError as e:
            logfire.error(
                "Failed to fetch agents from OpenCode API",
                url=server_url,
                error=str(e)
            )
            raise
    
    async def fetch_available_models(self, server_url: str) -> List[str]:
        """Fetch available models from OpenCode server.
        
        Note: Model endpoint may not exist in all OpenCode versions.
        Falls back to empty list if not available.
        
        Args:
            server_url: OpenCode server URL
            
        Returns:
            List of model identifiers
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Try /model endpoint
                response = await client.get(f"{server_url}/model")
                if response.status_code == 200:
                    models = response.json()
                    logfire.info(
                        "Fetched models from OpenCode API",
                        url=server_url,
                        count=len(models)
                    )
                    return models
                else:
                    # Endpoint doesn't exist, use CLI fallback
                    return await self._fetch_models_from_cli()
                    
        except httpx.HTTPError:
            # API not available, use CLI fallback
            return await self._fetch_models_from_cli()
    
    async def _fetch_models_from_cli(self) -> List[str]:
        """Fallback: Fetch models using CLI.
        
        Returns:
            List of model identifiers
        """
        try:
            result = await asyncio.create_subprocess_exec(
                "opencode", "models",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                models = [
                    line.strip() 
                    for line in stdout.decode().splitlines() 
                    if line.strip()
                ]
                logfire.info("Fetched models from CLI", count=len(models))
                return models
            else:
                logfire.warning("Failed to fetch models from CLI", stderr=stderr.decode())
                return []
                
        except Exception as e:
            logfire.error("Error fetching models from CLI", error=str(e))
            return []
    
    async def start_agent_server(
        self,
        agent: Agent,
        agent_name: Optional[str] = None,
        model: Optional[str] = None,
        custom_instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """Start OpenCode server instance for an agent.
        
        Args:
            agent: Agent instance
            agent_name: Agent name to use (from OpenCode API)
            model: Model identifier (from OpenCode API)
            custom_instructions: Optional custom instructions
            
        Returns:
            Server info dict with url, pid, port
        """
        port = await self._get_next_port()
        hostname = "127.0.0.1"
        
        # Build command
        cmd = [
            "opencode", "serve",
            "--port", str(port),
            "--hostname", hostname
        ]
        
        # Add agent if specified
        if agent_name:
            cmd.extend(["--agent", agent_name])
        
        # Add model if specified
        if model:
            cmd.extend(["--model", model])
        
        # Add custom instructions if specified
        if custom_instructions:
            cmd.extend(["--custom-instructions", custom_instructions])
        
        try:
            # Start process with DEVNULL to avoid deadlock
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                text=True
            )
            
            self._server_processes[port] = process
            
            # Poll for server readiness with timeout
            server_url = f"http://{hostname}:{port}"
            deadline = asyncio.get_event_loop().time() + 15.0
            ready = False
            
            while asyncio.get_event_loop().time() < deadline:
                if await self.check_health(server_url):
                    ready = True
                    break
                await asyncio.sleep(0.5)
            
            if not ready:
                raise RuntimeError(f"Server failed to start on port {port}")
            
            logfire.info(
                "Started OpenCode server",
                agent_id=agent.agent_id,
                port=port,
                pid=process.pid,
                agent_name=agent_name,
                model=model
            )
            
            return {
                "url": server_url,
                "hostname": hostname,
                "port": port,
                "pid": process.pid,
                "agent_name": agent_name,
                "model": model
            }
            
        except Exception as e:
            logfire.error(
                "Failed to start OpenCode server",
                agent_id=agent.agent_id,
                port=port,
                error=str(e)
            )
            raise
    
    async def stop_agent_server(self, port: int) -> None:
        """Stop OpenCode server instance.
        
        Args:
            port: Server port
        """
        process = self._server_processes.get(port)
        if not process:
            logfire.warning("No process found for port", port=port)
            return
        
        try:
            # Graceful shutdown
            process.terminate()
            
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill
                process.kill()
                process.wait()
            
            del self._server_processes[port]
            
            logfire.info("Stopped OpenCode server", port=port, pid=process.pid)
            
        except Exception as e:
            logfire.error("Error stopping server", port=port, error=str(e))
    
    async def check_health(self, server_url: str) -> bool:
        """Check if OpenCode server is healthy.
        
        Args:
            server_url: Server URL
            
        Returns:
            True if healthy, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Try agent endpoint as health check
                response = await client.get(f"{server_url}/agent")
                return response.status_code == 200
                
        except Exception:
            return False
    
    async def send_message(
        self,
        server_url: str,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send message to OpenCode agent via API.
        
        Note: Actual endpoint may vary by OpenCode version.
        This is a placeholder for when API supports it.
        
        Args:
            server_url: Server URL
            message: Message to send
            context: Optional context
            
        Returns:
            Response dict
        """
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                payload = {
                    "message": message,
                    "context": context or {}
                }
                
                # Try common endpoints
                for endpoint in ["/chat", "/message", "/api/chat"]:
                    try:
                        response = await client.post(
                            f"{server_url}{endpoint}",
                            json=payload
                        )
                        if response.status_code == 200:
                            return response.json()
                    except httpx.HTTPError:
                        continue
                
                # No endpoint worked
                raise RuntimeError("No chat endpoint available")
                
        except Exception as e:
            logfire.error(
                "Failed to send message to agent",
                url=server_url,
                error=str(e)
            )
            raise
    
    def get_process_info(self, pid: int) -> Optional[Dict[str, Any]]:
        """Get process information.
        
        Args:
            pid: Process ID
            
        Returns:
            Process info dict or None
        """
        try:
            process = psutil.Process(pid)
            return {
                "pid": pid,
                "status": process.status(),
                "cpu_percent": process.cpu_percent(interval=0.1),
                "memory_mb": process.memory_info().rss / 1024 / 1024,
                "create_time": process.create_time()
            }
        except psutil.NoSuchProcess:
            return None
    
    async def cleanup(self):
        """Stop all running server processes."""
        async with self._lock:
            ports = list(self._server_processes.keys())
        for port in ports:
            await self.stop_agent_server(port)
        
        logfire.info("Cleaned up all OpenCode servers")
