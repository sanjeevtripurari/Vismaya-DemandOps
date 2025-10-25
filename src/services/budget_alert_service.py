"""
Budget Alert Service
Handles budget monitoring and alerts
"""

import logging
from typing import List, Dict
from datetime import datetime

from ..core.models import BudgetInfo

logger = logging.getLogger(__name__)


class BudgetAlert:
    """Budget alert information"""
    
    def __init__(self, level: str, message: str, action_required: bool = False):
        self.level = level  # INFO, WARNING, CRITICAL
        self.message = message
        self.action_required = action_required
        self.timestamp = datetime.now()


class BudgetAlertService:
    """Service for budget monitoring and alerts"""
    
    def __init__(self):
        self._alert_history: List[BudgetAlert] = []
    
    def check_budget_status(self, budget_info: BudgetInfo) -> List[BudgetAlert]:
        """Check budget status and generate alerts"""
        alerts = []
        
        # Critical: Over maximum limit ($100)
        if budget_info.is_over_maximum:
            alert = BudgetAlert(
                level="CRITICAL",
                message=f"🔴 CRITICAL: Spending ${budget_info.current_spend:.2f} exceeds maximum limit of ${budget_info.maximum_limit:.2f}! "
                       f"Immediate action required to prevent further charges.",
                action_required=True
            )
            alerts.append(alert)
        
        # Warning: Over warning limit ($80)
        elif budget_info.is_over_warning:
            overage = budget_info.current_spend - budget_info.warning_limit
            remaining = budget_info.remaining_maximum_budget
            
            alert = BudgetAlert(
                level="WARNING",
                message=f"🚨 WARNING: Spending ${budget_info.current_spend:.2f} exceeds warning limit of ${budget_info.warning_limit:.2f} "
                       f"by ${overage:.2f}. Only ${remaining:.2f} remaining before hard limit!",
                action_required=True
            )
            alerts.append(alert)
        
        # Caution: Approaching warning limit (75% of $80 = $60)
        elif budget_info.utilization_percentage >= 75:
            remaining = budget_info.remaining_budget
            
            alert = BudgetAlert(
                level="CAUTION",
                message=f"⚠️ CAUTION: Spending ${budget_info.current_spend:.2f} is {budget_info.utilization_percentage:.1f}% "
                       f"of warning limit. ${remaining:.2f} remaining before warning threshold.",
                action_required=False
            )
            alerts.append(alert)
        
        # Healthy status
        else:
            alert = BudgetAlert(
                level="INFO",
                message=f"✅ Budget healthy: ${budget_info.current_spend:.2f} of ${budget_info.warning_limit:.2f} "
                       f"({budget_info.utilization_percentage:.1f}% utilized)",
                action_required=False
            )
            alerts.append(alert)
        
        # Store alerts in history
        self._alert_history.extend(alerts)
        
        return alerts
    
    def get_budget_recommendations(self, budget_info: BudgetInfo) -> List[str]:
        """Get budget-specific recommendations"""
        recommendations = []
        
        if budget_info.is_over_maximum:
            recommendations.extend([
                "🛑 IMMEDIATE: Stop all non-essential AWS services",
                "🔍 Review and terminate unused resources immediately",
                "📞 Contact AWS support to set up billing alerts",
                "💳 Consider setting up AWS Budget alerts for future prevention"
            ])
        
        elif budget_info.is_over_warning:
            recommendations.extend([
                "⚠️ Review current AWS usage and identify cost drivers",
                "🔄 Consider using AWS Cost Explorer to analyze spending patterns",
                "💰 Look for optimization opportunities (Reserved Instances, Spot Instances)",
                "📊 Set up AWS CloudWatch billing alarms",
                "🎯 Plan to reduce usage before reaching $100 limit"
            ])
        
        elif budget_info.utilization_percentage > 75:
            recommendations.extend([
                "📈 Monitor spending closely as you approach the warning limit",
                "🔍 Review Cost Explorer API usage (main cost driver)",
                "💡 Consider caching cost data to reduce API calls",
                "📊 Set up proactive monitoring for budget thresholds"
            ])
        
        else:
            recommendations.extend([
                "✅ Budget is healthy - continue current usage patterns",
                "💡 Consider setting up AWS Budget alerts for proactive monitoring",
                "📊 Regular cost reviews help maintain cost efficiency"
            ])
        
        return recommendations
    
    def get_cost_breakdown_insights(self, budget_info: BudgetInfo, service_costs: List) -> Dict:
        """Get insights about cost breakdown relative to budget"""
        total_services_cost = sum(sc.cost.amount for sc in service_costs)
        
        insights = {
            "budget_status": budget_info.budget_status,
            "budget_emoji": budget_info.budget_status_emoji,
            "utilization_percentage": budget_info.utilization_percentage,
            "remaining_warning": budget_info.remaining_budget,
            "remaining_maximum": budget_info.remaining_maximum_budget,
            "days_until_warning": None,
            "days_until_maximum": None
        }
        
        # Estimate days until limits based on current daily spend
        if budget_info.current_spend > 0:
            # Assume current spend is for current month, estimate daily rate
            daily_rate = budget_info.current_spend / 30  # Rough daily estimate
            
            if daily_rate > 0:
                if budget_info.remaining_budget > 0:
                    insights["days_until_warning"] = int(budget_info.remaining_budget / daily_rate)
                
                if budget_info.remaining_maximum_budget > 0:
                    insights["days_until_maximum"] = int(budget_info.remaining_maximum_budget / daily_rate)
        
        return insights
    
    def format_budget_dashboard(self, budget_info: BudgetInfo) -> str:
        """Format budget information for dashboard display"""
        status_emoji = budget_info.budget_status_emoji
        status = budget_info.budget_status
        
        dashboard = f"""
{status_emoji} **Budget Status: {status}**

💰 **Current Spending:** ${budget_info.current_spend:.2f}
⚠️ **Warning Limit:** ${budget_info.warning_limit:.2f} ({budget_info.utilization_percentage:.1f}% used)
🔴 **Maximum Limit:** ${budget_info.maximum_limit:.2f} ({budget_info.maximum_utilization_percentage:.1f}% used)

📊 **Remaining Budget:**
- Before Warning: ${budget_info.remaining_budget:.2f}
- Before Maximum: ${budget_info.remaining_maximum_budget:.2f}
"""
        
        return dashboard.strip()