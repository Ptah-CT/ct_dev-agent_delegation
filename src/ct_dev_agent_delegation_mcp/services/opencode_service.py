"""OpenCode service for managing agent server instances."""

import asyncio
import httpx
from typing import Optional, Dict, List
from pathlib import Path
import logfire

from ..models.agent import Agent, AgentRole, AgentStatus
from .process_manager import ProcessManager, ProcessConfig, ProcessState


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
        
        # Initialize professional process manager
        self.process_manager = ProcessManager()
        
        # Initialize agents directory path
        # Assuming agents are stored in project root/agents directory
        self.agents_dir = Path(__file__).parent.parent.parent / "agents"
        if not self.agents_dir.exists():
            logfire.warning(f"Agents directory not found: {self.agents_dir}")
            # Create directory if it doesn't exist
            self.agents_dir.mkdir(parents=True, exist_ok=True)
    
    async def initialize(self):
        """Initialize the OpenCode service and process manager."""
        await self.process_manager.start()
        logfire.info("OpenCode service initialized with process manager")
    
    async def shutdown(self):
        """Shutdown the OpenCode service and all managed processes."""
        await self.process_manager.stop()
        logfire.info("OpenCode service shutdown complete")
        
    
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
        """Start OpenCode server for agent using professional process management.
        
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
            
            # Storage for port detection
            port_container = {"port": None}
            
            def on_output_callback(line: str):
                """Callback to capture port from OpenCode output."""
                if "listening on" in line and "http://" in line:
                    import re
                    match = re.search(r'http://[^:]+:(\d+)', line)
                    if match:
                        port_container["port"] = int(match.group(1))
                        logfire.info(
                            f"OpenCode chose port {port_container['port']} for agent {agent.agent_id}"
                        )
            
            # Configure professional process management WITH callback
            # CRITICAL: Callback must be in config to avoid race condition
            process_config = ProcessConfig(
                auto_restart=True,
                max_restart_attempts=3,
                restart_delay_base=2.0,
                restart_delay_max=30.0,
                startup_timeout=30.0,
                shutdown_timeout=10.0,
                capture_output=True,
                max_memory_mb=1024.0,  # 1GB limit per agent
                max_cpu_percent=80.0,   # 80% CPU limit
                on_output=on_output_callback  # Set callback BEFORE process starts
            )
            
            # Create managed process through ProcessManager
            managed_process = await self.process_manager.create_process(
                process_id=agent.agent_id,
                command=cmd,
                config=process_config
            )
            
            # Wait for port detection
            max_wait = 5  # seconds
            start_time = asyncio.get_event_loop().time()
            
            while port_container["port"] is None and (asyncio.get_event_loop().time() - start_time) < max_wait:
                if managed_process.state == ProcessState.FAILED:
                    raise RuntimeError("Server process failed to start")
                await asyncio.sleep(0.1)
            
            if port_container["port"] is None:
                raise RuntimeError("Could not determine OpenCode port from output")
            
            # Update agent details
            agent.pid = managed_process.pid
            agent.port = port_container["port"]
            # Use /config as health check (no /health endpoint)
            agent.health_check_url = f"http://localhost:{agent.port}/config"
            agent.status = AgentStatus.STARTING
            
            # Wait for health check
            if await self._wait_for_health(agent, timeout=8):
                agent.status = AgentStatus.IDLE
                logfire.info(f"OpenCode server started for agent {agent.agent_id}", port=agent.port)
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
        """Stop OpenCode server for agent using professional process management.
        
        Args:
            agent: Agent instance
            
        Returns:
            True if stopped successfully
        """
        if not agent.agent_id:
            return True
        
        try:
            # Use ProcessManager for graceful shutdown
            success = await self.process_manager.stop_process(
                process_id=agent.agent_id,
                timeout=agent.status == AgentStatus.ERROR and 2.0 or None
            )
            
            if success:
                logfire.info(f"Agent {agent.agent_id} stopped", pid=agent.pid)
            else:
                logfire.warning(f"Agent {agent.agent_id} stop had issues")
            
            return success
            
        except Exception as e:
            logfire.error(f"Failed to stop agent {agent.agent_id}", error=str(e))
            return False
    
    async def check_health(self, agent: Agent) -> bool:
        """Check if agent is healthy using ProcessManager metrics.
        
        Args:
            agent: Agent instance
            
        Returns:
            True if healthy
        """
        # First check process state through ProcessManager
        managed_process = self.process_manager.get_process(agent.agent_id)
        if not managed_process:
            return False
        
        if managed_process.state not in [ProcessState.RUNNING, ProcessState.STARTING]:
            return False
        
        # Then check HTTP health endpoint
        if not agent.health_check_url:
            return managed_process.state == ProcessState.RUNNING
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    agent.health_check_url,
                    timeout=2.0
                )
                return response.status_code == 200
        except Exception:
            return False

    async def get_agent_metrics(self, agent: Agent) -> Optional[Dict]:
        """Get resource metrics for an agent.
        
        Args:
            agent: Agent instance
            
        Returns:
            Dict with metrics or None if not available
        """
        metrics = self.process_manager.get_process_metrics(agent.agent_id)
        if not metrics:
            return None
        
        return {
            "cpu_percent": metrics.cpu_percent,
            "memory_mb": metrics.memory_mb,
            "memory_percent": metrics.memory_percent,
            "num_threads": metrics.num_threads,
            "open_files": metrics.open_files,
            "connections": metrics.connections,
            "uptime_seconds": metrics.uptime_seconds,
            "restart_count": metrics.restart_count
        }
    
    async def get_agent_output(
        self, 
        agent: Agent, 
        lines: int = 100,
        include_stderr: bool = True
    ) -> Dict[str, List[str]]:
        """Get recent output from an agent's process.
        
        Args:
            agent: Agent instance
            lines: Number of lines to return
            include_stderr: Include stderr output
            
        Returns:
            Dict with 'stdout' and optionally 'stderr' lists
        """
        return await self.process_manager.get_process_output(
            agent.agent_id,
            lines=lines,
            include_stderr=include_stderr
        )
    
    async def restart_agent(self, agent: Agent) -> bool:
        """Restart an agent with exponential backoff.
        
        Args:
            agent: Agent instance
            
        Returns:
            True if restarted successfully
        """
        agent.status = AgentStatus.STARTING
        
        success = await self.process_manager.restart_process(agent.agent_id)
        
        if success:
            agent.status = AgentStatus.IDLE
            logfire.info(f"Agent {agent.agent_id} restarted successfully")
        else:
            agent.status = AgentStatus.ERROR
            logfire.error(f"Agent {agent.agent_id} restart failed")
        
        return success
    
    def get_all_process_states(self) -> Dict[str, Dict]:
        """Get state summary for all managed processes.
        
        Returns:
            Dict mapping agent_id to process state info
        """
        result = {}
        for process in self.process_manager.get_all_processes():
            result[process.process_id] = {
                "state": process.state.value,
                "pid": process.pid,
                "uptime_seconds": process.metrics.uptime_seconds,
                "restart_count": process.metrics.restart_count,
                "cpu_percent": process.metrics.cpu_percent,
                "memory_mb": process.metrics.memory_mb
            }
        return result
    
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
