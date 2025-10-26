"""
Unit tests for enhanced cross-agent context sharing and synchronization
Tests the implementation of task 2.3: Add cross-agent context sharing and synchronization
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from src.agentic.strands.framework import StrandsFramework, ContextManager
from src.agentic.strands.context_synchronizer import ContextSynchronizer, SyncStrategy, ConflictResolution
from src.agentic.strands.memory_store import DynamoDBMemoryStore
from src.agentic.core.models import AgentMessage, SystemEvent


class TestContextSynchronization:
    """Test suite for context synchronization functionality"""
    
    @pytest.fixture
    def mock_memory_store(self):
        """Create mock memory store"""
        store = Mock(spec=DynamoDBMemoryStore)
        store.store_conversation = AsyncMock(return_value=True)
        store.retrieve_conversation_history = AsyncMock(return_value=[])
        store.store_system_event = AsyncMock(return_value=True)
        store.get_system_events = AsyncMock(return_value=[])
        store.store_decision_proposal = AsyncMock(return_value=True)
        store.query_decisions_by_criteria = AsyncMock(return_value=[])
        return store
    
    @pytest.fixture
    async def strands_framework(self, mock_memory_store):
        """Create Strands framework instance"""
        config = {
            "batch_sync_interval": 1.0,
            "max_batch_size": 10,
            "conflict_timeout": 30,
            "sync_interval_seconds": 5
        }
        
        framework = StrandsFramework(mock_memory_store, config)
        await framework.initialize(config)
        return framework
    
    @pytest.fixture
    async def context_synchronizer(self, strands_framework):
        """Get context synchronizer from framework"""
        return strands_framework.context_synchronizer
    
    @pytest.mark.asyncio
    async def test_real_time_context_synchronization(self, strands_framework):
        """Test real-time context synchronization between agents"""
        # Setup test agents
        agent_ids = ["cost_management_1", "resource_management_1", "forecasting_1"]
        context_keys = ["budget_threshold", "cost_alert", "optimization_recommendation"]
        
        # Set initial context for each agent
        await strands_framework.context_manager.update_agent_context("cost_management_1", {
            "budget_threshold": {"value": 1000, "timestamp": datetime.now().isoformat()},
            "cost_alert": {"value": "high", "timestamp": datetime.now().isoformat()}
        })
        
        await strands_framework.context_manager.update_agent_context("resource_management_1", {
            "optimization_recommendation": {"value": "downsize_instances", "timestamp": datetime.now().isoformat()}
        })
        
        # Perform real-time synchronization
        result = await strands_framework.synchronize_context_real_time(agent_ids, context_keys)
        
        assert result is True
        
        # Verify all agents have synchronized context
        for agent_id in agent_ids:
            agent_context = await strands_framework.context_manager.get_agent_context(agent_id)
            assert "budget_threshold" in agent_context or "cost_alert" in agent_context or "optimization_recommendation" in agent_context
    
    @pytest.mark.asyncio
    async def test_context_sharing_policies(self, strands_framework):
        """Test context sharing policies for different agent types"""
        # Test orchestrator access (should have full access)
        orchestrator_access = await strands_framework._can_agent_access_context(
            "orchestrator_1", 
            ["budget_threshold", "system_alert", "user_credentials"]
        )
        assert orchestrator_access is True
        
        # Test cost management access (should have domain-specific access)
        cost_agent_access = await strands_framework._can_agent_access_context(
            "cost_management_1",
            ["budget_threshold", "cost_alert", "forecast_data"]
        )
        assert cost_agent_access is True
        
        # Test cost management restricted access (should be denied)
        cost_agent_restricted = await strands_framework._can_agent_access_context(
            "cost_management_1",
            ["user_credentials", "system_secrets"]
        )
        assert cost_agent_restricted is False
        
        # Test user interface isolation (should have limited access)
        ui_agent_access = await strands_framework._can_agent_access_context(
            "user_interface_1",
            ["ui_preferences", "dashboard_config"]
        )
        assert ui_agent_access is True
        
        ui_agent_restricted = await strands_framework._can_agent_access_context(
            "user_interface_1",
            ["system_secrets", "agent_internal_state"]
        )
        assert ui_agent_restricted is False
    
    @pytest.mark.asyncio
    async def test_context_versioning(self, strands_framework):
        """Test context versioning and conflict resolution"""
        agent_id = "cost_management_1"
        context_key = "budget_threshold"
        
        # Create initial context version
        initial_version = await strands_framework.context_manager.create_context_version(agent_id, context_key)
        assert initial_version > 0
        
        # Update context multiple times
        for i in range(3):
            await strands_framework.context_manager.update_agent_context(agent_id, {
                context_key: {"value": 1000 + i * 100, "timestamp": datetime.now().isoformat()}
            })
            version = await strands_framework.context_manager.create_context_version(agent_id, context_key)
            assert version > initial_version
        
        # Verify version tracking
        current_version = await strands_framework.context_manager.get_context_version(agent_id, context_key)
        assert current_version >= initial_version + 3
    
    @pytest.mark.asyncio
    async def test_conflict_resolution_strategies(self, context_synchronizer):
        """Test different conflict resolution strategies"""
        # Setup conflicting values
        values = [
            {
                "agent_id": "cost_management_1",
                "agent_type": "cost_management",
                "value": {"threshold": 1000},
                "timestamp": "2024-01-01T10:00:00",
                "version": 1,
                "priority": 80,
                "has_authority": False
            },
            {
                "agent_id": "orchestrator_1", 
                "agent_type": "orchestrator",
                "value": {"threshold": 1500},
                "timestamp": "2024-01-01T10:05:00",
                "version": 2,
                "priority": 100,
                "has_authority": True
            }
        ]
        
        # Test authority-based resolution
        resolved_value, metadata = await context_synchronizer._resolve_conflict_enhanced(
            "budget_threshold", values, ConflictResolution.PRIORITY_BASED
        )
        assert resolved_value == {"threshold": 1500}  # Orchestrator should win
        assert metadata["method"] == "priority_based"
        assert metadata["source"] == "orchestrator_1"
        
        # Test timestamp-based resolution
        resolved_value, metadata = await context_synchronizer._resolve_conflict_enhanced(
            "budget_threshold", values, ConflictResolution.LAST_WRITER_WINS
        )
        assert resolved_value == {"threshold": 1500}  # Later timestamp should win
        assert metadata["method"] == "timestamp_based"
    
    @pytest.mark.asyncio
    async def test_context_isolation_policies(self, context_synchronizer):
        """Test context isolation policy application"""
        agent_id = "user_interface_1"
        
        # Apply high isolation policy
        result = await context_synchronizer.apply_context_isolation_policy(agent_id, "high")
        assert result is True
        
        # Verify isolation policy is stored
        policies = getattr(context_synchronizer, '_agent_isolation_policies', {})
        assert agent_id in policies
        assert policies[agent_id]["level"] == "high"
        assert policies[agent_id]["policy"]["context_encryption"] is True
        assert policies[agent_id]["policy"]["cross_agent_access"] is False
    
    @pytest.mark.asyncio
    async def test_cross_agent_access_validation(self, context_synchronizer):
        """Test cross-agent access validation based on isolation policies"""
        # Apply isolation policies
        await context_synchronizer.apply_context_isolation_policy("user_interface_1", "high")
        await context_synchronizer.apply_context_isolation_policy("cost_management_1", "domain")
        
        # Test high isolation - should deny access
        access_allowed = await context_synchronizer.validate_cross_agent_access(
            "cost_management_1", "user_interface_1", ["ui_preferences"]
        )
        assert access_allowed is False
        
        # Test domain-level access between related agents
        access_allowed = await context_synchronizer.validate_cross_agent_access(
            "cost_management_1", "forecasting_1", ["forecast_data"]
        )
        assert access_allowed is True
        
        # Test orchestrator access (should always be allowed)
        access_allowed = await context_synchronizer.validate_cross_agent_access(
            "orchestrator_1", "user_interface_1", ["ui_preferences"]
        )
        assert access_allowed is True
    
    @pytest.mark.asyncio
    async def test_context_checkpoint_and_rollback(self, strands_framework):
        """Test context versioning checkpoints and rollback functionality"""
        agent_ids = ["cost_management_1", "resource_management_1"]
        context_keys = ["budget_threshold", "resource_limit"]
        
        # Set initial context
        await strands_framework.context_manager.update_agent_context("cost_management_1", {
            "budget_threshold": {"value": 1000, "version": 1}
        })
        await strands_framework.context_manager.update_agent_context("resource_management_1", {
            "resource_limit": {"value": 50, "version": 1}
        })
        
        # Create checkpoint
        checkpoint_id = await strands_framework.create_context_version_checkpoint(agent_ids, context_keys)
        assert checkpoint_id != ""
        
        # Modify context
        await strands_framework.context_manager.update_agent_context("cost_management_1", {
            "budget_threshold": {"value": 2000, "version": 2}
        })
        
        # Verify context was modified
        context = await strands_framework.context_manager.get_agent_context("cost_management_1")
        assert context["budget_threshold"]["value"] == 2000
        
        # Rollback to checkpoint
        rollback_result = await strands_framework.rollback_to_context_checkpoint(checkpoint_id)
        assert rollback_result is True
        
        # Verify context was restored
        context = await strands_framework.context_manager.get_agent_context("cost_management_1")
        assert context["budget_threshold"]["value"] == 1000
    
    @pytest.mark.asyncio
    async def test_sync_operation_with_checkpoints(self, context_synchronizer):
        """Test synchronization operations with automatic checkpointing"""
        agent_ids = ["cost_management_1", "forecasting_1"]
        context_keys = ["budget_forecast"]
        
        # Create sync operation
        operation = await context_synchronizer.sync_context_immediate(agent_ids, context_keys)
        
        assert operation.status in ["completed", "in_progress"]
        assert operation.operation_id is not None
        
        # Verify checkpoint was created if operation completed
        if operation.status == "completed" and hasattr(operation, 'metadata'):
            checkpoint_id = operation.metadata.get("checkpoint_id")
            if checkpoint_id:
                checkpoints = getattr(context_synchronizer, '_sync_checkpoints', {})
                assert checkpoint_id in checkpoints
    
    @pytest.mark.asyncio
    async def test_subscription_based_sync(self, context_synchronizer):
        """Test subscription-based context synchronization"""
        agent_id = "cost_management_1"
        context_keys = ["budget_alert", "cost_threshold"]
        
        # Subscribe agent to context changes
        result = await context_synchronizer.subscribe_to_context(agent_id, context_keys)
        assert result is True
        
        # Verify subscription
        assert agent_id in context_synchronizer.sync_subscriptions
        assert set(context_keys).issubset(context_synchronizer.sync_subscriptions[agent_id])
        
        # Test unsubscription
        result = await context_synchronizer.unsubscribe_from_context(agent_id, ["budget_alert"])
        assert result is True
        
        # Verify partial unsubscription
        remaining_keys = context_synchronizer.sync_subscriptions[agent_id]
        assert "budget_alert" not in remaining_keys
        assert "cost_threshold" in remaining_keys
    
    @pytest.mark.asyncio
    async def test_sync_statistics(self, context_synchronizer):
        """Test synchronization statistics collection"""
        # Perform some sync operations
        await context_synchronizer.subscribe_to_context("cost_management_1", ["budget_alert"])
        await context_synchronizer.sync_context_immediate(["cost_management_1"], ["budget_alert"])
        
        # Get statistics
        stats = context_synchronizer.get_sync_stats()
        
        assert "active_operations" in stats
        assert "pending_changes" in stats
        assert "subscriptions" in stats
        assert "operations_by_status" in stats
        assert "conflicts_detected" in stats
        assert "checkpoints_created" in stats
        assert "conflict_resolution_methods" in stats
        assert "agent_sync_activity" in stats
        
        # Verify subscription statistics
        assert "cost_management_1" in stats["subscriptions"]
        assert "budget_alert" in stats["subscriptions"]["cost_management_1"]


if __name__ == "__main__":
    pytest.main([__file__])