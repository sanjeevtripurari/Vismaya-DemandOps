"""
Logging infrastructure for the pricing system
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path


class PricingLogger:
    """Centralized logging for pricing system operations"""
    
    def __init__(self, log_level: str = "INFO", log_file: Optional[str] = None):
        self.logger = logging.getLogger("pricing_system")
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # File handler if specified
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def log_pricing_operation(self, operation: str, service: str, region: str, 
                            success: bool, duration_ms: float, details: Dict[str, Any] = None):
        """Log pricing operation with structured data"""
        log_data = {
            "operation": operation,
            "service": service,
            "region": region,
            "success": success,
            "duration_ms": duration_ms,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        
        level = logging.INFO if success else logging.ERROR
        self.logger.log(level, f"Pricing operation: {json.dumps(log_data)}")
    
    def log_cache_operation(self, operation: str, hit: bool, service: str = None, 
                          region: str = None, details: Dict[str, Any] = None):
        """Log cache operation"""
        log_data = {
            "operation": operation,
            "cache_hit": hit,
            "service": service,
            "region": region,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        
        self.logger.info(f"Cache operation: {json.dumps(log_data)}")
    
    def log_web_scraping(self, url: str, success: bool, entries_found: int = 0, 
                        error: str = None, duration_ms: float = 0):
        """Log web scraping operation"""
        log_data = {
            "operation": "web_scraping",
            "url": url,
            "success": success,
            "entries_found": entries_found,
            "duration_ms": duration_ms,
            "timestamp": datetime.now().isoformat(),
            "error": error
        }
        
        level = logging.INFO if success else logging.ERROR
        self.logger.log(level, f"Web scraping: {json.dumps(log_data)}")
    
    def log_cost_calculation(self, service: str, instance_type: str, quantity: int,
                           duration_months: int, total_cost: float, confidence: float):
        """Log cost calculation"""
        log_data = {
            "operation": "cost_calculation",
            "service": service,
            "instance_type": instance_type,
            "quantity": quantity,
            "duration_months": duration_months,
            "total_cost": total_cost,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat()
        }
        
        self.logger.info(f"Cost calculation: {json.dumps(log_data)}")
    
    def log_error(self, operation: str, error: Exception, context: Dict[str, Any] = None):
        """Log error with context"""
        log_data = {
            "operation": operation,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": datetime.now().isoformat(),
            "context": context or {}
        }
        
        self.logger.error(f"Error in {operation}: {json.dumps(log_data)}")
    
    def log_performance_metric(self, metric_name: str, value: float, unit: str, 
                             context: Dict[str, Any] = None):
        """Log performance metric"""
        log_data = {
            "metric": metric_name,
            "value": value,
            "unit": unit,
            "timestamp": datetime.now().isoformat(),
            "context": context or {}
        }
        
        self.logger.info(f"Performance metric: {json.dumps(log_data)}")


# Global logger instance
pricing_logger = PricingLogger(log_file="logs/pricing_system.log")


def log_pricing_operation(operation: str, service: str, region: str, 
                         success: bool, duration_ms: float, details: Dict[str, Any] = None):
    """Convenience function for logging pricing operations"""
    pricing_logger.log_pricing_operation(operation, service, region, success, duration_ms, details)


def log_cache_operation(operation: str, hit: bool, service: str = None, 
                       region: str = None, details: Dict[str, Any] = None):
    """Convenience function for logging cache operations"""
    pricing_logger.log_cache_operation(operation, hit, service, region, details)


def log_web_scraping(url: str, success: bool, entries_found: int = 0, 
                    error: str = None, duration_ms: float = 0):
    """Convenience function for logging web scraping"""
    pricing_logger.log_web_scraping(url, success, entries_found, error, duration_ms)


def log_cost_calculation(service: str, instance_type: str, quantity: int,
                        duration_months: int, total_cost: float, confidence: float):
    """Convenience function for logging cost calculations"""
    pricing_logger.log_cost_calculation(service, instance_type, quantity, duration_months, total_cost, confidence)


def log_error(operation: str, error: Exception, context: Dict[str, Any] = None):
    """Convenience function for logging errors"""
    pricing_logger.log_error(operation, error, context)


def log_performance_metric(metric_name: str, value: float, unit: str, 
                          context: Dict[str, Any] = None):
    """Convenience function for logging performance metrics"""
    pricing_logger.log_performance_metric(metric_name, value, unit, context)