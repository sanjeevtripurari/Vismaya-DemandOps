"""
Advanced Forecasting AI Assistant
Handles complex resource queries using AI agents and provides detailed cost analysis
"""

import json
import re
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import asyncio

from ..core.models import ServiceType
from ..strands.billing_analysis_strand import BillingAnalysisStrand
from ..infrastructure.pricing_logger import log_pricing_operation

logger = logging.getLogger(__name__)


class AdvancedForecastingAssistant:
    """Advanced AI assistant for complex forecasting queries"""
    
    def __init__(self, bedrock_client, aws_session, config):
        self.bedrock = bedrock_client
        self.session = aws_session
        self.config = config
        self.billing_strand = BillingAnalysisStrand()
        self.model_id = config.BEDROCK_MODEL_ID
    
    async def analyze_complex_query(self, user_query: str, current_usage: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze complex resource requirements query using AI agents"""
        try:
            logger.info(f"🤖 Analyzing complex query: {user_query[:100]}...")
            
            # Step 1: Parse the query using Bedrock AI
            parsed_requirements = await self._parse_resource_requirements(user_query)
            
            # Step 2: Get current AWS pricing using agent strands
            pricing_data = await self._get_current_pricing(parsed_requirements)
            
            # Step 3: Calculate costs for requested resources
            cost_analysis = await self._calculate_resource_costs(parsed_requirements, pricing_data)
            
            # Step 4: Compare with current usage
            comparison_analysis = await self._compare_with_current_usage(cost_analysis, current_usage)
            
            # Step 5: Generate comprehensive response
            ai_response = await self._generate_comprehensive_response(
                user_query, parsed_requirements, cost_analysis, comparison_analysis
            )
            
            return {
                'parsed_requirements': parsed_requirements,
                'cost_analysis': cost_analysis,
                'comparison_analysis': comparison_analysis,
                'ai_response': ai_response,
                'pricing_data': pricing_data,
                'query_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing complex query: {e}")
            return await self._generate_fallback_response(user_query)
    
    async def _parse_resource_requirements(self, user_query: str) -> Dict[str, Any]:
        """Parse user query to extract resource requirements using Bedrock AI"""
        try:
            prompt = f"""
            You are an AWS cost analysis expert. Parse this user query and extract the exact resource requirements in JSON format.

            User Query: "{user_query}"

            Extract and return ONLY a JSON object with this structure:
            {{
                "resources": [
                    {{
                        "type": "ec2|rds|s3|lambda|elastic_ip|eip|other",
                        "instance_type": "t3.large|db.t3.micro|standard|etc",
                        "quantity": number,
                        "duration_months": number,
                        "storage_gb": number (if applicable),
                        "specifications": {{
                            "any_additional_specs": "value"
                        }}
                    }}
                ],
                "total_duration_months": number,
                "summary": "brief summary of requirements"
            }}

            Examples:
            - "2 EC2 large instances" → type: "ec2", instance_type: "t3.large", quantity: 2
            - "3 postgres databases" → type: "rds", instance_type: "db.t3.micro", quantity: 3
            - "1 elastic ip" → type: "elastic_ip", instance_type: "standard", quantity: 1
            - "3 elastic ips" → type: "elastic_ip", instance_type: "standard", quantity: 3
            - "30 GB storage" → storage_gb: 30
            - "for 2 months" → duration_months: 2

            IMPORTANT: Always detect elastic IPs, EIPs, static IPs as type: "elastic_ip"

            Return ONLY the JSON, no other text.
            """
            
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "messages": [{"role": "user", "content": prompt}]
            })
            
            response = self.bedrock.invoke_model(
                body=body,
                modelId=self.model_id,
                accept='application/json',
                contentType='application/json'
            )
            
            response_body = json.loads(response.get('body').read())
            ai_text = response_body['content'][0]['text']
            
            # Extract JSON from AI response
            json_match = re.search(r'\{.*\}', ai_text, re.DOTALL)
            if json_match:
                parsed_json = json.loads(json_match.group())
                logger.info(f"✅ Parsed requirements: {len(parsed_json.get('resources', []))} resources")
                return parsed_json
            
            # Fallback parsing
            return await self._fallback_parse_query(user_query)
            
        except Exception as e:
            logger.error(f"Error parsing requirements: {e}")
            return await self._fallback_parse_query(user_query)
    
    async def _fallback_parse_query(self, user_query: str) -> Dict[str, Any]:
        """Fallback parsing using regex patterns"""
        resources = []
        query_lower = user_query.lower()
        
        # Parse EC2 instances
        ec2_match = re.search(r'(\d+)\s+ec2\s+(\w+)\s+instance', query_lower)
        if ec2_match:
            quantity = int(ec2_match.group(1))
            size = ec2_match.group(2)
            instance_type = f"t3.{size}" if size in ['micro', 'small', 'medium', 'large', 'xlarge'] else "t3.large"
            
            resources.append({
                "type": "ec2",
                "instance_type": instance_type,
                "quantity": quantity,
                "duration_months": 1,
                "storage_gb": 30,
                "specifications": {}
            })
        
        # Parse Elastic IPs
        eip_patterns = [
            r'(\d+)\s+elastic\s+ip',
            r'(\d+)\s+eip',
            r'(\d+)\s+static\s+ip'
        ]
        
        for pattern in eip_patterns:
            eip_match = re.search(pattern, query_lower)
            if eip_match:
                quantity = int(eip_match.group(1))
                resources.append({
                    "type": "elastic_ip",
                    "instance_type": "standard",
                    "quantity": quantity,
                    "duration_months": 1,
                    "storage_gb": 0,
                    "specifications": {}
                })
                break
        
        # Parse RDS/Postgres
        rds_match = re.search(r'(\d+)\s+postgres', query_lower)
        if rds_match:
            quantity = int(rds_match.group(1))
            resources.append({
                "type": "rds",
                "instance_type": "db.t3.micro",
                "quantity": quantity,
                "duration_months": 1,
                "storage_gb": 20,
                "specifications": {"engine": "postgres"}
            })
        
        # Parse duration
        duration_match = re.search(r'(\d+)\s+months?', query_lower)
        duration_months = int(duration_match.group(1)) if duration_match else 1
        
        # Parse storage
        storage_match = re.search(r'(\d+)\s+gb\s+storage', query_lower)
        storage_gb = int(storage_match.group(1)) if storage_match else 30
        
        # Update resources with parsed duration and storage
        for resource in resources:
            resource['duration_months'] = duration_months
            if resource['type'] == 'ec2':
                resource['storage_gb'] = storage_gb
        
        return {
            "resources": resources,
            "total_duration_months": duration_months,
            "summary": f"Parsed {len(resources)} resources for {duration_months} months"
        }
    
    async def _get_current_pricing(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Get current AWS pricing using agent strands"""
        try:
            pricing_data = {}
            
            for resource in requirements.get('resources', []):
                resource_type = resource['type']
                instance_type = resource.get('instance_type', '')
                
                # Get pricing from public AWS sources
                if resource_type == 'ec2':
                    pricing_data['ec2'] = await self._get_ec2_pricing(instance_type)
                elif resource_type == 'rds':
                    pricing_data['rds'] = await self._get_rds_pricing(instance_type)
                elif resource_type == 's3':
                    pricing_data['s3'] = await self._get_s3_pricing()
            
            return pricing_data
            
        except Exception as e:
            logger.error(f"Error getting pricing: {e}")
            return {}
    
    async def _get_ec2_pricing(self, instance_type: str) -> Dict[str, float]:
        """Get EC2 pricing from public sources"""
        # Standard EC2 pricing (approximate US East rates)
        ec2_pricing = {
            't3.micro': 0.0104,
            't3.small': 0.0208,
            't3.medium': 0.0416,
            't3.large': 0.0832,
            't3.xlarge': 0.1664,
            't3.2xlarge': 0.3328,
            'm5.large': 0.096,
            'm5.xlarge': 0.192,
            'c5.large': 0.085,
            'c5.xlarge': 0.17
        }
        
        hourly_rate = ec2_pricing.get(instance_type, 0.0832)  # Default to t3.large
        
        return {
            'hourly_rate': hourly_rate,
            'monthly_rate': hourly_rate * 24 * 30,
            'storage_rate_gb': 0.10,  # EBS GP3 pricing per GB per month
            'instance_type': instance_type
        }
    
    async def _get_rds_pricing(self, instance_type: str) -> Dict[str, float]:
        """Get RDS pricing from public sources"""
        # Standard RDS pricing (approximate US East rates)
        rds_pricing = {
            'db.t3.micro': 0.017,
            'db.t3.small': 0.034,
            'db.t3.medium': 0.068,
            'db.t3.large': 0.136,
            'db.t3.xlarge': 0.272,
            'db.m5.large': 0.192,
            'db.m5.xlarge': 0.384
        }
        
        hourly_rate = rds_pricing.get(instance_type, 0.017)  # Default to db.t3.micro
        
        return {
            'hourly_rate': hourly_rate,
            'monthly_rate': hourly_rate * 24 * 30,
            'storage_rate_gb': 0.115,  # RDS storage pricing per GB per month
            'instance_type': instance_type
        }
    
    async def _get_s3_pricing(self) -> Dict[str, float]:
        """Get S3 pricing from public sources"""
        return {
            'standard_storage_gb': 0.023,  # Per GB per month
            'requests_per_1000': 0.0004,  # PUT/POST requests
            'data_transfer_gb': 0.09  # Data transfer out per GB
        }
    
    async def _calculate_resource_costs(self, requirements: Dict[str, Any], pricing_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate detailed costs for all requested resources"""
        try:
            total_monthly_cost = 0
            total_cost = 0
            resource_costs = []
            
            for resource in requirements.get('resources', []):
                resource_type = resource['type']
                quantity = resource.get('quantity', 1)
                duration_months = resource.get('duration_months', 1) or 1  # Ensure not None
                storage_gb = resource.get('storage_gb', 20) or 0  # Default storage, ensure not None
                
                if resource_type == 'ec2' and 'ec2' in pricing_data:
                    pricing = pricing_data['ec2']
                    
                    # Calculate EC2 costs with null checks
                    monthly_compute = (pricing.get('monthly_rate', 0) or 0) * quantity
                    monthly_storage = (pricing.get('storage_rate_gb', 0) or 0) * storage_gb * quantity
                    monthly_total = monthly_compute + monthly_storage
                    total_resource_cost = monthly_total * duration_months
                    
                    resource_costs.append({
                        'type': 'EC2',
                        'instance_type': resource.get('instance_type', 't3.large'),
                        'quantity': quantity,
                        'duration_months': duration_months,
                        'storage_gb': storage_gb,
                        'monthly_compute_cost': monthly_compute,
                        'monthly_storage_cost': monthly_storage,
                        'monthly_total_cost': monthly_total,
                        'total_cost': total_resource_cost,
                        'hourly_rate': pricing.get('hourly_rate', 0) or 0
                    })
                    
                    total_monthly_cost += monthly_total
                    total_cost += total_resource_cost
                
                elif resource_type == 'rds' and 'rds' in pricing_data:
                    pricing = pricing_data['rds']
                    
                    # Calculate RDS costs with null checks
                    monthly_compute = (pricing.get('monthly_rate', 0) or 0) * quantity
                    monthly_storage = (pricing.get('storage_rate_gb', 0) or 0) * storage_gb * quantity
                    monthly_total = monthly_compute + monthly_storage
                    total_resource_cost = monthly_total * duration_months
                    
                    resource_costs.append({
                        'type': 'RDS',
                        'instance_type': resource.get('instance_type', 'db.t3.micro'),
                        'quantity': quantity,
                        'duration_months': duration_months,
                        'storage_gb': storage_gb,
                        'monthly_compute_cost': monthly_compute,
                        'monthly_storage_cost': monthly_storage,
                        'monthly_total_cost': monthly_total,
                        'total_cost': total_resource_cost,
                        'hourly_rate': pricing.get('hourly_rate', 0) or 0
                    })
                    
                    total_monthly_cost += monthly_total
                    total_cost += total_resource_cost
                
                elif resource_type in ['elastic_ip', 'eip']:
                    # Elastic IP pricing: $0.005 per hour when attached, $0.005 per hour when not attached
                    # Monthly cost: $0.005 * 24 * 30 = $3.60 per month per IP
                    hourly_rate = 0.005
                    monthly_cost_per_ip = hourly_rate * 24 * 30  # $3.60 per month
                    monthly_total = monthly_cost_per_ip * quantity
                    total_resource_cost = monthly_total * duration_months
                    
                    resource_costs.append({
                        'type': 'Elastic IP',
                        'instance_type': 'standard',
                        'quantity': quantity,
                        'duration_months': duration_months,
                        'storage_gb': 0,
                        'monthly_compute_cost': monthly_total,
                        'monthly_storage_cost': 0,
                        'monthly_total_cost': monthly_total,
                        'total_cost': total_resource_cost,
                        'hourly_rate': hourly_rate
                    })
                    
                    total_monthly_cost += monthly_total
                    total_cost += total_resource_cost
            
            return {
                'resource_costs': resource_costs,
                'total_monthly_cost': total_monthly_cost,
                'total_cost': total_cost,
                'duration_months': requirements.get('total_duration_months', 1),
                'cost_breakdown': self._generate_cost_breakdown(resource_costs)
            }
            
        except Exception as e:
            logger.error(f"Error calculating costs: {e}")
            return {'resource_costs': [], 'total_monthly_cost': 0, 'total_cost': 0}
    
    def _generate_cost_breakdown(self, resource_costs: List[Dict[str, Any]]) -> Dict[str, float]:
        """Generate cost breakdown by service type"""
        breakdown = {'EC2': 0, 'RDS': 0, 'S3': 0, 'Other': 0}
        
        for resource in resource_costs:
            service_type = resource['type']
            if service_type in breakdown:
                breakdown[service_type] += resource['total_cost']
            else:
                breakdown['Other'] += resource['total_cost']
        
        return breakdown
    
    async def _compare_with_current_usage(self, cost_analysis: Dict[str, Any], current_usage: Dict[str, Any]) -> Dict[str, Any]:
        """Compare requested resources with current usage"""
        try:
            current_monthly_cost = current_usage.get('current_spend', 0)
            requested_monthly_cost = cost_analysis.get('total_monthly_cost', 0)
            
            # Calculate impact
            cost_increase = requested_monthly_cost
            percentage_increase = (cost_increase / current_monthly_cost * 100) if current_monthly_cost > 0 else 0
            new_total_monthly = current_monthly_cost + requested_monthly_cost
            
            # Resource comparison
            current_resources = self._count_current_resources(current_usage)
            requested_resources = self._count_requested_resources(cost_analysis)
            
            return {
                'current_monthly_cost': current_monthly_cost,
                'requested_monthly_cost': requested_monthly_cost,
                'cost_increase': cost_increase,
                'percentage_increase': percentage_increase,
                'new_total_monthly': new_total_monthly,
                'current_resources': current_resources,
                'requested_resources': requested_resources,
                'resource_comparison': self._generate_resource_comparison(current_resources, requested_resources)
            }
            
        except Exception as e:
            logger.error(f"Error comparing usage: {e}")
            return {}
    
    def _count_current_resources(self, current_usage: Dict[str, Any]) -> Dict[str, int]:
        """Count current resources by type"""
        return {
            'ec2_instances': len(current_usage.get('ec2_instances', [])),
            'rds_instances': len(current_usage.get('database_instances', [])),
            's3_buckets': len(current_usage.get('storage_volumes', [])),
            'total_services': len(current_usage.get('service_costs', []))
        }
    
    def _count_requested_resources(self, cost_analysis: Dict[str, Any]) -> Dict[str, int]:
        """Count requested resources by type"""
        counts = {'ec2_instances': 0, 'rds_instances': 0, 's3_buckets': 0}
        
        for resource in cost_analysis.get('resource_costs', []):
            if resource['type'] == 'EC2':
                counts['ec2_instances'] += resource['quantity']
            elif resource['type'] == 'RDS':
                counts['rds_instances'] += resource['quantity']
            elif resource['type'] == 'S3':
                counts['s3_buckets'] += resource['quantity']
        
        return counts
    
    def _generate_resource_comparison(self, current: Dict[str, int], requested: Dict[str, int]) -> Dict[str, Dict[str, int]]:
        """Generate detailed resource comparison"""
        comparison = {}
        
        for resource_type in ['ec2_instances', 'rds_instances', 's3_buckets']:
            current_count = current.get(resource_type, 0)
            requested_count = requested.get(resource_type, 0)
            
            comparison[resource_type] = {
                'current': current_count,
                'requested': requested_count,
                'new_total': current_count + requested_count,
                'increase': requested_count
            }
        
        return comparison
    
    async def _generate_comprehensive_response(self, user_query: str, requirements: Dict[str, Any], 
                                            cost_analysis: Dict[str, Any], comparison: Dict[str, Any]) -> str:
        """Generate comprehensive AI response using Bedrock"""
        try:
            prompt = f"""
            You are Vismaya, an expert AWS FinOps AI assistant. Provide a comprehensive cost analysis response.

            User Query: "{user_query}"

            Parsed Requirements:
            {json.dumps(requirements, indent=2)}

            Cost Analysis:
            {json.dumps(cost_analysis, indent=2)}

            Current Usage Comparison:
            {json.dumps(comparison, indent=2)}

            Provide a detailed response that includes:
            1. **Resource Summary**: What exactly was requested
            2. **Cost Breakdown**: Detailed cost analysis with monthly and total costs
            3. **Current vs New**: How this compares to current usage
            4. **Recommendations**: Cost optimization suggestions
            5. **Timeline**: Cost progression over the requested duration

            Format the response in markdown with clear sections and bullet points.
            Be specific about numbers, costs, and resource specifications.
            Keep it professional but conversational.
            """
            
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 2000,
                "messages": [{"role": "user", "content": prompt}]
            })
            
            response = self.bedrock.invoke_model(
                body=body,
                modelId=self.model_id,
                accept='application/json',
                contentType='application/json'
            )
            
            response_body = json.loads(response.get('body').read())
            return response_body['content'][0]['text']
            
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return self._generate_fallback_ai_response(cost_analysis, comparison)
    
    def _generate_fallback_ai_response(self, cost_analysis: Dict[str, Any], comparison: Dict[str, Any]) -> str:
        """Generate fallback response if Bedrock fails"""
        total_cost = cost_analysis.get('total_cost', 0)
        monthly_cost = cost_analysis.get('total_monthly_cost', 0)
        duration = cost_analysis.get('duration_months', 1)
        
        response = f"""
        ## 📊 Cost Analysis Results

        ### 💰 **Cost Summary**
        - **Monthly Cost**: ${monthly_cost:.2f}
        - **Total Cost ({duration} months)**: ${total_cost:.2f}
        - **Current Monthly**: ${comparison.get('current_monthly_cost', 0):.2f}
        - **New Total Monthly**: ${comparison.get('new_total_monthly', 0):.2f}

        ### 📈 **Impact Analysis**
        - **Cost Increase**: +${comparison.get('cost_increase', 0):.2f}/month
        - **Percentage Increase**: +{comparison.get('percentage_increase', 0):.1f}%

        ### 🔧 **Resource Details**
        """
        
        for resource in cost_analysis.get('resource_costs', []):
            response += f"""
        - **{resource['type']} {resource['instance_type']}**: {resource['quantity']} instances
          - Monthly: ${resource['monthly_total_cost']:.2f}
          - Total: ${resource['total_cost']:.2f}
        """
        
        return response
    
    async def _generate_fallback_response(self, user_query: str) -> Dict[str, Any]:
        """Generate fallback response if analysis fails"""
        return {
            'parsed_requirements': {
                'resources': [],
                'summary': 'Could not parse requirements'
            },
            'cost_analysis': {
                'resource_costs': [],
                'total_monthly_cost': 0,
                'total_cost': 0
            },
            'comparison_analysis': {},
            'ai_response': f"I apologize, but I encountered an error analyzing your query: '{user_query}'. Please try rephrasing your request with specific details about the AWS resources you need.",
            'pricing_data': {},
            'query_timestamp': datetime.now().isoformat()
        }
    
    async def generate_cost_trend_data(self, cost_analysis: Dict[str, Any], current_usage: Dict[str, Any]) -> Dict[str, Any]:
        """Generate data for cost trend visualization"""
        try:
            current_monthly = current_usage.get('current_spend', 0)
            requested_monthly = cost_analysis.get('total_monthly_cost', 0)
            duration_months = cost_analysis.get('duration_months', 1)
            
            # Generate timeline data
            timeline_data = []
            cumulative_data = []
            
            # Current baseline
            for i in range(6):  # 6 months history
                month_date = datetime.now() - timedelta(days=(6-i) * 30)
                timeline_data.append({
                    'month': month_date.strftime('%b %Y'),
                    'current_cost': current_monthly,
                    'with_new_resources': current_monthly,
                    'new_resources_only': 0
                })
            
            # Future with new resources
            cumulative_new_cost = 0
            for i in range(duration_months):
                month_date = datetime.now() + timedelta(days=(i+1) * 30)
                cumulative_new_cost += requested_monthly
                
                timeline_data.append({
                    'month': month_date.strftime('%b %Y'),
                    'current_cost': current_monthly,
                    'with_new_resources': current_monthly + requested_monthly,
                    'new_resources_only': requested_monthly
                })
                
                cumulative_data.append({
                    'month': month_date.strftime('%b %Y'),
                    'cumulative_cost': cumulative_new_cost,
                    'monthly_cost': requested_monthly
                })
            
            return {
                'timeline_data': timeline_data,
                'cumulative_data': cumulative_data,
                'summary': {
                    'current_monthly': current_monthly,
                    'requested_monthly': requested_monthly,
                    'total_new_cost': cost_analysis.get('total_cost', 0),
                    'duration_months': duration_months
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating trend data: {e}")
            return {'timeline_data': [], 'cumulative_data': [], 'summary': {}}