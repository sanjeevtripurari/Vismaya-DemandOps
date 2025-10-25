"""
Demo Data Provider for Vismaya DemandOps
Provides realistic demo data when no AWS resources exist
"""

from datetime import datetime, timedelta
from typing import List

from ..core.models import (
    CostData, ServiceCost, ServiceType, EC2Instance, StorageVolume, 
    DatabaseInstance, InstanceState, UsageSummary, BudgetInfo, CostForecast
)
from config import Config


class DemoDataProvider:
    """Provides realistic demo data for platform demonstration"""
    
    @staticmethod
    def get_empty_usage_summary() -> UsageSummary:
        """Get empty usage summary for initial UI load"""
        
        # Empty budget info using Config values
        budget_info = BudgetInfo(
            total_budget=Config.BUDGET_WARNING_LIMIT,
            current_spend=0.0,  # Start with 0
            warning_limit=Config.BUDGET_WARNING_LIMIT,
            maximum_limit=Config.BUDGET_MAXIMUM_LIMIT
        )
        
        # Empty forecast
        cost_forecast = CostForecast(
            forecasted_amount=0.0,
            confidence_level=0.0,
            forecast_period_days=30,
            base_amount=0.0,
            trend_factor=1.0
        )
        
        return UsageSummary(
            budget_info=budget_info,
            service_costs=[],  # Empty list
            ec2_instances=[],  # Empty list
            storage_volumes=[],  # Empty list
            database_instances=[],  # Empty list
            cost_forecast=cost_forecast,
            recommendations=[],  # Empty list
            last_updated=datetime.now()
        )
    
    @staticmethod
    def get_realistic_usage_summary() -> UsageSummary:
        """Get realistic usage summary based on actual AWS costs (~$1.72)"""
        
        # Realistic service costs based on actual usage
        service_costs = [
            ServiceCost(
                service_type=ServiceType.COST_EXPLORER,
                cost=CostData(amount=1.70)  # Cost Explorer usage
            ),
            ServiceCost(
                service_type=ServiceType.BEDROCK,
                cost=CostData(amount=0.02)  # Claude 3 Haiku usage
            )
        ]
        
        # Realistic budget info using Config values
        current_spend = 1.72
        budget_info = BudgetInfo(
            total_budget=Config.BUDGET_WARNING_LIMIT,  # Warning threshold
            current_spend=current_spend,
            warning_limit=Config.BUDGET_WARNING_LIMIT,  # Alert at $80
            maximum_limit=Config.BUDGET_MAXIMUM_LIMIT  # Hard limit at $100
        )
        
        # Realistic forecast (minimal growth)
        cost_forecast = CostForecast(
            forecasted_amount=2.15,
            confidence_level=0.95,
            forecast_period_days=30,
            base_amount=current_spend,
            trend_factor=1.25
        )
        
        return UsageSummary(
            budget_info=budget_info,
            service_costs=service_costs,
            ec2_instances=[],  # No EC2 instances
            storage_volumes=[],  # No storage volumes
            database_instances=[],  # No databases
            cost_forecast=cost_forecast,
            recommendations=[]
        )
    
    @staticmethod
    def get_demo_usage_summary() -> UsageSummary:
        """Get complete demo usage summary"""
        
        # Demo EC2 instances
        ec2_instances = [
            EC2Instance(
                instance_id="i-1234567890abcdef0",
                instance_type="t3.medium",
                state=InstanceState.RUNNING,
                name="Web Server 1",
                monthly_cost=30.40,
                tags={"Environment": "Production", "Team": "WebDev", "Project": "VismayaDemo"}
            ),
            EC2Instance(
                instance_id="i-0987654321fedcba0",
                instance_type="t3.large",
                state=InstanceState.RUNNING,
                name="Database Server",
                monthly_cost=60.80,
                tags={"Environment": "Production", "Team": "Database", "Project": "VismayaDemo"}
            ),
            EC2Instance(
                instance_id="i-abcdef1234567890",
                instance_type="t3.small",
                state=InstanceState.STOPPED,
                name="Development Server",
                monthly_cost=0.0,  # Stopped instance
                tags={"Environment": "Development", "Team": "DevOps", "Project": "VismayaDemo"}
            )
        ]
        
        # Demo storage volumes
        storage_volumes = [
            StorageVolume(
                volume_id="vol-1234567890abcdef0",
                size_gb=100,
                volume_type="gp3",
                monthly_cost=8.0,
                attached_instance="i-1234567890abcdef0"
            ),
            StorageVolume(
                volume_id="vol-0987654321fedcba0",
                size_gb=500,
                volume_type="gp3",
                monthly_cost=40.0,
                attached_instance="i-0987654321fedcba0"
            ),
            StorageVolume(
                volume_id="vol-abcdef1234567890",
                size_gb=50,
                volume_type="gp2",
                monthly_cost=5.0,
                attached_instance=""  # Unattached - optimization opportunity
            )
        ]
        
        # Demo database instances
        database_instances = [
            DatabaseInstance(
                db_instance_id="prod-db-1",
                engine="mysql",
                instance_class="db.t3.medium",
                monthly_cost=49.64,
                status="available"
            ),
            DatabaseInstance(
                db_instance_id="analytics-db",
                engine="postgres",
                instance_class="db.r5.large",
                monthly_cost=174.72,
                status="available"
            )
        ]
        
        # Demo service costs
        service_costs = [
            ServiceCost(
                service_type=ServiceType.EC2,
                cost=CostData(amount=5500.0)
            ),
            ServiceCost(
                service_type=ServiceType.RDS,
                cost=CostData(amount=8000.0)
            ),
            ServiceCost(
                service_type=ServiceType.S3,
                cost=CostData(amount=3500.0)
            ),
            ServiceCost(
                service_type=ServiceType.EBS,
                cost=CostData(amount=7500.0)
            )
        ]
        
        # Demo budget info using Config values
        current_spend = 85.0  # Over warning limit to show alerts
        budget_info = BudgetInfo(
            total_budget=Config.BUDGET_WARNING_LIMIT,
            current_spend=current_spend,
            warning_limit=Config.BUDGET_WARNING_LIMIT,
            maximum_limit=Config.BUDGET_MAXIMUM_LIMIT
        )
        
        # Demo forecast
        cost_forecast = CostForecast(
            forecasted_amount=14200.0,
            confidence_level=0.85,
            forecast_period_days=30,
            base_amount=current_spend,
            trend_factor=1.136
        )
        
        return UsageSummary(
            budget_info=budget_info,
            service_costs=service_costs,
            ec2_instances=ec2_instances,
            storage_volumes=storage_volumes,
            database_instances=database_instances,
            cost_forecast=cost_forecast,
            recommendations=[]
        )
    
    @staticmethod
    def get_demo_monthly_trend() -> List[CostData]:
        """Get demo monthly trend data"""
        base_date = datetime.now().replace(day=1)
        return [
            CostData(amount=5000.0, start_date=base_date - timedelta(days=150)),
            CostData(amount=8000.0, start_date=base_date - timedelta(days=120)),
            CostData(amount=12000.0, start_date=base_date - timedelta(days=90)),
            CostData(amount=18000.0, start_date=base_date - timedelta(days=60)),
            CostData(amount=23000.0, start_date=base_date - timedelta(days=30)),
            CostData(amount=12500.0, start_date=base_date)
        ]