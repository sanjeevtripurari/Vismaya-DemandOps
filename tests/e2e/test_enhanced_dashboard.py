#!/usr/bin/env python3
"""
Enhanced Dashboard Test
Tests the complete dashboard functionality with:
1. Current Usage - Real actual values summary
2. Detailed Usage - Proper cost breakdown with tax/pre-tax
3. Forecast - Organic growth projections with warning/critical timeline
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import asyncio
from config import Config
from src.application.dependency_injection import DependencyContainer
from src.services.budget_forecasting_service import BudgetForecastingService


async def test_enhanced_dashboard():
    """Test all enhanced dashboard features"""
    print("🚀 Enhanced Dashboard Test")
    print("=" * 80)
    
    # Initialize services
    config = Config()
    container = DependencyContainer(config)
    usage_summary_use_case = container.get_use_case('get_usage_summary')
    forecasting_service = BudgetForecastingService()
    
    # Get comprehensive usage data
    usage_summary = await usage_summary_use_case.execute()
    
    # 1. CURRENT USAGE - Real Actual Values Summary
    print("\n📊 CURRENT USAGE SUMMARY")
    print("=" * 50)
    
    budget_info = usage_summary.budget_info
    print(f"💰 Current Spend: ${budget_info.current_spend:.2f}")
    print(f"⚠️ Warning Limit: ${budget_info.warning_limit:.2f}")
    print(f"🔴 Critical Limit: ${budget_info.maximum_limit:.2f}")
    print(f"📈 Budget Status: {budget_info.budget_status} {budget_info.budget_status_emoji}")
    print(f"📊 Utilization: {budget_info.utilization_percentage:.1f}%")
    print(f"💵 Remaining Budget: ${budget_info.remaining_budget:.2f}")
    
    # Service summary
    print(f"\n🔍 Service Summary ({len(usage_summary.service_costs)} services):")
    for service_cost in sorted(usage_summary.service_costs, key=lambda x: x.cost.amount, reverse=True)[:5]:
        service_name = service_cost.service_type.value
        amount = service_cost.cost.amount
        if amount > 0:
            percentage = (amount / budget_info.current_spend) * 100
            print(f"   • {service_name}: ${amount:.6f} ({percentage:.1f}%)")
    
    # 2. DETAILED USAGE - Proper Cost Breakdown
    print("\n\n📋 DETAILED USAGE BREAKDOWN")
    print("=" * 50)
    
    total_pre_tax = sum(getattr(sc.cost, 'pre_tax_amount', 0) or 0 for sc in usage_summary.service_costs)
    total_tax = sum(getattr(sc.cost, 'tax_amount', 0) or 0 for sc in usage_summary.service_costs)
    
    print(f"💰 Total Cost: ${budget_info.current_spend:.6f}")
    if total_tax > 0:
        print(f"💵 Pre-tax Cost: ${total_pre_tax:.6f}")
        print(f"🏛️ Tax Amount: ${total_tax:.6f}")
        print(f"📊 Tax Rate: {(total_tax/total_pre_tax*100):.2f}%")
    
    print("\n🔍 Service Breakdown:")
    for service_cost in usage_summary.service_costs:
        if service_cost.cost.amount > 0:
            service_name = getattr(service_cost.cost, 'service_name', service_cost.service_type.value)
            amount = service_cost.cost.amount
            usage_qty = getattr(service_cost.cost, 'usage_quantity', None)
            
            line = f"   💳 {service_name}: ${amount:.6f}"
            if usage_qty and usage_qty > 0:
                cost_per_unit = amount / usage_qty
                line += f" ({usage_qty:.0f} units @ ${cost_per_unit:.6f}/unit)"
            
            print(line)
    
    # 3. FORECAST - Organic Growth Projections
    print("\n\n📈 FORECAST & TIMELINE PROJECTIONS")
    print("=" * 50)
    
    cost_forecast = usage_summary.cost_forecast
    timeline = forecasting_service.generate_budget_timeline(budget_info, cost_forecast)
    
    # Current growth analysis
    print(f"📊 Growth Analysis:")
    print(f"   • Current Daily Cost: ${timeline['daily_cost_estimate']:.4f}")
    print(f"   • Daily Growth Rate: {timeline['daily_growth_rate']*100:.3f}%")
    print(f"   • Monthly Growth Rate: {timeline['monthly_growth_rate']:.1f}%")
    print(f"   • Next Month Projection: ${timeline['monthly_projection']:.2f}")
    
    # Timeline predictions - only show if there's a real concern
    print(f"\n⏰ Budget Timeline:")
    
    current_spend = budget_info.current_spend
    warning_limit = budget_info.warning_limit
    critical_limit = budget_info.maximum_limit
    
    # Check if we're already over limits or will hit them
    already_over_warning = current_spend > warning_limit
    already_over_critical = current_spend > critical_limit
    will_hit_warning = timeline.get('days_to_warning') and timeline['days_to_warning'] <= 365
    will_hit_critical = timeline.get('days_to_critical') and timeline['days_to_critical'] <= 365
    
    if already_over_warning:
        overage = current_spend - warning_limit
        print(f"   🚨 WARNING: Over warning limit by ${overage:.2f}")
    elif will_hit_warning:
        print(f"   ⚠️ Warning Limit: {timeline['days_to_warning']} days ({timeline['warning_date']})")
    
    if already_over_critical:
        overage = current_spend - critical_limit
        print(f"   🔴 CRITICAL: Over critical limit by ${overage:.2f}")
    elif will_hit_critical:
        print(f"   🔴 Critical Limit: {timeline['days_to_critical']} days ({timeline['critical_date']})")
    
    # If no concerns, show positive message
    if not (already_over_warning or already_over_critical or will_hit_warning or will_hit_critical):
        print(f"   ✅ No budget concerns - costs are stable")
        print(f"   💰 ${current_spend:.2f} of ${warning_limit:.2f} warning limit ({(current_spend/warning_limit*100):.1f}% used)")
        print(f"   🎯 ${warning_limit - current_spend:.2f} remaining before warning")
    
    # Safe spending recommendations
    if timeline['safe_daily_budget']:
        print(f"\n💡 Budget Recommendations:")
        print(f"   • Safe Daily Budget: ${timeline['safe_daily_budget']:.4f}")
        current_daily = timeline['daily_cost_estimate']
        if current_daily > timeline['safe_daily_budget']:
            reduction = current_daily - timeline['safe_daily_budget']
            print(f"   • Daily Reduction Needed: ${reduction:.4f}")
        else:
            buffer = timeline['safe_daily_budget'] - current_daily
            print(f"   • Daily Budget Buffer: ${buffer:.4f}")
    
    # Monthly projections
    projections = forecasting_service.generate_monthly_projections(cost_forecast, budget_info)
    print(f"\n📅 6-Month Projections:")
    for proj in projections['monthly_projections'][:3]:  # Show first 3 months
        print(f"   Month +{proj['month']}: ${proj['projected_cost']:.2f} {proj['status_emoji']} {proj['status']}")
    
    # Action items
    print(f"\n🎯 Recommended Actions:")
    for action in timeline['recommended_actions'][:5]:  # Top 5 actions
        print(f"   • {action}")
    
    # Cost optimization targets
    optimization_targets = forecasting_service.calculate_cost_optimization_targets(timeline, budget_info)
    
    if optimization_targets['reduction_needed_for_warning'] > 0:
        print(f"\n🔧 Cost Optimization Targets:")
        print(f"   • Immediate Reduction Needed: ${optimization_targets['reduction_needed_for_warning']:.2f}")
        if 'daily_reduction_needed' in optimization_targets:
            print(f"   • Daily Spending Reduction: ${optimization_targets['daily_reduction_needed']:.4f}")
    
    # Summary insights
    print(f"\n\n🎯 KEY INSIGHTS")
    print("=" * 30)
    
    if timeline['will_exceed_critical']:
        print("🚨 CRITICAL: Will exceed maximum budget this month!")
    elif timeline['will_exceed_warning']:
        print("⚠️ WARNING: Will exceed warning limit this month")
    else:
        print("✅ Budget timeline is healthy")
    
    print(f"💰 Current burn rate: ${timeline['daily_cost_estimate']:.4f}/day")
    print(f"📈 Growth trend: {timeline['monthly_growth_rate']:.1f}%/month")
    
    if timeline['safe_daily_budget']:
        utilization = (timeline['daily_cost_estimate'] / timeline['safe_daily_budget']) * 100
        print(f"🎯 Daily budget utilization: {utilization:.1f}%")


if __name__ == "__main__":
    asyncio.run(test_enhanced_dashboard())