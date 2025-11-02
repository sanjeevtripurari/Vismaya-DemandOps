"""
Budget Configuration Loader
Loads budget settings from .env file
"""

import os
from dotenv import load_dotenv
from typing import Dict, Any

class BudgetConfig:
    """Budget configuration loaded from environment variables"""
    
    def __init__(self):
        """Initialize budget configuration from .env file"""
        load_dotenv()
        
        # Load budget values from .env
        self.default_budget = float(os.getenv('DEFAULT_BUDGET', 80))
        self.warning_limit = float(os.getenv('BUDGET_WARNING_LIMIT', 80))
        self.maximum_limit = float(os.getenv('BUDGET_MAXIMUM_LIMIT', 100))
        
        # Validate configuration
        self._validate_config()
    
    def _validate_config(self):
        """Validate budget configuration values"""
        if self.warning_limit > self.maximum_limit:
            raise ValueError("Budget warning limit cannot exceed maximum limit")
        
        if self.default_budget <= 0:
            raise ValueError("Default budget must be positive")
    
    def get_budget_status(self, current_spend: float) -> str:
        """
        Get budget status based on current spend
        
        Args:
            current_spend: Current spending amount
            
        Returns:
            Budget status: 'healthy', 'warning', or 'critical'
        """
        if current_spend >= self.maximum_limit:
            return "critical"
        elif current_spend >= self.warning_limit:
            return "warning"
        else:
            return "healthy"
    
    def get_budget_utilization(self, current_spend: float) -> float:
        """
        Calculate budget utilization percentage
        
        Args:
            current_spend: Current spending amount
            
        Returns:
            Utilization percentage (0-100+)
        """
        return (current_spend / self.default_budget) * 100
    
    def get_remaining_budget(self, current_spend: float) -> float:
        """
        Calculate remaining budget
        
        Args:
            current_spend: Current spending amount
            
        Returns:
            Remaining budget amount
        """
        return max(0, self.default_budget - current_spend)
    
    def is_over_budget(self, current_spend: float) -> bool:
        """
        Check if spending exceeds default budget
        
        Args:
            current_spend: Current spending amount
            
        Returns:
            True if over budget, False otherwise
        """
        return current_spend > self.default_budget
    
    def get_budget_info(self) -> Dict[str, Any]:
        """
        Get complete budget configuration info
        
        Returns:
            Dictionary with all budget configuration values
        """
        return {
            'default_budget': self.default_budget,
            'warning_limit': self.warning_limit,
            'maximum_limit': self.maximum_limit,
            'currency': 'USD'
        }
    
    def __str__(self) -> str:
        """String representation of budget config"""
        return f"BudgetConfig(default=${self.default_budget}, warning=${self.warning_limit}, max=${self.maximum_limit})"