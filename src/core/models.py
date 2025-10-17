"""
Core domain models for Vismaya DemandOps
Following Domain-Driven Design principles
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum


class ServiceType(Enum):
    """AWS Service types"""
    EC2 = "Amazon Elastic Compute Cloud - Compute"
    RDS = "Amazon Relational Database Service"
    S3 = "Amazon Simple Storage Service"
    EBS = "Amazon Elastic Block Store"
    LAMBDA = "AWS Lambda"
    CLOUDWATCH = "Amazon CloudWatch"


class InstanceState(Enum):
    """EC2 Instance states"""
    RUNNING = "running"
    STOPPED = "stopped"
    TERMINATED = "terminated"
    PENDING = "pending"


@dataclass
class CostData:
    """Cost information for a time period"""
    amount: float
    currency: str = "USD"
    start_date: datetime = None
    end_date: datetime = None
    
    def __post_init__(self):
        if self.start_date is None:
            self.start_date = datetime.now()
        if self.end_date is None:
            self.end_date = datetime.now()


@dataclass
class ServiceCost:
    """Cost breakdown by AWS service"""
    service_type: ServiceType
    cost: CostData
    usage_metrics: Dict[str, float] = None
    
    def __post_init__(self):
        if self.usage_metrics is None:
            self.usage_metrics = {}


@dataclass
class BudgetInfo:
    """Budget configuration and status"""
    total_budget: float
    current_spend: float
    currency: str = "USD"
    period_start: datetime = None
    period_end: datetime = None
    
    @property
    def utilization_percentage(self) -> float:
        """Calculate budget utilization percentage"""
        if self.total_budget == 0:
            return 0.0
        return (self.current_spend / self.total_budget) * 100
    
    @property
    def remaining_budget(self) -> float:
        """Calculate remaining budget"""
        return max(0, self.total_budget - self.current_spend)
    
    @property
    def is_over_budget(self) -> bool:
        """Check if over budget"""
        return self.current_spend > self.total_budget


@dataclass
class EC2Instance:
    """EC2 Instance information"""
    instance_id: str
    instance_type: str
    state: InstanceState
    name: str = ""
    monthly_cost: float = 0.0
    tags: Dict[str, str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = {}


@dataclass
class StorageVolume:
    """EBS Volume information"""
    volume_id: str
    size_gb: int
    volume_type: str
    monthly_cost: float
    attached_instance: str = ""


@dataclass
class DatabaseInstance:
    """RDS Instance information"""
    db_instance_id: str
    engine: str
    instance_class: str
    monthly_cost: float
    status: str = "available"


@dataclass
class CostForecast:
    """Cost forecasting data"""
    forecasted_amount: float
    confidence_level: float
    forecast_period_days: int
    base_amount: float
    trend_factor: float = 1.0
    
    @property
    def projected_overspend(self) -> float:
        """Calculate projected overspend amount"""
        return max(0, self.forecasted_amount - self.base_amount)


@dataclass
class OptimizationRecommendation:
    """AI-generated optimization recommendation"""
    title: str
    description: str
    potential_savings: float
    confidence_score: float
    implementation_effort: str  # "Low", "Medium", "High"
    category: str  # "Cost", "Performance", "Security"
    
    @property
    def is_high_impact(self) -> bool:
        """Check if this is a high-impact recommendation"""
        return self.potential_savings > 100 and self.confidence_score > 0.8


@dataclass
class UsageSummary:
    """Overall usage and cost summary"""
    budget_info: BudgetInfo
    service_costs: List[ServiceCost]
    ec2_instances: List[EC2Instance]
    storage_volumes: List[StorageVolume]
    database_instances: List[DatabaseInstance]
    cost_forecast: CostForecast
    recommendations: List[OptimizationRecommendation]
    last_updated: datetime = None
    
    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now()
    
    @property
    def total_monthly_cost(self) -> float:
        """Calculate total monthly cost from all services"""
        return sum(service.cost.amount for service in self.service_costs)
    
    def get_service_cost(self, service_type: ServiceType) -> Optional[ServiceCost]:
        """Get cost for a specific service type"""
        for service in self.service_costs:
            if service.service_type == service_type:
                return service
        return None
    
    def get_high_impact_recommendations(self) -> List[OptimizationRecommendation]:
        """Get high-impact optimization recommendations"""
        return [rec for rec in self.recommendations if rec.is_high_impact]


@dataclass
class ScenarioInput:
    """Input for what-if scenario analysis"""
    additional_ec2_instances: int = 0
    additional_storage_gb: int = 0
    instance_type_changes: Dict[str, str] = None
    
    def __post_init__(self):
        if self.instance_type_changes is None:
            self.instance_type_changes = {}


@dataclass
class ScenarioResult:
    """Result of what-if scenario analysis"""
    scenario_input: ScenarioInput
    projected_monthly_cost: float
    cost_difference: float
    budget_impact: float
    recommendations: List[str]
    
    @property
    def exceeds_budget(self) -> bool:
        """Check if scenario exceeds budget"""
        return self.budget_impact > 0