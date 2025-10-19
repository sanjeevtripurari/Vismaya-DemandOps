#!/usr/bin/env python3
"""
Budget Alert System Test
Tests the budget monitoring and alert system
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import asyncio
from config import Config
from src.application.dependency_injection import DependencyContainer
from src.services.budget_alert_service import BudgetAlertService
from src.core.models import BudgetInfo


async def test_budget_alerts():
    """Test budget alert system with different spending scenarios"""
    print("🚨 Budget Alert System Test")
    print("=" * 50)
    
    # Initialize alert service
    alert_service = BudgetAlertService()
    
    # Test scenarios
    scenarios = [
        {
            "name": "Healthy Budget",
            "current_spend": 1.72,
            "expected_status": "HEALTHY"
        },
        {
            "name": "Approaching Warning (75%)",
            "current_spend": 60.0,
            "expected_status": "CAUTION"
        },
        {
            "name": "Over Warning Limit",
            "current_spend": 85.0,
            "expected_status": "WARNING"
        },
        {
            "name": "Over Maximum Limit",
            "current_spend": 105.0,
            "expected_status": "CRITICAL"
        }
    ]
    
    for scenario in scenarios:
        print(f"\n📊 Testing: {scenario['name']}")
        print("-" * 30)
        
        # Create budget info for scenario
        from config import Config
        budget_info = BudgetInfo(
            total_budget=Config.BUDGET_WARNING_LIMIT,  # Warning limit
            current_spend=scenario['current_spend'],
            warning_limit=Config.BUDGET_WARNING_LIMIT,
            maximum_limit=Config.BUDGET_MAXIMUM_LIMIT
            maximum_limit=100.0
        )
        
        # Check alerts
        alerts = alert_service.check_budget_status(budget_info)
        
        # Display results
        print(f"💰 Current Spend: ${budget_info.current_spend:.2f}")
        print(f"📈 Status: {budget_info.budget_status} {budget_info.budget_status_emoji}")
        print(f"📊 Warning Utilization: {budget_info.utilization_percentage:.1f}%")
        print(f"🔴 Maximum Utilization: {budget_info.maximum_utilization_percentage:.1f}%")
        
        # Show alerts
        for alert in alerts:
            print(f"🚨 {alert.level}: {alert.message}")
            if alert.action_required:
                print("   ⚡ ACTION REQUIRED!")
        
        # Show recommendations
        recommendations = alert_service.get_budget_recommendations(budget_info)
        print("\n💡 Recommendations:")
        for rec in recommendations[:3]:  # Show top 3
            print(f"   • {rec}")
        
        # Verify expected status
        if budget_info.budget_status == scenario['expected_status']:
            print(f"✅ Status matches expected: {scenario['expected_status']}")
        else:
            print(f"❌ Status mismatch! Expected: {scenario['expected_status']}, Got: {budget_info.budget_status}")


async def test_real_budget_status():
    """Test with real AWS spending data"""
    print("\n\n🔍 Real AWS Budget Status")
    print("=" * 50)
    
    # Get real data
    config = Config()
    container = DependencyContainer(config)
    usage_summary_use_case = container.get_use_case('get_usage_summary')
    
    usage_summary = await usage_summary_use_case.execute()
    
    # Initialize alert service
    alert_service = BudgetAlertService()
    
    # Check real budget status
    alerts = alert_service.check_budget_status(usage_summary.budget_info)
    
    # Display dashboard
    dashboard = alert_service.format_budget_dashboard(usage_summary.budget_info)
    print(dashboard)
    
    # Show alerts
    print("\n🚨 Current Alerts:")
    for alert in alerts:
        print(f"   {alert.level}: {alert.message}")
    
    # Show recommendations
    recommendations = alert_service.get_budget_recommendations(usage_summary.budget_info)
    print("\n💡 Recommendations:")
    for rec in recommendations:
        print(f"   • {rec}")
    
    # Show insights
    insights = alert_service.get_cost_breakdown_insights(
        usage_summary.budget_info, 
        usage_summary.service_costs
    )
    
    print(f"\n📈 Budget Insights:")
    print(f"   • Status: {insights['budget_status']} {insights['budget_emoji']}")
    print(f"   • Warning Utilization: {insights['utilization_percentage']:.1f}%")
    print(f"   • Remaining before warning: ${insights['remaining_warning']:.2f}")
    print(f"   • Remaining before maximum: ${insights['remaining_maximum']:.2f}")
    
    if insights['days_until_warning']:
        print(f"   • Estimated days until warning: {insights['days_until_warning']}")
    if insights['days_until_maximum']:
        print(f"   • Estimated days until maximum: {insights['days_until_maximum']}")


if __name__ == "__main__":
    asyncio.run(test_budget_alerts())
    asyncio.run(test_real_budget_status())