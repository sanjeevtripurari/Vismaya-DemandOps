"""
Core interfaces and abstract base classes
Following Interface Segregation Principle
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime

from .models import (
    UsageSummary, CostData, ServiceCost, EC2Instance, 
    StorageVolume, DatabaseInstance, CostForecast,
    OptimizationRecommendation, ScenarioInput, ScenarioResult
)


class ICostDataProvider(ABC):
    """Interface for cost data providers"""
    
    @abstractmethod
    async def get_current_costs(self) -> CostData:
        """Get current month's costs"""
        pass
    
    @abstractmethod
    async def get_service_costs(self) -> List[ServiceCost]:
        """Get costs broken down by service"""
        pass
    
    @abstractmethod
    async def get_monthly_trend(self, months: int = 6) -> List[CostData]:
        """Get monthly cost trend"""
        pass


class IResourceProvider(ABC):
    """Interface for AWS resource providers"""
    
    @abstractmethod
    async def get_ec2_instances(self) -> List[EC2Instance]:
        """Get EC2 instances"""
        pass
    
    @abstractmethod
    async def get_storage_volumes(self) -> List[StorageVolume]:
        """Get EBS volumes"""
        pass
    
    @abstractmethod
    async def get_database_instances(self) -> List[DatabaseInstance]:
        """Get RDS instances"""
        pass


class IForecastingService(ABC):
    """Interface for cost forecasting services"""
    
    @abstractmethod
    async def generate_forecast(self, historical_data: List[CostData]) -> CostForecast:
        """Generate cost forecast based on historical data"""
        pass
    
    @abstractmethod
    async def analyze_scenario(self, 
                             current_usage: UsageSummary, 
                             scenario: ScenarioInput) -> ScenarioResult:
        """Analyze what-if scenario"""
        pass


class IAIAssistant(ABC):
    """Interface for AI assistant services"""
    
    @abstractmethod
    async def analyze_costs(self, usage_summary: UsageSummary) -> str:
        """Analyze costs and provide insights"""
        pass
    
    @abstractmethod
    async def generate_recommendations(self, 
                                     usage_summary: UsageSummary) -> List[OptimizationRecommendation]:
        """Generate optimization recommendations"""
        pass
    
    @abstractmethod
    async def chat_response(self, message: str, context: UsageSummary) -> str:
        """Handle chat interactions"""
        pass


class IDataRepository(ABC):
    """Interface for data persistence"""
    
    @abstractmethod
    async def save_usage_summary(self, summary: UsageSummary) -> None:
        """Save usage summary"""
        pass
    
    @abstractmethod
    async def get_usage_summary(self, date: datetime) -> Optional[UsageSummary]:
        """Get usage summary for a specific date"""
        pass
    
    @abstractmethod
    async def get_historical_summaries(self, days: int = 30) -> List[UsageSummary]:
        """Get historical usage summaries"""
        pass


class INotificationService(ABC):
    """Interface for notification services"""
    
    @abstractmethod
    async def send_budget_alert(self, budget_info: Dict) -> None:
        """Send budget alert notification"""
        pass
    
    @abstractmethod
    async def send_optimization_alert(self, recommendations: List[OptimizationRecommendation]) -> None:
        """Send optimization recommendations"""
        pass


class IConfigurationService(ABC):
    """Interface for configuration management"""
    
    @abstractmethod
    def get_aws_config(self) -> Dict:
        """Get AWS configuration"""
        pass
    
    @abstractmethod
    def get_app_config(self) -> Dict:
        """Get application configuration"""
        pass
    
    @abstractmethod
    def get_budget_config(self) -> Dict:
        """Get budget configuration"""
        pass


class IAuthenticationService(ABC):
    """Interface for authentication services"""
    
    @abstractmethod
    async def authenticate(self) -> bool:
        """Authenticate with AWS"""
        pass
    
    @abstractmethod
    async def get_caller_identity(self) -> Dict:
        """Get current AWS caller identity"""
        pass
    
    @abstractmethod
    def is_authenticated(self) -> bool:
        """Check if currently authenticated"""
        pass