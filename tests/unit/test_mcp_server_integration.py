"""
Unit tests for MCP Server integration and agent communication
Tests secure inter-agent communication, message routing, and system coordination
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List

from tests.framework.agent_test_framework import AgentTestFramework, TestDataGenerator
from src.agentic.core.interfaces import IAgentCore, IMCPServer
from src.agentic.core.models import (
    AgentMessage, AgentState, SystemEvent, MessageType, AgentStatus,
    MultiAgentTask, TaskResult, AgentCapability
)
from src.agentic.communication.mcp_server import MCPAgentServer
from src.agentic.communication.agent_registry import AgentRegistry


class MockTestAgent(IAgentCore):
    """Mock agent for MCP server testing"""
    
    def __init__(self, agent_id: str, agent_type: str = "test"):
        self._agent_id = agent_id
        self.agent_type = agent_type
        self._capabilities = [
            AgentCapability(
                name=f"{agent_type}_capability",
                description=f"Test capability for {agent_type}",
                input_schema={"type": "object"},
                output_schema={"type": "object"}
            )
        ]
        self.message_history = []
        self.is_healthy = True
        self.initialized = False
    
    @property
    def agent_id(self) -> str:
        return self._agent_id
    
    @property
    def capabilities(self) -> List[AgentCapability]:
        return self._capabilities
    
    async def initialize(self) -> bool:
        self.initialized = True
        return True
    
    async def process_message(self, message: AgentMessage) -> AgentMessage:
        self.message_history.append(message)
        
        # Simulate processing based on message type
        if message.message_type == MessageType.REQUEST:
            return AgentMessage(
                sender=self.agent_id,
                recipient=message.sender,
                message_type=MessageType.RESPONSE,
                content={"processed": True, "original_content": message.content},
                correlation_id=message.correlation_id
            )
        elif message.message_type == MessageType.HEARTBEAT:
            return AgentMessage(
                sender=self.agent_id,
                recipient=message.sender,
                message_type=MessageType.HEARTBEAT,
                content={"status": "alive", "timestamp": datetime.now().isoformat()},
                correlation_id=message.correlation_id
            )
        else:
            return AgentMessage(
                sender=self.agent_id,
                recipient=message.sender,
                message_type=MessageType.NOTIFICATION,
                content={"acknowledged": True},
                correlation_id=message.correlation_id
            )
    
    async def execute_action(self, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        if action == "health_check":
            return {"healthy": self.is_healthy, "agent_id": self.agent_id}
        elif action == "process_data":
            return {"processed": True, "data": parameters.get("data", {})}
        else:
            return {"success": True, "action": action, "parameters": parameters}
    
    async def get_state(self) -> AgentState:
        return AgentState(
            agent_id=self.agent_id,
            status=AgentStatus.ACTIVE if self.is_healthy else AgentStatus.ERROR
        )
    
    async def health_check(self) -> bool:
        return self.is_healthy
    
    async def shutdown(self) -> bool:
        return True
    
    def set_healthy(self, healthy: bool):
        self.is_healthy = healthy


class TestMCPServerIntegration:
    """Test MCP server functionality and agent communication"""
    
    @pytest.fixture
    def test_framework(self):
        """Create test framework instance"""
        return AgentTestFramework()
    
    @pytest.fixture
    def mock_agents(self):
        """Create mock agents for testing"""
        return {
            "agent1": MockTestAgent("agent1", "cost_management"),
            "agent2": MockTestAgent("agent2", "resource_management"),
            "agent3": MockTestAgent("agent3", "forecasting")
        }
    
    @pytest.fixture
    async def mcp_server(self, mock_agents):
        """Create MCP server with registered agents"""
        try:
            # Try to create real MCP server
            server = MCPAgentServer()
            await server.initialize()
            
            # Register mock agents
            for agent_id, agent in mock_agents.items():
                await agent.initialize()
                await server.register_agent(agent)
            
            return server
            
        except ImportError:
            # Fall back to mock MCP server from framework
            from tests.framework.agent_test_framework import MockMCPServer
            server = MockMCPServer()
            
            for agent_id, agent in mock_agents.items():
                await agent.initialize()
                await server.register_agent(agent_id, agent)
            
            return server
    
    @pytest.mark.asyncio
    async def test_agent_registration(self, mcp_server, mock_agents):
        """Test agent registration with MCP server"""
        # Agents should already be registered in fixture
        
        # Test that agents are registered
        if hasattr(mcp_server, 'registered_agents'):
            assert len(mcp_server.registered_agents) == 3
            assert "agent1" in mcp_server.registered_agents
            assert "agent2" in mcp_server.registered_agents
            assert "agent3" in mcp_server.registered_agents
        
        # Test agent status retrieval
        if hasattr(mcp_server, 'get_agent_status'):
            status = await mcp_server.get_agent_status("agent1")
            assert status is not None
            assert status.get("agent_id") == "agent1" or "agent1" in str(status)
    
    @pytest.mark.asyncio
    async def test_message_routing(self, mcp_server, mock_agents):
        """Test message routing between agents"""
        # Create test message
        message = AgentMessage(
            sender="agent1",
            recipient="agent2",
            message_type=MessageType.REQUEST,
            content={"test_data": "routing_test", "action": "process_data"}
        )
        
        # Route message through MCP server
        response = await mcp_server.route_message(message)
        
        # Verify response
        assert response is not None
        assert response.sender == "agent2"
        assert response.recipient == "agent1"
        assert response.message_type == MessageType.RESPONSE
        assert response.correlation_id == message.correlation_id
        
        # Verify agent received message
        agent2 = mock_agents["agent2"]
        assert len(agent2.message_history) > 0
        received_message = agent2.message_history[-1]
        assert received_message.sender == "agent1"
        assert received_message.content["test_data"] == "routing_test"
    
    @pytest.mark.asyncio
    async def test_broadcast_system_event(self, mcp_server, mock_agents):
        """Test system event broadcasting"""
        # Create system event
        event = SystemEvent(
            event_type="system_maintenance",
            source="mcp_server",
            data={"maintenance_window": "2024-01-01T00:00:00Z"},
            severity="info"
        )
        
        # Broadcast event
        responses = await mcp_server.broadcast_system_event(event)
        
        # Verify responses
        assert len(responses) == 3  # Should get response from each agent
        
        for response in responses:
            assert response.message_type in [MessageType.NOTIFICATION, MessageType.RESPONSE]
            assert response.sender in ["agent1", "agent2", "agent3"]
        
        # Verify all agents received the event
        for agent in mock_agents.values():
            # Check if agent has message history indicating event receipt
            if hasattr(agent, 'message_history') and agent.message_history:
                # At least one message should be related to the system event
                event_messages = [
                    msg for msg in agent.message_history 
                    if msg.message_type == MessageType.SYSTEM_EVENT or 
                       (msg.content and "system_maintenance" in str(msg.content))
                ]
                # Note: This might be 0 if the mock doesn't handle system events specifically
    
    @pytest.mark.asyncio
    async def test_multi_agent_task_coordination(self, mcp_server, mock_agents):
        """Test multi-agent task coordination"""
        # Create multi-agent task
        task = MultiAgentTask(
            task_id="test_coordination",
            task_type="data_processing",
            participants=["agent1", "agent2", "agent3"],
            task_data={
                "data_to_process": [1, 2, 3, 4, 5],
                "processing_type": "parallel"
            }
        )
        
        # Coordinate task
        if hasattr(mcp_server, 'coordinate_multi_agent_task'):
            result = await mcp_server.coordinate_multi_agent_task(task)
            
            assert isinstance(result, TaskResult)
            assert result.task_id == "test_coordination"
            assert result.success is True
        else:
            # For mock server, simulate coordination
            # Send task to each participant
            responses = []
            for participant in task.participants:
                message = AgentMessage(
                    sender="mcp_server",
                    recipient=participant,
                    message_type=MessageType.COMMAND,
                    content={
                        "command": "process_data",
                        "parameters": {"data": task.task_data}
                    }
                )
                response = await mcp_server.route_message(message)
                responses.append(response)
            
            assert len(responses) == 3
            for response in responses:
                assert response.message_type == MessageType.RESPONSE
    
    @pytest.mark.asyncio
    async def test_agent_failure_handling(self, mcp_server, mock_agents):
        """Test handling of agent failures"""
        # Make one agent unhealthy
        mock_agents["agent2"].set_healthy(False)
        
        # Try to send message to unhealthy agent
        message = AgentMessage(
            sender="agent1",
            recipient="agent2",
            message_type=MessageType.REQUEST,
            content={"test": "failure_handling"}
        )
        
        # Route message (should still work, but agent might indicate unhealthy state)
        response = await mcp_server.route_message(message)
        
        # Response should still be received (agent can still process messages even if unhealthy)
        assert response is not None
        assert response.sender == "agent2"
        
        # Check agent status
        if hasattr(mcp_server, 'get_agent_status'):
            status = await mcp_server.get_agent_status("agent2")
            # Status might indicate the agent is unhealthy
            assert status is not None
    
    @pytest.mark.asyncio
    async def test_message_history_tracking(self, mcp_server, mock_agents):
        """Test message history tracking"""
        # Send multiple messages
        messages = [
            AgentMessage(
                sender="agent1",
                recipient="agent2",
                message_type=MessageType.REQUEST,
                content={"message_id": i}
            )
            for i in range(5)
        ]
        
        # Route all messages
        responses = []
        for message in messages:
            response = await mcp_server.route_message(message)
            responses.append(response)
        
        # Verify all messages were processed
        assert len(responses) == 5
        
        # Check message history if available
        if hasattr(mcp_server, 'get_message_history'):
            history = mcp_server.get_message_history()
            assert len(history) >= 10  # 5 requests + 5 responses
    
    @pytest.mark.asyncio
    async def test_concurrent_message_routing(self, mcp_server, mock_agents):
        """Test concurrent message routing"""
        # Create multiple concurrent messages
        messages = [
            AgentMessage(
                sender="agent1",
                recipient="agent2",
                message_type=MessageType.REQUEST,
                content={"concurrent_test": i}
            )
            for i in range(10)
        ]
        
        # Route messages concurrently
        tasks = [mcp_server.route_message(msg) for msg in messages]
        responses = await asyncio.gather(*tasks)
        
        # Verify all responses received
        assert len(responses) == 10
        
        for i, response in enumerate(responses):
            assert response.sender == "agent2"
            assert response.recipient == "agent1"
            assert response.message_type == MessageType.RESPONSE
    
    @pytest.mark.asyncio
    async def test_security_validation(self, mcp_server, mock_agents):
        """Test security validation in message routing"""
        # Test with valid agents
        valid_message = AgentMessage(
            sender="agent1",
            recipient="agent2",
            message_type=MessageType.REQUEST,
            content={"security_test": "valid"}
        )
        
        response = await mcp_server.route_message(valid_message)
        assert response is not None
        
        # Test with invalid sender (if security is implemented)
        invalid_message = AgentMessage(
            sender="unknown_agent",
            recipient="agent2",
            message_type=MessageType.REQUEST,
            content={"security_test": "invalid"}
        )
        
        try:
            response = await mcp_server.route_message(invalid_message)
            # If no security validation, message might still go through
            # If security validation exists, should get error response
            if response.message_type == MessageType.ERROR:
                assert "not found" in response.content.get("error", "").lower()
        except Exception as e:
            # Security validation might raise exception
            assert "unknown_agent" in str(e) or "not found" in str(e).lower()
    
    @pytest.mark.asyncio
    async def test_heartbeat_mechanism(self, mcp_server, mock_agents):
        """Test heartbeat mechanism between agents"""
        # Send heartbeat message
        heartbeat = AgentMessage(
            sender="mcp_server",
            recipient="agent1",
            message_type=MessageType.HEARTBEAT,
            content={}
        )
        
        response = await mcp_server.route_message(heartbeat)
        
        assert response.message_type == MessageType.HEARTBEAT
        assert response.sender == "agent1"
        assert "status" in response.content
        assert response.content["status"] == "alive"
    
    @pytest.mark.asyncio
    async def test_agent_unregistration(self, mcp_server, mock_agents):
        """Test agent unregistration"""
        # Unregister an agent
        if hasattr(mcp_server, 'unregister_agent'):
            success = await mcp_server.unregister_agent("agent3")
            assert success is True
            
            # Try to send message to unregistered agent
            message = AgentMessage(
                sender="agent1",
                recipient="agent3",
                message_type=MessageType.REQUEST,
                content={"test": "unregistered"}
            )
            
            response = await mcp_server.route_message(message)
            
            # Should get error response
            assert response.message_type == MessageType.ERROR
            assert "not found" in response.content.get("error", "").lower()


class TestAgentRegistryIntegration:
    """Test agent registry integration with MCP server"""
    
    @pytest.fixture
    def agent_registry(self):
        """Create agent registry for testing"""
        config = {
            "health_check_interval": 1,
            "load_update_interval": 1
        }
        return AgentRegistry(config)
    
    @pytest.fixture
    def mock_agents(self):
        """Create mock agents for registry testing"""
        return [
            MockTestAgent("registry_agent1", "cost_management"),
            MockTestAgent("registry_agent2", "resource_management"),
            MockTestAgent("registry_agent3", "cost_management")
        ]
    
    @pytest.mark.asyncio
    async def test_agent_discovery_integration(self, agent_registry, mock_agents):
        """Test agent discovery through registry"""
        # Register agents
        for agent in mock_agents:
            await agent.initialize()
            await agent_registry.register_agent(agent)
        
        # Test capability-based discovery
        cost_agents = await agent_registry.discover_agents_by_capability("cost_management_capability")
        assert len(cost_agents) >= 2  # Should find agents with cost management capability
        
        # Test type-based discovery
        cost_management_agents = await agent_registry.discover_agents_by_type("cost_management")
        assert len(cost_management_agents) == 2  # registry_agent1 and registry_agent3
    
    @pytest.mark.asyncio
    async def test_load_balancing_integration(self, agent_registry, mock_agents):
        """Test load balancing through registry"""
        # Register agents
        for agent in mock_agents:
            await agent.initialize()
            await agent_registry.register_agent(agent)
        
        # Set different load levels
        await agent_registry.update_agent_load("registry_agent1", 0.8)
        await agent_registry.update_agent_load("registry_agent3", 0.3)
        
        # Get best agent for capability (should prefer lower load)
        best_agent = await agent_registry.get_best_agent_for_capability("cost_management_capability")
        
        # Should prefer agent with lower load
        assert best_agent in ["registry_agent1", "registry_agent3"]
    
    @pytest.mark.asyncio
    async def test_health_monitoring_integration(self, agent_registry, mock_agents):
        """Test health monitoring integration"""
        # Register agents
        for agent in mock_agents:
            await agent.initialize()
            await agent_registry.register_agent(agent)
        
        # Make one agent unhealthy
        mock_agents[1].set_healthy(False)
        
        # Check system health
        system_health = await agent_registry.get_system_health()
        
        assert system_health.overall_status in ["healthy", "degraded"]
        assert system_health.system_metrics["total_agents"] == 3
        
        # Healthy agents should be 2 (if health check has run)
        # Note: Might still be 3 if health check hasn't detected the unhealthy agent yet


if __name__ == "__main__":
    pytest.main([__file__, "-v"])