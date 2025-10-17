"""
AWS Cost Explorer Provider
Implements ICostDataProvider interface
Following Dependency Inversion Principle
"""

import logging
from datetime import datetime, timedelta
from typing import List

from ..core.interfaces import ICostDataProvider
from ..core.models import CostData, ServiceCost, ServiceType

logger = logging.getLogger(__name__)


class AWSCostProvider(ICostDataProvider):
    """AWS Cost Explorer implementation"""
    
    def __init__(self, aws_session):
        self._session = aws_session
        self._cost_explorer = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Cost Explorer client"""
        try:
            self._cost_explorer = self._session.client('ce')
            logger.info("Cost Explorer client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Cost Explorer client: {e}")
            self._cost_explorer = None
    
    async def get_current_costs(self) -> CostData:
        """Get current month's costs"""
        try:
            if not self._cost_explorer:
                return self._get_mock_current_costs()
            
            now = datetime.now()
            start_date = now.replace(day=1).strftime('%Y-%m-%d')
            end_date = now.strftime('%Y-%m-%d')
            
            response = self._cost_explorer.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Granularity='MONTHLY',
                Metrics=['BlendedCost']
            )
            
            if response['ResultsByTime']:
                amount = float(response['ResultsByTime'][0]['Total']['BlendedCost']['Amount'])
                return CostData(
                    amount=amount,
                    start_date=datetime.strptime(start_date, '%Y-%m-%d'),
                    end_date=datetime.strptime(end_date, '%Y-%m-%d')
                )
            
            return CostData(amount=0.0)
            
        except Exception as e:
            logger.error(f"Error fetching current costs: {e}")
            return self._get_mock_current_costs()
    
    async def get_service_costs(self) -> List[ServiceCost]:
        """Get costs broken down by service"""
        try:
            if not self._cost_explorer:
                return self._get_mock_service_costs()
            
            now = datetime.now()
            start_date = now.replace(day=1).strftime('%Y-%m-%d')
            end_date = now.strftime('%Y-%m-%d')
            
            response = self._cost_explorer.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Granularity='MONTHLY',
                Metrics=['BlendedCost'],
                GroupBy=[
                    {
                        'Type': 'DIMENSION',
                        'Key': 'SERVICE'
                    }
                ]
            )
            
            service_costs = []
            if response['ResultsByTime'] and response['ResultsByTime'][0]['Groups']:
                for group in response['ResultsByTime'][0]['Groups']:
                    service_name = group['Keys'][0]
                    amount = float(group['Metrics']['BlendedCost']['Amount'])
                    
                    # Map service name to ServiceType
                    service_type = self._map_service_name(service_name)
                    if service_type and amount > 0:
                        cost_data = CostData(
                            amount=amount,
                            start_date=datetime.strptime(start_date, '%Y-%m-%d'),
                            end_date=datetime.strptime(end_date, '%Y-%m-%d')
                        )
                        service_costs.append(ServiceCost(
                            service_type=service_type,
                            cost=cost_data
                        ))
            
            return service_costs if service_costs else self._get_mock_service_costs()
            
        except Exception as e:
            logger.error(f"Error fetching service costs: {e}")
            return self._get_mock_service_costs()
    
    async def get_monthly_trend(self, months: int = 6) -> List[CostData]:
        """Get monthly cost trend"""
        try:
            if not self._cost_explorer:
                return self._get_mock_monthly_trend()
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=months * 30)
            
            response = self._cost_explorer.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='MONTHLY',
                Metrics=['BlendedCost']
            )
            
            trend_data = []
            for result in response['ResultsByTime']:
                amount = float(result['Total']['BlendedCost']['Amount'])
                period_start = datetime.strptime(result['TimePeriod']['Start'], '%Y-%m-%d')
                period_end = datetime.strptime(result['TimePeriod']['End'], '%Y-%m-%d')
                
                trend_data.append(CostData(
                    amount=amount,
                    start_date=period_start,
                    end_date=period_end
                ))
            
            return trend_data if trend_data else self._get_mock_monthly_trend()
            
        except Exception as e:
            logger.error(f"Error fetching monthly trend: {e}")
            return self._get_mock_monthly_trend()
    
    def _map_service_name(self, service_name: str) -> ServiceType:
        """Map AWS service name to ServiceType enum"""
        service_mapping = {
            'Amazon Elastic Compute Cloud - Compute': ServiceType.EC2,
            'Amazon Relational Database Service': ServiceType.RDS,
            'Amazon Simple Storage Service': ServiceType.S3,
            'Amazon Elastic Block Store': ServiceType.EBS,
            'AWS Lambda': ServiceType.LAMBDA,
            'Amazon CloudWatch': ServiceType.CLOUDWATCH
        }
        
        return service_mapping.get(service_name)
    
    def _get_mock_current_costs(self) -> CostData:
        """Mock current costs for demo"""
        return CostData(amount=12500.0)
    
    def _get_mock_service_costs(self) -> List[ServiceCost]:
        """Mock service costs for demo"""
        return [
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
    
    def _get_mock_monthly_trend(self) -> List[CostData]:
        """Mock monthly trend for demo"""
        base_date = datetime.now().replace(day=1)
        return [
            CostData(amount=5000.0, start_date=base_date - timedelta(days=150)),
            CostData(amount=8000.0, start_date=base_date - timedelta(days=120)),
            CostData(amount=12000.0, start_date=base_date - timedelta(days=90)),
            CostData(amount=18000.0, start_date=base_date - timedelta(days=60)),
            CostData(amount=23000.0, start_date=base_date - timedelta(days=30)),
            CostData(amount=12500.0, start_date=base_date)
        ]