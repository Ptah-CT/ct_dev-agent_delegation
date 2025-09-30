"""Agent manager service."""

import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timezone
import uuid
import logfire

from ..models.agent import Agent, AgentRole, AgentStatus
from .opencode_service import OpenCodeService


class AgentManager:
    """Manages agent lifecycle and pool."""
    
    def __init__(self, opencode_service: OpenCodeService):
        """Initialize agent manager.
        
        Args:
            opencode_service: OpenCode service instance
        """
        self.opencode_service = opencode_service
        self.agents: Dict[str, Agent] = {}
        self._lock = asyncio.Lock()
        self._health_check_task: Optional[asyncio.Task] = None
        
    async def start(self):
        """Start agent manager and health monitoring."""
        logfire.info("Starting agent manager")
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        
    async def stop(self):
        """Stop agent manager and all agents."""
        logfire.info("Stopping agent manager")
        
        # Cancel health checks
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        
        # Stop all agents
        for agent_id in list(self.agents.keys()):
            await self.remove_agent(agent_id)
    
    async def _health_check_loop(self):
        """Background task to check agent health."""
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                await self._check_all_agents()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logfire.error("Health check loop error", error=str(e))
    
    async def _check_all_agents(self):
        """Check health of all agents."""
        async with self._lock:
            for agent in list(self.agents.values()):
                if agent.status in [AgentStatus.IDLE, AgentStatus.BUSY]:
                    is_healthy = await self.opencode_service.check_health(agent)
                    
                    if not is_healthy:
                        logfire.warning(f"Agent {agent.agent_id} unhealthy")
                        agent.status = AgentStatus.ERROR
                    
                    agent.last_health_check = datetime.now(timezone.utc).isoformat()
    
    async def create_agent(self, role: AgentRole) -> Agent:
        """Create and start a new agent.
        
        Args:
            role: Agent role
            
        Returns:
            Created agent instance
        """
        async with self._lock:
            agent_id = str(uuid.uuid4())
            
            agent = Agent(
                agent_id=agent_id,
                role=role,
                status=AgentStatus.STARTING,
                created_at=datetime.now(timezone.utc).isoformat()
            )
            
            logfire.info(f"Creating agent {agent_id}", role=role.value)
            
            try:
                # Start OpenCode server
                agent = await self.opencode_service.start_agent(agent)
                
                # Add to pool
                self.agents[agent_id] = agent
                
                return agent
                
            except Exception as e:
                logfire.error(f"Failed to create agent {agent_id}", error=str(e))
                raise
    
    async def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get agent by ID.
        
        Args:
            agent_id: Agent UUID
            
        Returns:
            Agent instance or None
        """
        return self.agents.get(agent_id)
    
    async def get_idle_agent(self, role: AgentRole) -> Optional[Agent]:
        """Get an idle agent with the specified role.
        
        Args:
            role: Required agent role
            
        Returns:
            Idle agent or None
        """
        async with self._lock:
            for agent in self.agents.values():
                if agent.role == role and agent.status == AgentStatus.IDLE:
                    return agent
        return None
    
    async def get_or_create_agent(self, role: AgentRole) -> Agent:
        """Get an idle agent or create a new one.
        
        Args:
            role: Required agent role
            
        Returns:
            Agent instance
        """
        # Try to get idle agent
        agent = await self.get_idle_agent(role)
        if agent:
            return agent
        
        # Create new agent
        return await self.create_agent(role)
    
    async def mark_busy(self, agent_id: str, delegation_id: str):
        """Mark agent as busy.
        
        Args:
            agent_id: Agent UUID
            delegation_id: Delegation UUID
        """
        agent = self.agents.get(agent_id)
        if agent:
            agent.status = AgentStatus.BUSY
            agent.current_delegation_id = delegation_id
    
    async def mark_idle(self, agent_id: str):
        """Mark agent as idle.
        
        Args:
            agent_id: Agent UUID
        """
        agent = self.agents.get(agent_id)
        if agent:
            agent.status = AgentStatus.IDLE
            agent.current_delegation_id = None
    
    async def remove_agent(self, agent_id: str) -> bool:
        """Remove and stop an agent.
        
        Args:
            agent_id: Agent UUID
            
        Returns:
            True if removed successfully
        """
        async with self._lock:
            agent = self.agents.get(agent_id)
            if not agent:
                return False
            
            try:
                await self.opencode_service.stop_agent(agent)
                del self.agents[agent_id]
                logfire.info(f"Agent {agent_id} removed")
                return True
            except Exception as e:
                logfire.error(f"Failed to remove agent {agent_id}", error=str(e))
                return False
    
    async def list_agents(self) -> List[Agent]:
        """List all agents.
        
        Returns:
            List of agent instances
        """
        return list(self.agents.values())
    
    async def get_agent_count(self) -> int:
        """Get total agent count.
        
        Returns:
            Number of agents
        """
        return len(self.agents)
    
    async def get_agent_count_by_status(self) -> Dict[AgentStatus, int]:
        """Get agent count by status.
        
        Returns:
            Dict mapping status to count
        """
        counts = {status: 0 for status in AgentStatus}
        for agent in self.agents.values():
            counts[agent.status] += 1
        return counts
