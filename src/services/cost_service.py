"""
Cost Analysis Service
Orchestrates cost data collection and analysis
Following Single Responsibility Principle
"""

import logging
from typing import List, Optional, Dict
from datetime import datetime, timedelta

from ..core.interfaces import ICostDataProvider, IForecastingService, IAIAssistant
from ..core.models import UsageSummary, CostData, CostForecast, OptimizationRecommendation

logger = logging.getLogger(__name__)


class CostAnalysisService:
    """Service for cost analysis and insights"""
    
    def __init__(self, 
                 cost_provider: ICostDataProvider,
                 forecasting_service: IForecastingService,
                 ai_assistant: IAIAssistant):
        self._cost_provider = cost_provider
        self._forecasting_service = forecasting_service
        self._ai_assistant = ai_assistant
    
    async def get_cost_insights(self) -> str:
        """Get AI-powered cost insights"""
        try:
            # Get current costs
            current_costs = await self._cost_provider.get_current_costs()
            service_costs = await self._cost_provider.get_service_costs()
            
            # Create basic usage summary for analysis
            from ..core.models import BudgetInfo
            budget_info = BudgetInfo(
                total_budget=15000,  # Default budget
                current_spend=current_costs.amount
            )
            
            usage_summary = UsageSummary(
                budget_info=budget_info,
                service_costs=service_costs,
                ec2_instances=[],
                storage_volumes=[],
                database_instances=[],
                cost_forecast=CostForecast(
                    forecasted_amount=current_costs.amount * 1.1,
                    confidence_level=0.8,
                    forecast_period_days=30,
                    base_amount=current_costs.amount
                ),
                recommendations=[]
            )
            
            return await self._ai_assistant.analyze_costs(usage_summary)
            
        except Exception as e:
            logger.error(f"Error getting cost insights: {e}")
            return "Unable to analyze costs at this time. Please check your AWS connection."
    
    async def get_cost_forecast(self, days: int = 30) -> Optional[CostForecast]:
        """Get cost forecast for specified period"""
        try:
            # Get historical data
            historical_data = await self._cost_provider.get_monthly_trend(months=6)
            
            if not historical_data:
                logger.warning("No historical data available for forecasting")
                return None
            
            return await self._forecasting_service.generate_forecast(historical_data)
            
        except Exception as e:
            logger.error(f"Error generating forecast: {e}")
            return None
    
    async def get_optimization_recommendations(self, 
                                            usage_summary: UsageSummary) -> List[OptimizationRecommendation]:
        """Get AI-powered optimization recommendations"""
        try:
            return await self._ai_assistant.generate_recommendations(usage_summary)
        except Exception as e:
            logger.error(f"Error getting recommendations: {e}")
            return []
    
    async def analyze_cost_trends(self) -> Dict:
        """Analyze cost trends and patterns"""
        try:
            monthly_data = await self._cost_provider.get_monthly_trend(months=6)
            
            if len(monthly_data) < 2:
                return {"trend": "insufficient_data", "growth_rate": 0}
            
            # Calculate growth rate
            recent_cost = monthly_data[-1].amount
            previous_cost = monthly_data[-2].amount
            
            if previous_cost > 0:
                growth_rate = ((recent_cost - previous_cost) / previous_cost) * 100
            else:
                growth_rate = 0
            
            # Determine trend
            if growth_rate > 10:
                trend = "increasing_rapidly"
            elif growth_rate > 0:
                trend = "increasing"
            elif growth_rate < -10:
                trend = "decreasing_rapidly"
            elif growth_rate < 0:
                trend = "decreasing"
            else:
                trend = "stable"
            
            return {
                "trend": trend,
                "growth_rate": growth_rate,
                "current_cost": recent_cost,
                "previous_cost": previous_cost,
                "data_points": len(monthly_data)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing trends: {e}")
            return {"trend": "error", "growth_rate": 0}