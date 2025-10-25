"""
Forecasting AI Assistant Service
Main orchestrator for AI-powered cost estimation queries
"""

import json
import logging
from typing import Dict, List, Optional
from datetime import datetime

from ..core.interfaces import (
    IForecastingAIAssistant, IAWSPricingProvider, IQueryParser, 
    ICostEstimationEngine, IAIAssistant
)
from ..core.models import (
    ResourceSpecification, PricingData, CostEstimateResponse,
    TimePeriod, ForecastingContext, BudgetImpactAnalysis,
    PricingAPIError, PricingDataUnavailableError, 
    InvalidResourceSpecificationError, RateLimitExceededError
)

logger = logging.getLogger(__name__)


class ForecastingAIAssistant(IForecastingAIAssistant):
    """AI-powered assistant for AWS resource cost forecasting"""
    
    def __init__(self, 
                 pricing_provider: IAWSPricingProvider,
                 query_parser: IQueryParser,
                 cost_engine: ICostEstimationEngine,
                 ai_assistant: IAIAssistant):
        self._pricing_provider = pricing_provider
        self._query_parser = query_parser
        self._cost_engine = cost_engine
        self._ai_assistant = ai_assistant
        
        # Conversation context management
        self._conversation_contexts = {}  # session_id -> context
        
        # Example queries for user guidance
        self._example_queries = [
            "What would 2 t3.medium EC2 instances cost for 3 months?",
            "Cost of a db.t3.micro RDS MySQL instance for 6 months",
            "How much for 500 GB of EBS GP3 storage for 1 year?",
            "Price of m5.large instance in us-west-2 for 2 months",
            "Cost comparison: t3.small vs t3.medium for 90 days"
        ]
    
    async def process_cost_query(self, query: str, context: ForecastingContext) -> CostEstimateResponse:
        """Process natural language cost estimation query with smart defaults"""
        try:
            logger.info(f"Processing cost query: {query}")
            
            # Apply smart defaults to incomplete queries
            from .smart_defaults_processor import SmartDefaultsProcessor
            defaults_processor = SmartDefaultsProcessor()
            
            # Get complete specification with defaults applied
            complete_spec = defaults_processor.apply_defaults(query)
            
            # Convert to ResourceSpecification format
            try:
                resource_spec = self._convert_to_resource_spec(complete_spec)
            except Exception as e:
                return CostEstimateResponse(
                    resource_spec=ResourceSpecification(resource_type=None),
                    pricing_breakdown={},
                    total_cost=0.0,
                    duration=TimePeriod.from_months(1),
                    error_message=f"Could not process the query: {str(e)}",
                    defaults_applied=complete_spec.get('applied_defaults', []),
                    default_explanation=defaults_processor.format_defaults_explanation(
                        complete_spec.get('applied_defaults', []), 
                        complete_spec.get('resource_type', 'ec2')
                    )
                )
            
            # Extract time period from complete specification
            duration = TimePeriod.from_months(complete_spec.get('duration_months', 1))
            
            # No need to check for clarification - we have complete specs with defaults
            
            # Get pricing data
            try:
                pricing_data = await self.get_resource_pricing(resource_spec)
            except PricingAPIError as e:
                return CostEstimateResponse(
                    resource_spec=resource_spec,
                    pricing_breakdown={},
                    total_cost=0.0,
                    duration=duration,
                    error_message=str(e),
                    defaults_applied=complete_spec.get('applied_defaults', []),
                    default_explanation=defaults_processor.format_defaults_explanation(
                        complete_spec.get('applied_defaults', []), 
                        complete_spec.get('resource_type', 'ec2')
                    )
                )
            
            # Calculate cost estimate
            cost_estimate = await self._cost_engine.estimate_resource_cost(
                resource_spec, pricing_data, duration
            )
            
            # Add smart defaults information to the response
            cost_estimate.defaults_applied = complete_spec.get('applied_defaults', [])
            cost_estimate.default_explanation = defaults_processor.format_defaults_explanation(
                complete_spec.get('applied_defaults', []), 
                complete_spec.get('resource_type', 'ec2')
            )
            cost_estimate.refinement_suggestions = defaults_processor.get_refinement_suggestions(
                complete_spec.get('resource_type', 'ec2'),
                complete_spec.get('applied_defaults', [])
            )
            
            # Add multi-resource notes if available
            if complete_spec.get('storage_note'):
                cost_estimate.storage_note = complete_spec['storage_note']
            if complete_spec.get('database_note'):
                cost_estimate.database_note = complete_spec['database_note']
            if complete_spec.get('multi_resource_notes'):
                cost_estimate.multi_resource_notes = complete_spec['multi_resource_notes']
            
            # Add budget impact analysis if context is available
            if context and context.budget_info and cost_estimate.is_successful:
                budget_impact = await self._cost_engine.calculate_budget_impact(
                    cost_estimate.total_cost, context.budget_info
                )
                cost_estimate.budget_impact = budget_impact
            
            logger.info(f"✅ Cost query processed successfully: ${cost_estimate.total_cost:.2f}")
            return cost_estimate
            
        except Exception as e:
            logger.error(f"Failed to process cost query '{query}': {e}")
            return CostEstimateResponse(
                resource_spec=ResourceSpecification(resource_type=None),
                pricing_breakdown={},
                total_cost=0.0,
                duration=TimePeriod.from_months(1),
                error_message=f"Query processing failed: {str(e)}"
            )
    
    async def get_resource_pricing(self, resource_spec: ResourceSpecification) -> PricingData:
        """Get current pricing for specific resource configuration"""
        try:
            logger.info(f"Getting pricing for {resource_spec.resource_type.value}")
            
            if resource_spec.resource_type.value == 'ec2':
                if not resource_spec.instance_type:
                    raise InvalidResourceSpecificationError("EC2 instance type is required")
                
                return await self._pricing_provider.get_ec2_pricing(
                    instance_type=resource_spec.instance_type,
                    region=resource_spec.region,
                    os=resource_spec.operating_system or "Linux"
                )
            
            elif resource_spec.resource_type.value == 'rds':
                if not resource_spec.instance_type:
                    raise InvalidResourceSpecificationError("RDS instance class is required")
                
                return await self._pricing_provider.get_service_pricing(
                    service='rds',
                    region=resource_spec.region,
                    instance_class=resource_spec.instance_type,
                    engine=resource_spec.additional_specs.get('engine', 'mysql')
                )
            
            elif resource_spec.resource_type.value == 'ebs':
                volume_type = resource_spec.additional_specs.get('volume_type', 'gp3')
                return await self._pricing_provider.get_storage_pricing(
                    storage_type=volume_type,
                    region=resource_spec.region
                )
            
            elif resource_spec.resource_type.value == 's3':
                return await self._pricing_provider.get_storage_pricing(
                    storage_type='s3',
                    region=resource_spec.region
                )
            
            elif resource_spec.resource_type.value == 'lambda':
                return await self._pricing_provider.get_service_pricing(
                    service='lambda',
                    region=resource_spec.region
                )
            
            else:
                raise InvalidResourceSpecificationError(
                    f"Pricing not supported for resource type: {resource_spec.resource_type.value}"
                )
                
        except Exception as e:
            logger.error(f"Failed to get pricing for {resource_spec.resource_type.value}: {e}")
            raise
    
    def _convert_to_resource_spec(self, complete_spec: Dict) -> ResourceSpecification:
        """Convert smart defaults format to ResourceSpecification"""
        from ..core.models import ResourceType
        
        # Map resource type string to enum
        resource_type_map = {
            'ec2': ResourceType.EC2,
            'rds': ResourceType.RDS,
            'ebs': ResourceType.EBS,
            's3': ResourceType.S3,
            'lambda': ResourceType.LAMBDA
        }
        
        resource_type = resource_type_map.get(complete_spec.get('resource_type', 'ec2'), ResourceType.EC2)
        
        # Build additional specs based on resource type
        additional_specs = {}
        
        if resource_type == ResourceType.EC2:
            additional_specs = {
                'pricing_model': complete_spec.get('pricing_model', 'on-demand')
            }
        elif resource_type == ResourceType.RDS:
            additional_specs = {
                'engine': complete_spec.get('engine', 'mysql'),
                'storage_gb': complete_spec.get('storage_gb', 20)
            }
        elif resource_type == ResourceType.EBS:
            additional_specs = {
                'volume_type': complete_spec.get('volume_type', 'gp3'),
                'size_gb': complete_spec.get('size_gb', 20)
            }
        elif resource_type == ResourceType.LAMBDA:
            additional_specs = {
                'memory_mb': complete_spec.get('memory_mb', 128),
                'executions_per_month': complete_spec.get('executions_per_month', 1000)
            }
        
        return ResourceSpecification(
            resource_type=resource_type,
            instance_type=complete_spec.get('instance_type'),
            quantity=complete_spec.get('quantity', 1),
            region=complete_spec.get('region', 'us-east-2'),
            additional_specs=additional_specs
        )
    
    async def chat_response(self, message: str, context: ForecastingContext) -> str:
        """Handle chat interactions with forecasting context"""
        try:
            logger.info(f"Generating chat response for: {message}")
            
            # Check if this is a cost estimation query
            if self._is_cost_query(message):
                cost_estimate = await self.process_cost_query(message, context)
                return self._format_cost_response(cost_estimate, context)
            
            # Handle general forecasting questions
            if self._is_forecasting_question(message):
                return await self._handle_forecasting_question(message, context)
            
            # Handle help requests
            if self._is_help_request(message):
                return self._generate_help_response()
            
            # Use the general AI assistant for other queries
            if context and context.current_usage:
                return await self._ai_assistant.chat_response(message, context.current_usage)
            else:
                return self._generate_default_response(message)
                
        except Exception as e:
            logger.error(f"Failed to generate chat response: {e}")
            return f"I'm having trouble processing your request: {str(e)}. Please try rephrasing your question."
    
    def _is_cost_query(self, message: str) -> bool:
        """Check if message is a cost estimation query"""
        cost_keywords = [
            'cost', 'price', 'pricing', 'how much', 'what would', 'estimate',
            'expense', 'budget', 'spend', 'charge', 'bill', 'fee'
        ]
        
        resource_keywords = [
            'ec2', 'instance', 'server', 'rds', 'database', 'ebs', 'storage',
            's3', 'lambda', 'function', 'volume', 'disk'
        ]
        
        message_lower = message.lower()
        has_cost_keyword = any(keyword in message_lower for keyword in cost_keywords)
        has_resource_keyword = any(keyword in message_lower for keyword in resource_keywords)
        
        return has_cost_keyword and has_resource_keyword
    
    def _is_forecasting_question(self, message: str) -> bool:
        """Check if message is about forecasting concepts"""
        forecasting_keywords = [
            'forecast', 'prediction', 'trend', 'growth', 'projection',
            'future', 'budget', 'timeline', 'planning'
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in forecasting_keywords)
    
    def _is_help_request(self, message: str) -> bool:
        """Check if message is a help request"""
        help_keywords = [
            'help', 'how to', 'what can', 'example', 'guide', 'tutorial',
            'explain', 'show me', 'demonstrate'
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in help_keywords)
    
    def _format_cost_response(self, cost_estimate: CostEstimateResponse, 
                            context: ForecastingContext) -> str:
        """Format cost estimate into natural language response"""
        if cost_estimate.error_message:
            return f"❌ {cost_estimate.error_message}"
        
        if not cost_estimate.is_successful:
            return "I couldn't calculate the cost for that resource. Please check your query and try again."
        
        # Build response
        response_parts = []
        
        # Main cost information
        resource_desc = self._describe_resource(cost_estimate.resource_spec)
        response_parts.append(
            f"💰 **Cost Estimate for {resource_desc}**\n"
            f"Duration: {cost_estimate.duration.description}\n"
            f"**Total Cost: ${cost_estimate.total_cost:.2f}**"
        )
        
        # Pricing breakdown
        if cost_estimate.pricing_breakdown:
            response_parts.append("\n📊 **Pricing Options:**")
            for pricing_model, cost in cost_estimate.pricing_breakdown.items():
                response_parts.append(f"• {pricing_model}: ${cost:.2f}")
        
        # Budget impact
        if cost_estimate.budget_impact:
            impact = cost_estimate.budget_impact
            response_parts.append(f"\n📈 **Budget Impact:**")
            response_parts.append(f"• New total spending: ${impact.new_total_cost:.2f}")
            
            if impact.exceeds_critical:
                response_parts.append(f"🚨 **CRITICAL**: Exceeds maximum budget by ${impact.critical_threshold_impact:.2f}")
            elif impact.exceeds_warning:
                response_parts.append(f"⚠️ **WARNING**: Exceeds warning limit by ${impact.warning_threshold_impact:.2f}")
            else:
                response_parts.append("✅ Within budget limits")
        
        # Smart defaults explanation
        if cost_estimate.defaults_applied and len(cost_estimate.defaults_applied) > 0:
            response_parts.append(f"\n{cost_estimate.default_explanation}")
        
        # Multi-resource notes
        if hasattr(cost_estimate, 'storage_note') and cost_estimate.storage_note:
            response_parts.append(f"\n💾 **Storage:** {cost_estimate.storage_note}")
        
        if hasattr(cost_estimate, 'database_note') and cost_estimate.database_note:
            response_parts.append(f"\n🗄️ **Database:** {cost_estimate.database_note}")
        
        if hasattr(cost_estimate, 'multi_resource_notes') and cost_estimate.multi_resource_notes:
            response_parts.append(f"\n📝 **Note:** {cost_estimate.multi_resource_notes}")
        
        # Refinement suggestions
        if cost_estimate.refinement_suggestions:
            response_parts.append("\n🎯 **For more precise estimates:**")
            for suggestion in cost_estimate.refinement_suggestions:
                response_parts.append(f"• {suggestion}")
        
        # Recommendations
        if cost_estimate.recommendations:
            response_parts.append("\n💡 **Recommendations:**")
            for rec in cost_estimate.recommendations[:3]:  # Limit to top 3
                response_parts.append(f"• {rec}")
        
        # Data source and timestamp
        response_parts.append(f"\n📅 *Data from {cost_estimate.data_source} at {cost_estimate.timestamp.strftime('%Y-%m-%d %H:%M')} UTC*")
        
        return "\n".join(response_parts)
    
    def _describe_resource(self, resource_spec: ResourceSpecification) -> str:
        """Generate human-readable resource description"""
        if resource_spec.resource_type.value == 'ec2':
            desc = f"{resource_spec.quantity}x {resource_spec.instance_type} EC2 instance"
            if resource_spec.quantity > 1:
                desc += "s"
            if resource_spec.operating_system != "Linux":
                desc += f" ({resource_spec.operating_system})"
            if resource_spec.region != "us-east-1":
                desc += f" in {resource_spec.region}"
            return desc
        
        elif resource_spec.resource_type.value == 'rds':
            engine = resource_spec.additional_specs.get('engine', 'MySQL')
            desc = f"{resource_spec.quantity}x {resource_spec.instance_type} RDS {engine} instance"
            if resource_spec.quantity > 1:
                desc += "s"
            if resource_spec.region != "us-east-1":
                desc += f" in {resource_spec.region}"
            return desc
        
        elif resource_spec.resource_type.value == 'ebs':
            size_gb = resource_spec.additional_specs.get('size_gb', 'unknown size')
            volume_type = resource_spec.additional_specs.get('volume_type', 'GP3')
            desc = f"{size_gb} GB {volume_type.upper()} EBS volume"
            if resource_spec.quantity > 1:
                desc = f"{resource_spec.quantity}x {desc}s"
            return desc
        
        else:
            return f"{resource_spec.quantity}x {resource_spec.resource_type.value} resource"
    
    async def _handle_forecasting_question(self, message: str, context: ForecastingContext) -> str:
        """Handle general forecasting questions"""
        message_lower = message.lower()
        
        if 'budget' in message_lower and context and context.budget_info:
            budget = context.budget_info
            return (
                f"📊 **Current Budget Status:**\n"
                f"• Current spend: ${budget.current_spend:.2f}\n"
                f"• Warning limit: ${budget.warning_limit:.2f}\n"
                f"• Maximum limit: ${budget.maximum_limit:.2f}\n"
                f"• Budget utilization: {budget.utilization_percentage:.1f}%\n"
                f"• Status: {budget.budget_status_emoji} {budget.budget_status}\n\n"
                f"💡 Ask me about specific resource costs to see budget impact!"
            )
        
        elif 'forecast' in message_lower and context and context.cost_forecast:
            forecast = context.cost_forecast
            return (
                f"📈 **Cost Forecast:**\n"
                f"• Current monthly cost: ${forecast.base_amount:.2f}\n"
                f"• Forecasted cost: ${forecast.forecasted_amount:.2f}\n"
                f"• Growth rate: {forecast.monthly_growth_rate:.1f}% per month\n"
                f"• Confidence: {forecast.confidence_level*100:.0f}%\n\n"
                f"💰 Ask me about adding specific resources to see the impact!"
            )
        
        else:
            return (
                "I can help you with AWS cost forecasting! Here's what I can do:\n\n"
                "💰 **Cost Estimation**: Ask about specific AWS resources\n"
                "📊 **Budget Impact**: See how new resources affect your budget\n"
                "🔍 **Price Comparison**: Compare different pricing models\n\n"
                "Try asking: 'What would 2 t3.medium instances cost for 3 months?'"
            )
    
    def _generate_help_response(self) -> str:
        """Generate help response with examples"""
        return (
            "🤖 **Forecasting AI Assistant Help**\n\n"
            "I can help you estimate AWS resource costs accurately using real pricing data.\n\n"
            "📝 **Example Queries:**\n" +
            "\n".join(f"• {example}" for example in self._example_queries) +
            "\n\n💡 **Tips:**\n"
            "• Specify instance types (e.g., t3.micro, m5.large)\n"
            "• Include time periods (e.g., 2 months, 90 days)\n"
            "• Mention regions for accurate pricing\n"
            "• Ask about budget impact to see spending effects\n\n"
            "🔍 **Supported Resources:**\n"
            "• EC2 instances (all types)\n"
            "• RDS databases (MySQL, PostgreSQL, etc.)\n"
            "• EBS storage (GP2, GP3, IO1, IO2)\n"
            "• S3 storage\n"
            "• Lambda functions\n\n"
            "❓ Just ask me about any AWS resource cost!"
        )
    
    def _generate_default_response(self, message: str) -> str:
        """Generate default response for unrecognized queries"""
        return (
            "I specialize in AWS cost forecasting and resource pricing. "
            "Try asking me about specific AWS resource costs, like:\n\n"
            "• 'How much would a t3.medium instance cost for 2 months?'\n"
            "• 'Price of 100 GB EBS storage for 6 months'\n"
            "• 'Cost comparison: m5.large vs c5.large'\n\n"
            "Type 'help' for more examples and guidance!"
        )