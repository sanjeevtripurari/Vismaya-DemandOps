"""
Enhanced Data Collector
Collects comprehensive AWS resource and cost data for tabular storage
Integrates with existing real usage analyzer and stores in SQLite
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json

from .tabular_data_service import TabularDataService
from ..infrastructure.real_usage_analyzer import RealUsageAnalyzer
from ..core.models import UsageSummary

logger = logging.getLogger(__name__)


class EnhancedDataCollector:
    """Enhanced data collector for comprehensive AWS resource and cost data"""
    
    def __init__(self, aws_session, config=None):
        self.aws_session = aws_session
        self.config = config
        self.tabular_service = TabularDataService()
        self.real_usage_analyzer = RealUsageAnalyzer(aws_session, config)
    
    async def collect_and_store_current_usage(self) -> Dict[str, Any]:
        """Collect current usage data and store in tabular format"""
        try:
            logger.info("🔍 Collecting comprehensive current usage data...")
            
            # Get usage summary from real usage analyzer
            usage_summary = await self._get_usage_summary()
            
            # Collect detailed resource data
            current_resources = await self._collect_current_resources(usage_summary)
            
            # Collect billing breakdown
            billing_breakdown = await self._collect_billing_breakdown(usage_summary)
            
            # Calculate cost summary
            cost_summary = self._calculate_cost_summary(current_resources, billing_breakdown, 'current')
            
            # Store all data
            await self._store_current_data(current_resources, billing_breakdown, cost_summary)
            
            logger.info("✅ Current usage data collected and stored successfully")
            
            return {
                'usage_summary': usage_summary,
                'current_resources': current_resources,
                'billing_breakdown': billing_breakdown,
                'cost_summary': cost_summary,
                'total_resources': len(current_resources),
                'total_cost': cost_summary.get('total_cost', 0)
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to collect current usage data: {e}")
            raise
    
    async def collect_and_store_forecasting_data(self, forecast_analysis: Dict[str, Any], query_context: str = "") -> Dict[str, Any]:
        """Collect forecasting data and store in tabular format"""
        try:
            logger.info("🔮 Processing forecasting data for tabular storage...")
            
            # Extract resource costs from forecast analysis
            resource_costs = forecast_analysis.get('cost_analysis', {}).get('resource_costs', [])
            
            # Prepare forecasting data for storage
            forecasting_data = []
            for resource in resource_costs:
                forecasting_data.append({
                    'type': resource.get('type', 'Unknown'),
                    'quantity': resource.get('quantity', 1),
                    'instance_type': resource.get('instance_type', ''),
                    'duration_months': resource.get('duration_months', 1),
                    'storage_gb': resource.get('storage_gb', 0),
                    'hourly_rate': resource.get('hourly_rate', 0),
                    'monthly_compute_cost': resource.get('monthly_compute_cost', 0),
                    'monthly_storage_cost': resource.get('monthly_storage_cost', 0),
                    'monthly_total_cost': resource.get('monthly_total_cost', 0),
                    'total_cost': resource.get('total_cost', 0),
                    'ai_analysis': forecast_analysis.get('ai_response', '')
                })
            
            # Calculate forecast summary
            forecast_summary = self._calculate_cost_summary([], forecasting_data, 'forecast')
            
            # Store forecasting data
            success = self.tabular_service.store_forecasting_data(forecasting_data, query_context)
            if success:
                self.tabular_service.store_cost_summary('forecast', forecast_summary)
            
            logger.info(f"✅ Stored {len(forecasting_data)} forecasting records")
            
            return {
                'forecasting_data': forecasting_data,
                'forecast_summary': forecast_summary,
                'total_resources': sum(r.get('quantity', 0) for r in forecasting_data),
                'total_cost': forecast_summary.get('total_cost', 0)
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to process forecasting data: {e}")
            raise
    
    async def _get_usage_summary(self) -> UsageSummary:
        """Get usage summary from real usage analyzer using the existing use case"""
        try:
            # Use the existing GetUsageSummaryUseCase which already works correctly
            from ..application.use_cases import GetUsageSummaryUseCase
            from ..services.cost_service import CostAnalysisService
            from ..services.resource_service import ResourceManagementService
            from ..infrastructure.aws_resource_provider import AWSResourceProvider
            
            # Create the services needed for the use case
            cost_service = CostAnalysisService(
                self.real_usage_analyzer,  # Use real usage analyzer as cost provider
                None,  # No forecasting service needed here
                None   # No AI assistant needed here
            )
            
            resource_service = ResourceManagementService(
                AWSResourceProvider(self.aws_session)
            )
            
            # Create and execute the use case
            usage_summary_use_case = GetUsageSummaryUseCase(
                cost_service,
                resource_service,
                self.config
            )
            
            # Execute the use case to get real usage summary
            usage_summary = await usage_summary_use_case.execute()
            
            logger.info(f"✅ Retrieved real usage summary with {len(usage_summary.service_costs)} services")
            return usage_summary
            
        except Exception as e:
            logger.error(f"❌ Failed to get usage summary: {e}")
            raise
    
    async def _collect_current_resources(self, usage_summary: UsageSummary) -> List[Dict[str, Any]]:
        """Collect detailed current resource data including all AWS services"""
        try:
            current_resources = []
            
            # Process EC2 instances (only if they have costs)
            for ec2 in usage_summary.ec2_instances:
                if ec2.monthly_cost <= 0:
                    continue
                    
                resource_data = {
                    'resource_type': 'EC2 Instance',
                    'resource_id': ec2.instance_id,
                    'instance_type': ec2.instance_type,
                    'region': 'us-east-2',  # Default region since not in model
                    'availability_zone': 'us-east-2a',  # Default AZ since not in model
                    'state': str(ec2.state.value) if hasattr(ec2.state, 'value') else str(ec2.state),
                    'monthly_cost': ec2.monthly_cost,
                    'daily_cost': ec2.monthly_cost / 30,
                    'hourly_cost': ec2.monthly_cost / (30 * 24),
                    'storage_gb': 0,  # Will be calculated from attached volumes
                    'storage_cost': 0,
                    'compute_cost': ec2.monthly_cost,
                    'network_cost': 0,
                    'tags': ec2.tags or {},
                    'metadata': {
                        'service_category': 'Compute',
                        'is_serverless': False,
                        'usage_type': 'Instance Hours',
                        'billing_mode': 'Hourly'
                    }
                }
                current_resources.append(resource_data)
            
            # Process storage volumes (only if they have costs)
            for volume in usage_summary.storage_volumes:
                if volume.monthly_cost <= 0:
                    continue
                    
                resource_data = {
                    'resource_type': 'EBS Volume',
                    'resource_id': volume.volume_id,
                    'instance_type': volume.volume_type,
                    'region': 'us-east-2',  # Default region since not in model
                    'availability_zone': 'us-east-2a',  # Default AZ since not in model
                    'state': 'in-use',  # Default state since not in model
                    'monthly_cost': volume.monthly_cost,
                    'daily_cost': volume.monthly_cost / 30,
                    'hourly_cost': volume.monthly_cost / (30 * 24),
                    'storage_gb': volume.size_gb,
                    'storage_cost': volume.monthly_cost,
                    'compute_cost': 0,
                    'network_cost': 0,
                    'tags': {},
                    'metadata': {
                        'service_category': 'Storage',
                        'is_serverless': False,
                        'attached_instance': volume.attached_instance or '',
                        'usage_type': 'Storage',
                        'billing_mode': 'Monthly'
                    }
                }
                current_resources.append(resource_data)
            
            # Process database instances (only if they have costs)
            for db in usage_summary.database_instances:
                if db.monthly_cost <= 0:
                    continue
                    
                resource_data = {
                    'resource_type': 'RDS Database',
                    'resource_id': db.db_instance_id,
                    'instance_type': db.instance_class,
                    'region': 'us-east-2',  # Default region since not in model
                    'availability_zone': 'us-east-2a',  # Default AZ since not in model
                    'state': db.status,
                    'monthly_cost': db.monthly_cost,
                    'daily_cost': db.monthly_cost / 30,
                    'hourly_cost': db.monthly_cost / (30 * 24),
                    'storage_gb': 0,  # Not available in simplified model
                    'storage_cost': db.monthly_cost * 0.3,  # Estimate 30% for storage
                    'compute_cost': db.monthly_cost * 0.7,  # Estimate 70% for compute
                    'network_cost': 0,
                    'tags': {},
                    'metadata': {
                        'service_category': 'Database',
                        'is_serverless': False,
                        'engine': db.engine,
                        'usage_type': 'Database Hours',
                        'billing_mode': 'Hourly'
                    }
                }
                current_resources.append(resource_data)
            
            # Process ALL AWS services from service costs (including serverless)
            for service_cost in usage_summary.service_costs:
                # ServiceCost has service_type and cost attributes
                service_type = service_cost.service_type
                service_amount = service_cost.cost.amount
                
                # Skip if cost is zero or very small (less than $0.01)
                if service_amount < 0.01:
                    continue
                
                # Get service name from service type
                service_name = service_type.value if hasattr(service_type, 'value') else str(service_type)
                
                # Determine service category and type
                service_info = self._analyze_service_info(service_name)
                
                resource_data = {
                    'resource_type': service_info['display_name'],
                    'resource_id': service_info['resource_id'],
                    'instance_type': service_info['service_type'],
                    'region': service_info['region'],
                    'availability_zone': service_info['availability_zone'],
                    'state': service_info['state'],
                    'monthly_cost': service_amount,
                    'daily_cost': service_amount / 30,
                    'hourly_cost': service_amount / (30 * 24),
                    'storage_gb': service_info['storage_gb'],
                    'storage_cost': service_info['storage_cost'],
                    'compute_cost': service_info['compute_cost'],
                    'network_cost': service_info['network_cost'],
                    'tags': {},
                    'metadata': {
                        'service_category': service_info['category'],
                        'service_name': service_name,
                        'is_serverless': service_info['is_serverless'],
                        'usage_type': service_info['usage_type'],
                        'billing_mode': service_info['billing_mode']
                    }
                }
                current_resources.append(resource_data)
            
            return current_resources
            
        except Exception as e:
            logger.error(f"❌ Failed to collect current resources: {e}")
            return []
    
    def _analyze_service_info(self, service_name: str) -> Dict[str, Any]:
        """Analyze AWS service to extract detailed information"""
        service_name_lower = service_name.lower()
        
        # Bedrock AI Services
        if 'bedrock' in service_name_lower or 'claude' in service_name_lower:
            return {
                'display_name': 'Bedrock AI Service',
                'resource_id': f"bedrock-{service_name.replace(' ', '-').lower()}",
                'service_type': 'AI/ML API',
                'region': 'us-east-2',
                'availability_zone': 'Multi-AZ',
                'state': 'active',
                'storage_gb': 0,
                'storage_cost': 0,
                'compute_cost': 0,  # All cost is usage-based
                'network_cost': 0,
                'category': 'AI/ML',
                'is_serverless': True,
                'usage_type': 'API Calls',
                'billing_mode': 'Pay-per-use'
            }
        
        # EC2 Related Services
        elif 'ec2' in service_name_lower or 'elastic compute' in service_name_lower:
            return {
                'display_name': 'EC2 Service',
                'resource_id': f"ec2-{service_name.replace(' ', '-').lower()}",
                'service_type': 'Compute Service',
                'region': 'us-east-2',
                'availability_zone': 'Multi-AZ',
                'state': 'active',
                'storage_gb': 0,
                'storage_cost': 0,
                'compute_cost': 0,
                'network_cost': 0,
                'category': 'Compute',
                'is_serverless': False,
                'usage_type': 'Instance Hours',
                'billing_mode': 'Hourly'
            }
        
        # VPC and Networking
        elif 'vpc' in service_name_lower or 'virtual private cloud' in service_name_lower:
            return {
                'display_name': 'VPC Service',
                'resource_id': f"vpc-{service_name.replace(' ', '-').lower()}",
                'service_type': 'Network Service',
                'region': 'us-east-2',
                'availability_zone': 'Multi-AZ',
                'state': 'active',
                'storage_gb': 0,
                'storage_cost': 0,
                'compute_cost': 0,
                'network_cost': 0,
                'category': 'Network',
                'is_serverless': True,
                'usage_type': 'Network Usage',
                'billing_mode': 'Usage-based'
            }
        
        # Cost Explorer
        elif 'cost explorer' in service_name_lower:
            return {
                'display_name': 'Cost Explorer',
                'resource_id': 'cost-explorer-api',
                'service_type': 'Management Service',
                'region': 'Global',
                'availability_zone': 'Global',
                'state': 'active',
                'storage_gb': 0,
                'storage_cost': 0,
                'compute_cost': 0,
                'network_cost': 0,
                'category': 'Management',
                'is_serverless': True,
                'usage_type': 'API Requests',
                'billing_mode': 'Per-request'
            }
        
        # S3 Storage
        elif 's3' in service_name_lower or 'simple storage' in service_name_lower:
            return {
                'display_name': 'S3 Storage',
                'resource_id': f"s3-{service_name.replace(' ', '-').lower()}",
                'service_type': 'Object Storage',
                'region': 'us-east-2',
                'availability_zone': 'Multi-AZ',
                'state': 'active',
                'storage_gb': 0,  # Would need to query S3 API for actual size
                'storage_cost': 0,
                'compute_cost': 0,
                'network_cost': 0,
                'category': 'Storage',
                'is_serverless': True,
                'usage_type': 'Storage + Requests',
                'billing_mode': 'Usage-based'
            }
        
        # Lambda Functions
        elif 'lambda' in service_name_lower:
            return {
                'display_name': 'Lambda Function',
                'resource_id': f"lambda-{service_name.replace(' ', '-').lower()}",
                'service_type': 'Serverless Compute',
                'region': 'us-east-2',
                'availability_zone': 'Multi-AZ',
                'state': 'active',
                'storage_gb': 0,
                'storage_cost': 0,
                'compute_cost': 0,
                'network_cost': 0,
                'category': 'Compute',
                'is_serverless': True,
                'usage_type': 'Invocations + Duration',
                'billing_mode': 'Pay-per-use'
            }
        
        # API Gateway
        elif 'api gateway' in service_name_lower:
            return {
                'display_name': 'API Gateway',
                'resource_id': f"apigateway-{service_name.replace(' ', '-').lower()}",
                'service_type': 'API Management',
                'region': 'us-east-2',
                'availability_zone': 'Multi-AZ',
                'state': 'active',
                'storage_gb': 0,
                'storage_cost': 0,
                'compute_cost': 0,
                'network_cost': 0,
                'category': 'Network',
                'is_serverless': True,
                'usage_type': 'API Requests',
                'billing_mode': 'Per-request'
            }
        
        # CloudWatch
        elif 'cloudwatch' in service_name_lower:
            return {
                'display_name': 'CloudWatch',
                'resource_id': f"cloudwatch-{service_name.replace(' ', '-').lower()}",
                'service_type': 'Monitoring Service',
                'region': 'us-east-2',
                'availability_zone': 'Multi-AZ',
                'state': 'active',
                'storage_gb': 0,
                'storage_cost': 0,
                'compute_cost': 0,
                'network_cost': 0,
                'category': 'Management',
                'is_serverless': True,
                'usage_type': 'Metrics + Logs',
                'billing_mode': 'Usage-based'
            }
        
        # DynamoDB
        elif 'dynamodb' in service_name_lower:
            return {
                'display_name': 'DynamoDB',
                'resource_id': f"dynamodb-{service_name.replace(' ', '-').lower()}",
                'service_type': 'NoSQL Database',
                'region': 'us-east-2',
                'availability_zone': 'Multi-AZ',
                'state': 'active',
                'storage_gb': 0,
                'storage_cost': 0,
                'compute_cost': 0,
                'network_cost': 0,
                'category': 'Database',
                'is_serverless': True,
                'usage_type': 'Read/Write Units',
                'billing_mode': 'On-demand'
            }
        
        # Default for unknown services
        else:
            return {
                'display_name': service_name,
                'resource_id': f"service-{service_name.replace(' ', '-').lower()}",
                'service_type': 'AWS Service',
                'region': 'us-east-2',
                'availability_zone': 'Multi-AZ',
                'state': 'active',
                'storage_gb': 0,
                'storage_cost': 0,
                'compute_cost': 0,
                'network_cost': 0,
                'category': 'Other',
                'is_serverless': True,
                'usage_type': 'Usage-based',
                'billing_mode': 'Pay-per-use'
            }
    
    async def _collect_billing_breakdown(self, usage_summary: UsageSummary) -> List[Dict[str, Any]]:
        """Collect detailed billing breakdown"""
        try:
            billing_breakdown = []
            
            # Process service costs
            for service_cost in usage_summary.service_costs:
                # Get service name from service type
                service_name = service_cost.service_type.value if hasattr(service_cost.service_type, 'value') else str(service_cost.service_type)
                service_amount = service_cost.cost.amount
                
                billing_item = {
                    'service_name': service_name,
                    'service_category': self._categorize_service(service_name),
                    'usage_type': 'Monthly Usage',
                    'operation': 'Standard',
                    'resource_id': '',
                    'usage_amount': 1,
                    'usage_unit': 'month',
                    'rate': service_amount,
                    'cost': service_amount,
                    'currency': 'USD',
                    'tax_amount': service_amount * 0.08,  # Estimate 8% tax
                    'total_amount': service_amount * 1.08,
                    'region': 'us-east-2',  # Default region
                    'metadata': {
                        'service_type': str(service_cost.service_type)
                    }
                }
                billing_breakdown.append(billing_item)
            
            return billing_breakdown
            
        except Exception as e:
            logger.error(f"❌ Failed to collect billing breakdown: {e}")
            return []
    
    def _categorize_service(self, service_name: str) -> str:
        """Categorize AWS service"""
        service_name_lower = service_name.lower()
        
        if any(keyword in service_name_lower for keyword in ['ec2', 'compute', 'instance']):
            return 'Compute'
        elif any(keyword in service_name_lower for keyword in ['s3', 'storage', 'ebs']):
            return 'Storage'
        elif any(keyword in service_name_lower for keyword in ['rds', 'database', 'dynamodb']):
            return 'Database'
        elif any(keyword in service_name_lower for keyword in ['vpc', 'network', 'cloudfront']):
            return 'Network'
        elif any(keyword in service_name_lower for keyword in ['bedrock', 'ai', 'ml']):
            return 'AI/ML'
        else:
            return 'Other'
    
    def _calculate_cost_summary(self, current_resources: List[Dict[str, Any]], 
                               billing_data: List[Dict[str, Any]], summary_type: str) -> Dict[str, Any]:
        """Calculate comprehensive cost summary"""
        try:
            summary = {
                'total_compute_cost': 0,
                'total_storage_cost': 0,
                'total_network_cost': 0,
                'total_database_cost': 0,
                'total_other_cost': 0,
                'subtotal': 0,
                'tax_amount': 0,
                'total_cost': 0,
                'resource_count': len(current_resources),
                'active_services': 0,
                'metadata': {}
            }
            
            # Calculate from current resources
            for resource in current_resources:
                resource_type = resource.get('resource_type', '').upper()
                monthly_cost = resource.get('monthly_cost', 0)
                
                if resource_type == 'EC2':
                    summary['total_compute_cost'] += monthly_cost
                elif resource_type == 'EBS':
                    summary['total_storage_cost'] += monthly_cost
                elif resource_type == 'RDS':
                    summary['total_database_cost'] += monthly_cost
                else:
                    summary['total_other_cost'] += monthly_cost
            
            # Calculate from billing data
            service_categories = set()
            for item in billing_data:
                category = item.get('service_category', 'Other')
                cost = item.get('cost', 0)
                tax = item.get('tax_amount', 0)
                
                service_categories.add(category)
                
                if category == 'Compute':
                    summary['total_compute_cost'] += cost
                elif category == 'Storage':
                    summary['total_storage_cost'] += cost
                elif category == 'Network':
                    summary['total_network_cost'] += cost
                elif category == 'Database':
                    summary['total_database_cost'] += cost
                else:
                    summary['total_other_cost'] += cost
                
                summary['tax_amount'] += tax
            
            # Calculate totals
            summary['subtotal'] = (
                summary['total_compute_cost'] + 
                summary['total_storage_cost'] + 
                summary['total_network_cost'] + 
                summary['total_database_cost'] + 
                summary['total_other_cost']
            )
            
            summary['total_cost'] = summary['subtotal'] + summary['tax_amount']
            summary['active_services'] = len(service_categories)
            
            # Add metadata
            summary['metadata'] = {
                'summary_type': summary_type,
                'calculation_date': datetime.now().isoformat(),
                'service_categories': list(service_categories)
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ Failed to calculate cost summary: {e}")
            return {}
    
    async def _store_current_data(self, current_resources: List[Dict[str, Any]], 
                                 billing_breakdown: List[Dict[str, Any]], 
                                 cost_summary: Dict[str, Any]):
        """Store all current data in database"""
        try:
            # Store current resources
            if current_resources:
                self.tabular_service.store_current_resources(current_resources)
            
            # Store billing breakdown
            if billing_breakdown:
                self.tabular_service.store_billing_breakdown(billing_breakdown)
            
            # Store cost summary
            if cost_summary:
                self.tabular_service.store_cost_summary('current', cost_summary)
            
            logger.info("✅ All current data stored successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to store current data: {e}")
            raise