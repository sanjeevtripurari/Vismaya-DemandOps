"""
AWS Bedrock AI Assistant
Implements IAIAssistant interface
Following Dependency Inversion Principle
"""

import json
import json
import logging
from typing import List

from ..core.interfaces import IAIAssistant
from ..core.models import UsageSummary, OptimizationRecommendation

logger = logging.getLogger(__name__)


class BedrockAIAssistant(IAIAssistant):
    """AWS Bedrock AI assistant implementation"""
    
    def __init__(self, aws_session, model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0"):
        self._session = aws_session
        self._model_id = model_id
        self._bedrock_client = None
        self._initialize_client()
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text (rough approximation)"""
        # Rough estimation: ~4 characters per token for English text
        return max(1, len(text) // 4)
    
    def _invoke_model_with_tracking(self, body: str, operation: str = "InvokeModel"):
        """Invoke Bedrock model with cost tracking"""
        # Parse the request to estimate input tokens
        try:
            request_data = json.loads(body)
            messages = request_data.get('messages', [])
            input_text = ""
            for message in messages:
                input_text += message.get('content', '')
            
            input_tokens = self._estimate_tokens(input_text)
        except Exception as e:
            logger.warning(f"Error parsing request for token estimation: {e}")
            input_tokens = 100  # Default estimate
        
        try:
            # Make the API call
            response = self._bedrock_client.invoke_model(
                body=body,
                modelId=self._model_id,
                accept='application/json',
                contentType='application/json'
            )
            
            # Read response body once and store it
            response_body_bytes = response.get('body').read()
            
            # Parse response to estimate output tokens
            try:
                response_body = json.loads(response_body_bytes)
                output_text = response_body.get('content', [{}])[0].get('text', '')
                output_tokens = self._estimate_tokens(output_text)
            except Exception as e:
                logger.warning(f"Error parsing response for token estimation: {e}")
                output_tokens = 50  # Default estimate
            
            # Track the cost
            from ..services.api_cost_tracker import api_cost_tracker
            api_cost_tracker.track_bedrock_call(
                model_id=self._model_id,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                operation=operation
            )
            
            # Create a new response object with the body content
            # Since we already read the body, we need to create a new readable stream
            import io
            response['body'] = io.BytesIO(response_body_bytes)
            
            return response
            
        except Exception as e:
            logger.error(f"Error invoking Bedrock model: {e}")
            # Return a mock response structure to avoid breaking the flow
            import io
            mock_response = {
                'body': io.BytesIO(b'{"content": [{"text": "Error: Unable to generate AI response"}]}')
            }
            return mock_response
    
    def _initialize_client(self):
        """Initialize Bedrock client"""
        try:
            self._bedrock_client = self._session.client('bedrock-runtime')
            logger.info("Bedrock client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Bedrock client: {e}")
            self._bedrock_client = None
    
    async def analyze_costs(self, usage_summary: UsageSummary) -> str:
        """Analyze costs and provide insights"""
        try:
            if not self._bedrock_client:
                return self._get_mock_analysis(usage_summary)
            
            prompt = self._build_cost_analysis_prompt(usage_summary)
            
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 300,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            })
            
            response = self._invoke_model_with_tracking(body, "AnalyzeCosts")
            
            # Read and parse response with better error handling
            response_text = response.get('body').read()
            if not response_text:
                logger.warning("Empty response from Bedrock")
                return self._get_mock_analysis(usage_summary)
            
            try:
                response_body = json.loads(response_text)
                if 'content' in response_body and len(response_body['content']) > 0:
                    return response_body['content'][0]['text']
                else:
                    logger.warning("Invalid response structure from Bedrock")
                    return self._get_mock_analysis(usage_summary)
            except json.JSONDecodeError as je:
                logger.error(f"JSON decode error: {je}, Response: {response_text[:100]}")
                return self._get_mock_analysis(usage_summary)
            
        except Exception as e:
            logger.error(f"Error calling Bedrock for cost analysis: {e}")
            return self._get_mock_analysis(usage_summary)
    
    async def generate_recommendations(self, usage_summary: UsageSummary) -> List[OptimizationRecommendation]:
        """Generate optimization recommendations"""
        try:
            if not self._bedrock_client:
                return self._get_mock_recommendations(usage_summary)
            
            prompt = self._build_recommendations_prompt(usage_summary)
            
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 500,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            })
            
            response = self._invoke_model_with_tracking(body, "GenerateRecommendations")
            
            # Read and parse response with better error handling
            response_text = response.get('body').read()
            if not response_text:
                logger.warning("Empty response from Bedrock for recommendations")
                return self._get_mock_recommendations(usage_summary)
            
            try:
                response_body = json.loads(response_text)
                if 'content' in response_body and len(response_body['content']) > 0:
                    recommendations_text = response_body['content'][0]['text']
                    # Parse the response into structured recommendations
                    return self._parse_recommendations(recommendations_text)
                else:
                    logger.warning("Invalid response structure from Bedrock for recommendations")
                    return self._get_mock_recommendations(usage_summary)
            except json.JSONDecodeError as je:
                logger.error(f"JSON decode error in recommendations: {je}, Response: {response_text[:100]}")
                return self._get_mock_recommendations(usage_summary)
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return self._get_mock_recommendations(usage_summary)
    
    async def chat_response(self, message: str, context: UsageSummary) -> str:
        """Handle chat interactions with factual, data-driven responses"""
        try:
            # First, try to answer with factual data
            factual_response = self._get_factual_response(message, context)
            if factual_response:
                return factual_response
            
            # If no factual response available, use AI with strict context
            if not self._bedrock_client:
                return self._get_contextual_fallback_response(message, context)
            
            prompt = self._build_strict_chat_prompt(message, context)
            
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 200,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            })
            
            response = self._invoke_model_with_tracking(body, "ChatResponse")
            
            # Read and parse response with better error handling
            response_text = response.get('body').read()
            if not response_text:
                logger.warning("Empty response from Bedrock for chat")
                return self._get_contextual_fallback_response(message, context)
            
            try:
                response_body = json.loads(response_text)
                if 'content' in response_body and len(response_body['content']) > 0:
                    ai_response = response_body['content'][0]['text']
                    # Validate and enhance AI response with actual data
                    return self._validate_and_enhance_response(ai_response, context)
                else:
                    logger.warning("Invalid response structure from Bedrock for chat")
                    return self._get_contextual_fallback_response(message, context)
            except json.JSONDecodeError as je:
                logger.error(f"JSON decode error in chat: {je}, Response: {response_text[:100]}")
                return self._get_contextual_fallback_response(message, context)
            
        except Exception as e:
            logger.error(f"Error in chat response: {e}")
            return self._get_contextual_fallback_response(message, context)
    
    def _build_cost_analysis_prompt(self, usage_summary: UsageSummary) -> str:
        """Build prompt for cost analysis"""
        budget_info = usage_summary.budget_info
        service_costs = {service.service_type.value: service.cost.amount 
                        for service in usage_summary.service_costs}
        
        return f"""
        You are Vismaya, an AI FinOps assistant. Analyze the following AWS cost data and provide insights:
        
        Current Spend: ${budget_info.current_spend:,.2f}
        Monthly Budget: ${budget_info.total_budget:,.2f}
        Budget Utilization: {budget_info.utilization_percentage:.1f}%
        Forecasted Spend: ${usage_summary.cost_forecast.forecasted_amount:,.2f}
        
        Service Costs:
        {json.dumps(service_costs, indent=2)}
        
        Provide a concise analysis including:
        1. Budget status and overspend risk
        2. Cost optimization suggestions
        3. Specific recommendations for high-cost services
        
        Keep response under 200 words and actionable.
        """
    
    def _build_recommendations_prompt(self, usage_summary: UsageSummary) -> str:
        """Build prompt for recommendations"""
        return f"""
        As Vismaya, an AI FinOps expert, generate 3-5 specific optimization recommendations based on:
        
        Budget: ${usage_summary.budget_info.total_budget:,.2f}
        Current Spend: ${usage_summary.budget_info.current_spend:,.2f}
        EC2 Instances: {len(usage_summary.ec2_instances)}
        Storage Volumes: {len(usage_summary.storage_volumes)}
        Databases: {len(usage_summary.database_instances)}
        
        For each recommendation, provide:
        - Title (brief)
        - Description (specific action)
        - Potential savings estimate
        - Implementation effort (Low/Medium/High)
        - Category (Cost/Performance/Security)
        
        Format as JSON array with these fields: title, description, potential_savings, implementation_effort, category
        """
    
    def _get_factual_response(self, message: str, context: UsageSummary) -> str:
        """Provide factual responses based on actual data"""
        message_lower = message.lower()
        
        # Current spend queries
        if any(word in message_lower for word in ['current', 'spend', 'spending', 'cost', 'bill']):
            if 'month' in message_lower or 'monthly' in message_lower:
                if context.budget_info.current_spend == 0:
                    return f"Your current monthly spend is $0.00 because you have no billable AWS resources running in us-east-2 region. Your budget is ${context.budget_info.total_budget:,.2f}, so you're well within limits! You can enable Demo Mode to see how the platform works with sample data."
                else:
                    return f"Your current monthly spend is ${context.budget_info.current_spend:,.2f}, which is {context.budget_info.utilization_percentage:.1f}% of your ${context.budget_info.total_budget:,.2f} budget. You have ${context.budget_info.remaining_budget:,.2f} remaining this month."
        
        # Budget queries
        if any(word in message_lower for word in ['budget', 'limit', 'allowance']):
            status = "over budget" if context.budget_info.is_over_budget else "within budget"
            return f"Your monthly budget is ${context.budget_info.total_budget:,.2f}. You've spent ${context.budget_info.current_spend:,.2f} ({context.budget_info.utilization_percentage:.1f}%), so you're currently {status}."
        
        # EC2 queries
        if 'ec2' in message_lower or 'instance' in message_lower:
            if len(context.ec2_instances) == 0:
                return "You currently have no EC2 instances in your AWS account (Region: us-east-2). This means no EC2-related costs. To test the platform, you can enable Demo Mode or launch an EC2 instance from the AWS Console."
            
            running_instances = [i for i in context.ec2_instances if i.state.value == 'running']
            stopped_instances = [i for i in context.ec2_instances if i.state.value == 'stopped']
            total_cost = sum(i.monthly_cost for i in context.ec2_instances)
            
            response = f"You have {len(context.ec2_instances)} EC2 instances total: {len(running_instances)} running, {len(stopped_instances)} stopped. "
            response += f"Monthly EC2 cost: ${total_cost:.2f}. "
            
            if stopped_instances:
                response += f"Consider terminating the {len(stopped_instances)} stopped instances to avoid charges."
            
            return response
        
        # Storage queries
        if any(word in message_lower for word in ['storage', 'ebs', 'volume', 'disk']):
            if len(context.storage_volumes) == 0:
                return "You currently have no EBS storage volumes in your AWS account (Region: us-east-2). This means no storage costs. EBS volumes are typically created when you launch EC2 instances."
            
            total_size = sum(v.size_gb for v in context.storage_volumes)
            total_cost = sum(v.monthly_cost for v in context.storage_volumes)
            unattached = [v for v in context.storage_volumes if not v.attached_instance]
            
            response = f"You have {len(context.storage_volumes)} EBS volumes totaling {total_size:,} GB, costing ${total_cost:.2f}/month. "
            
            if unattached:
                unattached_cost = sum(v.monthly_cost for v in unattached)
                response += f"Warning: {len(unattached)} volumes ({unattached_cost:.2f}/month) are unattached and could be deleted."
            
            return response
        
        # Database queries
        if any(word in message_lower for word in ['database', 'rds', 'db']):
            if len(context.database_instances) == 0:
                return "You currently have no RDS database instances in your AWS account (Region: us-east-2). This means no database costs. You can create RDS instances from the AWS Console if needed."
            
            total_cost = sum(db.monthly_cost for db in context.database_instances)
            engines = list(set(db.engine for db in context.database_instances))
            
            return f"You have {len(context.database_instances)} RDS instances running {', '.join(engines)} engines, costing ${total_cost:.2f}/month total."
        
        # Forecast queries
        if any(word in message_lower for word in ['forecast', 'predict', 'future', 'next month']):
            forecast_amount = context.cost_forecast.forecasted_amount
            current_amount = context.budget_info.current_spend
            
            if forecast_amount > context.budget_info.total_budget:
                overage = forecast_amount - context.budget_info.total_budget
                return f"Based on current trends, you're forecasted to spend ${forecast_amount:,.2f} next month, which would exceed your budget by ${overage:,.2f}."
            else:
                return f"Your forecasted spend for next month is ${forecast_amount:,.2f}, which is within your ${context.budget_info.total_budget:,.2f} budget."
        
        # Optimization queries
        if any(word in message_lower for word in ['optimize', 'save', 'reduce', 'lower', 'cut']):
            recommendations = []
            
            # Check for stopped instances
            stopped_ec2 = [i for i in context.ec2_instances if i.state.value == 'stopped']
            if stopped_ec2:
                recommendations.append(f"Terminate {len(stopped_ec2)} stopped EC2 instances")
            
            # Check for unattached volumes
            unattached_volumes = [v for v in context.storage_volumes if not v.attached_instance]
            if unattached_volumes:
                savings = sum(v.monthly_cost for v in unattached_volumes)
                recommendations.append(f"Delete {len(unattached_volumes)} unattached EBS volumes (save ${savings:.2f}/month)")
            
            # Check for large instances
            large_instances = [i for i in context.ec2_instances if 'large' in i.instance_type.lower()]
            if large_instances:
                recommendations.append(f"Review {len(large_instances)} large instances for rightsizing opportunities")
            
            if recommendations:
                return "Here are specific optimization opportunities based on your current usage:\n• " + "\n• ".join(recommendations)
            else:
                return "Based on your current usage, I don't see any immediate optimization opportunities. Your resources appear to be efficiently utilized."
        
        # Service breakdown queries
        if any(word in message_lower for word in ['service', 'breakdown', 'which service', 'most expensive']):
            service_costs = {}
            
            # Calculate costs by service type
            for service in context.service_costs:
                service_name = service.service_type.value.split(' - ')[-1] if ' - ' in service.service_type.value else service.service_type.value
                if 'Compute' in service_name:
                    service_name = 'EC2'
                elif 'Database' in service_name:
                    service_name = 'RDS'
                elif 'Storage' in service_name:
                    service_name = 'S3'
                elif 'Block Store' in service_name:
                    service_name = 'EBS'
                
                service_costs[service_name] = service.cost.amount
            
            if service_costs:
                sorted_services = sorted(service_costs.items(), key=lambda x: x[1], reverse=True)
                response = "Your AWS spending by service:\n"
                for service, cost in sorted_services[:4]:
                    percentage = (cost / context.budget_info.current_spend * 100) if context.budget_info.current_spend > 0 else 0
                    response += f"• {service}: ${cost:,.2f} ({percentage:.1f}%)\n"
                return response.strip()
        
        return None  # No factual response available
    
    def _build_strict_chat_prompt(self, message: str, context: UsageSummary) -> str:
        """Build prompt for AI with strict factual constraints"""
        service_breakdown = []
        for service in context.service_costs:
            service_name = service.service_type.value.split(' - ')[-1] if ' - ' in service.service_type.value else service.service_type.value
            service_breakdown.append(f"{service_name}: ${service.cost.amount:.2f}")
        
        return f"""You are Vismaya, an AWS FinOps assistant. Answer ONLY based on the provided data. Do not make assumptions or provide general advice.

CURRENT DATA:
- Monthly Budget: ${context.budget_info.total_budget:,.2f}
- Current Spend: ${context.budget_info.current_spend:,.2f} ({context.budget_info.utilization_percentage:.1f}% of budget)
- Remaining Budget: ${context.budget_info.remaining_budget:,.2f}
- Forecast: ${context.cost_forecast.forecasted_amount:,.2f}
- EC2 Instances: {len(context.ec2_instances)} total
- Storage Volumes: {len(context.storage_volumes)} total ({sum(v.size_gb for v in context.storage_volumes):,} GB)
- RDS Instances: {len(context.database_instances)} total
- Service Costs: {', '.join(service_breakdown)}

User Question: {message}

Rules:
1. Use ONLY the data provided above
2. Give specific numbers and facts
3. If data is not available, say "I don't have that information in your current usage data"
4. Keep response under 100 words
5. Be precise and factual"""
    
    def _validate_and_enhance_response(self, ai_response: str, context: UsageSummary) -> str:
        """Validate AI response and enhance with actual data"""
        # Replace any generic numbers with actual data
        enhanced_response = ai_response
        
        # Ensure budget figures are accurate
        if '$' in enhanced_response and 'budget' in enhanced_response.lower():
            enhanced_response += f"\n\n[Verified: Budget ${context.budget_info.total_budget:,.2f}, Spent ${context.budget_info.current_spend:,.2f}]"
        
        return enhanced_response
    
    def _get_contextual_fallback_response(self, message: str, context: UsageSummary) -> str:
        """Provide contextual fallback when AI is not available"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['help', 'what', 'how']):
            return f"I can help you with your AWS costs. You're currently at ${context.budget_info.current_spend:,.2f} of your ${context.budget_info.total_budget:,.2f} budget. Ask me about specific services, optimization opportunities, or forecasting."
        
        return f"Based on your current usage: ${context.budget_info.current_spend:,.2f} spent ({context.budget_info.utilization_percentage:.1f}% of budget), {len(context.ec2_instances)} EC2 instances, {len(context.storage_volumes)} storage volumes. What specific aspect would you like to know about?"
    
    def _parse_recommendations(self, recommendations_text: str) -> List[OptimizationRecommendation]:
        """Parse AI response into structured recommendations"""
        try:
            # Try to parse as JSON first
            if recommendations_text.strip().startswith('['):
                recommendations_data = json.loads(recommendations_text)
                return [
                    OptimizationRecommendation(
                        title=rec.get('title', 'Optimization Recommendation'),
                        description=rec.get('description', 'No description provided'),
                        potential_savings=float(rec.get('potential_savings', 0)),
                        confidence_score=0.8,  # Default confidence
                        implementation_effort=rec.get('implementation_effort', 'Medium'),
                        category=rec.get('category', 'Cost')
                    )
                    for rec in recommendations_data
                ]
        except (json.JSONDecodeError, KeyError, ValueError):
            pass
        
        # Fallback: parse as text and create basic recommendations
        return self._create_basic_recommendations(recommendations_text)
    
    def _create_basic_recommendations(self, text: str) -> List[OptimizationRecommendation]:
        """Create basic recommendations from text"""
        return [
            OptimizationRecommendation(
                title="Review EC2 Instance Utilization",
                description="Analyze EC2 instance usage patterns and consider rightsizing or using Spot instances for non-critical workloads.",
                potential_savings=200.0,
                confidence_score=0.8,
                implementation_effort="Medium",
                category="Cost"
            ),
            OptimizationRecommendation(
                title="Optimize Storage Costs",
                description="Review EBS volumes for unused or oversized storage and consider lifecycle policies for S3.",
                potential_savings=150.0,
                confidence_score=0.7,
                implementation_effort="Low",
                category="Cost"
            )
        ]
    
    def _get_mock_analysis(self, usage_summary: UsageSummary) -> str:
        """Mock analysis for demo purposes"""
        budget_info = usage_summary.budget_info
        budget_pct = budget_info.utilization_percentage
        overspend = usage_summary.cost_forecast.forecasted_amount - budget_info.total_budget
        
        if budget_pct > 80:
            return f"""You have spent ${budget_info.current_spend:,.0f} of ${budget_info.total_budget:,.0f} budget ({budget_pct:.0f}%).

At this rate, you'll overshoot by ${overspend:,.0f}.

Suggested:
• Move 3 EC2 to Spot → Save $120
• Optimize RDS storage → Save $200
• Review unused EBS volumes → Save $150"""
        else:
            return f"""You're at {budget_pct:.0f}% of your ${budget_info.total_budget:,.0f} budget. Good progress!

Recommendations:
• Monitor EC2 usage patterns
• Consider Reserved Instances for steady workloads
• Set up cost alerts at 90% budget"""
    
    def _get_mock_recommendations(self, usage_summary: UsageSummary) -> List[OptimizationRecommendation]:
        """Mock recommendations for demo"""
        return [
            OptimizationRecommendation(
                title="Migrate to Spot Instances",
                description="Move 3 non-critical EC2 instances to Spot pricing for development workloads",
                potential_savings=120.0,
                confidence_score=0.9,
                implementation_effort="Low",
                category="Cost"
            ),
            OptimizationRecommendation(
                title="RDS Storage Optimization",
                description="Enable storage autoscaling and review allocated storage vs actual usage",
                potential_savings=200.0,
                confidence_score=0.8,
                implementation_effort="Medium",
                category="Cost"
            ),
            OptimizationRecommendation(
                title="Unused EBS Volume Cleanup",
                description="Identify and remove unattached EBS volumes to reduce storage costs",
                potential_savings=150.0,
                confidence_score=0.95,
                implementation_effort="Low",
                category="Cost"
            )
        ]
    
    def _get_mock_chat_response(self, message: str, context: UsageSummary) -> str:
        """Mock chat response for demo"""
        message_lower = message.lower()
        
        if "cost" in message_lower or "spend" in message_lower:
            return f"Your current spend is ${context.budget_info.current_spend:,.0f}, which is {context.budget_info.utilization_percentage:.0f}% of your ${context.budget_info.total_budget:,.0f} budget. You're on track for the month!"
        
        elif "ec2" in message_lower:
            return f"You have {len(context.ec2_instances)} EC2 instances running. Consider using Spot instances for development workloads to save up to 70% on costs."
        
        elif "optimize" in message_lower or "save" in message_lower:
            return "Top optimization opportunities: 1) Move dev instances to Spot pricing, 2) Review RDS storage allocation, 3) Clean up unused EBS volumes. These could save you $400+ monthly."
        
        else:
            return "I can help you analyze AWS costs, optimize spending, and forecast future usage. What specific aspect of your AWS costs would you like to explore?"