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
    OptimizationRecommendation, ScenarioInput, ScenarioResult,
    ResourceSpecification, PricingData, CostEstimateResponse,
    TimePeriod, BudgetImpactAnalysis, ForecastingContext
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


class IForecastingAIAssistant(ABC):
    """Interface for forecasting AI assistant services"""
    
    @abstractmethod
    async def process_cost_query(self, query: str, context: ForecastingContext) -> CostEstimateResponse:
        """Process natural language cost estimation query"""
        pass
    
    @abstractmethod
    async def get_resource_pricing(self, resource_spec: ResourceSpecification) -> PricingData:
        """Get current pricing for specific resource configuration"""
        pass
    
    @abstractmethod
    async def chat_response(self, message: str, context: ForecastingContext) -> str:
        """Handle chat interactions with forecasting context"""
        pass


class IAWSPricingProvider(ABC):
    """Interface for AWS Pricing API provider"""
    
    @abstractmethod
    async def get_ec2_pricing(self, instance_type: str, region: str, os: str = "Linux") -> PricingData:
        """Get EC2 instance pricing for all models (On-Demand, Reserved, Spot)"""
        pass
    
    @abstractmethod
    async def get_storage_pricing(self, storage_type: str, region: str) -> PricingData:
        """Get EBS/S3 storage pricing"""
        pass
    
    @abstractmethod
    async def get_service_pricing(self, service: str, region: str, **kwargs) -> PricingData:
        """Get pricing for other AWS services"""
        pass
    
    @abstractmethod
    async def clear_cache(self) -> None:
        """Clear pricing data cache"""
        pass


class IQueryParser(ABC):
    """Interface for natural language query parsing"""
    
    @abstractmethod
    def parse_resource_query(self, query: str) -> ResourceSpecification:
        """Parse natural language query into structured resource specification"""
        pass
    
    @abstractmethod
    def extract_time_period(self, query: str) -> TimePeriod:
        """Extract time period from query (e.g., '2 months', '6 weeks')"""
        pass
    
    @abstractmethod
    def needs_clarification(self, resource_spec: ResourceSpecification) -> bool:
        """Check if resource specification needs clarification"""
        pass


class ICostEstimationEngine(ABC):
    """Interface for cost estimation engine"""
    
    @abstractmethod
    async def estimate_resource_cost(self, resource_spec: ResourceSpecification, 
                                   pricing_data: PricingData, 
                                   duration: TimePeriod) -> CostEstimateResponse:
        """Calculate total cost estimate for resource over specified duration"""
        pass
    
    @abstractmethod
    async def calculate_budget_impact(self, cost_estimate: float, 
                                    current_budget: 'BudgetInfo') -> BudgetImpactAnalysis:
        """Analyze impact of additional costs on current budget"""
        pass