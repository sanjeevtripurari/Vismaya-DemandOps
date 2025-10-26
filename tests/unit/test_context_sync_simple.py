"""
Simple validation test for cross-agent context sharing and synchronization
Tests the core functionality implemented in task 2.3
"""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock

from src.agentic.strands.context_synchronizer import ContextSynchronizer, SyncStrategy, ConflictResolution


def test_context_synchronizer_initialization():
    """Test that ContextSynchronizer can be initialized with proper configuration"""
    mock_context_manager = Mock()
    config = {
        "batch_sync_interval": 5.0,
        "max_batch_size": 100,
        "conflict_timeout": 300,
        "agent_priorities": {
            "orchestrator": 100,
            "cost_management": 80,
            "resource_management": 80
        }
    }
    
    synchronizer = ContextSynchronizer(mock_context_manager, config)
    
    assert synchronizer.context_manager == mock_context_manager
    assert synchronizer.batch_interval == 5.0
    assert synchronizer.max_batch_size == 100
    assert synchronizer.conflict_timeout == 300
    assert synchronizer.agent_priorities["orchestrator"] == 100


def test_sync_strategy_enum():
    """Test that SyncStrategy enum has expected values"""
    assert SyncStrategy.IMMEDIATE.value == "immediate"
    assert SyncStrategy.BATCHED.value == "batched"
    assert SyncStrategy.ON_DEMAND.value == "on_demand"
    assert SyncStrategy.CONFLICT_AWARE.value == "conflict_aware"


def test_conflict_resolution_enum():
    """Test that ConflictResolution enum has expected values"""
    assert ConflictResolution.LAST_WRITER_WINS.value == "last_writer_wins"
    assert ConflictResolution.FIRST_WRITER_WINS.value == "first_writer_wins"
    assert ConflictResolution.MERGE_VALUES.value == "merge_values"
    assert ConflictResolution.MANUAL_RESOLUTION.value == "manual_resolution"
    assert ConflictResolution.PRIORITY_BASED.value == "priority_based"


@pytest.mark.asyncio
async def test_subscription_management():
    """Test subscription and unsubscription functionality"""
    mock_context_manager = Mock()
    config = {"batch_sync_interval": 1.0}
    
    synchronizer = ContextSynchronizer(mock_context_manager, config)
    
    # Test subscription
    result = await synchronizer.subscribe_to_context("cost_management_1", ["budget_alert", "cost_threshold"])
    assert result is True
    assert "cost_management_1" in synchronizer.sync_subscriptions
    assert "budget_alert" in synchronizer.sync_subscriptions["cost_management_1"]
    assert "cost_threshold" in synchronizer.sync_subscriptions["cost_management_1"]
    
    # Test unsubscription
    result = await synchronizer.unsubscribe_from_context("cost_management_1", ["budget_alert"])
    assert result is True
    assert "budget_alert" not in synchronizer.sync_subscriptions["cost_management_1"]
    assert "cost_threshold" in synchronizer.sync_subscriptions["cost_management_1"]


@pytest.mark.asyncio
async def test_isolation_policy_application():
    """Test context isolation policy application"""
    mock_context_manager = Mock()
    config = {"batch_sync_interval": 1.0}
    
    synchronizer = ContextSynchronizer(mock_context_manager, config)
    
    # Apply high isolation policy
    result = await synchronizer.apply_context_isolation_policy("user_interface_1", "high")
    assert result is True
    
    # Verify policy is stored
    policies = getattr(synchronizer, '_agent_isolation_policies', {})
    assert "user_interface_1" in policies
    assert policies["user_interface_1"]["level"] == "high"
    assert policies["user_interface_1"]["policy"]["context_encryption"] is True
    assert policies["user_interface_1"]["policy"]["cross_agent_access"] is False


@pytest.mark.asyncio
async def test_cross_agent_access_validation():
    """Test cross-agent access validation"""
    mock_context_manager = Mock()
    config = {"batch_sync_interval": 1.0}
    
    synchronizer = ContextSynchronizer(mock_context_manager, config)
    
    # Apply isolation policies
    await synchronizer.apply_context_isolation_policy("user_interface_1", "high")
    await synchronizer.apply_context_isolation_policy("cost_management_1", "domain")
    await synchronizer.apply_context_isolation_policy("forecasting_1", "domain")
    
    # Test high isolation - should deny access
    access_allowed = await synchronizer.validate_cross_agent_access(
        "cost_management_1", "user_interface_1", ["ui_preferences"]
    )
    assert access_allowed is False
    
    # Test that isolation policies are properly stored
    policies = getattr(synchronizer, '_agent_isolation_policies', {})
    assert len(policies) >= 2  # At least user_interface_1 and cost_management_1


def test_agent_conflict_authority():
    """Test agent conflict resolution authority"""
    mock_context_manager = Mock()
    config = {"batch_sync_interval": 1.0}
    
    synchronizer = ContextSynchronizer(mock_context_manager, config)
    
    # Test authority agents
    assert synchronizer._agent_has_conflict_authority("orchestrator") is True
    assert synchronizer._agent_has_conflict_authority("approval") is True
    assert synchronizer._agent_has_conflict_authority("alert_management") is True
    
    # Test non-authority agents
    assert synchronizer._agent_has_conflict_authority("user_interface") is False
    assert synchronizer._agent_has_conflict_authority("cost_management") is False


def test_sync_statistics():
    """Test synchronization statistics collection"""
    mock_context_manager = Mock()
    config = {"batch_sync_interval": 1.0}
    
    synchronizer = ContextSynchronizer(mock_context_manager, config)
    
    # Get initial statistics
    stats = synchronizer.get_sync_stats()
    
    assert "active_operations" in stats
    assert "pending_changes" in stats
    assert "subscriptions" in stats
    assert "operations_by_status" in stats
    assert "conflicts_detected" in stats
    assert "checkpoints_created" in stats
    assert "conflict_resolution_methods" in stats
    assert "agent_sync_activity" in stats
    
    # Initial values should be zero/empty
    assert stats["active_operations"] == 0
    assert stats["pending_changes"] == 0
    assert stats["conflicts_detected"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])