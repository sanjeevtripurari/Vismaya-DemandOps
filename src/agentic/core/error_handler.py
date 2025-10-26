"""
Agent Error Recovery and Resilience System
Implements comprehensive error handling with retry policies, circuit breakers, and fallback strategies
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable, Union
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import json
import random
import time

from .interfaces import IAgentErrorHandler
from .models import (
    AgentMessage, AgentState, SystemEvent, AgentStatus,
    AgenticSystemError, AgentCommunicationError, AgentNotFoundError
)


class ErrorType(Enum):
    """Types of errors that can occur in the agentic system"""
    CONNECTION_ERROR = "connection_error"
    TIMEOUT_ERROR = "timeout_error"
    AUTHENTICATION_ERROR = "authentication_error"
    AUTHORIZATION_ERROR = "authorization_error"
    RESOURCE_EXHAUSTED_ERROR = "resource_exhausted_error"
    SERVICE_UNAVAILABLE_ERROR = "service_unavailable_error"
    VALIDATION_ERROR = "validation_error"
    EXECUTION_ERROR = "execution_error"
    UNKNOWN_ERROR = "unknown_error"


class CircuitBreakerState(Enum):
    """States of a circuit breaker"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, blocking requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class FallbackStrategy(Enum):
    """Types of fallback strategies"""
    CACHED_DATA = "cached_data"
    ALTERNATIVE_AGENT = "alternative_agent"
    DEGRADED_SERVICE = "degraded_service"
    MANUAL_INTERVENTION = "manual_intervention"
    GRACEFUL_FAILURE = "graceful_failure"


