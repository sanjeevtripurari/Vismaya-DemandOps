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
    COST_EXPLORER = "AWS Cost Explorer"
    BEDROCK = "Amazon Bedrock"
    OTHER = "Other AWS Services"


class InstanceState(Enum):
    """EC2 Instance states"""
    RUNNING = "running"
    STOPPED = "stopped"
    TERMINATED = "terminated"
    PENDING = "pending"


@dataclass
class CostData:
    """Cost information for a time period"""
    amount: float  # Total cost including tax
    currency: str = "USD"
    start_date: datetime = None
    end_date: datetime = None
    service_name: str = None  # For detailed service tracking
    pre_tax_amount: float = None  # Cost before tax
    tax_amount: float = None  # Tax portion
    usage_quantity: float = None  # Usage quantity (requests, GB, etc.)
    
    def __post_init__(self):
        if self.start_date is None:
            self.start_date = datetime.now()
        if self.end_date is None:
            self.end_date = datetime.now()
        
        # Calculate tax if not provided
        if self.pre_tax_amount is not None and self.tax_amount is None:
            self.tax_amount = self.amount - self.pre_tax_amount
        elif self.tax_amount is not None and self.pre_tax_amount is None:
            self.pre_tax_amount = self.amount - self.tax_amount


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
    total_budget: float  # Warning threshold ($80)
    current_spend: float
    currency: str = "USD"
    period_start: datetime = None
    period_end: datetime = None
    warning_limit: float = None  # Warning threshold ($80)
    maximum_limit: float = None  # Hard limit ($100)
    
    def __post_init__(self):
        # Set defaults if not provided
        if self.warning_limit is None:
            self.warning_limit = self.total_budget
        if self.maximum_limit is None:
            self.maximum_limit = self.total_budget * 1.25  # 25% above warning
    
    @property
    def utilization_percentage(self) -> float:
        """Calculate budget utilization percentage based on warning limit"""
        if self.warning_limit == 0:
            return 0.0
        return (self.current_spend / self.warning_limit) * 100
    
    @property
    def maximum_utilization_percentage(self) -> float:
        """Calculate utilization percentage based on maximum limit"""
        if self.maximum_limit == 0:
            return 0.0
        return (self.current_spend / self.maximum_limit) * 100
    
    @property
    def remaining_budget(self) -> float:
        """Calculate remaining budget before warning"""
        return max(0, self.warning_limit - self.current_spend)
    
    @property
    def remaining_maximum_budget(self) -> float:
        """Calculate remaining budget before hard limit"""
        return max(0, self.maximum_limit - self.current_spend)
    
    @property
    def is_over_warning(self) -> bool:
        """Check if over warning threshold"""
        return self.current_spend > self.warning_limit
    
    @property
    def is_over_maximum(self) -> bool:
        """Check if over maximum limit"""
        return self.current_spend > self.maximum_limit
    
    @property
    def budget_status(self) -> str:
        """Get budget status description"""
        if self.is_over_maximum:
            return "CRITICAL"
        elif self.is_over_warning:
            return "WARNING"
        elif self.utilization_percentage >= 75:
            return "CAUTION"
        else:
            return "HEALTHY"
    
    @property
    def budget_status_emoji(self) -> str:
        """Get emoji for budget status"""
        status_emojis = {
            "HEALTHY": "✅",
            "CAUTION": "⚠️",
            "WARNING": "🚨",
            "CRITICAL": "🔴"
        }
        return status_emojis.get(self.budget_status, "❓")


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
    """Enhanced cost forecasting data with timeline predictions"""
    forecasted_amount: float
    confidence_level: float
    forecast_period_days: int
    base_amount: float
    trend_factor: float = 1.0
    daily_growth_rate: float = 0.0
    
    @property
    def projected_overspend(self) -> float:
        """Calculate projected overspend amount"""
        return max(0, self.forecasted_amount - self.base_amount)
    
    @property
    def daily_cost_estimate(self) -> float:
        """Estimate daily cost based on current spending"""
        return self.base_amount / 30  # Assume current amount is monthly
    
    @property
    def monthly_growth_rate(self) -> float:
        """Monthly growth rate as percentage"""
        return (self.trend_factor - 1) * 100
    
    def days_to_reach_amount(self, target_amount: float) -> int:
        """Calculate days to reach a target amount with organic growth"""
        if target_amount <= self.base_amount:
            return 0
        
        if self.daily_growth_rate <= 0:
            return float('inf')  # Will never reach if no growth
        
        # Using compound growth formula: target = base * (1 + daily_rate)^days
        # Solving for days: days = log(target/base) / log(1 + daily_rate)
        import math
        try:
            days = math.log(target_amount / self.base_amount) / math.log(1 + self.daily_growth_rate)
            return max(0, int(days))
        except (ValueError, ZeroDivisionError):
            return float('inf')
    
    def cost_at_day(self, days: int) -> float:
        """Calculate projected cost at a specific day"""
        return self.base_amount * ((1 + self.daily_growth_rate) ** days)


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