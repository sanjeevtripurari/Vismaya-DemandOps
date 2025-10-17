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


class DemoDataProvider:
    """Provides realistic demo data for platform demonstration"""
    
    @staticmethod
    def get_demo_usage_summary(budget: float = 15000) -> UsageSummary:
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
        
        # Demo budget info
        current_spend = 12500.0
        budget_info = BudgetInfo(
            total_budget=budget,
            current_spend=current_spend
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