"""
Unit tests for agentic AI core infrastructure
Tests interfaces, models, base agent, and core functionality
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List

from src.agentic.core.interfaces import (
    IAgentCore, IOrchestrator, ISpecializedAgent, IApprovalAgent,
    IMCPServer, IStrandsFramework, IContextManager, IMemoryStore,
    ISecurityManager
)
from src.agentic.core.models import (
    AgentMessage, AgentState, DecisionProposal, WorkflowDefinition,
    SystemEvent, AgentCapability, AgentConfiguration, MessageType,
    AgentStatus, DecisionStatus, RiskLevel, ConversationContext,
    DecisionContext, AgentMetrics, SystemHealth
)
from src.agentic.core.base_agent import BaseAgent


class TestAgentModels:
    """Test core agent data models"""
    
    def test_agent_message_creation(self):
        """Test AgentMessage creation and serialization"""
        message = AgentMessage(
            sender="test_sender",
            recipient="test_recipient",
            message_type=MessageType.REQUEST,
            content={"test": "data"}
        )
        
        assert message.sender == "test_sender"
        assert message.recipient == "test_recipient"
        assert message.message_type == MessageType.REQUEST
        assert message.content == {"test": "data"}
        assert message.priority == "normal"
        assert message.requires_response is False
        
        # Test serialization
        message_dict = message.to_dict()
        assert message_dict["sender"] == "test_sender"
        assert message_dict["message_type"] == "request"
        
        # Test deserialization
        restored_message = AgentMessage.from_dict(message_dict)
        assert restored_message.sender == message.sender
        assert restored_message.message_type == message.message_type
    
    def test_agent_state_management(self):
        """Test AgentState functionality"""
        state = AgentState(
            agent_id="test_agent",
            status=AgentStatus.ACTIVE
        )
        
        assert state.agent_id == "test_agent"
        assert state.status == AgentStatus.ACTIVE
        assert state.error_count == 0
        assert state.is_healthy() is True
        
        # Test error recording
        state.record_error("Test error")
        assert state.error_count == 1
        assert state.last_error == "Test error"
        
        # Test performance update
        state.update_performance({"response_time": 100.0})
        assert state.performance_metrics["response_time"] == 100.0
    
    def test_agent_capability_validation(self):
        """Test AgentCapability input validation"""
        capability = AgentCapability(
            name="test_capability",
            description="Test capability",
            input_schema={
                "type": "object",
                "required": ["param1", "param2"],
                "properties": {
                    "param1": {"type": "string"},
                    "param2": {"type": "number"}
                }
            },
            output_schema={"type": "object"}
        )
        
        # Test valid input
        valid_input = {"param1": "test", "param2": 123}
        assert capability.validate_input(valid_input) is True
        
        # Test invalid input (missing required field)
        invalid_input = {"param1": "test"}
        assert capability.validate_input(invalid_input) is False
    
    def test_decision_proposal_workflow(self):
        """Test DecisionProposal approval workflow"""
        proposal = DecisionProposal(
            title="Test Decision",
            description="Test decision description",
            required_approvers=["approver1", "approver2"],
            estimated_cost_impact=1000.0,
            risk_level=RiskLevel.MEDIUM
        )
        
        assert proposal.status == DecisionStatus.DRAFT
        assert proposal.is_approved() is False
        assert proposal.is_rejected() is False
        
        # Add approval responses
        proposal.add_approval_response("approver1", "approved", "Looks good")
        assert proposal.is_approved() is False  # Need both approvers
        
        proposal.add_approval_response("approver2", "approved", "Approved")
        assert proposal.is_approved() is True
        
        # Test approval summary
        summary = proposal.get_approval_summary()
        assert summary["approved"] == 2
        assert summary["rejected"] == 0
        assert summary["is_approved"] is True
    
    def test_workflow_definition_execution_order(self):
        """Test WorkflowDefinition step dependencies"""
        from src.agentic.core.models import WorkflowStep
        
        step1 = WorkflowStep(
            step_id="step1",
            agent_id="agent1",
            action="action1"
        )
        
        step2 = WorkflowStep(
            step_id="step2",
            agent_id="agent2",
            action="action2",
            dependencies=["step1"]
        )
        
        workflow = WorkflowDefinition(
            name="Test Workflow",
            steps=[step1, step2]
        )
        
        # Test initial steps (no dependencies)
        initial_steps = workflow.get_initial_steps()
        assert len(initial_steps) == 1
        assert initial_steps[0].step_id == "step1"
        
        # Test next steps after step1 completion
        next_steps = workflow.get_next_steps(["step1"])
        assert len(next_steps) == 1
        assert next_steps[0].step_id == "step2"
    
    def test_system_event_creation(self):
        """Test SystemEvent creation and serialization"""
        event = SystemEvent(
            event_type="test_event",
            source="test_source",
            data={"key": "value"},
            severity="info"
        )
        
        assert event.event_type == "test_event"
        assert event.source == "test_source"
        assert event.severity == "info"
        
        # Test serialization
        event_dict = event.to_dict()
        assert event_dict["event_type"] == "test_event"
        assert event_dict["data"] == {"key": "value"}
    
    def test_agent_metrics_calculations(self):
        """Test AgentMetrics calculations"""
        metrics = AgentMetrics(agent_id="test_agent")
        
        # Test initial state
        assert metrics.calculate_success_rate() == 100.0
        
        # Update metrics
        metrics.tasks_completed = 8
        metrics.tasks_failed = 2
        
        success_rate = metrics.calculate_success_rate()
        assert success_rate == 80.0  # 8/10 * 100
        
        # Test metrics update
        metrics.update_metrics(
            messages_processed=100,
            average_response_time_ms=150.0
        )
        
        assert metrics.messages_processed == 100
        assert metrics.average_response_time_ms == 150.0


class MockAgent(BaseAgent):
    """Mock agent for testing BaseAgent functionality"""
    
    def __init__(self, agent_id: str = "mock_agent"):
        capabilities = [
            AgentCapability(
                name="test_action",
                description="Test action",
                input_schema={"type": "object"},
                output_schema={"type": "object"}
            )
        ]
        
        super().__init__(
            agent_id=agent_id,
            agent_type="mock",
            capabilities=capabilities,
            config={"test_config": True}
        )
    
    async def _agent_specific_initialization(self):
        """Mock agent-specific initialization"""
        self.initialized_flag = True
    
    async def _agent_specific_health_check(self) -> bool:
        """Mock health check"""
        return True
    
    async def _agent_specific_cleanup(self):
        """Mock cleanup"""
        self.cleanup_called = True


class TestBaseAgent:
    """Test BaseAgent functionality"""
    
    @pytest.fixture
    def mock_agent(self):
        """Create mock agent for testing"""
        return MockAgent()
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self, mock_agent):
        """Test agent initialization process"""
        # Test initial state
        assert mock_agent.agent_id == "mock_agent"
        assert mock_agent._state.status == AgentStatus.INITIALIZING
        
        # Initialize agent
        success = await mock_agent.initialize()
        assert success is True
        assert mock_agent._state.status == AgentStatus.ACTIVE
        assert hasattr(mock_agent, 'initialized_flag')
    
    @pytest.mark.asyncio
    async def test_agent_message_processing(self, mock_agent):
        """Test agent message processing"""
        await mock_agent.initialize()
        
        # Test request message
        request_message = AgentMessage(
            sender="test_sender",
            recipient=mock_agent.agent_id,
            message_type=MessageType.REQUEST,
            content={"test": "data"}
        )
        
        response = await mock_agent.process_message(request_message)
        
        assert response.sender == mock_agent.agent_id
        assert response.recipient == "test_sender"
        assert response.message_type == MessageType.RESPONSE
        assert response.correlation_id == request_message.correlation_id
    
    @pytest.mark.asyncio
    async def test_agent_action_execution(self, mock_agent):
        """Test agent action execution"""
        await mock_agent.initialize()
        
        # Test health check action
        result = await mock_agent.execute_action("health_check", {})
        
        assert result["success"] is True
        assert "healthy" in result["result"]
        
        # Test invalid action
        result = await mock_agent.execute_action("invalid_action", {})
        assert result["success"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_agent_state_management(self, mock_agent):
        """Test agent state management"""
        await mock_agent.initialize()
        
        # Get initial state
        state = await mock_agent.get_state()
        assert state.agent_id == mock_agent.agent_id
        assert state.status == AgentStatus.ACTIVE
        
        # Test health check
        is_healthy = await mock_agent.health_check()
        assert is_healthy is True
    
    @pytest.mark.asyncio
    async def test_agent_shutdown(self, mock_agent):
        """Test agent shutdown process"""
        await mock_agent.initialize()
        
        # Shutdown agent
        success = await mock_agent.shutdown()
        assert success is True
        assert mock_agent._state.status == AgentStatus.OFFLINE
        assert hasattr(mock_agent, 'cleanup_called')
    
    @pytest.mark.asyncio
    async def test_agent_error_handling(self, mock_agent):
        """Test agent error handling"""
        await mock_agent.initialize()
        
        # Test error message handling
        error_message = AgentMessage(
            sender="test_sender",
            recipient=mock_agent.agent_id,
            message_type=MessageType.ERROR,
            content={"error": "Test error"}
        )
        
        response = await mock_agent.process_message(error_message)
        assert response.message_type == MessageType.NOTIFICATION
        assert response.content["status"] == "error_acknowledged"
    
    @pytest.mark.asyncio
    async def test_agent_heartbeat(self, mock_agent):
        """Test agent heartbeat functionality"""
        await mock_agent.initialize()
        
        initial_heartbeat = mock_agent.last_heartbeat
        
        # Send heartbeat message
        heartbeat_message = AgentMessage(
            sender="test_sender",
            recipient=mock_agent.agent_id,
            message_type=MessageType.HEARTBEAT,
            content={}
        )
        
        response = await mock_agent.process_message(heartbeat_message)
        
        assert response.message_type == MessageType.HEARTBEAT
        assert response.content["status"] == "alive"
        assert mock_agent.last_heartbeat > initial_heartbeat


class TestConversationContext:
    """Test conversation context management"""
    
    def test_conversation_creation(self):
        """Test conversation context creation"""
        context = ConversationContext(
            participants=["agent1", "agent2"],
            topic="Test conversation"
        )
        
        assert len(context.participants) == 2
        assert context.topic == "Test conversation"
        assert context.is_active is True
    
    def test_participant_management(self):
        """Test adding participants to conversation"""
        context = ConversationContext(participants=["agent1"])
        
        # Add new participant
        context.add_participant("agent2")
        assert len(context.participants) == 2
        assert "agent2" in context.participants
        
        # Try to add existing participant
        context.add_participant("agent1")
        assert len(context.participants) == 2  # Should not duplicate
    
    def test_activity_tracking(self):
        """Test conversation activity tracking"""
        context = ConversationContext()
        initial_activity = context.last_activity
        
        # Wait a small amount to ensure time difference
        time.sleep(0.001)
        
        # Update activity
        context.update_activity()
        assert context.last_activity > initial_activity


class TestDecisionContext:
    """Test decision context management"""
    
    def test_decision_context_creation(self):
        """Test decision context creation"""
        context = DecisionContext(decision_id="test_decision")
        
        assert context.decision_id == "test_decision"
        assert len(context.related_decisions) == 0
    
    def test_related_decisions(self):
        """Test related decision management"""
        context = DecisionContext(decision_id="test_decision")
        
        # Add related decision
        context.add_related_decision("related_decision_1")
        assert len(context.related_decisions) == 1
        assert "related_decision_1" in context.related_decisions
        
        # Try to add duplicate
        context.add_related_decision("related_decision_1")
        assert len(context.related_decisions) == 1  # Should not duplicate


class TestSystemHealth:
    """Test system health monitoring"""
    
    def test_system_health_creation(self):
        """Test system health status creation"""
        health = SystemHealth()
        
        assert health.overall_status == "healthy"
        assert health.is_healthy() is True
        assert len(health.get_unhealthy_agents()) == 0
    
    def test_unhealthy_agent_detection(self):
        """Test detection of unhealthy agents"""
        health = SystemHealth(
            agent_statuses={
                "agent1": "active",
                "agent2": "error",
                "agent3": "offline"
            }
        )
        
        unhealthy_agents = health.get_unhealthy_agents()
        assert len(unhealthy_agents) == 2
        assert "agent2" in unhealthy_agents
        assert "agent3" in unhealthy_agents
    
    def test_health_with_alerts(self):
        """Test system health with active alerts"""
        health = SystemHealth(
            overall_status="healthy",
            active_alerts=["alert1", "alert2"]
        )
        
        assert health.is_healthy() is False  # Has active alerts


if __name__ == "__main__":
    pytest.main([__file__])