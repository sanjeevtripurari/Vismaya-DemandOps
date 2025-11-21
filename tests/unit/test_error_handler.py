"""
Unit tests for Agent Error Handler and Graceful Degradation
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from src.agentic.core.error_handler import (
    AgentErrorHandler, ErrorType, CircuitBreaker, CircuitBreakerConfig,
    RetryPolicy, ErrorRecord, FallbackStrategy, create_error_handler
)
from src.agentic.core.graceful_degradation import (
    GracefulDegradationManager, ServiceLevel, FeatureCategory, Feature,
    DegradationRule, create_graceful_degradation_manager
)
from src.agentic.core.models import AgentStatus, SystemHealth


class TestRetryPolicy:
    """Test retry policy functionality"""
    
    def test_retry_policy_creation(self):
        """Test retry policy creation with defaults"""
        policy = RetryPolicy()
        
        assert policy.max_attempts == 3
        assert policy.base_delay_seconds == 1.0
        assert policy.jitter is True
        assert ErrorType.CONNECTION_ERROR in policy.retry_on_errors
    
    def test_calculate_delay(self):
        """Test delay calculation with exponential backoff"""
        policy = RetryPolicy(base_delay_seconds=2.0, exponential_base=2.0, jitter=False)
        
        assert policy.calculate_delay(0) == 2.0
        assert policy.calculate_delay(1) == 4.0
        assert policy.calculate_delay(2) == 8.0
    
    def test_calculate_delay_with_max(self):
        """Test delay calculation with maximum limit"""
        policy = RetryPolicy(base_delay_seconds=10.0, max_delay_seconds=15.0, jitter=False)
        
        assert policy.calculate_delay(0) == 10.0
        assert policy.calculate_delay(1) == 15.0  # Capped at max
        assert policy.calculate_delay(2) == 15.0  # Still capped
    
    def test_should_retry(self):
        """Test retry decision logic"""
        policy = RetryPolicy(max_attempts=3, retry_on_errors=[ErrorType.CONNECTION_ERROR])
        
        assert policy.should_retry(ErrorType.CONNECTION_ERROR, 0) is True
        assert policy.should_retry(ErrorType.CONNECTION_ERROR, 2) is True
        assert policy.should_retry(ErrorType.CONNECTION_ERROR, 3) is False
        assert policy.should_retry(ErrorType.AUTHENTICATION_ERROR, 0) is False


class TestCircuitBreaker:
    """Test circuit breaker functionality"""
    
    def test_circuit_breaker_creation(self):
        """Test circuit breaker creation"""
        config = CircuitBreakerConfig(failure_threshold=3, recovery_timeout_seconds=30)
        breaker = CircuitBreaker("test_service", config)
        
        assert breaker.service_name == "test_service"
        assert breaker.state.value == "closed"
        assert breaker.failure_count == 0
    
    def test_circuit_breaker_failure_tracking(self):
        """Test failure tracking and state transitions"""
        config = CircuitBreakerConfig(failure_threshold=2)
        breaker = CircuitBreaker("test_service", config)
        
        # Initially closed and can execute
        assert breaker.can_execute() is True
        
        # Record failures
        breaker.record_failure()
        assert breaker.failure_count == 1
        assert breaker.can_execute() is True  # Still closed
        
        breaker.record_failure()
        assert breaker.failure_count == 2
        assert breaker.state.value == "open"
        assert breaker.can_execute() is False  # Now open
    
    def test_circuit_breaker_recovery(self):
        """Test circuit breaker recovery after timeout"""
        config = CircuitBreakerConfig(failure_threshold=1, recovery_timeout_seconds=0)
        breaker = CircuitBreaker("test_service", config)
        
        # Trigger failure
        breaker.record_failure()
        assert breaker.state.value == "open"
        
        # Simulate timeout passage
        breaker.last_failure_time = datetime.now() - timedelta(seconds=1)
        
        # Should transition to half-open
        assert breaker.can_execute() is True
        assert breaker.state.value == "half_open"
    
    def test_circuit_breaker_half_open_success(self):
        """Test successful recovery from half-open state"""
        config = CircuitBreakerConfig(failure_threshold=1, success_threshold=2)
        breaker = CircuitBreaker("test_service", config)
        
        # Force to half-open state
        breaker.state = breaker.state.HALF_OPEN
        
        # Record successes
        breaker.record_success()
        assert breaker.success_count == 1
        assert breaker.state.value == "half_open"
        
        breaker.record_success()
        assert breaker.success_count == 2
        assert breaker.state.value == "closed"  # Should close after threshold


class TestAgentErrorHandler:
    """Test agent error handler functionality"""
    
    @pytest.fixture
    def error_handler(self):
        """Create error handler for testing"""
        config = {
            "retry_policies": {
                "test_agent": {
                    "max_attempts": 2,
                    "base_delay_seconds": 0.1
                }
            },
            "circuit_breakers": {
                "test_service": {
                    "failure_threshold": 2,
                    "recovery_timeout_seconds": 1
                }
            }
        }
        return AgentErrorHandler(config)
    
    def test_error_classification(self, error_handler):
        """Test error classification"""
        # Connection error
        conn_error = ConnectionError("Connection failed")
        assert error_handler._classify_error(conn_error) == ErrorType.CONNECTION_ERROR
        
        # Timeout error
        timeout_error = TimeoutError("Request timed out")
        assert error_handler._classify_error(timeout_error) == ErrorType.TIMEOUT_ERROR
        
        # Authentication error
        auth_error = Exception("Authentication failed")
        assert error_handler._classify_error(auth_error) == ErrorType.AUTHENTICATION_ERROR
        
        # Unknown error
        unknown_error = ValueError("Some validation error")
        assert error_handler._classify_error(unknown_error) == ErrorType.VALIDATION_ERROR
    
    @pytest.mark.asyncio
    async def test_handle_agent_failure(self, error_handler):
        """Test agent failure handling"""
        agent_id = "test_agent"
        error = ConnectionError("Connection lost")
        
        # Mock the recovery handler
        with patch.object(error_handler, '_handle_connection_error', return_value=True):
            result = await error_handler.handle_agent_failure(agent_id, error)
            
            assert result is True
            assert agent_id in error_handler.error_history
            assert len(error_handler.error_history[agent_id]) == 1
            assert error_handler.agent_failure_counts[agent_id] == 1
    
    @pytest.mark.asyncio
    async def test_retry_with_backoff_success(self, error_handler):
        """Test successful retry with backoff"""
        agent_id = "test_agent"
        action = "test_action"
        parameters = {"param": "value"}
        
        # Mock successful execution on second attempt
        call_count = 0
        async def mock_execute(aid, act, params):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionError("First attempt fails")
            return {"success": True}
        
        with patch.object(error_handler, '_execute_agent_action', side_effect=mock_execute):
            result = await error_handler.retry_with_backoff(agent_id, action, parameters)
            
            assert result["success"] is True
            assert result["attempts"] == 2
    
    @pytest.mark.asyncio
    async def test_retry_with_backoff_failure(self, error_handler):
        """Test retry failure after max attempts"""
        agent_id = "test_agent"
        action = "test_action"
        parameters = {"param": "value"}
        
        # Mock always failing execution
        async def mock_execute(aid, act, params):
            raise ConnectionError("Always fails")
        
        with patch.object(error_handler, '_execute_agent_action', side_effect=mock_execute):
            result = await error_handler.retry_with_backoff(agent_id, action, parameters)
            
            assert result["success"] is False
            assert result["attempts"] == 2  # Max attempts from config
    
    @pytest.mark.asyncio
    async def test_apply_fallback_strategy(self, error_handler):
        """Test fallback strategy application"""
        agent_id = "cost_management"
        failed_action = "get_costs"
        
        result = await error_handler.apply_fallback_strategy(agent_id, failed_action)
        
        # Should succeed with cached data fallback
        assert result["success"] is True
        assert "fallback_strategy" in result
    
    def test_get_error_statistics(self, error_handler):
        """Test error statistics generation"""
        # Add some test errors
        error1 = ErrorRecord(
            error_id="1",
            agent_id="agent1",
            error_type=ErrorType.CONNECTION_ERROR,
            error_message="Connection failed",
            context={},
            timestamp=datetime.now()
        )
        
        error2 = ErrorRecord(
            error_id="2",
            agent_id="agent1",
            error_type=ErrorType.TIMEOUT_ERROR,
            error_message="Timeout",
            context={},
            timestamp=datetime.now()
        )
        
        error_handler._record_error(error1)
        error_handler._record_error(error2)
        error_handler.total_errors_handled = 2
        error_handler.successful_recoveries = 1
        
        stats = error_handler.get_error_statistics()
        
        assert stats["total_errors_handled"] == 2
        assert stats["successful_recoveries"] == 1
        assert stats["recovery_success_rate"] == 50.0
        assert "agent1" in stats["agent_error_counts"]
        assert stats["agent_error_counts"]["agent1"] == 2


class TestGracefulDegradationManager:
    """Test graceful degradation manager"""
    
    @pytest.fixture
    def degradation_manager(self):
        """Create degradation manager for testing"""
        config = {
            "features": {
                "test_feature": {
                    "category": "important",
                    "dependencies": [],
                    "resource_cost": 2.0,
                    "user_impact": 5.0
                }
            }
        }
        return GracefulDegradationManager(config)
    
    def test_feature_initialization(self, degradation_manager):
        """Test feature initialization"""
        assert "user_authentication" in degradation_manager.features
        assert "test_feature" in degradation_manager.features
        
        auth_feature = degradation_manager.features["user_authentication"]
        assert auth_feature.category == FeatureCategory.CRITICAL
        assert auth_feature.enabled is True
        assert auth_feature.degraded is False
    
    def test_dependency_graph(self, degradation_manager):
        """Test dependency graph building"""
        # Check that features with dependencies have them tracked
        assert "basic_cost_tracking" in degradation_manager.feature_dependencies
        deps = degradation_manager.feature_dependencies["basic_cost_tracking"]
        assert "user_authentication" in deps
    
    @pytest.mark.asyncio
    async def test_disable_feature(self, degradation_manager):
        """Test feature disabling"""
        feature_name = "advanced_analytics"
        
        # Initially enabled
        assert degradation_manager.features[feature_name].enabled is True
        
        # Disable feature
        await degradation_manager._disable_feature(feature_name)
        
        # Should be disabled
        assert degradation_manager.features[feature_name].enabled is False
    
    @pytest.mark.asyncio
    async def test_degrade_feature(self, degradation_manager):
        """Test feature degradation"""
        feature_name = "real_time_monitoring"
        
        # Initially not degraded
        assert degradation_manager.features[feature_name].degraded is False
        
        # Degrade feature
        await degradation_manager._degrade_feature(feature_name)
        
        # Should be degraded
        assert degradation_manager.features[feature_name].degraded is True
    
    def test_condition_evaluation(self, degradation_manager):
        """Test condition evaluation"""
        conditions = {
            "cpu_usage": 85,
            "memory_usage": 70,
            "failed_agents": 2
        }
        
        # Test simple condition
        assert degradation_manager._evaluate_condition("cpu_usage > 80", conditions) is True
        assert degradation_manager._evaluate_condition("cpu_usage < 80", conditions) is False
        
        # Test compound condition
        assert degradation_manager._evaluate_condition("cpu_usage > 80 and failed_agents >= 2", conditions) is True
        assert degradation_manager._evaluate_condition("cpu_usage > 90 or failed_agents >= 2", conditions) is True
    
    @pytest.mark.asyncio
    async def test_force_service_level(self, degradation_manager):
        """Test forcing service level"""
        # Initially at full service
        assert degradation_manager.current_service_level == ServiceLevel.FULL
        
        # Force to minimal
        result = await degradation_manager.force_service_level(ServiceLevel.MINIMAL)
        
        assert result is True
        assert degradation_manager.current_service_level == ServiceLevel.MINIMAL
        
        # Check that optional features are disabled
        optional_features = [name for name, feature in degradation_manager.features.items() 
                           if feature.category == FeatureCategory.OPTIONAL]
        
        for feature_name in optional_features:
            assert degradation_manager.features[feature_name].enabled is False
    
    def test_get_current_status(self, degradation_manager):
        """Test status reporting"""
        status = degradation_manager.get_current_status()
        
        assert "service_level" in status
        assert "enabled_features" in status
        assert "disabled_features" in status
        assert "feature_breakdown" in status
        
        assert status["service_level"] == "full"
        assert len(status["enabled_features"]) > 0
    
    def test_get_feature_status(self, degradation_manager):
        """Test individual feature status"""
        feature_status = degradation_manager.get_feature_status("user_authentication")
        
        assert feature_status is not None
        assert feature_status["name"] == "user_authentication"
        assert feature_status["category"] == "critical"
        assert feature_status["enabled"] is True
        assert feature_status["degraded"] is False
    
    @pytest.mark.asyncio
    async def test_system_state_update(self, degradation_manager):
        """Test system state update triggering degradation"""
        # Create system health indicating problems
        system_health = SystemHealth(
            overall_status="degraded",
            agent_statuses={"cost_management": "error", "forecasting": "active"}
        )
        
        agent_statuses = {
            "cost_management": AgentStatus.ERROR,
            "forecasting": AgentStatus.ACTIVE
        }
        
        resource_utilization = {
            "cpu_usage": 85,
            "memory_usage": 75,
            "error_rate": 15
        }
        
        # Mock rule evaluation to avoid complex setup
        with patch.object(degradation_manager, '_evaluate_degradation_rules'):
            await degradation_manager.update_system_state(
                system_health, agent_statuses, resource_utilization
            )
            
            assert degradation_manager.system_health == system_health
            assert degradation_manager.agent_statuses == agent_statuses
            assert degradation_manager.resource_utilization == resource_utilization


class TestIntegration:
    """Integration tests for error handling and degradation"""
    
    @pytest.mark.asyncio
    async def test_error_handler_with_degradation(self):
        """Test error handler triggering degradation"""
        # Create both components
        error_handler = create_error_handler()
        degradation_manager = create_graceful_degradation_manager()
        
        # Simulate multiple agent failures
        for i in range(3):
            await error_handler.handle_agent_failure(f"agent_{i}", ConnectionError("Failed"))
        
        # Check that errors were recorded
        assert error_handler.total_errors_handled == 3
        
        # Simulate system state that would trigger degradation
        system_health = SystemHealth(overall_status="degraded")
        agent_statuses = {f"agent_{i}": AgentStatus.ERROR for i in range(3)}
        resource_utilization = {"cpu_usage": 90, "memory_usage": 85}
        
        # Update degradation manager (would normally be triggered by orchestrator)
        with patch.object(degradation_manager, '_evaluate_degradation_rules'):
            await degradation_manager.update_system_state(
                system_health, agent_statuses, resource_utilization
            )
    
    def test_factory_functions(self):
        """Test factory functions create valid instances"""
        error_handler = create_error_handler()
        assert isinstance(error_handler, AgentErrorHandler)
        assert len(error_handler.retry_policies) > 0
        assert len(error_handler.circuit_breakers) > 0
        
        degradation_manager = create_graceful_degradation_manager()
        assert isinstance(degradation_manager, GracefulDegradationManager)
        assert len(degradation_manager.features) > 0
        assert len(degradation_manager.degradation_rules) > 0


if __name__ == "__main__":
    pytest.main([__file__])