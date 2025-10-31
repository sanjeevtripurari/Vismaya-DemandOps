"""
Error handling utilities for the pricing system
"""

import asyncio
import time
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Type, Union
from contextlib import asynccontextmanager

from ..core.pricing_interfaces import PricingError, DataSourceError, ValidationError, CacheError
from .pricing_logger import log_error, log_performance_metric


class CircuitBreaker:
    """Circuit breaker pattern for external service calls"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60, expected_exception: Type[Exception] = Exception):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def __call__(self, func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if self.state == "OPEN":
                if self._should_attempt_reset():
                    self.state = "HALF_OPEN"
                else:
                    raise DataSourceError("Circuit breaker is OPEN")
            
            try:
                result = await func(*args, **kwargs)
                self._on_success()
                return result
            except self.expected_exception as e:
                self._on_failure()
                raise
        
        return wrapper
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        return (
            self.last_failure_time and
            time.time() - self.last_failure_time >= self.recovery_timeout
        )
    
    def _on_success(self):
        """Handle successful call"""
        self.failure_count = 0
        self.state = "CLOSED"
    
    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"


class RetryHandler:
    """Retry handler with exponential backoff"""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0, 
                 backoff_factor: float = 2.0, exceptions: tuple = (Exception,)):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.exceptions = exceptions
    
    def __call__(self, func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(self.max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except self.exceptions as e:
                    last_exception = e
                    
                    if attempt == self.max_retries:
                        log_error(f"retry_exhausted_{func.__name__}", e, {
                            "attempts": attempt + 1,
                            "max_retries": self.max_retries
                        })
                        raise
                    
                    # Calculate delay with exponential backoff
                    delay = min(
                        self.base_delay * (self.backoff_factor ** attempt),
                        self.max_delay
                    )
                    
                    log_error(f"retry_attempt_{func.__name__}", e, {
                        "attempt": attempt + 1,
                        "delay_seconds": delay,
                        "max_retries": self.max_retries
                    })
                    
                    await asyncio.sleep(delay)
            
            # This should never be reached, but just in case
            raise last_exception
        
        return wrapper


class TimeoutHandler:
    """Timeout handler for async operations"""
    
    def __init__(self, timeout_seconds: float):
        self.timeout_seconds = timeout_seconds
    
    def __call__(self, func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=self.timeout_seconds)
            except asyncio.TimeoutError:
                error = DataSourceError(f"Operation timed out after {self.timeout_seconds} seconds")
                log_error(f"timeout_{func.__name__}", error, {
                    "timeout_seconds": self.timeout_seconds
                })
                raise error
        
        return wrapper


@asynccontextmanager
async def performance_monitor(operation_name: str, context: Dict[str, Any] = None):
    """Context manager for monitoring operation performance"""
    start_time = time.time()
    success = False
    error = None
    
    try:
        yield
        success = True
    except Exception as e:
        error = e
        raise
    finally:
        duration_ms = (time.time() - start_time) * 1000
        
        log_performance_metric(
            f"{operation_name}_duration",
            duration_ms,
            "milliseconds",
            {
                "success": success,
                "error": str(error) if error else None,
                **(context or {})
            }
        )


def handle_pricing_errors(func):
    """Decorator to handle and categorize pricing system errors"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except (ConnectionError, TimeoutError, asyncio.TimeoutError) as e:
            # Network/connectivity issues
            error = DataSourceError(f"Network error in {func.__name__}: {e}")
            log_error(func.__name__, error)
            raise error
        except (ValueError, KeyError, TypeError) as e:
            # Data validation/parsing issues
            error = ValidationError(f"Data validation error in {func.__name__}: {e}")
            log_error(func.__name__, error)
            raise error
        except Exception as e:
            # Generic error handling
            if isinstance(e, PricingError):
                # Already a pricing error, just log and re-raise
                log_error(func.__name__, e)
                raise
            else:
                # Wrap unknown errors
                error = PricingError(f"Unexpected error in {func.__name__}: {e}")
                log_error(func.__name__, error)
                raise error
    
    return wrapper


class GracefulDegradation:
    """Handles graceful degradation when primary data sources fail"""
    
    def __init__(self):
        self.fallback_strategies = []
    
    def add_fallback(self, strategy: Callable, priority: int = 0):
        """Add a fallback strategy with priority (lower number = higher priority)"""
        self.fallback_strategies.append((priority, strategy))
        self.fallback_strategies.sort(key=lambda x: x[0])
    
    async def execute_with_fallback(self, primary_operation: Callable, *args, **kwargs):
        """Execute primary operation with fallback strategies"""
        # Try primary operation first
        try:
            return await primary_operation(*args, **kwargs)
        except Exception as primary_error:
            log_error("primary_operation_failed", primary_error, {
                "operation": primary_operation.__name__,
                "fallback_strategies_available": len(self.fallback_strategies)
            })
            
            # Try fallback strategies in order of priority
            for priority, strategy in self.fallback_strategies:
                try:
                    result = await strategy(*args, **kwargs)
                    log_performance_metric(
                        "fallback_success",
                        1,
                        "count",
                        {
                            "strategy": strategy.__name__,
                            "priority": priority
                        }
                    )
                    return result
                except Exception as fallback_error:
                    log_error(f"fallback_failed_{strategy.__name__}", fallback_error)
                    continue
            
            # All strategies failed
            raise DataSourceError(f"All fallback strategies failed. Primary error: {primary_error}")


# Global instances
circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)
retry_handler = RetryHandler(max_retries=3, base_delay=1.0)
timeout_handler = TimeoutHandler(timeout_seconds=30.0)
graceful_degradation = GracefulDegradation()


# Convenience decorators
def with_circuit_breaker(func):
    """Apply circuit breaker to function"""
    return circuit_breaker(func)


def with_retry(max_retries: int = 3, base_delay: float = 1.0):
    """Apply retry logic to function"""
    return RetryHandler(max_retries=max_retries, base_delay=base_delay)


def with_timeout(timeout_seconds: float = 30.0):
    """Apply timeout to function"""
    return TimeoutHandler(timeout_seconds=timeout_seconds)


def robust_pricing_operation(func):
    """Apply comprehensive error handling to pricing operations"""
    return handle_pricing_errors(
        with_timeout(30.0)(
            with_retry(max_retries=2, base_delay=1.0)(
                with_circuit_breaker(func)
            )
        )
    )