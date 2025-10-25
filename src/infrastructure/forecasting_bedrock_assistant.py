"""
Forecasting Bedrock AI Assistant
Enhanced Bedrock integration for forecasting-specific AI responses
"""

import json
import logging
from typing import Dict, Any

from .bedrock_ai_assistant import BedrockAIAssistant
from ..core.models import (
    CostEstimateResponse, ForecastingContext, ResourceSpecification,
    PricingData, TimePeriod
)

logger = logging.getLogger(__name__)


class ForecastingBedrockAssistant(BedrockAIAssistant):
    """Enhanced Bedrock AI assistant for forecasting scenarios"""
    
    def __init__(self, aws_session, model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0"):
        super().__init__(aws_session, model_id)
    
    async def enhance_cost_response(self, cost_estimate: CostEstimateResponse, 
                                  context: ForecastingContext, 
                                  original_query: str) -> str:
        """Enhance cost estimate response with AI-generated insights"""
        try:
            if not self._bedrock_client:
                return self._get_mock_enhanced_response(cost_estimate, original_query)
            
            prompt = self._build_cost_enhancement_prompt(cost_estimate, context, original_query)
            
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 400,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            })
            
            response = self._invoke_model_with_tracking(body, "EnhanceCostResponse")
            
            # Read and parse response
            response_text = response.get('body').read()
            if not response_text:
                logger.warning("Empty response from Bedrock for cost enhancement")
                return self._get_mock_enhanced_response(cost_estimate, original_query)
            
            try:
                response_body = json.loads(response_text)
                if 'content' in response_body and len(response_body['content']) > 0:
                    enhanced_text = response_body['content'][0]['text']
                    # Validate the response contains actual data
                    return self._validate_enhanced_response(enhanced_text, cost_estimate)
                else:
                    logger.warning("Invalid response structure from Bedrock for cost enhancement")
                    return self._get_mock_enhanced_response(cost_estimate, original_query)
            except json.JSONDecodeError as je:
                logger.error(f"JSON decode error in cost enhancement: {je}")
                return self._get_mock_enhanced_response(cost_estimate, original_query)
                
        except Exception as e:
            logger.error(f"Error enhancing cost response: {e}")
            return self._get_mock_enhanced_response(cost_estimate, original_query)
    
    async def generate_pricing_insights(self, resource_spec: ResourceSpecification, 
                                      pricing_data: PricingData, 
                                      duration: TimePeriod) -> str:
        """Generate AI insights about pricing options and recommendations"""
        try:
            if not self._bedrock_client:
                return self._get_mock_pricing_insights(resource_spec, pricing_data)
            
            prompt = self._build_pricing_insights_prompt(resource_spec, pricing_data, duration)
            
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
            
            response = self._invoke_model_with_tracking(body, "GeneratePricingInsights")
            
            # Read and parse response
            response_text = response.get('body').read()
            if not response_text:
                return self._get_mock_pricing_insights(resource_spec, pricing_data)
            
            try:
                response_body = json.loads(response_text)
                if 'content' in response_body and len(response_body['content']) > 0:
                    return response_body['content'][0]['text']
                else:
                    return self._get_mock_pricing_insights(resource_spec, pricing_data)
            except json.JSONDecodeError:
                return self._get_mock_pricing_insights(resource_spec, pricing_data)
                
        except Exception as e:
            logger.error(f"Error generating pricing insights: {e}")
            return self._get_mock_pricing_insights(resource_spec, pricing_data)
    
    async def explain_budget_impact(self, cost_estimate: float, 
                                  context: ForecastingContext) -> str:
        """Generate AI explanation of budget impact"""
        try:
            if not context or not context.budget_info:
                return "Budget impact analysis requires current budget information."
            
            if not self._bedrock_client:
                return self._get_mock_budget_explanation(cost_estimate, context)
            
            prompt = self._build_budget_impact_prompt(cost_estimate, context)
            
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 250,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            })
            
            response = self._invoke_model_with_tracking(body, "ExplainBudgetImpact")
            
            # Read and parse response
            response_text = response.get('body').read()
            if not response_text:
                return self._get_mock_budget_explanation(cost_estimate, context)
            
            try:
                response_body = json.loads(response_text)
                if 'content' in response_body and len(response_body['content']) > 0:
                    return response_body['content'][0]['text']
                else:
                    return self._get_mock_budget_explanation(cost_estimate, context)
            except json.JSONDecodeError:
                return self._get_mock_budget_explanation(cost_estimate, context)
                
        except Exception as e:
            logger.error(f"Error explaining budget impact: {e}")
            return self._get_mock_budget_explanation(cost_estimate, context)
    
    def _build_cost_enhancement_prompt(self, cost_estimate: CostEstimateResponse, 
                                     context: ForecastingContext, 
                                     original_query: str) -> str:
        """Build prompt for enhancing cost estimate response"""
        resource_desc = self._describe_resource_for_ai(cost_estimate.resource_spec)
        
        context_info = ""
        if context and context.budget_info:
            context_info = f"""
Current Budget Context:
- Monthly Budget: ${context.budget_info.warning_limit:.2f}
- Current Spend: ${context.budget_info.current_spend:.2f}
- Budget Utilization: {context.budget_info.utilization_percentage:.1f}%
- Remaining Budget: ${context.budget_info.remaining_budget:.2f}
"""
        
        pricing_breakdown = ""
        if cost_estimate.pricing_breakdown:
            pricing_breakdown = "Pricing Options:\n"
            for model, cost in cost_estimate.pricing_breakdown.items():
                pricing_breakdown += f"- {model}: ${cost:.2f}\n"
        
        return f"""You are Vismaya, an expert AWS FinOps assistant. The user asked: "{original_query}"

I've calculated the following cost estimate:
Resource: {resource_desc}
Duration: {cost_estimate.duration.description}
Total Cost: ${cost_estimate.total_cost:.2f}

{pricing_breakdown}

{context_info}

Provide a conversational, helpful response that:
1. Confirms the cost estimate clearly
2. Explains the best pricing option and why
3. Gives practical advice about the resource choice
4. Mentions budget impact if relevant
5. Suggests alternatives if cost is high

Keep it under 200 words, friendly but professional. Use actual numbers from the data provided.
Data source: {cost_estimate.data_source} at {cost_estimate.timestamp.strftime('%Y-%m-%d %H:%M')} UTC"""
    
    def _build_pricing_insights_prompt(self, resource_spec: ResourceSpecification, 
                                     pricing_data: PricingData, 
                                     duration: TimePeriod) -> str:
        """Build prompt for pricing insights"""
        resource_desc = self._describe_resource_for_ai(resource_spec)
        
        pricing_info = ""
        if pricing_data.on_demand_hourly:
            pricing_info += f"On-Demand: ${pricing_data.on_demand_hourly:.4f}/hour\n"
        if pricing_data.reserved_monthly:
            pricing_info += f"Reserved: ${pricing_data.reserved_monthly:.2f}/month\n"
        if pricing_data.spot_hourly:
            pricing_info += f"Spot: ${pricing_data.spot_hourly:.4f}/hour\n"
        
        return f"""As Vismaya, an AWS pricing expert, provide insights about:

Resource: {resource_desc}
Duration: {duration.description}
Region: {resource_spec.region}

Available Pricing:
{pricing_info}

Provide brief insights about:
1. Which pricing model is best for this duration
2. Potential savings opportunities
3. Any important considerations for this resource type

Keep response under 150 words and practical."""
    
    def _build_budget_impact_prompt(self, cost_estimate: float, 
                                  context: ForecastingContext) -> str:
        """Build prompt for budget impact explanation"""
        budget_info = context.budget_info
        new_total = budget_info.current_spend + cost_estimate
        
        return f"""As Vismaya, explain the budget impact of adding ${cost_estimate:.2f} to current spending:

Current Situation:
- Current Spend: ${budget_info.current_spend:.2f}
- Budget Limit: ${budget_info.warning_limit:.2f}
- Current Utilization: {budget_info.utilization_percentage:.1f}%

After Adding Resource:
- New Total: ${new_total:.2f}
- New Utilization: {(new_total/budget_info.warning_limit)*100:.1f}%

Explain the impact in simple terms and provide actionable advice. Keep under 100 words."""
    
    def _describe_resource_for_ai(self, resource_spec: ResourceSpecification) -> str:
        """Describe resource for AI prompts"""
        if resource_spec.resource_type.value == 'ec2':
            return f"{resource_spec.quantity}x {resource_spec.instance_type} EC2 instance(s) ({resource_spec.operating_system})"
        elif resource_spec.resource_type.value == 'rds':
            engine = resource_spec.additional_specs.get('engine', 'MySQL')
            return f"{resource_spec.quantity}x {resource_spec.instance_type} RDS {engine} instance(s)"
        elif resource_spec.resource_type.value == 'ebs':
            size = resource_spec.additional_specs.get('size_gb', 'unknown')
            volume_type = resource_spec.additional_specs.get('volume_type', 'GP3')
            return f"{size} GB {volume_type.upper()} EBS volume(s)"
        else:
            return f"{resource_spec.quantity}x {resource_spec.resource_type.value} resource(s)"
    
    def _validate_enhanced_response(self, ai_response: str, 
                                  cost_estimate: CostEstimateResponse) -> str:
        """Validate AI response contains actual cost data"""
        # Ensure the response mentions the actual cost
        if f"${cost_estimate.total_cost:.2f}" not in ai_response:
            # Prepend actual cost if AI didn't include it
            ai_response = f"💰 **Total Cost: ${cost_estimate.total_cost:.2f}** for {cost_estimate.duration.description}\n\n" + ai_response
        
        # Add data source if not mentioned
        if cost_estimate.data_source not in ai_response:
            ai_response += f"\n\n*Pricing from {cost_estimate.data_source}*"
        
        return ai_response
    
    def _get_mock_enhanced_response(self, cost_estimate: CostEstimateResponse, 
                                  original_query: str) -> str:
        """Mock enhanced response when AI is unavailable"""
        resource_desc = self._describe_resource_for_ai(cost_estimate.resource_spec)
        
        if cost_estimate.error_message:
            return f"❌ I couldn't calculate the cost for {resource_desc}: {cost_estimate.error_message}"
        
        response = f"💰 **{resource_desc}** will cost **${cost_estimate.total_cost:.2f}** for {cost_estimate.duration.description}.\n\n"
        
        if cost_estimate.pricing_breakdown:
            cheapest = min(cost_estimate.pricing_breakdown.items(), key=lambda x: x[1])
            response += f"💡 Best option: {cheapest[0]} at ${cheapest[1]:.2f}\n\n"
        
        if cost_estimate.budget_impact:
            if cost_estimate.budget_impact.exceeds_critical:
                response += "🚨 **Warning**: This would exceed your budget limit!"
            elif cost_estimate.budget_impact.exceeds_warning:
                response += "⚠️ **Caution**: This approaches your budget limit."
            else:
                response += "✅ This fits within your current budget."
        
        return response
    
    def _get_mock_pricing_insights(self, resource_spec: ResourceSpecification, 
                                 pricing_data: PricingData) -> str:
        """Mock pricing insights when AI is unavailable"""
        insights = []
        
        if pricing_data.on_demand_hourly and pricing_data.reserved_monthly:
            on_demand_monthly = pricing_data.on_demand_hourly * 24 * 30
            if pricing_data.reserved_monthly < on_demand_monthly * 0.7:
                insights.append("💡 Reserved instances offer significant savings for long-term usage")
        
        if resource_spec.resource_type.value == 'ec2':
            if 't3' in (resource_spec.instance_type or ''):
                insights.append("⚡ T3 instances are burstable - great for variable workloads")
            elif 'm5' in (resource_spec.instance_type or ''):
                insights.append("🔧 M5 instances provide balanced compute for general workloads")
        
        if not insights:
            insights.append("📊 Pricing data retrieved from AWS Pricing API for accuracy")
        
        return " • ".join(insights)
    
    def _get_mock_budget_explanation(self, cost_estimate: float, 
                                   context: ForecastingContext) -> str:
        """Mock budget explanation when AI is unavailable"""
        budget_info = context.budget_info
        new_total = budget_info.current_spend + cost_estimate
        new_utilization = (new_total / budget_info.warning_limit) * 100
        
        if new_utilization > 100:
            overage = new_total - budget_info.warning_limit
            return f"🚨 Adding this resource would put you ${overage:.2f} over budget ({new_utilization:.1f}% utilization). Consider reducing the resource size or duration."
        elif new_utilization > 80:
            return f"⚠️ This would bring you to {new_utilization:.1f}% of your budget. Monitor spending closely if you proceed."
        else:
            remaining = budget_info.warning_limit - new_total
            return f"✅ You'd be at {new_utilization:.1f}% of budget with ${remaining:.2f} remaining. This fits comfortably within your limits."