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
    
    def __init__(self, base_port: int = 8000, max_agents: int = 5):
        """Initialize OpenCode service.
        
        Args:
            base_port: Starting port for agent servers
            max_agents: Maximum concurrent agents
        """
        self.base_port = base_port
        self.max_agents = max_agents
        self._port_offset = 0
        self._available_agents_cache: Optional[List[Dict]] = None
        self._available_models_cache: Optional[List[str]] = None
        
        # Initialize agents directory path
        # Assuming agents are stored in project root/agents directory
        self.agents_dir = Path(__file__).parent.parent.parent / "agents"
        if not self.agents_dir.exists():
            logfire.warning(f"Agents directory not found: {self.agents_dir}")
            # Create directory if it doesn't exist
            self.agents_dir.mkdir(parents=True, exist_ok=True)
        
    def _get_next_port(self) -> int:
        """Get next available port."""
        port = self.base_port + self._port_offset
        self._port_offset = (self._port_offset + 1) % self.max_agents
        return port
    
    def _get_agent_file(self, role: AgentRole) -> Path:
        """Get agent configuration file path.
        
        Args:
            role: Agent role (can be AgentRole enum or string value)
            
        Returns:
            Path to agent markdown file
        """
        # Convert enum to filename (e.g., backend_specialist -> backend-specialist.md)
        # Handle both enum and string values due to use_enum_values = True in Agent model
        role_str = role.value if isinstance(role, AgentRole) else role
        filename = role_str.replace("_", "-") + ".md"
        agent_file = self.agents_dir / filename
        
        if not agent_file.exists():
            raise FileNotFoundError(f"Agent file not found: {agent_file}")
        
        return agent_file
    
    async def start_agent(self, agent: Agent) -> Agent:
        """Start OpenCode server for agent.
        
        Args:
            agent: Agent instance
            
        Returns:
            Updated agent with server details
        """
        try:
            agent_file = self._get_agent_file(agent.role)
            port = self._get_next_port()
            
            # Start opencode serve with custom instructions
            cmd = [
                "opencode", "serve",
                "--port", str(port),
                "--custom-instructions", str(agent_file)
            ]
            
            logfire.info(
                f"Starting agent {agent.agent_id}",
                role=agent.role.value,
                port=port,
                command=" ".join(cmd)
            )
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            
            # Wait for startup (max 10 seconds)
            await asyncio.sleep(2)
            
            # Check if process is running
            if process.poll() is not None:
                raise RuntimeError(f"Agent process died immediately: {process.returncode}")
            
            # Update agent details
            agent.pid = process.pid
            agent.port = port
            agent.health_check_url = f"http://localhost:{port}/health"
            agent.status = AgentStatus.STARTING
            
            # Wait for health check
            if await self._wait_for_health(agent, timeout=8):
                agent.status = AgentStatus.IDLE
                logfire.info(f"Agent {agent.agent_id} started successfully", port=port)
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
