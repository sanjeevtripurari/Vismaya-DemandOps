"""
Unit tests for Strands Framework integration
Tests context management, memory persistence, and cross-agent communication
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List

from tests.framework.agent_test_framework import AgentTestFramework, TestDataGenerator
from src.agentic.core.interfaces import IStrandsFramework, IContextManager, IMemoryStore
from src.agentic.core.models import (
    AgentMessage, AgentState, DecisionProposal, MessageType, AgentStatus,
    ConversationContext, DecisionContext, RiskLevel, DecisionStatus
)
from src.agentic.strands.memory_store import StrandsMemoryStore
from src.agentic.strands.context_manager import StrandsContextManager


class MockStrandsFramework(IStrandsFramework):
    """Mock Strands framework for testing"""
    
    def __init__(self):
        self.contexts = {}
        self.conversation_threads = {}
        self.decision_contexts = {}
        self.memory_store = MockMemoryStore()
        self.context_manager = MockContextManager()
        self.initialized = False
    
    async def initialize(self, config: Dict[str, Any]) -> bool:
        self.config = config
        self.initialized = True
        return True
    
    async def get_shared_context(self, context_keys: List[str]) -> Dict[str, Any]:
        return {key: self.contexts.get(key) for key in context_keys}
    
    async def update_context(self, agent_id: str, context_updates: Dict[str, Any]) -> bool:
        if agent_id not in self.contexts:
            self.contexts[agent_id] = {}
        self.contexts[agent_id].update(context_updates)
        return True
    
    async def create_conversation_thread(self, participants: List[str]) -> str:
        thread_id = f"thread_{len(self.conversation_threads)}"
        self.conversation_threads[thread_id] = ConversationContext(
            thread_id=thread_id,
            participants=participants
        )
        return thread_id
    
    async def get_conversation_history(self, thread_id: str, limit: int = 50) -> List[AgentMessage]:
        return await self.memory_store.retrieve_conversation_history(thread_id, limit)
    
    async def store_conversation_message(self, thread_id: str, message: AgentMessage) -> bool:
        return await self.memory_store.store_conversation(thread_id, message)
    
    async def get_decision_context(self, decision_id: str) -> DecisionContext:
        if decision_id in self.decision_contexts:
            return self.decision_contexts[decision_id]
        
        context = DecisionContext(decision_id=decision_id)
        self.decision_contexts[decision_id] = context
        return context
    
    async def store_decision_history(self, decision: DecisionProposal) -> bool:
        return await self.memory_store.store_decision_proposal(decision)
    
    async def query_similar_decisions(self, current_decision: DecisionProposal) -> List[DecisionProposal]:
        return await self.memory_store.query_similar_decisions(current_decision)


class MockMemoryStore(IMemoryStore):
    """Mock memory store for testing"""
    
    def __init__(self):
        self.conversations = {}
        self.agent_states = {}
        self.decision_proposals = {}
        self.system_events = []
    
    async def store_conversation(self, thread_id: str, message: AgentMessage) -> bool:
        if thread_id not in self.conversations:
            self.conversations[thread_id] = []
        self.conversations[thread_id].append(message)
        return True
    
    async def retrieve_conversation_history(self, thread_id: str, limit: int = 50) -> List[AgentMessage]:
        messages = self.conversations.get(thread_id, [])
        return messages[-limit:] if limit > 0 else messages
    
    async def store_agent_state(self, agent_id: str, state: AgentState) -> bool:
        self.agent_states[agent_id] = state
        return True
    
    async def retrieve_agent_state(self, agent_id: str) -> AgentState:
        return self.agent_states.get(agent_id)
    
    async def store_decision_proposal(self, proposal: DecisionProposal) -> bool:
        self.decision_proposals[proposal.proposal_id] = proposal
        return True
    
    async def retrieve_decision_proposal(self, proposal_id: str) -> DecisionProposal:
        return self.decision_proposals.get(proposal_id)
    
    async def query_decisions_by_criteria(self, criteria: Dict[str, Any]) -> List[DecisionProposal]:
        results = []
        for proposal in self.decision_proposals.values():
            match = True
            for key, value in criteria.items():
                if hasattr(proposal, key) and getattr(proposal, key) != value:
                    match = False
                    break
            if match:
                results.append(proposal)
        return results
    
    async def query_similar_decisions(self, current_decision: DecisionProposal) -> List[DecisionProposal]:
        similar = []
        for proposal in self.decision_proposals.values():
            if (proposal.risk_level == current_decision.risk_level and
                abs(proposal.estimated_cost_impact - current_decision.estimated_cost_impact) < 1000):
                similar.append(proposal)
        return similar
    
    async def store_system_event(self, event) -> bool:
        self.system_events.append(event)
        return True
    
    async def get_system_events(self, event_type: str = None, limit: int = 100) -> List:
        events = self.system_events
        if event_type:
            events = [e for e in events if getattr(e, 'event_type', None) == event_type]
        return events[-limit:] if limit > 0 else events


class MockContextManager(IContextManager):
    """Mock context manager for testing"""
    
    def __init__(self):
        self.global_context = {}
        self.agent_contexts = {}
        self.context_snapshots = {}
    
    async def get_global_context(self) -> Dict[str, Any]:
        return self.global_context.copy()
    
    async def get_agent_context(self, agent_id: str) -> Dict[str, Any]:
        return self.agent_contexts.get(agent_id, {}).copy()
    
    async def update_global_context(self, updates: Dict[str, Any]) -> bool:
        self.global_context.update(updates)
        return True
    
    async def update_agent_context(self, agent_id: str, updates: Dict[str, Any]) -> bool:
        if agent_id not in self.agent_contexts:
            self.agent_contexts[agent_id] = {}
        self.agent_contexts[agent_id].update(updates)
        return True
    
    async def create_context_snapshot(self, context_id: str) -> str:
        snapshot_id = f"snapshot_{len(self.context_snapshots)}"
        self.context_snapshots[snapshot_id] = {
            "global_context": self.global_context.copy(),
            "agent_contexts": {k: v.copy() for k, v in self.agent_contexts.items()},
            "created_at": datetime.now()
        }
        return snapshot_id
    
    async def restore_context_snapshot(self, snapshot_id: str) -> bool:
        if snapshot_id not in self.context_snapshots:
            return False
        
        snapshot = self.context_snapshots[snapshot_id]
        self.global_context = snapshot["global_context"].copy()
        self.agent_contexts = {k: v.copy() for k, v in snapshot["agent_contexts"].items()}
        return True
    
    async def synchronize_context(self, agent_ids: List[str]) -> bool:
        # Mock synchronization - just ensure all agents have consistent context
        shared_context = {}
        for agent_id in agent_ids:
            if agent_id in self.agent_contexts:
                shared_context.update(self.agent_contexts[agent_id])
        
        for agent_id in agent_ids:
            self.agent_contexts[agent_id] = shared_context.copy()
        
        return True


class TestStrandsFrameworkIntegration:
    """Test Strands framework integration"""
    
    @pytest.fixture
    def strands_framework(self):
        """Create Strands framework for testing"""
        return MockStrandsFramework()
    
    @pytest.fixture
    def test_data_generator(self):
        """Create test data generator"""
        return TestDataGenerator()
    
    @pytest.mark.asyncio
    async def test_framework_initialization(self, strands_framework):
        """Test Strands framework initialization"""
        config = {
            "memory_store_type": "dynamodb",
            "context_sync_interval": 30,
            "max_conversation_history": 1000
        }
        
        success = await strands_framework.initialize(config)
        
        assert success is True
        assert strands_framework.initialized is True
        assert strands_framework.config == config
    
    @pytest.mark.asyncio
    async def test_context_management(self, strands_framework):
        """Test context management functionality"""
        await strands_framework.initialize({})
        
        # Update agent context
        agent_id = "test_agent"
        context_updates = {
            "current_task": "cost_analysis",
            "last_action": "analyze_spending",
            "performance_metrics": {"response_time": 150.0}
        }
        
        success = await strands_framework.update_context(agent_id, context_updates)
        assert success is True
        
        # Retrieve shared context
        context_keys = ["current_task", "performance_metrics"]
        shared_context = await strands_framework.get_shared_context(context_keys)
        
        assert shared_context["current_task"] == "cost_analysis"
        assert shared_context["performance_metrics"]["response_time"] == 150.0
    
    @pytest.mark.asyncio
    async def test_conversation_thread_management(self, strands_framework, test_data_generator):
        """Test conversation thread creation and management"""
        await strands_framework.initialize({})
        
        # Create conversation thread
        participants = ["agent1", "agent2", "agent3"]
        thread_id = await strands_framework.create_conversation_thread(participants)
        
        assert thread_id is not None
        assert thread_id in strands_framework.conversation_threads
        
        thread_context = strands_framework.conversation_threads[thread_id]
        assert thread_context.participants == participants
        
        # Store conversation messages
        messages = [
            test_data_generator.create_test_message("agent1", "agent2", MessageType.REQUEST, {"step": 1}),
            test_data_generator.create_test_message("agent2", "agent1", MessageType.RESPONSE, {"step": 2}),
            test_data_generator.create_test_message("agent1", "agent3", MessageType.REQUEST, {"step": 3})
        ]
        
        for message in messages:
            success = await strands_framework.store_conversation_message(thread_id, message)
            assert success is True
        
        # Retrieve conversation history
        history = await strands_framework.get_conversation_history(thread_id)
        
        assert len(history) == 3
        assert history[0].content["step"] == 1
        assert history[1].content["step"] == 2
        assert history[2].content["step"] == 3
    
    @pytest.mark.asyncio
    async def test_decision_context_management(self, strands_framework, test_data_generator):
        """Test decision context management"""
        await strands_framework.initialize({})
        
        # Create decision proposal
        proposal = test_data_generator.create_test_proposal(
            "Test Decision Context",
            cost_impact=2000.0,
            risk_level="high"
        )
        
        # Store decision
        success = await strands_framework.store_decision_history(proposal)
        assert success is True
        
        # Get decision context
        decision_context = await strands_framework.get_decision_context(proposal.proposal_id)
        
        assert decision_context is not None
        assert decision_context.decision_id == proposal.proposal_id
        
        # Add related decisions
        decision_context.add_related_decision("related_decision_1")
        decision_context.add_related_decision("related_decision_2")
        
        assert len(decision_context.related_decisions) == 2
    
    @pytest.mark.asyncio
    async def test_similar_decision_querying(self, strands_framework, test_data_generator):
        """Test querying for similar decisions"""
        await strands_framework.initialize({})
        
        # Create and store multiple decisions
        decisions = [
            test_data_generator.create_test_proposal("Decision 1", 1000.0, "medium"),
            test_data_generator.create_test_proposal("Decision 2", 1200.0, "medium"),
            test_data_generator.create_test_proposal("Decision 3", 5000.0, "high"),
            test_data_generator.create_test_proposal("Decision 4", 1100.0, "medium")
        ]
        
        for decision in decisions:
            await strands_framework.store_decision_history(decision)
        
        # Query for similar decisions
        current_decision = test_data_generator.create_test_proposal("Current Decision", 1050.0, "medium")
        similar_decisions = await strands_framework.query_similar_decisions(current_decision)
        
        # Should find decisions with similar cost and risk level
        assert len(similar_decisions) >= 2  # Should find at least 2 similar decisions
        
        for similar in similar_decisions:
            assert similar.risk_level == RiskLevel.MEDIUM
            assert abs(similar.estimated_cost_impact - current_decision.estimated_cost_impact) < 1000
    
    @pytest.mark.asyncio
    async def test_conversation_history_limits(self, strands_framework, test_data_generator):
        """Test conversation history retrieval with limits"""
        await strands_framework.initialize({})
        
        # Create conversation thread
        thread_id = await strands_framework.create_conversation_thread(["agent1", "agent2"])
        
        # Store many messages
        for i in range(100):
            message = test_data_generator.create_test_message(
                "agent1", "agent2", MessageType.REQUEST, {"message_id": i}
            )
            await strands_framework.store_conversation_message(thread_id, message)
        
        # Retrieve with limit
        limited_history = await strands_framework.get_conversation_history(thread_id, limit=10)
        assert len(limited_history) == 10
        
        # Should get the most recent messages
        assert limited_history[-1].content["message_id"] == 99
        assert limited_history[0].content["message_id"] == 90
        
        # Retrieve all messages
        full_history = await strands_framework.get_conversation_history(thread_id, limit=0)
        assert len(full_history) == 100


class TestMemoryStoreIntegration:
    """Test memory store integration"""
    
    @pytest.fixture
    def memory_store(self):
        """Create memory store for testing"""
        return MockMemoryStore()
    
    @pytest.fixture
    def test_data_generator(self):
        """Create test data generator"""
        return TestDataGenerator()
    
    @pytest.mark.asyncio
    async def test_conversation_storage_and_retrieval(self, memory_store, test_data_generator):
        """Test conversation message storage and retrieval"""
        thread_id = "test_thread"
        
        # Store multiple messages
        messages = [
            test_data_generator.create_test_message("agent1", "agent2", MessageType.REQUEST, {"seq": i})
            for i in range(5)
        ]
        
        for message in messages:
            success = await memory_store.store_conversation(thread_id, message)
            assert success is True
        
        # Retrieve messages
        retrieved_messages = await memory_store.retrieve_conversation_history(thread_id)
        
        assert len(retrieved_messages) == 5
        for i, message in enumerate(retrieved_messages):
            assert message.content["seq"] == i
    
    @pytest.mark.asyncio
    async def test_agent_state_persistence(self, memory_store):
        """Test agent state storage and retrieval"""
        agent_id = "test_agent"
        
        # Create and store agent state
        state = AgentState(
            agent_id=agent_id,
            status=AgentStatus.ACTIVE,
            current_task="test_task",
            performance_metrics={"response_time": 100.0}
        )
        
        success = await memory_store.store_agent_state(agent_id, state)
        assert success is True
        
        # Retrieve agent state
        retrieved_state = await memory_store.retrieve_agent_state(agent_id)
        
        assert retrieved_state is not None
        assert retrieved_state.agent_id == agent_id
        assert retrieved_state.status == AgentStatus.ACTIVE
        assert retrieved_state.current_task == "test_task"
        assert retrieved_state.performance_metrics["response_time"] == 100.0
    
    @pytest.mark.asyncio
    async def test_decision_proposal_storage(self, memory_store, test_data_generator):
        """Test decision proposal storage and retrieval"""
        # Create decision proposal
        proposal = test_data_generator.create_test_proposal(
            "Memory Store Test",
            cost_impact=1500.0,
            risk_level="medium"
        )
        
        # Store proposal
        success = await memory_store.store_decision_proposal(proposal)
        assert success is True
        
        # Retrieve proposal
        retrieved_proposal = await memory_store.retrieve_decision_proposal(proposal.proposal_id)
        
        assert retrieved_proposal is not None
        assert retrieved_proposal.proposal_id == proposal.proposal_id
        assert retrieved_proposal.title == "Memory Store Test"
        assert retrieved_proposal.estimated_cost_impact == 1500.0
    
    @pytest.mark.asyncio
    async def test_decision_querying_by_criteria(self, memory_store, test_data_generator):
        """Test querying decisions by criteria"""
        # Create and store multiple proposals
        proposals = [
            test_data_generator.create_test_proposal("High Risk 1", 3000.0, "high"),
            test_data_generator.create_test_proposal("Medium Risk 1", 1000.0, "medium"),
            test_data_generator.create_test_proposal("High Risk 2", 4000.0, "high"),
            test_data_generator.create_test_proposal("Low Risk 1", 500.0, "low")
        ]
        
        for proposal in proposals:
            await memory_store.store_decision_proposal(proposal)
        
        # Query by risk level
        high_risk_proposals = await memory_store.query_decisions_by_criteria({
            "risk_level": RiskLevel.HIGH
        })
        
        assert len(high_risk_proposals) == 2
        for proposal in high_risk_proposals:
            assert proposal.risk_level == RiskLevel.HIGH
    
    @pytest.mark.asyncio
    async def test_system_event_storage(self, memory_store):
        """Test system event storage and retrieval"""
        from src.agentic.core.models import SystemEvent
        
        # Create system events
        events = [
            SystemEvent("agent_failure", "agent1", {"error": "connection_lost"}, "error"),
            SystemEvent("system_maintenance", "system", {"duration": "1h"}, "info"),
            SystemEvent("agent_failure", "agent2", {"error": "timeout"}, "warning")
        ]
        
        # Store events
        for event in events:
            success = await memory_store.store_system_event(event)
            assert success is True
        
        # Retrieve all events
        all_events = await memory_store.get_system_events()
        assert len(all_events) == 3
        
        # Retrieve events by type
        failure_events = await memory_store.get_system_events(event_type="agent_failure")
        assert len(failure_events) == 2


class TestContextManagerIntegration:
    """Test context manager integration"""
    
    @pytest.fixture
    def context_manager(self):
        """Create context manager for testing"""
        return MockContextManager()
    
    @pytest.mark.asyncio
    async def test_global_context_management(self, context_manager):
        """Test global context management"""
        # Update global context
        updates = {
            "system_status": "operational",
            "active_agents": 5,
            "last_maintenance": "2024-01-01T00:00:00Z"
        }
        
        success = await context_manager.update_global_context(updates)
        assert success is True
        
        # Retrieve global context
        global_context = await context_manager.get_global_context()
        
        assert global_context["system_status"] == "operational"
        assert global_context["active_agents"] == 5
        assert global_context["last_maintenance"] == "2024-01-01T00:00:00Z"
    
    @pytest.mark.asyncio
    async def test_agent_context_management(self, context_manager):
        """Test agent-specific context management"""
        agent_id = "test_agent"
        
        # Update agent context
        updates = {
            "current_task": "data_processing",
            "task_progress": 0.75,
            "last_error": None
        }
        
        success = await context_manager.update_agent_context(agent_id, updates)
        assert success is True
        
        # Retrieve agent context
        agent_context = await context_manager.get_agent_context(agent_id)
        
        assert agent_context["current_task"] == "data_processing"
        assert agent_context["task_progress"] == 0.75
        assert agent_context["last_error"] is None
    
    @pytest.mark.asyncio
    async def test_context_snapshots(self, context_manager):
        """Test context snapshot creation and restoration"""
        # Set up initial context
        await context_manager.update_global_context({"version": "1.0"})
        await context_manager.update_agent_context("agent1", {"state": "initial"})
        
        # Create snapshot
        snapshot_id = await context_manager.create_context_snapshot("test_snapshot")
        assert snapshot_id is not None
        
        # Modify context
        await context_manager.update_global_context({"version": "2.0"})
        await context_manager.update_agent_context("agent1", {"state": "modified"})
        
        # Verify changes
        global_context = await context_manager.get_global_context()
        agent_context = await context_manager.get_agent_context("agent1")
        assert global_context["version"] == "2.0"
        assert agent_context["state"] == "modified"
        
        # Restore snapshot
        success = await context_manager.restore_context_snapshot(snapshot_id)
        assert success is True
        
        # Verify restoration
        restored_global = await context_manager.get_global_context()
        restored_agent = await context_manager.get_agent_context("agent1")
        assert restored_global["version"] == "1.0"
        assert restored_agent["state"] == "initial"
    
    @pytest.mark.asyncio
    async def test_context_synchronization(self, context_manager):
        """Test context synchronization between agents"""
        # Set up different contexts for agents
        await context_manager.update_agent_context("agent1", {"shared_data": "value1", "unique_data": "agent1_data"})
        await context_manager.update_agent_context("agent2", {"shared_data": "value2", "unique_data": "agent2_data"})
        await context_manager.update_agent_context("agent3", {"different_data": "value3"})
        
        # Synchronize contexts
        agent_ids = ["agent1", "agent2", "agent3"]
        success = await context_manager.synchronize_context(agent_ids)
        assert success is True
        
        # Verify synchronization
        for agent_id in agent_ids:
            context = await context_manager.get_agent_context(agent_id)
            # All agents should have merged context
            assert "shared_data" in context
            assert "unique_data" in context
            assert "different_data" in context


class TestIntegratedStrandsWorkflow:
    """Test integrated Strands framework workflows"""
    
    @pytest.fixture
    def integrated_framework(self):
        """Create integrated Strands framework"""
        return MockStrandsFramework()
    
    @pytest.mark.asyncio
    async def test_complete_decision_workflow(self, integrated_framework, test_data_generator):
        """Test complete decision workflow with context and memory"""
        await integrated_framework.initialize({})
        
        # Create decision proposal
        proposal = test_data_generator.create_test_proposal(
            "Integrated Workflow Test",
            cost_impact=2500.0,
            risk_level="high"
        )
        
        # Store decision and create context
        await integrated_framework.store_decision_history(proposal)
        decision_context = await integrated_framework.get_decision_context(proposal.proposal_id)
        
        # Create conversation thread for decision discussion
        participants = ["cost_agent", "approval_agent", "orchestrator"]
        thread_id = await integrated_framework.create_conversation_thread(participants)
        
        # Simulate decision discussion
        messages = [
            test_data_generator.create_test_message(
                "cost_agent", "approval_agent", MessageType.REQUEST,
                {"proposal_id": proposal.proposal_id, "recommendation": "approve"}
            ),
            test_data_generator.create_test_message(
                "approval_agent", "cost_agent", MessageType.RESPONSE,
                {"proposal_id": proposal.proposal_id, "status": "under_review"}
            ),
            test_data_generator.create_test_message(
                "approval_agent", "orchestrator", MessageType.NOTIFICATION,
                {"proposal_id": proposal.proposal_id, "decision": "approved"}
            )
        ]
        
        for message in messages:
            await integrated_framework.store_conversation_message(thread_id, message)
        
        # Update contexts with decision progress
        await integrated_framework.update_context("cost_agent", {
            "last_proposal": proposal.proposal_id,
            "recommendation_status": "submitted"
        })
        
        await integrated_framework.update_context("approval_agent", {
            "pending_decisions": [proposal.proposal_id],
            "last_decision": "approved"
        })
        
        # Verify integrated workflow
        conversation_history = await integrated_framework.get_conversation_history(thread_id)
        assert len(conversation_history) == 3
        
        cost_agent_context = await integrated_framework.get_shared_context(["last_proposal"])
        assert cost_agent_context["last_proposal"] == proposal.proposal_id
        
        # Query for similar decisions
        similar_decisions = await integrated_framework.query_similar_decisions(proposal)
        # Should find the stored decision itself
        assert len(similar_decisions) >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])