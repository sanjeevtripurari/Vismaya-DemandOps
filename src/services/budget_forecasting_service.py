"""
Budget Forecasting Service
Provides detailed budget projections and timeline predictions
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import math

from ..core.models import BudgetInfo, CostForecast

logger = logging.getLogger(__name__)


class BudgetForecastingService:
    """Service for budget forecasting and timeline predictions"""
    
    def __init__(self):
        pass
    
    def generate_budget_timeline(self, budget_info: BudgetInfo, cost_forecast: CostForecast) -> Dict:
        """Generate detailed budget timeline with warning and critical predictions"""
        
        current_spend = budget_info.current_spend
        warning_limit = budget_info.warning_limit
        maximum_limit = budget_info.maximum_limit
        
        # Calculate timeline predictions
        timeline = {
            'current_spend': current_spend,
            'warning_limit': warning_limit,
            'maximum_limit': maximum_limit,
            'daily_cost_estimate': cost_forecast.daily_cost_estimate,
            'daily_growth_rate': cost_forecast.daily_growth_rate,
            'monthly_growth_rate': cost_forecast.monthly_growth_rate,
            'days_to_warning': None,
            'days_to_critical': None,
            'warning_date': None,
            'critical_date': None,
            'monthly_projection': cost_forecast.forecasted_amount,
            'will_exceed_warning': False,
            'will_exceed_critical': False,
            'safe_daily_budget': None,
            'recommended_actions': []
        }
        
        # Calculate days to reach limits (only if there's positive growth)
        if current_spend < warning_limit and cost_forecast.daily_growth_rate > 0:
            days_to_warning = cost_forecast.days_to_reach_amount(warning_limit)
            if days_to_warning != float('inf') and days_to_warning > 0:
                timeline['days_to_warning'] = days_to_warning
                timeline['warning_date'] = (datetime.now() + timedelta(days=days_to_warning)).strftime('%Y-%m-%d')
                timeline['will_exceed_warning'] = days_to_warning <= 30
        
        if current_spend < maximum_limit and cost_forecast.daily_growth_rate > 0:
            days_to_critical = cost_forecast.days_to_reach_amount(maximum_limit)
            if days_to_critical != float('inf') and days_to_critical > 0:
                timeline['days_to_critical'] = days_to_critical
                timeline['critical_date'] = (datetime.now() + timedelta(days=days_to_critical)).strftime('%Y-%m-%d')
                timeline['will_exceed_critical'] = days_to_critical <= 30
        
        # Calculate safe daily budget to stay under warning limit
        remaining_days_in_month = 30 - datetime.now().day
        if remaining_days_in_month > 0:
            remaining_budget = warning_limit - current_spend
            timeline['safe_daily_budget'] = remaining_budget / remaining_days_in_month
        
        # Generate recommendations based on timeline
        timeline['recommended_actions'] = self._generate_timeline_recommendations(timeline)
        
        return timeline
    
    def _generate_timeline_recommendations(self, timeline: Dict) -> List[str]:
        """Generate recommendations based on budget timeline"""
        recommendations = []
        
        days_to_warning = timeline.get('days_to_warning')
        days_to_critical = timeline.get('days_to_critical')
        safe_daily_budget = timeline.get('safe_daily_budget', 0)
        current_daily_cost = timeline.get('daily_cost_estimate', 0)
        
        if timeline['will_exceed_critical']:
            recommendations.extend([
                f"🚨 URGENT: Will hit critical limit (${timeline['maximum_limit']}) in {days_to_critical} days",
                "🛑 Immediately reduce AWS usage to prevent overage charges",
                "📞 Contact AWS support to set up billing alerts",
                f"💰 Reduce daily spending from ${current_daily_cost:.2f} to ${safe_daily_budget:.2f}"
            ])
        
        elif timeline['will_exceed_warning']:
            recommendations.extend([
                f"⚠️ WARNING: Will hit warning limit (${timeline['warning_limit']}) in {days_to_warning} days",
                "📊 Monitor usage closely and optimize high-cost services",
                f"🎯 Target daily budget: ${safe_daily_budget:.2f} (currently ${current_daily_cost:.2f})",
                "🔍 Review Cost Explorer API usage - main cost driver"
            ])
        
        elif days_to_warning and days_to_warning <= 60:
            recommendations.extend([
                f"📈 Approaching warning limit in {days_to_warning} days at current growth rate",
                "💡 Consider optimizing usage patterns to extend timeline",
                f"🎯 Safe daily budget: ${safe_daily_budget:.2f}",
                "📊 Set up proactive monitoring"
            ])
        
        else:
            recommendations.extend([
                "✅ Budget is healthy - no immediate concerns",
                f"💰 Current daily cost: ${current_daily_cost:.2f}",
                f"🎯 Daily budget capacity: ${safe_daily_budget:.2f}",
                "📊 Costs are stable - continue current usage patterns",
                "💡 Consider this a good baseline for future planning"
            ])
        
        # Add growth-specific recommendations
        growth_rate = timeline.get('monthly_growth_rate', 0)
        if growth_rate > 20:
            recommendations.append(f"📈 High growth rate ({growth_rate:.1f}%/month) - investigate usage spikes")
        elif growth_rate < -10:
            recommendations.append(f"📉 Declining usage ({growth_rate:.1f}%/month) - good cost optimization")
        
        return recommendations
    
    def generate_monthly_projections(self, cost_forecast: CostForecast, budget_info: BudgetInfo) -> Dict:
        """Generate detailed monthly cost projections"""
        
        projections = {
            'current_month': cost_forecast.base_amount,
            'next_month': cost_forecast.forecasted_amount,
            'monthly_projections': [],
            'budget_status_timeline': []
        }
        
        # Generate 6-month projections
        current_amount = cost_forecast.base_amount
        for month in range(1, 7):
            # Apply monthly growth
            projected_amount = current_amount * (cost_forecast.trend_factor ** month)
            
            # Determine budget status
            if projected_amount > budget_info.maximum_limit:
                status = "CRITICAL"
                status_emoji = "🔴"
            elif projected_amount > budget_info.warning_limit:
                status = "WARNING"
                status_emoji = "🚨"
            elif projected_amount > budget_info.warning_limit * 0.75:
                status = "CAUTION"
                status_emoji = "⚠️"
            else:
                status = "HEALTHY"
                status_emoji = "✅"
            
            month_data = {
                'month': month,
                'projected_cost': projected_amount,
                'status': status,
                'status_emoji': status_emoji,
                'over_warning': projected_amount > budget_info.warning_limit,
                'over_critical': projected_amount > budget_info.maximum_limit
            }
            
            projections['monthly_projections'].append(month_data)
            projections['budget_status_timeline'].append({
                'month': f"Month +{month}",
                'status': f"{status_emoji} {status}",
                'amount': f"${projected_amount:.2f}"
            })
        
        return projections
    
    def calculate_cost_optimization_targets(self, timeline: Dict, budget_info: BudgetInfo) -> Dict:
        """Calculate cost optimization targets to stay within budget"""
        
        current_spend = budget_info.current_spend
        warning_limit = budget_info.warning_limit
        maximum_limit = budget_info.maximum_limit
        
        # Calculate required cost reductions
        targets = {
            'current_spend': current_spend,
            'warning_limit': warning_limit,
            'maximum_limit': maximum_limit,
            'reduction_needed_for_warning': max(0, current_spend - warning_limit),
            'reduction_needed_for_critical': max(0, current_spend - maximum_limit),
            'optimization_opportunities': []
        }
        
        # If already over limits, calculate immediate reductions needed
        if current_spend > warning_limit:
            overage = current_spend - warning_limit
            targets['optimization_opportunities'].extend([
                f"Immediate reduction needed: ${overage:.2f} to reach warning limit",
                "Focus on highest-cost services first",
                "Consider pausing non-essential services"
            ])
        
        # Calculate sustainable daily spending rates
        remaining_days = 30 - datetime.now().day
        if remaining_days > 0:
            safe_daily_rate = (warning_limit - current_spend) / remaining_days
            targets['safe_daily_spending_rate'] = max(0, safe_daily_rate)
            
            current_daily_rate = timeline.get('daily_cost_estimate', 0)
            if current_daily_rate > safe_daily_rate:
                daily_reduction = current_daily_rate - safe_daily_rate
                targets['daily_reduction_needed'] = daily_reduction
                targets['optimization_opportunities'].append(
                    f"Reduce daily spending by ${daily_reduction:.2f} (from ${current_daily_rate:.2f} to ${safe_daily_rate:.2f})"
                )
        
        return targets