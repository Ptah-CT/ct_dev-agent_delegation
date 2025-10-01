"""OpenCode service for managing agent server instances."""

import asyncio
import subprocess
import httpx
import psutil
from typing import Optional, Dict, List
from pathlib import Path
import logfire

from ..models.agent import Agent, AgentRole, AgentStatus


class OpenCodeService:
    """Manages OpenCode server instances for agents."""
    
    def __init__(self, max_agents: int = 5):
        """Initialize OpenCode service.
        
        NOTE: Port allocation is now handled by OpenCode itself.
        Each agent server chooses its own available port dynamically.
        
        Args:
            max_agents: Maximum concurrent agents
        """
        self.max_agents = max_agents
        self._available_agents_cache: Optional[List[Dict]] = None
        self._available_models_cache: Optional[List[str]] = None
        
        # Initialize agents directory path
        # Assuming agents are stored in project root/agents directory
        self.agents_dir = Path(__file__).parent.parent.parent / "agents"
        if not self.agents_dir.exists():
            logfire.warning(f"Agents directory not found: {self.agents_dir}")
            # Create directory if it doesn't exist
            self.agents_dir.mkdir(parents=True, exist_ok=True)
        
    
    def _get_agent_file(self, role: AgentRole) -> Path:
        """Get agent configuration file path.
        
        Args:
            role: Agent role enum
            
        Returns:
            Path to agent markdown file
        """
        # Convert enum to filename (e.g., backend_specialist -> backend-specialist.md)
        filename = role.value.replace("_", "-") + ".md"
        agent_file = self.agents_dir / filename
        
        if not agent_file.exists():
            raise FileNotFoundError(f"Agent file not found: {agent_file}")
        
        return agent_file
    
    async def start_agent(self, agent: Agent) -> Agent:
        """Start OpenCode server for agent.
        
        NOTE: OpenCode 0.13.5+ uses session-based architecture.
        Server starts WITHOUT agent specification. Agent selection
        happens per-message via POST /session/{id}/message.
        
        OpenCode automatically selects an available port. We parse
        the port from its startup output.
        
        Args:
            agent: Agent instance
            
        Returns:
            Updated agent with server details
        """
        try:
            # Start generic OpenCode server (NO --port, NO --custom-instructions)
            # OpenCode will choose its own available port
            cmd = ["opencode", "serve"]
            
            logfire.info(
                f"Starting OpenCode server for agent {agent.agent_id}",
                role=agent.role.value,
                command=" ".join(cmd)
            )
            
            # Capture stdout to read the port OpenCode chooses
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True,
                text=True,
                bufsize=1  # Line buffered
            )
            
            # Read port from output
            # OpenCode outputs: "opencode server listening on http://127.0.0.1:XXXX"
            port = None
            max_wait = 5  # seconds
            start_time = asyncio.get_event_loop().time()
            
            while port is None and (asyncio.get_event_loop().time() - start_time) < max_wait:
                # Check if process died
                if process.poll() is not None:
                    stderr_output = process.stderr.read() if process.stderr else ""
                    raise RuntimeError(
                        f"Server process died immediately: {process.returncode}\n"
                        f"stderr: {stderr_output}"
                    )
                
                # Try to read a line from stdout
                try:
                    line = process.stdout.readline()
                    if not line:
                        await asyncio.sleep(0.1)
                        continue
                    
                    logfire.debug(f"OpenCode output: {line.strip()}")
                    
                    # Parse port from line like "opencode server listening on http://127.0.0.1:8000"
                    if "listening on" in line and "http://" in line:
                        import re
                        match = re.search(r'http://[^:]+:(\d+)', line)
                        if match:
                            port = int(match.group(1))
                            logfire.info(f"OpenCode chose port {port} for agent {agent.agent_id}")
                            break
                except Exception as e:
                    logfire.debug(f"Error reading OpenCode output: {e}")
                    await asyncio.sleep(0.1)
            
            if port is None:
                raise RuntimeError("Could not determine OpenCode port from output")
            
            # Update agent details
            agent.pid = process.pid
            agent.port = port
            # Use /config as health check (no /health endpoint)
            agent.health_check_url = f"http://localhost:{port}/config"
            agent.status = AgentStatus.STARTING
            
            # Wait for health check
            if await self._wait_for_health(agent, timeout=8):
                agent.status = AgentStatus.IDLE
                logfire.info(f"OpenCode server started for agent {agent.agent_id}", port=port)
            else:
                agent.status = AgentStatus.ERROR
                logfire.error(f"Agent {agent.agent_id} health check failed")
            
            return agent
            
        except Exception as e:
            logfire.error(f"Failed to start agent {agent.agent_id}", error=str(e))
            agent.status = AgentStatus.ERROR
            raise
    
    async def _wait_for_health(self, agent: Agent, timeout: int = 10) -> bool:
        """Wait for agent to become healthy.
        
        Args:
            agent: Agent instance
            timeout: Max wait time in seconds
            
        Returns:
            True if healthy, False otherwise
        """
        if not agent.health_check_url:
            return False
        
        async with httpx.AsyncClient() as client:
            for _ in range(timeout):
                try:
                    response = await client.get(
                        agent.health_check_url,
                        timeout=1.0
                    )
                    if response.status_code == 200:
                        return True
                except (httpx.RequestError, httpx.TimeoutException):
                    pass
                await asyncio.sleep(1)
        
        return False
    
    async def stop_agent(self, agent: Agent) -> bool:
        """Stop OpenCode server for agent.
        
        Args:
            agent: Agent instance
            
        Returns:
            True if stopped successfully
        """
        if not agent.pid:
            return True
        
        try:
            process = psutil.Process(agent.pid)
            
            # Terminate gracefully
            process.terminate()
            
            # Wait up to 5 seconds
            try:
                process.wait(timeout=5)
            except psutil.TimeoutExpired:
                # Force kill if still running
                process.kill()
                process.wait(timeout=2)
            
            logfire.info(f"Agent {agent.agent_id} stopped", pid=agent.pid)
            return True
            
        except psutil.NoSuchProcess:
            # Already stopped
            return True
        except Exception as e:
            logfire.error(f"Failed to stop agent {agent.agent_id}", error=str(e))
            return False
    
    async def check_health(self, agent: Agent) -> bool:
        """Check if agent is healthy.
        
        Args:
            agent: Agent instance
            
        Returns:
            True if healthy
        """
        if not agent.health_check_url:
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    agent.health_check_url,
                    timeout=2.0
                )
                return response.status_code == 200
        except Exception:
            return False
    
    async def send_request(
        self,
        agent: Agent,
        endpoint: str,
        data: Dict
    ) -> Dict:
        """Send request to agent server.
        
        Args:
            agent: Agent instance
            endpoint: API endpoint path
            data: Request payload
            
        Returns:
            Response data
        """
        if not agent.port:
            raise RuntimeError(f"Agent {agent.agent_id} has no port assigned")
        
        url = f"http://localhost:{agent.port}{endpoint}"
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=data)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logfire.error(
                f"Request to agent {agent.agent_id} failed",
                url=url,
                error=str(e)
            )
            raise