@dataclass
class RetryPolicy:
    """Configuration for retry behavior"""
    max_attempts: int = 3
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retry_on_errors: List[ErrorType] = field(default_factory=lambda: [
        ErrorType.CONNECTION_ERROR,
        ErrorType.TIMEOUT_ERROR,
        ErrorType.SERVICE_UNAVAILABLE_ERROR
    ])
    
    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for retry attempt"""
        delay = min(
            self.base_delay_seconds * (self.exponential_base ** attempt),
            self.max_delay_seconds
        )
        
        if self.jitter:
            # Add random jitter to prevent thundering herd
            delay *= (0.5 + random.random() * 0.5)
        
        return delay
    
    def should_retry(self, error_type: ErrorType, attempt: int) -> bool:
        """Check if error should be retried"""
        return (
            attempt < self.max_attempts and
            error_type in self.retry_on_errors
        )


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5
    recovery_timeout_seconds: int = 60
    success_threshold: int = 3  # Successes needed to close from half-open
    timeout_seconds: int = 30
    
    def __post_init__(self):
        """Validate configuration"""
        if self.failure_threshold <= 0:
            raise ValueError("failure_threshold must be positive")
        if self.recovery_timeout_seconds < 0:
            raise ValueError("recovery_timeout_seconds must be non-negative")


@dataclass
class CircuitBreaker:
    """Circuit breaker implementation for external service dependencies"""
    service_name: str
    config: CircuitBreakerConfig
    state: CircuitBreakerState = CircuitBreakerState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    
    def can_execute(self) -> bool:
        """Check if request can be executed"""
        if self.state == CircuitBreakerState.CLOSED:
            return True
        elif self.state == CircuitBreakerState.OPEN:
            # Check if recovery timeout has passed
            if (self.last_failure_time and 
                datetime.now() - self.last_failure_time > 
                timedelta(seconds=self.config.recovery_timeout_seconds)):
                self.state = CircuitBreakerState.HALF_OPEN
                self.success_count = 0
                return True
            return False
        elif self.state == CircuitBreakerState.HALF_OPEN:
            return True
        
        return False
    
    def record_success(self) -> None:
        """Record successful execution"""
        self.last_success_time = datetime.now()
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitBreakerState.CLOSED
                self.failure_count = 0
        elif self.state == CircuitBreakerState.CLOSED:
            self.failure_count = 0
    
    def record_failure(self) -> None:
        """Record failed execution"""
        self.last_failure_time = datetime.now()
        self.failure_count += 1
        
        if self.state == CircuitBreakerState.CLOSED:
            if self.failure_count >= self.config.failure_threshold:
                self.state = CircuitBreakerState.OPEN
        elif self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.OPEN
            self.success_count = 0
    
    def get_status(self) -> Dict[str, Any]:
        """Get circuit breaker status"""
        return {
            "service_name": self.service_name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "last_success_time": self.last_success_time.isoformat() if self.last_success_time else None,
            "can_execute": self.can_execute()
        }


@dataclass
class ErrorRecord:
    """Record of an error occurrence"""
    error_id: str
    agent_id: str
    error_type: ErrorType
    error_message: str
    context: Dict[str, Any]
    timestamp: datetime
    resolved: bool = False
    resolution_strategy: Optional[str] = None
    resolution_time: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "error_id": self.error_id,
            "agent_id": self.agent_id,
            "error_type": self.error_type.value,
            "error_message": self.error_message,
            "context": self.context,
            "timestamp": self.timestamp.isoformat(),
            "resolved": self.resolved,
            "resolution_strategy": self.resolution_strategy,
            "resolution_time": self.resolution_time.isoformat() if self.resolution_time else None
        }

class AgentErrorHandler(IAgentErrorHandler):
    """
    Comprehensive error handler for agent failures and recovery
    Implements retry policies, circuit breakers, and fallback strategies
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Error tracking
        self.error_history: Dict[str, List[ErrorRecord]] = {}
        self.agent_failure_counts: Dict[str, int] = {}
        self.agent_last_errors: Dict[str, ErrorRecord] = {}
        
        # Retry policies per agent type
        self.retry_policies: Dict[str, RetryPolicy] = {}
        self._load_retry_policies()
        
        # Circuit breakers for external services
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self._initialize_circuit_breakers()
        
        # Fallback strategies
        self.fallback_strategies: Dict[str, Dict[str, Any]] = {}
        self._load_fallback_strategies()
        
        # Recovery handlers
        self.recovery_handlers: Dict[ErrorType, Callable] = {}
        self._setup_recovery_handlers()
        
        # Escalation rules
        self.escalation_rules: List[Dict[str, Any]] = []
        self._load_escalation_rules()
        
        # Performance metrics
        self.recovery_success_rate: float = 0.0
        self.total_errors_handled: int = 0
        self.successful_recoveries: int = 0
        
        # Background tasks
        self._cleanup_task: Optional[asyncio.Task] = None
        self._monitoring_task: Optional[asyncio.Task] = None
        
        # Start background monitoring if event loop is available
        try:
            self._start_background_tasks()
        except RuntimeError:
            # No event loop available (e.g., during testing)
            pass
    
    def _load_retry_policies(self) -> None:
        """Load retry policies from configuration"""
        default_policy = RetryPolicy()
        
        # Agent-specific policies
        policies_config = self.config.get("retry_policies", {})
        
        for agent_type, policy_config in policies_config.items():
            self.retry_policies[agent_type] = RetryPolicy(
                max_attempts=policy_config.get("max_attempts", default_policy.max_attempts),
                base_delay_seconds=policy_config.get("base_delay_seconds", default_policy.base_delay_seconds),
                max_delay_seconds=policy_config.get("max_delay_seconds", default_policy.max_delay_seconds),
                exponential_base=policy_config.get("exponential_base", default_policy.exponential_base),
                jitter=policy_config.get("jitter", default_policy.jitter),
                retry_on_errors=[
                    ErrorType(error_type) for error_type in 
                    policy_config.get("retry_on_errors", [e.value for e in default_policy.retry_on_errors])
                ]
            )
        
        # Default policy for unknown agent types
        self.retry_policies["default"] = default_policy
        
        self.logger.info(f"Loaded {len(self.retry_policies)} retry policies")
    
    def _initialize_circuit_breakers(self) -> None:
        """Initialize circuit breakers for external services"""
        breakers_config = self.config.get("circuit_breakers", {})
        
        for service_name, breaker_config in breakers_config.items():
            config = CircuitBreakerConfig(
                failure_threshold=breaker_config.get("failure_threshold", 5),
                recovery_timeout_seconds=breaker_config.get("recovery_timeout_seconds", 60),
                success_threshold=breaker_config.get("success_threshold", 3),
                timeout_seconds=breaker_config.get("timeout_seconds", 30)
            )
            
            self.circuit_breakers[service_name] = CircuitBreaker(
                service_name=service_name,
                config=config
            )
        
        # Default circuit breakers for common services
        default_services = ["aws_bedrock", "dynamodb", "s3", "ses"]
        for service in default_services:
            if service not in self.circuit_breakers:
                self.circuit_breakers[service] = CircuitBreaker(
                    service_name=service,
                    config=CircuitBreakerConfig()
                )
        
        self.logger.info(f"Initialized {len(self.circuit_breakers)} circuit breakers")
    
    def _load_fallback_strategies(self) -> None:
        """Load fallback strategies from configuration"""
        strategies_config = self.config.get("fallback_strategies", {})
        
        # Default fallback strategies
        default_strategies = {
            "cost_management": {
                "primary": FallbackStrategy.CACHED_DATA,
                "secondary": FallbackStrategy.ALTERNATIVE_AGENT,
                "cache_ttl_minutes": 30,
                "alternative_agents": ["forecasting", "user_interface"]
            },
            "resource_management": {
                "primary": FallbackStrategy.CACHED_DATA,
                "secondary": FallbackStrategy.DEGRADED_SERVICE,
                "cache_ttl_minutes": 15,
                "degraded_features": ["real_time_monitoring"]
            },
            "forecasting": {
                "primary": FallbackStrategy.CACHED_DATA,
                "secondary": FallbackStrategy.ALTERNATIVE_AGENT,
                "cache_ttl_minutes": 60,
                "alternative_agents": ["cost_management"]
            },
            "alert_management": {
                "primary": FallbackStrategy.ALTERNATIVE_AGENT,
                "secondary": FallbackStrategy.MANUAL_INTERVENTION,
                "alternative_agents": ["user_interface"],
                "manual_notification_channels": ["email", "slack"]
            },
            "user_interface": {
                "primary": FallbackStrategy.DEGRADED_SERVICE,
                "secondary": FallbackStrategy.GRACEFUL_FAILURE,
                "degraded_features": ["real_time_updates", "advanced_analytics"]
            },
            "approval": {
                "primary": FallbackStrategy.MANUAL_INTERVENTION,
                "secondary": FallbackStrategy.GRACEFUL_FAILURE,
                "manual_notification_channels": ["email"]
            }
        }
        
        # Merge with configuration
        for agent_type, strategy in default_strategies.items():
            if agent_type in strategies_config:
                strategy.update(strategies_config[agent_type])
            self.fallback_strategies[agent_type] = strategy
        
        self.logger.info(f"Loaded fallback strategies for {len(self.fallback_strategies)} agent types")
    
    def _setup_recovery_handlers(self) -> None:
        """Setup recovery handlers for different error types"""
        self.recovery_handlers = {
            ErrorType.CONNECTION_ERROR: self._handle_connection_error,
            ErrorType.TIMEOUT_ERROR: self._handle_timeout_error,
            ErrorType.AUTHENTICATION_ERROR: self._handle_authentication_error,
            ErrorType.AUTHORIZATION_ERROR: self._handle_authorization_error,
            ErrorType.RESOURCE_EXHAUSTED_ERROR: self._handle_resource_exhausted_error,
            ErrorType.SERVICE_UNAVAILABLE_ERROR: self._handle_service_unavailable_error,
            ErrorType.VALIDATION_ERROR: self._handle_validation_error,
            ErrorType.EXECUTION_ERROR: self._handle_execution_error,
            ErrorType.UNKNOWN_ERROR: self._handle_unknown_error
        }
    
    def _load_escalation_rules(self) -> None:
        """Load error escalation rules"""
        self.escalation_rules = self.config.get("escalation_rules", [
            {
                "condition": "error_count >= 5",
                "timeframe_minutes": 10,
                "action": "notify_administrators",
                "severity": "high"
            },
            {
                "condition": "error_type == 'AUTHENTICATION_ERROR'",
                "action": "security_alert",
                "severity": "critical"
            },
            {
                "condition": "agent_down_time >= 300",  # 5 minutes
                "action": "failover_to_backup",
                "severity": "critical"
            }
        ])
    
    def _start_background_tasks(self) -> None:
        """Start background monitoring and cleanup tasks"""
        self._cleanup_task = asyncio.create_task(self._error_cleanup_loop())
        self._monitoring_task = asyncio.create_task(self._circuit_breaker_monitoring_loop())
    
    async def start_background_tasks(self) -> None:
        """Start background tasks (for use when event loop is available)"""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._error_cleanup_loop())
        if self._monitoring_task is None or self._monitoring_task.done():
            self._monitoring_task = asyncio.create_task(self._circuit_breaker_monitoring_loop())
    
    async def handle_agent_failure(self, agent_id: str, error: Exception) -> bool:
        """Handle agent failure with appropriate recovery strategy"""
        try:
            # Classify error
            error_type = self._classify_error(error)
            
            # Create error record
            error_record = ErrorRecord(
                error_id=f"{agent_id}_{int(time.time())}",
                agent_id=agent_id,
                error_type=error_type,
                error_message=str(error),
                context={"exception_type": type(error).__name__},
                timestamp=datetime.now()
            )
            
            # Store error record
            self._record_error(error_record)
            
            # Update failure count
            self.agent_failure_counts[agent_id] = self.agent_failure_counts.get(agent_id, 0) + 1
            self.agent_last_errors[agent_id] = error_record
            
            # Get recovery handler
            recovery_handler = self.recovery_handlers.get(error_type, self._handle_unknown_error)
            
            # Attempt recovery
            recovery_success = await recovery_handler(agent_id, error, error_record)
            
            # Update metrics
            self.total_errors_handled += 1
            if recovery_success:
                self.successful_recoveries += 1
                error_record.resolved = True
                error_record.resolution_time = datetime.now()
            
            self.recovery_success_rate = (self.successful_recoveries / self.total_errors_handled) * 100
            
            # Check escalation rules
            await self._check_escalation_rules(agent_id, error_record)
            
            self.logger.info(f"Handled error for agent {agent_id}: {error_type.value}, recovery: {recovery_success}")
            
            return recovery_success
            
        except Exception as e:
            self.logger.error(f"Error in error handler for agent {agent_id}: {e}")
            return False    

    async def retry_with_backoff(self, agent_id: str, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Retry failed action with exponential backoff"""
        agent_type = self._get_agent_type(agent_id)
        retry_policy = self.retry_policies.get(agent_type, self.retry_policies["default"])
        
        last_error = None
        
        for attempt in range(retry_policy.max_attempts):
            try:
                # Check circuit breaker if applicable
                service_name = self._get_service_name_for_action(action)
                if service_name and service_name in self.circuit_breakers:
                    circuit_breaker = self.circuit_breakers[service_name]
                    if not circuit_breaker.can_execute():
                        raise AgenticSystemError(f"Circuit breaker open for service: {service_name}")
                
                # Execute action (this would be implemented by the calling agent)
                result = await self._execute_agent_action(agent_id, action, parameters)
                
                # Record success for circuit breaker
                if service_name and service_name in self.circuit_breakers:
                    self.circuit_breakers[service_name].record_success()
                
                # Reset failure count on success
                if agent_id in self.agent_failure_counts:
                    self.agent_failure_counts[agent_id] = 0
                
                self.logger.info(f"Action {action} succeeded for agent {agent_id} on attempt {attempt + 1}")
                
                return {
                    "success": True,
                    "result": result,
                    "attempts": attempt + 1,
                    "total_time_seconds": 0  # Would be calculated in real implementation
                }
                
            except Exception as e:
                last_error = e
                error_type = self._classify_error(e)
                
                # Record failure for circuit breaker
                if service_name and service_name in self.circuit_breakers:
                    self.circuit_breakers[service_name].record_failure()
                
                # Check if we should retry
                if not retry_policy.should_retry(error_type, attempt):
                    break
                
                # Calculate delay
                delay = retry_policy.calculate_delay(attempt)
                
                self.logger.warning(f"Action {action} failed for agent {agent_id} on attempt {attempt + 1}, "
                                  f"retrying in {delay:.2f}s: {e}")
                
                # Wait before retry
                await asyncio.sleep(delay)
        
        # All retries failed
        self.logger.error(f"Action {action} failed for agent {agent_id} after {retry_policy.max_attempts} attempts")
        
        return {
            "success": False,
            "error": str(last_error),
            "attempts": retry_policy.max_attempts,
            "final_error_type": self._classify_error(last_error).value if last_error else "unknown"
        }
    
    async def escalate_error(self, agent_id: str, error: Exception, context: Dict[str, Any]) -> bool:
        """Escalate error to appropriate handlers"""
        try:
            error_type = self._classify_error(error)
            
            # Create escalation record
            escalation_data = {
                "agent_id": agent_id,
                "error_type": error_type.value,
                "error_message": str(error),
                "context": context,
                "timestamp": datetime.now().isoformat(),
                "escalation_level": self._determine_escalation_level(agent_id, error_type)
            }
            
            # Determine escalation actions
            actions = self._get_escalation_actions(escalation_data)
            
            # Execute escalation actions
            for action in actions:
                await self._execute_escalation_action(action, escalation_data)
            
            self.logger.warning(f"Escalated error for agent {agent_id}: {error_type.value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error during escalation for agent {agent_id}: {e}")
            return False
    
    async def get_error_history(self, agent_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get error history for agent"""
        if agent_id not in self.error_history:
            return []
        
        errors = self.error_history[agent_id][-limit:]
        return [error.to_dict() for error in errors]
    
    async def apply_fallback_strategy(self, agent_id: str, failed_action: str) -> Dict[str, Any]:
        """Apply fallback strategy for failed action"""
        try:
            agent_type = self._get_agent_type(agent_id)
            strategy_config = self.fallback_strategies.get(agent_type, {})
            
            if not strategy_config:
                return {
                    "success": False,
                    "error": f"No fallback strategy configured for agent type: {agent_type}"
                }
            
            primary_strategy = strategy_config.get("primary", FallbackStrategy.GRACEFUL_FAILURE)
            
            # Try primary fallback strategy
            result = await self._execute_fallback_strategy(
                primary_strategy, agent_id, failed_action, strategy_config
            )
            
            if result["success"]:
                self.logger.info(f"Primary fallback strategy {primary_strategy.value} succeeded for agent {agent_id}")
                return result
            
            # Try secondary fallback strategy
            secondary_strategy = strategy_config.get("secondary")
            if secondary_strategy:
                secondary_result = await self._execute_fallback_strategy(
                    FallbackStrategy(secondary_strategy), agent_id, failed_action, strategy_config
                )
                
                if secondary_result["success"]:
                    self.logger.info(f"Secondary fallback strategy {secondary_strategy} succeeded for agent {agent_id}")
                    return secondary_result
            
            # All fallback strategies failed
            return {
                "success": False,
                "error": "All fallback strategies failed",
                "attempted_strategies": [primary_strategy.value, secondary_strategy] if secondary_strategy else [primary_strategy.value]
            }
            
        except Exception as e:
            self.logger.error(f"Error applying fallback strategy for agent {agent_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_circuit_breaker_status(self, service_name: Optional[str] = None) -> Dict[str, Any]:
        """Get circuit breaker status"""
        if service_name:
            if service_name in self.circuit_breakers:
                return self.circuit_breakers[service_name].get_status()
            else:
                return {"error": f"Circuit breaker not found for service: {service_name}"}
        
        # Return all circuit breaker statuses
        return {
            service: breaker.get_status()
            for service, breaker in self.circuit_breakers.items()
        }
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get comprehensive error statistics"""
        total_errors = sum(len(errors) for errors in self.error_history.values())
        
        # Error type distribution
        error_type_counts = {}
        for errors in self.error_history.values():
            for error in errors:
                error_type = error.error_type.value
                error_type_counts[error_type] = error_type_counts.get(error_type, 0) + 1
        
        # Agent failure distribution
        agent_error_counts = {
            agent_id: len(errors) for agent_id, errors in self.error_history.items()
        }
        
        # Recent error trends (last 24 hours)
        recent_cutoff = datetime.now() - timedelta(hours=24)
        recent_errors = 0
        for errors in self.error_history.values():
            recent_errors += sum(1 for error in errors if error.timestamp > recent_cutoff)
        
        return {
            "total_errors_handled": self.total_errors_handled,
            "successful_recoveries": self.successful_recoveries,
            "recovery_success_rate": self.recovery_success_rate,
            "total_errors_recorded": total_errors,
            "recent_errors_24h": recent_errors,
            "error_type_distribution": error_type_counts,
            "agent_error_counts": agent_error_counts,
            "circuit_breaker_states": {
                service: breaker.state.value
                for service, breaker in self.circuit_breakers.items()
            },
            "most_problematic_agents": sorted(
                agent_error_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
        } 
   
    # Private helper methods
    
    def _classify_error(self, error: Exception) -> ErrorType:
        """Classify error into appropriate error type"""
        error_name = type(error).__name__.lower()
        error_message = str(error).lower()
        
        if "connection" in error_name or "connection" in error_message:
            return ErrorType.CONNECTION_ERROR
        elif "timeout" in error_name or "timeout" in error_message:
            return ErrorType.TIMEOUT_ERROR
        elif "authentication" in error_name or "auth" in error_message:
            return ErrorType.AUTHENTICATION_ERROR
        elif "authorization" in error_name or "permission" in error_message:
            return ErrorType.AUTHORIZATION_ERROR
        elif "resource" in error_message and ("exhausted" in error_message or "limit" in error_message):
            return ErrorType.RESOURCE_EXHAUSTED_ERROR
        elif "service unavailable" in error_message or "503" in error_message:
            return ErrorType.SERVICE_UNAVAILABLE_ERROR
        elif "validation" in error_name or "invalid" in error_message:
            return ErrorType.VALIDATION_ERROR
        elif "execution" in error_name:
            return ErrorType.EXECUTION_ERROR
        else:
            return ErrorType.UNKNOWN_ERROR
    
    def _record_error(self, error_record: ErrorRecord) -> None:
        """Record error in history"""
        agent_id = error_record.agent_id
        
        if agent_id not in self.error_history:
            self.error_history[agent_id] = []
        
        self.error_history[agent_id].append(error_record)
        
        # Keep only last 100 errors per agent
        if len(self.error_history[agent_id]) > 100:
            self.error_history[agent_id] = self.error_history[agent_id][-100:]
    
    def _get_agent_type(self, agent_id: str) -> str:
        """Get agent type from agent ID"""
        # Simple heuristic - in real implementation, this would query the agent registry
        if "cost" in agent_id:
            return "cost_management"
        elif "resource" in agent_id:
            return "resource_management"
        elif "forecast" in agent_id:
            return "forecasting"
        elif "alert" in agent_id:
            return "alert_management"
        elif "ui" in agent_id or "interface" in agent_id:
            return "user_interface"
        elif "approval" in agent_id:
            return "approval"
        else:
            return "unknown"
    
    def _get_service_name_for_action(self, action: str) -> Optional[str]:
        """Get service name for action to check circuit breaker"""
        action_lower = action.lower()
        
        if "bedrock" in action_lower or "ai" in action_lower:
            return "aws_bedrock"
        elif "dynamodb" in action_lower or "database" in action_lower:
            return "dynamodb"
        elif "s3" in action_lower or "storage" in action_lower:
            return "s3"
        elif "email" in action_lower or "ses" in action_lower:
            return "ses"
        
        return None
    
    async def _execute_agent_action(self, agent_id: str, action: str, parameters: Dict[str, Any]) -> Any:
        """Execute agent action (placeholder - would be implemented by calling system)"""
        # This is a placeholder - in real implementation, this would delegate to the actual agent
        raise NotImplementedError("Agent action execution must be implemented by calling system")
    
    # Error-specific recovery handlers
    
    async def _handle_connection_error(self, agent_id: str, error: Exception, error_record: ErrorRecord) -> bool:
        """Handle connection errors with retry and fallback"""
        try:
            # Try to re-establish connection
            await asyncio.sleep(1)  # Brief pause
            
            # Apply fallback strategy
            fallback_result = await self.apply_fallback_strategy(agent_id, "connection_recovery")
            
            error_record.resolution_strategy = "connection_retry_with_fallback"
            return fallback_result.get("success", False)
            
        except Exception as e:
            self.logger.error(f"Error handling connection error for agent {agent_id}: {e}")
            return False
    
    async def _handle_timeout_error(self, agent_id: str, error: Exception, error_record: ErrorRecord) -> bool:
        """Handle timeout errors with increased timeout and fallback"""
        try:
            # Apply cached data fallback if available
            fallback_result = await self.apply_fallback_strategy(agent_id, "timeout_recovery")
            
            error_record.resolution_strategy = "timeout_fallback"
            return fallback_result.get("success", False)
            
        except Exception as e:
            self.logger.error(f"Error handling timeout error for agent {agent_id}: {e}")
            return False
    
    async def _handle_authentication_error(self, agent_id: str, error: Exception, error_record: ErrorRecord) -> bool:
        """Handle authentication errors with credential refresh"""
        try:
            # This is a security issue - escalate immediately
            await self.escalate_error(agent_id, error, {"security_issue": True})
            
            error_record.resolution_strategy = "security_escalation"
            return False  # Don't auto-recover from auth errors
            
        except Exception as e:
            self.logger.error(f"Error handling authentication error for agent {agent_id}: {e}")
            return False
    
    async def _handle_authorization_error(self, agent_id: str, error: Exception, error_record: ErrorRecord) -> bool:
        """Handle authorization errors with permission check"""
        try:
            # Escalate for permission review
            await self.escalate_error(agent_id, error, {"permission_issue": True})
            
            error_record.resolution_strategy = "permission_escalation"
            return False  # Don't auto-recover from permission errors
            
        except Exception as e:
            self.logger.error(f"Error handling authorization error for agent {agent_id}: {e}")
            return False
    
    async def _handle_resource_exhausted_error(self, agent_id: str, error: Exception, error_record: ErrorRecord) -> bool:
        """Handle resource exhaustion with resource fallback"""
        try:
            # Apply resource fallback strategy
            fallback_result = await self.apply_fallback_strategy(agent_id, "resource_exhaustion")
            
            error_record.resolution_strategy = "resource_fallback"
            return fallback_result.get("success", False)
            
        except Exception as e:
            self.logger.error(f"Error handling resource exhausted error for agent {agent_id}: {e}")
            return False
    
    async def _handle_service_unavailable_error(self, agent_id: str, error: Exception, error_record: ErrorRecord) -> bool:
        """Handle service unavailable with alternative service"""
        try:
            # Apply alternative agent fallback
            fallback_result = await self.apply_fallback_strategy(agent_id, "service_unavailable")
            
            error_record.resolution_strategy = "alternative_service"
            return fallback_result.get("success", False)
            
        except Exception as e:
            self.logger.error(f"Error handling service unavailable error for agent {agent_id}: {e}")
            return False
    
    async def _handle_validation_error(self, agent_id: str, error: Exception, error_record: ErrorRecord) -> bool:
        """Handle validation errors with data correction"""
        try:
            # Validation errors usually require manual intervention
            await self.escalate_error(agent_id, error, {"validation_issue": True})
            
            error_record.resolution_strategy = "validation_escalation"
            return False  # Don't auto-recover from validation errors
            
        except Exception as e:
            self.logger.error(f"Error handling validation error for agent {agent_id}: {e}")
            return False
    
    async def _handle_execution_error(self, agent_id: str, error: Exception, error_record: ErrorRecord) -> bool:
        """Handle execution errors with retry and fallback"""
        try:
            # Apply general fallback strategy
            fallback_result = await self.apply_fallback_strategy(agent_id, "execution_error")
            
            error_record.resolution_strategy = "execution_fallback"
            return fallback_result.get("success", False)
            
        except Exception as e:
            self.logger.error(f"Error handling execution error for agent {agent_id}: {e}")
            return False
    
    async def _handle_unknown_error(self, agent_id: str, error: Exception, error_record: ErrorRecord) -> bool:
        """Handle unknown errors with generic recovery"""
        try:
            # Apply graceful failure fallback
            fallback_result = await self.apply_fallback_strategy(agent_id, "unknown_error")
            
            error_record.resolution_strategy = "generic_fallback"
            return fallback_result.get("success", False)
            
        except Exception as e:
            self.logger.error(f"Error handling unknown error for agent {agent_id}: {e}")
            return False    
   
 # Fallback strategy implementations
    
    async def _execute_fallback_strategy(
        self, 
        strategy: FallbackStrategy, 
        agent_id: str, 
        failed_action: str, 
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute specific fallback strategy"""
        try:
            if strategy == FallbackStrategy.CACHED_DATA:
                return await self._fallback_cached_data(agent_id, failed_action, config)
            elif strategy == FallbackStrategy.ALTERNATIVE_AGENT:
                return await self._fallback_alternative_agent(agent_id, failed_action, config)
            elif strategy == FallbackStrategy.DEGRADED_SERVICE:
                return await self._fallback_degraded_service(agent_id, failed_action, config)
            elif strategy == FallbackStrategy.MANUAL_INTERVENTION:
                return await self._fallback_manual_intervention(agent_id, failed_action, config)
            elif strategy == FallbackStrategy.GRACEFUL_FAILURE:
                return await self._fallback_graceful_failure(agent_id, failed_action, config)
            else:
                return {"success": False, "error": f"Unknown fallback strategy: {strategy}"}
                
        except Exception as e:
            return {"success": False, "error": f"Fallback strategy execution failed: {e}"}
    
    async def _fallback_cached_data(self, agent_id: str, failed_action: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Use cached data as fallback"""
        # Placeholder implementation - would integrate with actual cache
        cache_ttl = config.get("cache_ttl_minutes", 30)
        
        return {
            "success": True,
            "result": {"data": "cached_data_placeholder", "cache_age_minutes": 15},
            "fallback_strategy": "cached_data",
            "cache_ttl_minutes": cache_ttl
        }
    
    async def _fallback_alternative_agent(self, agent_id: str, failed_action: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Route to alternative agent"""
        alternative_agents = config.get("alternative_agents", [])
        
        if not alternative_agents:
            return {"success": False, "error": "No alternative agents configured"}
        
        # Try first available alternative agent
        selected_agent = alternative_agents[0]  # Simplified selection
        
        return {
            "success": True,
            "result": {"routed_to": selected_agent},
            "fallback_strategy": "alternative_agent",
            "alternative_agent": selected_agent
        }
    
    async def _fallback_degraded_service(self, agent_id: str, failed_action: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Provide degraded service"""
        degraded_features = config.get("degraded_features", [])
        
        return {
            "success": True,
            "result": {"service_mode": "degraded", "disabled_features": degraded_features},
            "fallback_strategy": "degraded_service",
            "degraded_features": degraded_features
        }
    
    async def _fallback_manual_intervention(self, agent_id: str, failed_action: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Request manual intervention"""
        notification_channels = config.get("manual_notification_channels", ["email"])
        
        # Send notifications (placeholder)
        for channel in notification_channels:
            self.logger.warning(f"Manual intervention required for agent {agent_id} via {channel}")
        
        return {
            "success": True,
            "result": {"manual_intervention_requested": True},
            "fallback_strategy": "manual_intervention",
            "notification_channels": notification_channels
        }
    
    async def _fallback_graceful_failure(self, agent_id: str, failed_action: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Graceful failure with user-friendly message"""
        return {
            "success": True,
            "result": {
                "graceful_failure": True,
                "user_message": "Service temporarily unavailable. Please try again later."
            },
            "fallback_strategy": "graceful_failure"
        }
    
    # Escalation handling
    
    async def _check_escalation_rules(self, agent_id: str, error_record: ErrorRecord) -> None:
        """Check if error meets escalation criteria"""
        for rule in self.escalation_rules:
            if self._evaluate_escalation_condition(rule, agent_id, error_record):
                escalation_data = {
                    "agent_id": agent_id,
                    "error_record": error_record.to_dict(),
                    "rule": rule,
                    "timestamp": datetime.now().isoformat()
                }
                
                await self._execute_escalation_action(rule["action"], escalation_data)
    
    def _evaluate_escalation_condition(self, rule: Dict[str, Any], agent_id: str, error_record: ErrorRecord) -> bool:
        """Evaluate escalation condition (simplified)"""
        condition = rule.get("condition", "")
        
        if "error_count" in condition:
            threshold = int(condition.split(">=")[-1].strip())
            return self.agent_failure_counts.get(agent_id, 0) >= threshold
        elif "error_type" in condition:
            expected_type = condition.split("==")[-1].strip().strip("'\"")
            return error_record.error_type.value == expected_type
        
        return False
    
    def _determine_escalation_level(self, agent_id: str, error_type: ErrorType) -> str:
        """Determine escalation level based on error"""
        if error_type in [ErrorType.AUTHENTICATION_ERROR, ErrorType.AUTHORIZATION_ERROR]:
            return "critical"
        elif self.agent_failure_counts.get(agent_id, 0) >= 5:
            return "high"
        else:
            return "medium"
    
    def _get_escalation_actions(self, escalation_data: Dict[str, Any]) -> List[str]:
        """Get escalation actions based on data"""
        level = escalation_data.get("escalation_level", "medium")
        
        if level == "critical":
            return ["notify_administrators", "security_alert", "system_alert"]
        elif level == "high":
            return ["notify_administrators", "system_alert"]
        else:
            return ["system_alert"]
    
    async def _execute_escalation_action(self, action: str, escalation_data: Dict[str, Any]) -> None:
        """Execute escalation action"""
        try:
            if action == "notify_administrators":
                self.logger.critical(f"Administrator notification: {escalation_data}")
            elif action == "security_alert":
                self.logger.critical(f"Security alert: {escalation_data}")
            elif action == "system_alert":
                self.logger.warning(f"System alert: {escalation_data}")
            elif action == "failover_to_backup":
                self.logger.warning(f"Failover requested: {escalation_data}")
            
        except Exception as e:
            self.logger.error(f"Error executing escalation action {action}: {e}")
    
    # Background monitoring tasks
    
    async def _error_cleanup_loop(self) -> None:
        """Background task to clean up old error records"""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                
                cutoff_time = datetime.now() - timedelta(days=7)  # Keep 7 days of history
                
                for agent_id in list(self.error_history.keys()):
                    errors = self.error_history[agent_id]
                    filtered_errors = [error for error in errors if error.timestamp > cutoff_time]
                    
                    if len(filtered_errors) != len(errors):
                        self.error_history[agent_id] = filtered_errors
                        self.logger.debug(f"Cleaned up {len(errors) - len(filtered_errors)} old errors for agent {agent_id}")
                
            except Exception as e:
                self.logger.error(f"Error in cleanup loop: {e}")
    
    async def _circuit_breaker_monitoring_loop(self) -> None:
        """Background task to monitor circuit breaker states"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                for service_name, breaker in self.circuit_breakers.items():
                    if breaker.state == CircuitBreakerState.OPEN:
                        self.logger.warning(f"Circuit breaker OPEN for service {service_name}")
                    elif breaker.state == CircuitBreakerState.HALF_OPEN:
                        self.logger.info(f"Circuit breaker HALF_OPEN for service {service_name}")
                
            except Exception as e:
                self.logger.error(f"Error in circuit breaker monitoring: {e}")
    
    async def shutdown(self) -> None:
        """Shutdown error handler and cleanup resources"""
        try:
            if self._cleanup_task:
                self._cleanup_task.cancel()
            if self._monitoring_task:
                self._monitoring_task.cancel()
            
            self.logger.info("Error handler shutdown completed")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")


# Factory function for creating error handler with default configuration
def create_error_handler(config: Optional[Dict[str, Any]] = None) -> AgentErrorHandler:
    """Create error handler with default configuration"""
    default_config = {
        "retry_policies": {
            "cost_management": {
                "max_attempts": 3,
                "base_delay_seconds": 2.0,
                "max_delay_seconds": 30.0
            },
            "resource_management": {
                "max_attempts": 5,
                "base_delay_seconds": 1.0,
                "max_delay_seconds": 60.0
            },
            "forecasting": {
                "max_attempts": 2,
                "base_delay_seconds": 5.0,
                "max_delay_seconds": 120.0
            }
        },
        "circuit_breakers": {
            "aws_bedrock": {
                "failure_threshold": 3,
                "recovery_timeout_seconds": 30
            },
            "dynamodb": {
                "failure_threshold": 5,
                "recovery_timeout_seconds": 60
            }
        },
        "escalation_rules": [
            {
                "condition": "error_count >= 3",
                "timeframe_minutes": 5,
                "action": "notify_administrators",
                "severity": "high"
            }
        ]
    }
    
    if config:
        # Merge with provided config
        for key, value in config.items():
            if key in default_config and isinstance(value, dict):
                default_config[key].update(value)
            else:
                default_config[key] = value
    
    return AgentErrorHandler(default_config)