"""
Application Use Cases
Orchestrates business logic and coordinates between services
Following Use Case pattern and Single Responsibility Principle
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

from ..core.models import UsageSummary, BudgetInfo, CostForecast, ScenarioInput, ScenarioResult
from ..services.cost_service import CostAnalysisService
from ..services.resource_service import ResourceManagementService

logger = logging.getLogger(__name__)


class GetUsageSummaryUseCase:
    """Use case for getting complete usage summary"""
    
    def __init__(self, 
                 cost_service: CostAnalysisService,
                 resource_service: ResourceManagementService,
                 config):
        self._cost_service = cost_service
        self._resource_service = resource_service
        self._config = config
    
    async def execute(self) -> UsageSummary:
        """Execute the use case"""
        try:
            logger.info("Executing GetUsageSummaryUseCase")
            
            # Get cost data
            current_costs = await self._cost_service._cost_provider.get_current_costs()
            service_costs = await self._cost_service._cost_provider.get_service_costs()
            
            # Get resource inventory
            inventory = await self._resource_service.get_resource_inventory()
            
            # Get cost forecast
            forecast = await self._cost_service.get_cost_forecast()
            if not forecast:
                forecast = CostForecast(
                    forecasted_amount=current_costs.amount * 1.1,
                    confidence_level=0.7,
                    forecast_period_days=30,
                    base_amount=current_costs.amount
                )
            
            # Create budget info with warning and maximum limits
            budget_info = BudgetInfo(
                total_budget=self._config.BUDGET_WARNING_LIMIT,
                current_spend=current_costs.amount,
                warning_limit=self._config.BUDGET_WARNING_LIMIT,
                maximum_limit=self._config.BUDGET_MAXIMUM_LIMIT
            )
            
            # Create usage summary
            usage_summary = UsageSummary(
                budget_info=budget_info,
                service_costs=service_costs,
                ec2_instances=inventory["ec2_instances"],
                storage_volumes=inventory["storage_volumes"],
                database_instances=inventory["database_instances"],
                cost_forecast=forecast,
                recommendations=[]
            )
            
            # Get AI recommendations
            recommendations = await self._cost_service.get_optimization_recommendations(usage_summary)
            usage_summary.recommendations = recommendations
            
            logger.info("UsageSummary created successfully")
            return usage_summary
            
        except Exception as e:
            logger.error(f"Error in GetUsageSummaryUseCase: {e}")
            # Return minimal summary on error
            return self._create_minimal_summary()
    
    def _create_minimal_summary(self) -> UsageSummary:
        """Create minimal summary for error cases"""
        return UsageSummary(
            budget_info=BudgetInfo(
                total_budget=self._config.BUDGET_WARNING_LIMIT,
                current_spend=0.0,
                warning_limit=self._config.BUDGET_WARNING_LIMIT,
                maximum_limit=self._config.BUDGET_MAXIMUM_LIMIT
            ),
            service_costs=[],
            ec2_instances=[],
            storage_volumes=[],
            database_instances=[],
            cost_forecast=CostForecast(
                forecasted_amount=0.0,
                confidence_level=0.0,
                forecast_period_days=30,
                base_amount=0.0
            ),
            recommendations=[]
        )


class AnalyzeScenarioUseCase:
    """Use case for analyzing what-if scenarios"""
    
    def __init__(self, 
                 resource_service: ResourceManagementService,
                 default_budget: float = 15000):
        self._resource_service = resource_service
        self._default_budget = default_budget
    
    async def execute(self, scenario: ScenarioInput) -> ScenarioResult:
        """Execute scenario analysis"""
        try:
            logger.info(f"Executing AnalyzeScenarioUseCase with scenario: {scenario}")
            
            # Get current resource inventory
            inventory = await self._resource_service.get_resource_inventory()
            
            # Calculate scenario impact
            impact = self._resource_service.calculate_scenario_impact(inventory, scenario)
            
            # Calculate budget impact
            budget_impact = max(0, impact["new_total_monthly_cost"] - self._default_budget)
            
            # Generate recommendations
            recommendations = self._generate_scenario_recommendations(impact, scenario)
            
            return ScenarioResult(
                scenario_input=scenario,
                projected_monthly_cost=impact["new_total_monthly_cost"],
                cost_difference=impact["additional_monthly_cost"],
                budget_impact=budget_impact,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Error in AnalyzeScenarioUseCase: {e}")
            return ScenarioResult(
                scenario_input=scenario,
                projected_monthly_cost=0.0,
                cost_difference=0.0,
                budget_impact=0.0,
                recommendations=["Error analyzing scenario. Please try again."]
            )
    
    def _generate_scenario_recommendations(self, impact: Dict, scenario: ScenarioInput) -> List[str]:
        """Generate recommendations based on scenario impact"""
        recommendations = []
        
        if impact["cost_increase_percentage"] > 20:
            recommendations.append("⚠️ This scenario increases costs by more than 20%. Consider phased implementation.")
        
        if scenario.additional_ec2_instances > 0:
            recommendations.append(f"💡 Consider using Spot instances for the {scenario.additional_ec2_instances} new EC2 instances to save up to 70%.")
        
        if scenario.additional_storage_gb > 100:
            recommendations.append("💾 For large storage additions, consider using S3 with lifecycle policies for cost optimization.")
        
        if impact["new_total_monthly_cost"] > self._default_budget:
            overage = impact["new_total_monthly_cost"] - self._default_budget
            recommendations.append(f"💰 This scenario exceeds budget by ${overage:.2f}. Consider budget adjustment or cost optimization.")
        
        if not recommendations:
            recommendations.append("✅ This scenario looks cost-effective and within budget limits.")
        
        return recommendations


class GetCostInsightsUseCase:
    """Use case for getting AI-powered cost insights"""
    
    def __init__(self, cost_service: CostAnalysisService):
        self._cost_service = cost_service
    
    async def execute(self) -> str:
        """Execute cost insights analysis"""
        try:
            logger.info("Executing GetCostInsightsUseCase")
            return await self._cost_service.get_cost_insights()
        except Exception as e:
            logger.error(f"Error in GetCostInsightsUseCase: {e}")
            return "Unable to generate cost insights at this time. Please check your AWS connection."


class HandleChatUseCase:
    """Use case for handling chat interactions with comprehensive context"""
    
    def __init__(self, 
                 cost_service: CostAnalysisService,
                 get_usage_summary_use_case: GetUsageSummaryUseCase):
        self._cost_service = cost_service
        self._get_usage_summary_use_case = get_usage_summary_use_case
    
    async def execute(self, message: str) -> str:
        """Execute chat interaction with full context"""
        try:
            logger.info(f"Executing HandleChatUseCase with message: {message[:50]}...")
            
            # Get comprehensive usage summary for context
            usage_summary = await self._get_usage_summary_use_case.execute()
            
            # Enhance context with real-time data if needed
            if not usage_summary.service_costs:
                # Try to get fresh service cost data
                try:
                    service_costs = await self._cost_service._cost_provider.get_service_costs()
                    usage_summary.service_costs = service_costs
                except Exception as e:
                    logger.warning(f"Could not refresh service costs: {e}")
            
            # Get AI response with enhanced context
            response = await self._cost_service._ai_assistant.chat_response(message, usage_summary)
            
            # Add data freshness indicator
            if usage_summary.last_updated:
                from datetime import datetime, timedelta
                if datetime.now() - usage_summary.last_updated > timedelta(hours=1):
                    response += "\n\n*Note: Data is from your last refresh. Use the refresh button for the latest information.*"
            
            return response
            
        except Exception as e:
            logger.error(f"Error in HandleChatUseCase: {e}")
            return f"I'm having trouble accessing your AWS data right now. Please check your connection and try again. (Error: {str(e)[:50]}...)"


class GetResourceDetailsUseCase:
    """Use case for getting detailed resource information"""
    
    def __init__(self, resource_service: ResourceManagementService):
        self._resource_service = resource_service
    
    async def execute(self) -> Dict:
        """Execute resource details retrieval"""
        try:
            logger.info("Executing GetResourceDetailsUseCase")
            
            ec2_summary = await self._resource_service.get_ec2_summary()
            storage_summary = await self._resource_service.get_storage_summary()
            database_summary = await self._resource_service.get_database_summary()
            
            return {
                "ec2": ec2_summary,
                "storage": storage_summary,
                "databases": database_summary,
                "total_monthly_cost": (
                    ec2_summary["total_monthly_cost"] +
                    storage_summary["total_monthly_cost"] +
                    database_summary["total_monthly_cost"]
                )
            }
            
        except Exception as e:
            logger.error(f"Error in GetResourceDetailsUseCase: {e}")
            return {
                "ec2": {"total_instances": 0, "total_monthly_cost": 0, "instances": []},
                "storage": {"total_volumes": 0, "total_monthly_cost": 0, "volumes": []},
                "databases": {"total_databases": 0, "total_monthly_cost": 0, "databases": []},
                "total_monthly_cost": 0
            }