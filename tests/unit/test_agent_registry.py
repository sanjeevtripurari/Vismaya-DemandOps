"""
Unit tests for Agent Registry and Discovery System
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timedelta

from src.agentic.communication.agent_registry import AgentRegistry, AgentRegistration
from src.agentic.core.models import AgentCapability, AgentState, AgentStatus
from src.agentic.core.interfaces import IAgentCore


class MockAgent(IAgentCore):
    """Mock agent for testing"""
    
    def __init__(self, agent_id: str, agent_type: str = "test", capabilities: list = None):
        self._agent_id = agent_id
        self.agent_type = agent_type
        self._capabilities = capabilities or [
            AgentCapability(
                name=f"{agent_type}_capability",
                description=f"Test capability for {agent_type}",
                input_schema={"type": "object"},
                output_schema={"type": "object"}
            )
        ]
        self._healthy = True
        self._state = AgentState(
            agent_id=agent_id,
            status=AgentStatus.ACTIVE
        )
    
    @property
    def agent_id(self) -> str:
        return self._agent_id
    
    @property
    def capabilities(self) -> list:
        return self._capabilities
    
    async def initialize(self) -> bool:
        return True
    
    async def process_message(self, message):
        return message
    
    async def execute_action(self, action: str, parameters: dict) -> dict:
        return {"result": "success"}
    
    async def get_state(self):
        return self._state
    
    async def health_check(self) -> bool:
        return self._healthy
    
    async def shutdown(self) -> bool:
        return True
    
    def set_healthy(self, healthy: bool):
        self._healthy = healthy
        if not healthy:
            self._state.status = AgentStatus.ERROR
        else:
            self._state.status = AgentStatus.ACTIVE


@pytest.fixture
def registry_config():
    return {
        "health_check_interval": 1,  # Fast for testing
        "load_update_interval": 1,
        "unhealthy_threshold": 2
    }


@pytest.fixture
def agent_registry(registry_config):
    return AgentRegistry(registry_config)


@pytest.fixture
def mock_agents():
    return [
        MockAgent("agent1", "cost_management", [
            AgentCapability("cost_analysis", "Analyze costs", {}, {}),
            AgentCapability("budget_monitoring", "Monitor budgets", {}, {})
        ]),
        MockAgent("agent2", "resource_management", [
            AgentCapability("resource_monitoring", "Monitor resources", {}, {})
        ]),
        MockAgent("agent3", "cost_management", [
            AgentCapability("cost_analysis", "Analyze costs", {}, {})
        ])
    ]


class TestAgentRegistry:
    """Test cases for AgentRegistry"""
    
    @pytest.mark.asyncio
    async def test_register_agent(self, agent_registry, mock_agents):
        """Test agent registration"""
        agent = mock_agents[0]
        
        # Register agent
        result = await agent_registry.register_agent(agent)
        assert result is True
        
        # Check registration
        assert agent.agent_id in agent_registry.registrations
        registration = agent_registry.registrations[agent.agent_id]
        assert registration.agent_id == agent.agent_id
        assert registration.agent_type == agent.agent_type
        assert len(registration.capabilities) == 2
    
    @pytest.mark.asyncio
    async def test_unregister_agent(self, agent_registry, mock_agents):
        """Test agent unregistration"""
        agent = mock_agents[0]
        
        # Register then unregister
        await agent_registry.register_agent(agent)
        result = await agent_registry.unregister_agent(agent.agent_id)
        
        assert result is True
        assert agent.agent_id not in agent_registry.registrations
    
    @pytest.mark.asyncio
    async def test_discover_agents_by_capability(self, agent_registry, mock_agents):
        """Test capability-based agent discovery"""
        # Register multiple agents
        for agent in mock_agents:
            await agent_registry.register_agent(agent)
        
        # Discover agents with cost_analysis capability (with load balancing disabled)
        agents = await agent_registry.discover_agents_by_capability("cost_analysis", load_balance=False)
        assert len(agents) == 2  # agent1 and agent3
        assert "agent1" in agents and "agent3" in agents
    
    @pytest.mark.asyncio
    async def test_discover_agents_by_type(self, agent_registry, mock_agents):
        """Test type-based agent discovery"""
        # Register multiple agents
        for agent in mock_agents:
            await agent_registry.register_agent(agent)
        
        # Discover cost_management agents
        agents = await agent_registry.discover_agents_by_type("cost_management")
        assert len(agents) == 2  # agent1 and agent3
        assert "agent1" in agents
        assert "agent3" in agents
        
        # Discover resource_management agents
        agents = await agent_registry.discover_agents_by_type("resource_management")
        assert len(agents) == 1  # agent2
        assert "agent2" in agents
    
    @pytest.mark.asyncio
    async def test_get_best_agent_for_capability(self, agent_registry, mock_agents):
        """Test best agent selection"""
        # Register agents
        for agent in mock_agents:
            await agent_registry.register_agent(agent)
        
        # Get best agent for cost_analysis
        best_agent = await agent_registry.get_best_agent_for_capability("cost_analysis")
        assert best_agent in ["agent1", "agent3"]
    
    @pytest.mark.asyncio
    async def test_health_monitoring(self, agent_registry, mock_agents):
        """Test health monitoring functionality"""
        agent = mock_agents[0]
        await agent_registry.register_agent(agent)
        
        # Agent should be healthy initially
        status = await agent_registry.get_agent_status(agent.agent_id)
        assert status["is_available"] is True
        
        # Make agent unhealthy
        agent.set_healthy(False)
        
        # Simulate health check failures
        for _ in range(3):  # Exceed unhealthy_threshold
            agent_registry.health_failures[agent.agent_id] += 1
        
        # Agent should now be unhealthy
        assert not agent_registry._is_agent_healthy(agent.agent_id)
    
    @pytest.mark.asyncio
    async def test_load_balancing(self, agent_registry, mock_agents):
        """Test load balancing functionality"""
        # Register agents
        for agent in mock_agents:
            await agent_registry.register_agent(agent)
        
        # Set different load scores
        await agent_registry.update_agent_load("agent1", 0.8)
        await agent_registry.update_agent_load("agent3", 0.2)
        
        # Get agents with least_loaded strategy
        agents = agent_registry._apply_load_balancing(["agent1", "agent3"], "least_loaded")
        assert agents[0] == "agent3"  # Should select agent with lower load
    
    @pytest.mark.asyncio
    async def test_system_health(self, agent_registry, mock_agents):
        """Test system health reporting"""
        # Register agents
        for agent in mock_agents:
            await agent_registry.register_agent(agent)
        
        # Get system health
        health = await agent_registry.get_system_health()
        assert health.overall_status == "healthy"
        assert health.system_metrics["total_agents"] == 3
        assert health.system_metrics["healthy_agents"] == 3
        
        # Make one agent unhealthy
        mock_agents[0].set_healthy(False)
        agent_registry.health_failures["agent1"] = 5  # Exceed threshold
        
        # System should still be healthy (2/3 agents healthy)
        health = await agent_registry.get_system_health()
        assert health.system_metrics["unhealthy_agents"] == 1
    
    @pytest.mark.asyncio
    async def test_failover_configuration(self, agent_registry, mock_agents):
        """Test failover agent configuration"""
        agent = mock_agents[0]
        await agent_registry.register_agent(agent)
        
        # Set failover agents
        result = await agent_registry.set_agent_failover("agent1", ["agent2", "agent3"])
        assert result is True
        
        # Check failover configuration
        registration = agent_registry.registrations["agent1"]
        assert registration.failover_agents == ["agent2", "agent3"]
    
    def test_registry_stats(self, agent_registry):
        """Test registry statistics"""
        stats = agent_registry.get_registry_stats()
        
        assert "total_agents" in stats
        assert "healthy_agents" in stats
        assert "capabilities_indexed" in stats
        assert "agent_types" in stats
        assert "registration_count" in stats
        assert "discovery_requests" in stats


if __name__ == "__main__":
    pytest.main([__file__])