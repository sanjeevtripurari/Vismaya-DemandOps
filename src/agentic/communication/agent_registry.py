"""
Agent Registry and Discovery System
Manages agent registration, capability discovery, health monitoring, and load balancing
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import weakref
from collections import defaultdict

from ..core.interfaces import IAgentCore
from ..core.models import (
    AgentConfiguration, AgentCapability, AgentState, AgentStatus,
    SystemEvent, AgentMetrics, SystemHealth
)


@dataclass
class AgentRegistration:
    """Registration information for an agent"""
    agent_id: str
    agent_type: str
    capabilities: List[AgentCapability]
    configuration: AgentConfiguration
    registered_at: datetime = field(default_factory=datetime.now)
    last_heartbeat: datetime = field(default_factory=datetime.now)
    health_status: str = "healthy"
    load_score: float = 0.0  # 0.0 = no load, 1.0 = fully loaded
    instance_count: int = 1
    failover_agents: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CapabilityIndex:
    """Index for capability-based agent discovery"""
    capability_name: str
    agents: List[str] = field(default_factory=list)
    load_balancing_strategy: str = "round_robin"  # round_robin, least_loaded, random
    current_index: int = 0


class AgentRegistry:
    """
    Agent registry and discovery system with health monitoring and load balancing
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Registry storage
        self.agents: Dict[str, weakref.ReferenceType] = {}  # agent_id -> weak reference to agent
        self.registrations: Dict[str, AgentRegistration] = {}  # agent_id -> registration info
        self.capability_index: Dict[str, CapabilityIndex] = {}  # capability -> index
        self.type_index: Dict[str, List[str]] = defaultdict(list)  # agent_type -> agent_ids
        
        # Health monitoring
        self.health_check_interval = config.get("health_check_interval", 30)  # seconds
        self.unhealthy_threshold = config.get("unhealthy_threshold", 3)  # failed checks
        self.health_failures: Dict[str, int] = defaultdict(int)
        
        # Load balancing
        self.load_update_interval = config.get("load_update_interval", 10)  # seconds
        self.max_load_threshold = config.get("max_load_threshold", 0.8)
        
        # Monitoring tasks
        self.health_monitor_task: Optional[asyncio.Task] = None
        self.load_monitor_task: Optional[asyncio.Task] = None
        self.registry_running = False
        
        # Statistics
        self.registration_count = 0
        self.discovery_requests = 0
        self.health_checks_performed = 0
        self.load_balancing_decisions = 0
    
    async def start_registry(self) -> bool:
        """Start the agent registry with monitoring tasks"""
        try:
            self.registry_running = True
            
            # Start health monitoring
            self.health_monitor_task = asyncio.create_task(self._health_monitoring_loop())
            
            # Start load monitoring
            self.load_monitor_task = asyncio.create_task(self._load_monitoring_loop())
            
            self.logger.info("Agent registry started with monitoring")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start agent registry: {e}")
            return False
    
    async def stop_registry(self) -> bool:
        """Stop the agent registry and monitoring tasks"""
        try:
            self.registry_running = False
            
            # Cancel monitoring tasks
            if self.health_monitor_task:
                self.health_monitor_task.cancel()
                try:
                    await self.health_monitor_task
                except asyncio.CancelledError:
                    pass
            
            if self.load_monitor_task:
                self.load_monitor_task.cancel()
                try:
                    await self.load_monitor_task
                except asyncio.CancelledError:
                    pass
            
            self.logger.info("Agent registry stopped")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping agent registry: {e}")
            return False
    
    async def register_agent(self, agent: IAgentCore) -> bool:
        """Register agent with capability discovery and health monitoring"""
        try:
            agent_id = agent.agent_id
            
            # Check if agent already registered
            if agent_id in self.registrations:
                self.logger.warning(f"Agent {agent_id} already registered, updating registration")
                return await self.update_agent_registration(agent)
            
            # Perform initial health check
            if not await agent.health_check():
                self.logger.error(f"Agent {agent_id} failed initial health check")
                return False
            
            # Create registration
            registration = AgentRegistration(
                agent_id=agent_id,
                agent_type=getattr(agent, 'agent_type', 'unknown'),
                capabilities=agent.capabilities,
                configuration=getattr(agent, 'configuration', AgentConfiguration(
                    agent_id=agent_id,
                    agent_type=getattr(agent, 'agent_type', 'unknown'),
                    capabilities=agent.capabilities
                ))
            )
            
            # Store agent reference and registration
            self.agents[agent_id] = weakref.ref(agent, self._agent_cleanup_callback(agent_id))
            self.registrations[agent_id] = registration
            
            # Update indices
            self._update_capability_index(agent_id, agent.capabilities)
            self._update_type_index(agent_id, registration.agent_type)
            
            # Initialize health tracking
            self.health_failures[agent_id] = 0
            
            self.registration_count += 1
            self.logger.info(f"Agent {agent_id} registered successfully with {len(agent.capabilities)} capabilities")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error registering agent {agent.agent_id}: {e}")
            return False
    
    async def unregister_agent(self, agent_id: str) -> bool:
        """Unregister agent and clean up indices"""
        try:
            if agent_id not in self.registrations:
                self.logger.warning(f"Agent {agent_id} not found for unregistration")
                return False
            
            registration = self.registrations[agent_id]
            
            # Remove from indices
            self._remove_from_capability_index(agent_id, registration.capabilities)
            self._remove_from_type_index(agent_id, registration.agent_type)
            
            # Clean up
            self.agents.pop(agent_id, None)
            self.registrations.pop(agent_id, None)
            self.health_failures.pop(agent_id, None)
            
            self.logger.info(f"Agent {agent_id} unregistered successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error unregistering agent {agent_id}: {e}")
            return False
    
    async def discover_agents_by_capability(self, capability_name: str, 
                                          load_balance: bool = True) -> List[str]:
        """Discover agents by capability with optional load balancing"""
        try:
            self.discovery_requests += 1
            
            if capability_name not in self.capability_index:
                return []
            
            capability_index = self.capability_index[capability_name]
            available_agents = []
            
            # Filter healthy agents
            for agent_id in capability_index.agents:
                if self._is_agent_healthy(agent_id):
                    available_agents.append(agent_id)
            
            if not available_agents:
                return []
            
            if not load_balance:
                return available_agents
            
            # Apply load balancing
            return self._apply_load_balancing(available_agents, capability_index.load_balancing_strategy)
            
        except Exception as e:
            self.logger.error(f"Error discovering agents by capability {capability_name}: {e}")
            return []
    
    async def discover_agents_by_type(self, agent_type: str) -> List[str]:
        """Discover agents by type"""
        try:
            self.discovery_requests += 1
            
            agent_ids = self.type_index.get(agent_type, [])
            healthy_agents = [agent_id for agent_id in agent_ids if self._is_agent_healthy(agent_id)]
            
            return healthy_agents
            
        except Exception as e:
            self.logger.error(f"Error discovering agents by type {agent_type}: {e}")
            return []
    
    async def get_best_agent_for_capability(self, capability_name: str, 
                                          context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Get the best agent for a specific capability based on load and context"""
        try:
            available_agents = await self.discover_agents_by_capability(capability_name, load_balance=False)
            
            if not available_agents:
                return None
            
            if len(available_agents) == 1:
                return available_agents[0]
            
            # Score agents based on load, health, and context
            agent_scores = {}
            
            for agent_id in available_agents:
                score = self._calculate_agent_score(agent_id, context)
                agent_scores[agent_id] = score
            
            # Return agent with highest score (lower is better)
            best_agent = min(agent_scores.items(), key=lambda x: x[1])[0]
            self.load_balancing_decisions += 1
            
            return best_agent
            
        except Exception as e:
            self.logger.error(f"Error getting best agent for capability {capability_name}: {e}")
            return None
    
    async def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed status of specific agent"""
        try:
            if agent_id not in self.registrations:
                return None
            
            registration = self.registrations[agent_id]
            agent_ref = self.agents.get(agent_id)
            
            status = {
                "agent_id": agent_id,
                "agent_type": registration.agent_type,
                "registered_at": registration.registered_at.isoformat(),
                "last_heartbeat": registration.last_heartbeat.isoformat(),
                "health_status": registration.health_status,
                "load_score": registration.load_score,
                "capabilities": [cap.name for cap in registration.capabilities],
                "health_failures": self.health_failures.get(agent_id, 0),
                "is_available": self._is_agent_healthy(agent_id)
            }
            
            # Get live agent state if available
            if agent_ref and agent_ref():
                try:
                    agent = agent_ref()
                    agent_state = await agent.get_state()
                    status.update({
                        "current_status": agent_state.status.value,
                        "current_task": agent_state.current_task,
                        "performance_metrics": agent_state.performance_metrics,
                        "error_count": agent_state.error_count
                    })
                except Exception as e:
                    self.logger.warning(f"Could not get live state for agent {agent_id}: {e}")
            
            return status
            
        except Exception as e:
            self.logger.error(f"Error getting agent status for {agent_id}: {e}")
            return None
    
    async def get_system_health(self) -> SystemHealth:
        """Get overall system health status"""
        try:
            agent_statuses = {}
            unhealthy_agents = []
            total_load = 0.0
            
            for agent_id, registration in self.registrations.items():
                is_healthy = self._is_agent_healthy(agent_id)
                status = "healthy" if is_healthy else "unhealthy"
                agent_statuses[agent_id] = status
                
                if not is_healthy:
                    unhealthy_agents.append(agent_id)
                
                total_load += registration.load_score
            
            # Calculate overall status
            total_agents = len(self.registrations)
            healthy_agents = total_agents - len(unhealthy_agents)
            health_percentage = (healthy_agents / max(total_agents, 1)) * 100
            
            if health_percentage >= 90:
                overall_status = "healthy"
            elif health_percentage >= 70:
                overall_status = "degraded"
            elif health_percentage >= 50:
                overall_status = "critical"
            else:
                overall_status = "offline"
            
            # System metrics
            avg_load = total_load / max(total_agents, 1)
            system_metrics = {
                "total_agents": total_agents,
                "healthy_agents": healthy_agents,
                "unhealthy_agents": len(unhealthy_agents),
                "health_percentage": health_percentage,
                "average_load": avg_load,
                "discovery_requests": self.discovery_requests,
                "health_checks_performed": self.health_checks_performed
            }
            
            return SystemHealth(
                overall_status=overall_status,
                agent_statuses=agent_statuses,
                system_metrics=system_metrics,
                active_alerts=unhealthy_agents
            )
            
        except Exception as e:
            self.logger.error(f"Error getting system health: {e}")
            return SystemHealth(overall_status="error")
    
    async def update_agent_load(self, agent_id: str, load_score: float) -> bool:
        """Update agent load score for load balancing"""
        try:
            if agent_id in self.registrations:
                self.registrations[agent_id].load_score = max(0.0, min(1.0, load_score))
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error updating agent load for {agent_id}: {e}")
            return False
    
    async def set_agent_failover(self, agent_id: str, failover_agents: List[str]) -> bool:
        """Set failover agents for high availability"""
        try:
            if agent_id in self.registrations:
                self.registrations[agent_id].failover_agents = failover_agents
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error setting failover agents for {agent_id}: {e}")
            return False
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """Get registry statistics"""
        capability_count = len(self.capability_index)
        type_count = len(self.type_index)
        
        return {
            "total_agents": len(self.registrations),
            "healthy_agents": sum(1 for agent_id in self.registrations if self._is_agent_healthy(agent_id)),
            "capabilities_indexed": capability_count,
            "agent_types": type_count,
            "registration_count": self.registration_count,
            "discovery_requests": self.discovery_requests,
            "health_checks_performed": self.health_checks_performed,
            "load_balancing_decisions": self.load_balancing_decisions
        }
    
    # Private methods
    
    def _update_capability_index(self, agent_id: str, capabilities: List[AgentCapability]) -> None:
        """Update capability index with agent capabilities"""
        for capability in capabilities:
            if capability.name not in self.capability_index:
                self.capability_index[capability.name] = CapabilityIndex(capability_name=capability.name)
            
            if agent_id not in self.capability_index[capability.name].agents:
                self.capability_index[capability.name].agents.append(agent_id)
    
    def _remove_from_capability_index(self, agent_id: str, capabilities: List[AgentCapability]) -> None:
        """Remove agent from capability index"""
        for capability in capabilities:
            if capability.name in self.capability_index:
                capability_index = self.capability_index[capability.name]
                if agent_id in capability_index.agents:
                    capability_index.agents.remove(agent_id)
                
                # Clean up empty indices
                if not capability_index.agents:
                    del self.capability_index[capability.name]
    
    def _update_type_index(self, agent_id: str, agent_type: str) -> None:
        """Update type index with agent"""
        if agent_id not in self.type_index[agent_type]:
            self.type_index[agent_type].append(agent_id)
    
    def _remove_from_type_index(self, agent_id: str, agent_type: str) -> None:
        """Remove agent from type index"""
        if agent_type in self.type_index:
            if agent_id in self.type_index[agent_type]:
                self.type_index[agent_type].remove(agent_id)
            
            # Clean up empty indices
            if not self.type_index[agent_type]:
                del self.type_index[agent_type]
    
    def _is_agent_healthy(self, agent_id: str) -> bool:
        """Check if agent is healthy"""
        if agent_id not in self.registrations:
            return False
        
        registration = self.registrations[agent_id]
        health_failures = self.health_failures.get(agent_id, 0)
        
        # Check health status and failure count
        if registration.health_status != "healthy" or health_failures >= self.unhealthy_threshold:
            return False
        
        # Check if agent reference is still valid
        agent_ref = self.agents.get(agent_id)
        if not agent_ref or not agent_ref():
            return False
        
        # Check last heartbeat
        time_since_heartbeat = datetime.now() - registration.last_heartbeat
        if time_since_heartbeat > timedelta(seconds=self.health_check_interval * 2):
            return False
        
        return True
    
    def _apply_load_balancing(self, agents: List[str], strategy: str) -> List[str]:
        """Apply load balancing strategy to agent list"""
        if not agents:
            return []
        
        if strategy == "round_robin":
            # Simple round-robin selection
            return [agents[0]]  # Return first available for simplicity
        
        elif strategy == "least_loaded":
            # Sort by load score (ascending)
            agents_with_load = [(agent_id, self.registrations[agent_id].load_score) 
                              for agent_id in agents]
            agents_with_load.sort(key=lambda x: x[1])
            return [agents_with_load[0][0]]
        
        elif strategy == "random":
            import random
            return [random.choice(agents)]
        
        else:
            # Default to return all available agents
            return agents
    
    def _calculate_agent_score(self, agent_id: str, context: Optional[Dict[str, Any]]) -> float:
        """Calculate agent score for selection (lower is better)"""
        if agent_id not in self.registrations:
            return float('inf')
        
        registration = self.registrations[agent_id]
        score = 0.0
        
        # Load score (0.0 to 1.0, lower is better)
        score += registration.load_score * 100
        
        # Health failures penalty
        score += self.health_failures.get(agent_id, 0) * 10
        
        # Time since last heartbeat penalty
        time_since_heartbeat = datetime.now() - registration.last_heartbeat
        score += time_since_heartbeat.total_seconds() / 10
        
        # Context-based scoring (if provided)
        if context:
            # Example: prefer agents with specific metadata
            preferred_region = context.get("preferred_region")
            if preferred_region and registration.metadata.get("region") == preferred_region:
                score -= 50  # Bonus for preferred region
        
        return score
    
    def _agent_cleanup_callback(self, agent_id: str):
        """Callback for agent cleanup when weak reference is garbage collected"""
        def cleanup(ref):
            try:
                # Try to create task if event loop is running
                loop = asyncio.get_running_loop()
                loop.create_task(self.unregister_agent(agent_id))
            except RuntimeError:
                # No event loop running, cleanup synchronously
                if agent_id in self.registrations:
                    registration = self.registrations[agent_id]
                    self._remove_from_capability_index(agent_id, registration.capabilities)
                    self._remove_from_type_index(agent_id, registration.agent_type)
                    self.agents.pop(agent_id, None)
                    self.registrations.pop(agent_id, None)
                    self.health_failures.pop(agent_id, None)
        return cleanup
    
    async def _health_monitoring_loop(self) -> None:
        """Health monitoring loop for all registered agents"""
        while self.registry_running:
            try:
                for agent_id, agent_ref in list(self.agents.items()):
                    try:
                        agent = agent_ref()
                        if not agent:
                            # Agent was garbage collected
                            await self.unregister_agent(agent_id)
                            continue
                        
                        # Perform health check
                        is_healthy = await agent.health_check()
                        self.health_checks_performed += 1
                        
                        if is_healthy:
                            self.health_failures[agent_id] = 0
                            self.registrations[agent_id].health_status = "healthy"
                            self.registrations[agent_id].last_heartbeat = datetime.now()
                        else:
                            self.health_failures[agent_id] += 1
                            if self.health_failures[agent_id] >= self.unhealthy_threshold:
                                self.registrations[agent_id].health_status = "unhealthy"
                        
                    except Exception as e:
                        self.logger.error(f"Health check failed for agent {agent_id}: {e}")
                        self.health_failures[agent_id] += 1
                
                # Wait before next health check cycle
                await asyncio.sleep(self.health_check_interval)
                
            except Exception as e:
                self.logger.error(f"Error in health monitoring loop: {e}")
                await asyncio.sleep(self.health_check_interval)
    
    async def _load_monitoring_loop(self) -> None:
        """Load monitoring loop for updating agent load scores"""
        while self.registry_running:
            try:
                for agent_id, agent_ref in list(self.agents.items()):
                    try:
                        agent = agent_ref()
                        if not agent:
                            continue
                        
                        # Get agent state for load calculation
                        agent_state = await agent.get_state()
                        
                        # Calculate load score based on various factors
                        load_score = self._calculate_load_score(agent_state)
                        
                        # Update load score
                        await self.update_agent_load(agent_id, load_score)
                        
                    except Exception as e:
                        self.logger.error(f"Load monitoring failed for agent {agent_id}: {e}")
                
                # Wait before next load update cycle
                await asyncio.sleep(self.load_update_interval)
                
            except Exception as e:
                self.logger.error(f"Error in load monitoring loop: {e}")
                await asyncio.sleep(self.load_update_interval)
    
    def _calculate_load_score(self, agent_state: AgentState) -> float:
        """Calculate load score based on agent state"""
        load_score = 0.0
        
        # CPU usage contribution (0.0 to 0.4)
        cpu_contribution = min(agent_state.cpu_usage_percent / 100.0, 1.0) * 0.4
        load_score += cpu_contribution
        
        # Memory usage contribution (0.0 to 0.3)
        memory_contribution = min(agent_state.memory_usage_mb / 1000.0, 1.0) * 0.3
        load_score += memory_contribution
        
        # Task status contribution (0.0 to 0.3)
        if agent_state.status == AgentStatus.BUSY:
            load_score += 0.3
        elif agent_state.status == AgentStatus.ERROR:
            load_score += 0.5  # Higher penalty for error state
        
        return min(load_score, 1.0)
    
    async def update_agent_registration(self, agent: IAgentCore) -> bool:
        """Update existing agent registration"""
        try:
            agent_id = agent.agent_id
            
            if agent_id not in self.registrations:
                return await self.register_agent(agent)
            
            # Update agent reference
            self.agents[agent_id] = weakref.ref(agent, self._agent_cleanup_callback(agent_id))
            
            # Update capabilities if changed
            old_capabilities = self.registrations[agent_id].capabilities
            new_capabilities = agent.capabilities
            
            if old_capabilities != new_capabilities:
                # Remove old capabilities
                self._remove_from_capability_index(agent_id, old_capabilities)
                # Add new capabilities
                self._update_capability_index(agent_id, new_capabilities)
                # Update registration
                self.registrations[agent_id].capabilities = new_capabilities
            
            # Reset health status
            self.health_failures[agent_id] = 0
            self.registrations[agent_id].health_status = "healthy"
            self.registrations[agent_id].last_heartbeat = datetime.now()
            
            self.logger.info(f"Agent {agent_id} registration updated")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating agent registration for {agent.agent_id}: {e}")
            return False