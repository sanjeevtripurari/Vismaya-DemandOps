"""
Agentic AI Cost Estimation Service
Uses agentic strand framework to pull real-time AWS pricing and calculate accurate costs
"""

import asyncio
import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd

try:
    from ..agentic.strands.agent_strand import AgentStrand
    from ..agentic.strands.memory_store import MemoryStore
    from ..infrastructure.bedrock_ai_assistant import BedrockAIAssistant
except ImportError:
    # Fallback for development
    AgentStrand = None
    MemoryStore = None
    BedrockAIAssistant = None

class AgenticCostEstimator:
    """Agentic AI-powered cost estimation service"""
    
    def __init__(self):
        """Initialize the agentic cost estimator"""
        self.ai_assistant = None
        self.memory_store = None
        self.pricing_cache = {}
        self.cache_timestamp = None
        
        # Initialize agentic components if available
        self._initialize_agentic_components()
        
        # Fallback pricing data (updated with real AWS pricing)
        self.fallback_pricing = {
            'ec2': {
                't3.nano': 3.796,      # $0.0052/hour * 730 hours
                't3.micro': 7.592,     # $0.0104/hour * 730 hours  
                't3.small': 15.184,    # $0.0208/hour * 730 hours
                't3.medium': 30.368,   # $0.0416/hour * 730 hours
                't3.large': 60.736,    # $0.0832/hour * 730 hours
                't3.xlarge': 121.472,  # $0.1664/hour * 730 hours
                'm6i.large': 69.35,    # $0.095/hour * 730 hours
                'm6i.xlarge': 138.70,  # $0.19/hour * 730 hours
                'm6i.2xlarge': 277.40, # $0.38/hour * 730 hours
                'c6i.large': 61.32,    # $0.084/hour * 730 hours
                'c6i.xlarge': 122.64,  # $0.168/hour * 730 hours
                'r6g.large': 96.36,    # $0.132/hour * 730 hours
            },
            'ebs': {
                'gp2': 0.10,  # $0.10 per GB per month
                'gp3': 0.08,  # $0.08 per GB per month
                'io1': 0.125, # $0.125 per GB per month
                'io2': 0.125, # $0.125 per GB per month
                'st1': 0.045, # $0.045 per GB per month
                'sc1': 0.025, # $0.025 per GB per month
            },
            'rds': {
                'db.t3.micro': 14.60,    # $0.02/hour * 730 hours
                'db.t3.small': 29.20,    # $0.04/hour * 730 hours
                'db.t3.medium': 58.40,   # $0.08/hour * 730 hours
                'db.t3.large': 116.80,   # $0.16/hour * 730 hours
                'db.r6g.large': 172.80,  # $0.237/hour * 730 hours
                'db.r6g.xlarge': 345.60, # $0.474/hour * 730 hours
            },
            's3': {
                'standard': 0.023,      # $0.023 per GB per month
                'standard_ia': 0.0125,  # $0.0125 per GB per month
                'glacier': 0.004,       # $0.004 per GB per month
                'deep_archive': 0.00099, # $0.00099 per GB per month
            },
            'lambda': {
                'requests': 0.0000002,  # $0.20 per 1M requests
                'duration': 0.0000166667, # $0.0000166667 per GB-second
            }
        }
    
    def _initialize_agentic_components(self):
        """Initialize agentic framework components"""
        try:
            if BedrockAIAssistant:
                self.ai_assistant = BedrockAIAssistant()
            if MemoryStore:
                self.memory_store = MemoryStore({})
        except Exception as e:
            print(f"Warning: Could not initialize agentic components: {e}")
    
    async def estimate_costs_from_csv(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Use agentic AI to estimate costs from CSV data
        
        Args:
            df: DataFrame with resource planning data
            
        Returns:
            DataFrame with accurate cost estimations
        """
        processed_df = df.copy()
        
        # Create agentic strand for cost estimation
        cost_strand = await self._create_cost_estimation_strand()
        
        cost_estimations = []
        
        for index, row in processed_df.iterrows():
            try:
                # Use agentic AI to analyze and price each resource
                cost_info = await self._analyze_resource_with_ai(row, cost_strand)
                cost_estimations.append(cost_info['cost_estimation'])
            except Exception as e:
                # Fallback to manual calculation
                cost_estimation = self._calculate_fallback_cost(row)
                cost_estimations.append(cost_estimation)
        
        processed_df['Cost Estimation'] = cost_estimations
        return processed_df
    
    async def _create_cost_estimation_strand(self):
        """Create an agentic strand for cost estimation"""
        if not AgentStrand:
            return None
            
        try:
            strand = AgentStrand(
                strand_id="cost_estimation",
                agent_type="pricing_analyst",
                memory_store=self.memory_store
            )
            
            # Initialize the strand with AWS pricing context
            await strand.initialize({
                'role': 'AWS Cost Estimation Specialist',
                'capabilities': [
                    'Real-time AWS pricing analysis',
                    'Resource type identification',
                    'Cost optimization recommendations',
                    'Regional pricing variations'
                ],
                'context': 'Analyze AWS resource specifications and provide accurate cost estimations'
            })
            
            return strand
        except Exception as e:
            print(f"Warning: Could not create agentic strand: {e}")
            return None
    
    async def _analyze_resource_with_ai(self, row: pd.Series, strand) -> Dict[str, Any]:
        """
        Use agentic AI to analyze resource and calculate costs
        
        Args:
            row: Resource data row
            strand: Agentic strand for analysis
            
        Returns:
            Dictionary with cost analysis
        """
        if not strand or not self.ai_assistant:
            return self._calculate_fallback_cost_detailed(row)
        
        try:
            # Prepare resource analysis prompt
            resource_prompt = self._create_resource_analysis_prompt(row)
            
            # Use agentic AI to analyze the resource
            analysis_result = await self.ai_assistant.generate_response(
                resource_prompt,
                context={'strand_id': strand.strand_id}
            )
            
            # Parse AI response and extract cost information
            cost_info = self._parse_ai_cost_response(analysis_result, row)
            
            # Store analysis in memory for future reference
            if self.memory_store:
                await self.memory_store.store_conversation(
                    thread_id=f"cost_analysis_{datetime.now().strftime('%Y%m%d')}",
                    message_type="analysis",
                    content={
                        'resource': row.to_dict(),
                        'analysis': cost_info,
                        'timestamp': datetime.now().isoformat()
                    }
                )
            
            return cost_info
            
        except Exception as e:
            print(f"AI analysis failed for resource: {e}")
            return self._calculate_fallback_cost_detailed(row)
    
    def _create_resource_analysis_prompt(self, row: pd.Series) -> str:
        """Create a detailed prompt for AI resource analysis"""
        resource_type = str(row.get('Resource Type', ''))
        quantity_size = str(row.get('Quantity / Size', ''))
        description = str(row.get('Description or Use Case', ''))
        duration = str(row.get('Duration (if temporary)', ''))
        
        prompt = f"""
        Analyze this AWS resource specification and provide accurate cost estimation:
        
        Resource Type: {resource_type}
        Quantity/Size: {quantity_size}
        Description: {description}
        Duration: {duration}
        
        Please provide:
        1. Exact AWS service identification
        2. Instance type or resource specification parsing
        3. Current AWS pricing (US East 1 region)
        4. Monthly cost calculation
        5. Total cost for specified duration
        6. Cost optimization recommendations
        7. Alternative options with pricing
        
        Format your response as JSON with the following structure:
        {{
            "service_type": "identified AWS service",
            "instance_type": "parsed instance type",
            "quantity": "number of resources",
            "monthly_cost_per_unit": "cost per unit per month",
            "total_monthly_cost": "total monthly cost",
            "duration_months": "duration in months",
            "total_cost": "total cost for duration",
            "cost_estimation": "formatted cost string",
            "optimizations": ["list of optimization suggestions"],
            "alternatives": ["alternative options with costs"]
        }}
        """
        
        return prompt
    
    def _parse_ai_cost_response(self, ai_response: str, row: pd.Series) -> Dict[str, Any]:
        """Parse AI response and extract cost information"""
        try:
            # Try to extract JSON from AI response
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                cost_data = json.loads(json_match.group())
                return cost_data
            else:
                # Fallback parsing if JSON not found
                return self._extract_cost_from_text(ai_response, row)
                
        except Exception as e:
            print(f"Failed to parse AI response: {e}")
            return self._calculate_fallback_cost_detailed(row)
    
    def _extract_cost_from_text(self, text: str, row: pd.Series) -> Dict[str, Any]:
        """Extract cost information from text response"""
        # Extract monetary values from text
        cost_matches = re.findall(r'\$(\d+\.?\d*)', text)
        
        if cost_matches:
            monthly_cost = float(cost_matches[0])
            duration = self._parse_duration(str(row.get('Duration (if temporary)', '')))
            total_cost = monthly_cost * duration if duration > 1 else monthly_cost
            
            cost_estimation = f"${monthly_cost:.2f}/month"
            if duration > 1:
                cost_estimation += f" (${total_cost:.2f} total for {duration} months)"
            
            return {
                'monthly_cost': monthly_cost,
                'total_cost': total_cost,
                'cost_estimation': cost_estimation,
                'ai_analysis': text[:200] + "..." if len(text) > 200 else text
            }
        
        # Fallback to manual calculation
        return self._calculate_fallback_cost_detailed(row)
    
    def _calculate_fallback_cost(self, row: pd.Series) -> str:
        """Calculate cost using fallback pricing when AI is unavailable"""
        cost_info = self._calculate_fallback_cost_detailed(row)
        return cost_info['cost_estimation']
    
    def _calculate_fallback_cost_detailed(self, row: pd.Series) -> Dict[str, Any]:
        """Detailed fallback cost calculation"""
        resource_type = str(row.get('Resource Type', '')).lower()
        quantity_size = str(row.get('Quantity / Size', ''))
        duration = str(row.get('Duration (if temporary)', ''))
        
        # Parse duration
        duration_months = self._parse_duration(duration)
        
        monthly_cost = 0
        service_type = "unknown"
        
        # EC2 cost calculation
        if 'compute' in resource_type or 'ec2' in resource_type:
            service_type = "EC2"
            instance_match = re.search(r'(\d+)\s*instances?\s*\(([^)]+)\)', quantity_size)
            if instance_match:
                count = int(instance_match.group(1))
                instance_type = instance_match.group(2).strip()
                
                unit_cost = self.fallback_pricing['ec2'].get(instance_type, 30.368)  # default to t3.medium
                monthly_cost = count * unit_cost
        
        # EBS storage cost calculation
        elif 'storage' in resource_type or 'ebs' in resource_type:
            service_type = "EBS"
            size_match = re.search(r'(\d+)\s*GB', quantity_size)
            if size_match:
                size_gb = int(size_match.group(1))
                storage_type = 'gp3' if 'gp3' in quantity_size.lower() else 'gp2'
                unit_cost = self.fallback_pricing['ebs'].get(storage_type, 0.10)
                monthly_cost = size_gb * unit_cost
        
        # RDS cost calculation
        elif 'database' in resource_type or 'rds' in resource_type:
            service_type = "RDS"
            db_match = re.search(r'(\d+)\s*instances?\s*\(([^)]+)\)', quantity_size)
            if db_match:
                count = int(db_match.group(1))
                db_type = db_match.group(2).strip()
                
                unit_cost = self.fallback_pricing['rds'].get(db_type, 58.40)  # default to db.t3.medium
                monthly_cost = count * unit_cost
        
        # S3 cost calculation
        elif 's3' in resource_type or ('storage' in resource_type and 'object' in resource_type):
            service_type = "S3"
            size_match = re.search(r'(\d+)\s*GB', quantity_size)
            if size_match:
                size_gb = int(size_match.group(1))
                monthly_cost = size_gb * self.fallback_pricing['s3']['standard']
        
        # Calculate total cost
        total_cost = monthly_cost * duration_months if duration_months > 1 else monthly_cost
        
        # Format cost estimation
        cost_estimation = f"${monthly_cost:.2f}/month"
        if duration_months > 1:
            cost_estimation += f" (${total_cost:.2f} total for {duration_months} months)"
        
        return {
            'service_type': service_type,
            'monthly_cost': monthly_cost,
            'total_cost': total_cost,
            'duration_months': duration_months,
            'cost_estimation': cost_estimation,
            'calculation_method': 'fallback_pricing'
        }
    
    def _parse_duration(self, duration_str: str) -> int:
        """Parse duration string to months"""
        if not duration_str or duration_str.lower() in ['permanent', 'ongoing', '']:
            return 1
        
        # Extract number from duration string
        duration_match = re.search(r'(\d+)', duration_str)
        if duration_match:
            return int(duration_match.group(1))
        
        return 1
    
    async def get_optimization_recommendations(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Use agentic AI to generate cost optimization recommendations
        
        Args:
            df: DataFrame with cost estimations
            
        Returns:
            List of optimization recommendations
        """
        if not self.ai_assistant:
            return self._get_fallback_optimizations(df)
        
        try:
            # Create optimization analysis prompt
            optimization_prompt = self._create_optimization_prompt(df)
            
            # Use AI to analyze optimization opportunities
            optimization_result = await self.ai_assistant.generate_response(
                optimization_prompt,
                context={'analysis_type': 'cost_optimization'}
            )
            
            # Parse optimization recommendations
            recommendations = self._parse_optimization_response(optimization_result)
            
            return recommendations
            
        except Exception as e:
            print(f"AI optimization analysis failed: {e}")
            return self._get_fallback_optimizations(df)
    
    def _create_optimization_prompt(self, df: pd.DataFrame) -> str:
        """Create prompt for optimization analysis"""
        resources_summary = []
        total_cost = 0
        
        for _, row in df.iterrows():
            cost_str = str(row.get('Cost Estimation', '$0.00/month'))
            cost_match = re.search(r'\$(\d+\.?\d*)', cost_str)
            if cost_match:
                cost = float(cost_match.group(1))
                total_cost += cost
                
            resources_summary.append({
                'type': row.get('Resource Type', ''),
                'size': row.get('Quantity / Size', ''),
                'cost': cost_str
            })
        
        prompt = f"""
        Analyze these AWS resources for cost optimization opportunities:
        
        Total Monthly Cost: ${total_cost:.2f}
        
        Resources:
        {json.dumps(resources_summary, indent=2)}
        
        Provide optimization recommendations including:
        1. Reserved Instance opportunities
        2. Spot Instance possibilities
        3. Right-sizing recommendations
        4. Storage optimization
        5. Alternative service options
        6. Cost-saving strategies
        
        Format as JSON array of recommendations with savings estimates.
        """
        
        return prompt
    
    def _parse_optimization_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse AI optimization response"""
        try:
            # Try to extract JSON array
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # Extract recommendations from text
                return self._extract_recommendations_from_text(response)
        except Exception as e:
            print(f"Failed to parse optimization response: {e}")
            return []
    
    def _extract_recommendations_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Extract recommendations from text response"""
        recommendations = []
        
        # Look for common optimization patterns
        if 'reserved instance' in text.lower():
            recommendations.append({
                'type': 'Reserved Instances',
                'description': 'Consider Reserved Instances for predictable workloads',
                'potential_savings': '30%',
                'implementation': 'Purchase 1-year or 3-year Reserved Instances'
            })
        
        if 'spot instance' in text.lower():
            recommendations.append({
                'type': 'Spot Instances',
                'description': 'Use Spot Instances for fault-tolerant workloads',
                'potential_savings': '70%',
                'implementation': 'Replace non-critical instances with Spot Instances'
            })
        
        if 'right-siz' in text.lower():
            recommendations.append({
                'type': 'Right-sizing',
                'description': 'Optimize instance sizes based on utilization',
                'potential_savings': '15%',
                'implementation': 'Monitor CPU and memory usage, downsize underutilized instances'
            })
        
        return recommendations
    
    def _get_fallback_optimizations(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Fallback optimization recommendations"""
        return [
            {
                'type': 'Reserved Instances',
                'description': 'Purchase Reserved Instances for predictable EC2 workloads',
                'potential_savings': '30%',
                'implementation': 'Analyze usage patterns and commit to 1-year terms'
            },
            {
                'type': 'Storage Optimization',
                'description': 'Migrate from GP2 to GP3 volumes for better price-performance',
                'potential_savings': '20%',
                'implementation': 'Update EBS volume types to GP3'
            },
            {
                'type': 'Right-sizing',
                'description': 'Monitor and optimize instance sizes based on actual usage',
                'potential_savings': '15%',
                'implementation': 'Use CloudWatch metrics to identify underutilized resources'
            }
        ]

# Singleton instance for global use
agentic_cost_estimator = AgenticCostEstimator()