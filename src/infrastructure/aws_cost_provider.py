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
    """AWS Cost Explorer implementation - Production Ready"""
    
    def __init__(self, aws_session, config=None):
        self._session = aws_session
        self._config = config
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
    
    def _refresh_client_if_needed(self):
        """Refresh client if credentials are expired - production ready"""
        try:
            if self._cost_explorer:
                # Test if current client works by making a simple STS call
                sts = self._session.client('sts')
                sts.get_caller_identity()
                logger.debug("AWS credentials are valid")
        except Exception as e:
            error_str = str(e)
            if any(keyword in error_str for keyword in ['ExpiredToken', 'RequestExpired', 'TokenRefreshRequired']):
                logger.warning("AWS credentials expired, attempting refresh...")
                try:
                    # For production environments, recreate the session
                    from .aws_session_factory import AWSSessionFactory
                    session_factory = AWSSessionFactory(self._config)
                    self._session = session_factory.create_session()
                    self._initialize_client()
                    logger.info("✅ AWS session refreshed successfully")
                except Exception as refresh_error:
                    logger.error(f"❌ Failed to refresh AWS session: {refresh_error}")
                    self._cost_explorer = None
                    raise Exception(f"AWS credential refresh failed: {refresh_error}")
            else:
                logger.error(f"AWS client test failed: {e}")
                raise Exception(f"AWS client error: {e}")
    
    def _validate_aws_permissions(self):
        """Validate that we have the required AWS permissions"""
        try:
            if not self._cost_explorer:
                raise Exception("Cost Explorer client not initialized")
            
            # Test Cost Explorer permissions with a minimal call
            from datetime import datetime, timedelta
            test_start = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            test_end = datetime.now().strftime('%Y-%m-%d')
            
            self._cost_explorer.get_cost_and_usage(
                TimePeriod={'Start': test_start, 'End': test_end},
                Granularity='DAILY',
                Metrics=['BlendedCost']
            )
            
            logger.info("✅ AWS Cost Explorer permissions validated")
            return True
            
        except Exception as e:
            error_msg = str(e)
            if 'AccessDenied' in error_msg:
                raise Exception("Access denied to AWS Cost Explorer. Check IAM permissions for 'ce:GetCostAndUsage'")
            elif 'UnauthorizedOperation' in error_msg:
                raise Exception("Unauthorized to access Cost Explorer. Ensure proper IAM role/policy is attached")
            else:
                raise Exception(f"Cost Explorer validation failed: {error_msg}")
    
    async def get_current_costs(self) -> CostData:
        """Get current month's costs from AWS Cost Explorer - REAL DATA ONLY"""
        try:
            # Refresh client and validate permissions
            self._refresh_client_if_needed()
            self._validate_aws_permissions()
            
            if not self._cost_explorer:
                raise Exception("AWS Cost Explorer client not available")
            
            now = datetime.now()
            start_date = now.replace(day=1).strftime('%Y-%m-%d')
            end_date = now.strftime('%Y-%m-%d')
            
            logger.info(f"Fetching real AWS costs from {start_date} to {end_date}")
            
            # Track API cost
            from ..services.api_cost_tracker import api_cost_tracker
            api_cost_tracker.track_cost_explorer_call('GetCostAndUsage', {
                'start_date': start_date,
                'end_date': end_date,
                'granularity': 'MONTHLY'
            })
            
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
                logger.info(f"✅ Real AWS costs retrieved: ${amount:.2f}")
                return CostData(
                    amount=amount,
                    start_date=datetime.strptime(start_date, '%Y-%m-%d'),
                    end_date=datetime.strptime(end_date, '%Y-%m-%d')
                )
            
            logger.info("No cost data found in AWS response - returning $0.00")
            return CostData(amount=0.0)
            
        except Exception as e:
            from .error_handler import AWSErrorHandler
            user_email = getattr(self._config, 'AWS_USER_EMAIL', None) if self._config else None
            error_message = AWSErrorHandler.handle_aws_error(e, "Cost Explorer", user_email)
            logger.error(f"❌ Failed to fetch real AWS costs: {error_message}")
            raise Exception(error_message)
    
    async def get_service_costs(self) -> List[ServiceCost]:
        """Get costs broken down by service from AWS Cost Explorer - REAL DATA ONLY"""
        try:
            # Always try to refresh/initialize client
            self._refresh_client_if_needed()
            
            if not self._cost_explorer:
                logger.error("Cost Explorer client not available for service costs")
                raise Exception("AWS Cost Explorer not accessible for service breakdown")
            
            now = datetime.now()
            start_date = now.replace(day=1).strftime('%Y-%m-%d')
            end_date = now.strftime('%Y-%m-%d')
            
            logger.info(f"Fetching real AWS service costs from {start_date} to {end_date}")
            
            # Track API cost
            from ..services.api_cost_tracker import api_cost_tracker
            api_cost_tracker.track_cost_explorer_call('GetCostAndUsage', {
                'start_date': start_date,
                'end_date': end_date,
                'granularity': 'MONTHLY',
                'group_by': 'SERVICE'
            })
            
            response = self._cost_explorer.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Granularity='MONTHLY',
                Metrics=['BlendedCost', 'UnblendedCost', 'UsageQuantity'],
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
                    
                    # Extract different cost metrics
                    blended_cost = float(group['Metrics']['BlendedCost']['Amount'])
                    unblended_cost = float(group['Metrics']['UnblendedCost']['Amount']) if 'UnblendedCost' in group['Metrics'] else blended_cost
                    usage_quantity = float(group['Metrics']['UsageQuantity']['Amount']) if 'UsageQuantity' in group['Metrics'] else 0
                    
                    # Use blended cost as the primary amount
                    amount = blended_cost
                    
                    # Include services with any costs, even micro-costs
                    if amount >= 0:
                        # Create a comprehensive service cost entry
                        cost_data = CostData(
                            amount=amount,
                            start_date=datetime.strptime(start_date, '%Y-%m-%d'),
                            end_date=datetime.strptime(end_date, '%Y-%m-%d'),
                            service_name=service_name,
                            pre_tax_amount=unblended_cost,  # Unblended is typically pre-tax
                            usage_quantity=usage_quantity
                        )
                        
                        # Map to known service types or create a generic one
                        service_type = self._map_service_name(service_name)
                        if service_type:
                            service_costs.append(ServiceCost(
                                service_type=service_type,
                                cost=cost_data
                            ))
                        else:
                            # For unmapped services, log them for visibility and include them
                            logger.info(f"Unmapped AWS service: {service_name} - ${amount:.2f}")
                            
                            # Use the existing cost_data that already has the service_name set
                            service_costs.append(ServiceCost(
                                service_type=ServiceType.OTHER,
                                cost=cost_data
                            ))
            
            logger.info(f"✅ Retrieved {len(service_costs)} real AWS service costs")
            return service_costs
            
        except Exception as e:
            from .error_handler import AWSErrorHandler
            user_email = getattr(self._config, 'AWS_USER_EMAIL', None) if self._config else None
            error_message = AWSErrorHandler.handle_aws_error(e, "Service Costs", user_email)
            logger.error(f"❌ Failed to fetch real AWS service costs: {error_message}")
            raise Exception(error_message)
    
    async def get_monthly_trend(self, months: int = 6) -> List[CostData]:
        """Get monthly cost trend from AWS Cost Explorer - REAL DATA ONLY"""
        try:
            # Always try to refresh/initialize client
            self._refresh_client_if_needed()
            
            if not self._cost_explorer:
                logger.error("Cost Explorer client not available for monthly trend")
                raise Exception("AWS Cost Explorer not accessible for trend data")
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=months * 30)
            
            logger.info(f"Fetching real AWS monthly trend from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
            
            # Track API cost
            from ..services.api_cost_tracker import api_cost_tracker
            api_cost_tracker.track_cost_explorer_call('GetCostAndUsage', {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'granularity': 'MONTHLY',
                'months': months
            })
            
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
            
            logger.info(f"✅ Retrieved {len(trend_data)} months of real AWS cost trend data")
            return trend_data
            
        except Exception as e:
            from .error_handler import AWSErrorHandler
            user_email = getattr(self._config, 'AWS_USER_EMAIL', None) if self._config else None
            error_message = AWSErrorHandler.handle_aws_error(e, "Monthly Trend", user_email)
            logger.error(f"❌ Failed to fetch real AWS monthly trend: {error_message}")
            raise Exception(error_message)
    
    def _map_service_name(self, service_name: str) -> ServiceType:
        """Map AWS service name to ServiceType enum"""
        service_mapping = {
            'Amazon Elastic Compute Cloud - Compute': ServiceType.EC2,
            'Amazon Relational Database Service': ServiceType.RDS,
            'Amazon Simple Storage Service': ServiceType.S3,
            'Amazon Elastic Block Store': ServiceType.EBS,
            'AWS Lambda': ServiceType.LAMBDA,
            'Amazon CloudWatch': ServiceType.CLOUDWATCH,
            'AWS Cost Explorer': ServiceType.COST_EXPLORER,
            'Amazon Bedrock': ServiceType.BEDROCK,
            # Additional common AWS services
            'AWS Key Management Service': ServiceType.OTHER,
            'AWS CloudTrail': ServiceType.OTHER,
            'AWS Config': ServiceType.OTHER,
            'Amazon CloudFront': ServiceType.OTHER,
            'Amazon Route 53': ServiceType.OTHER,
            'AWS Identity and Access Management': ServiceType.OTHER,
            'AWS Security Token Service': ServiceType.OTHER,
            'Amazon Virtual Private Cloud': ServiceType.OTHER,
            'AWS Support (Business)': ServiceType.OTHER,
            'AWS Support (Developer)': ServiceType.OTHER,
            'Tax': ServiceType.OTHER
        }
        
        # Try exact match first
        mapped_service = service_mapping.get(service_name)
        if mapped_service:
            return mapped_service
        
        # Try partial matches for common patterns
        service_lower = service_name.lower()
        if 'bedrock' in service_lower:
            return ServiceType.BEDROCK
        elif 'cost explorer' in service_lower:
            return ServiceType.COST_EXPLORER
        elif 'ec2' in service_lower or 'elastic compute' in service_lower:
            return ServiceType.EC2
        elif 's3' in service_lower or 'simple storage' in service_lower:
            return ServiceType.S3
        elif 'rds' in service_lower or 'relational database' in service_lower:
            return ServiceType.RDS
        elif 'ebs' in service_lower or 'elastic block store' in service_lower:
            return ServiceType.EBS
        elif 'lambda' in service_lower:
            return ServiceType.LAMBDA
        elif 'cloudwatch' in service_lower:
            return ServiceType.CLOUDWATCH
        
        # If no match found, return None (will be handled as unmapped)
        return None
    
