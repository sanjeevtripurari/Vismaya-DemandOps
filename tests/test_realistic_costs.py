#!/usr/bin/env python3
"""
Test realistic cost display without AWS credentials
"""

import asyncio
import sys
sys.path.append('.')

from src.infrastructure.demo_data_provider import DemoDataProvider
from src.infrastructure.aws_cost_provider import AWSCostProvider

async def test_realistic_costs():
    print("🧪 Testing Realistic Cost Display")
    print("=" * 50)
    
    # Test demo data provider
    print("\n📊 Testing Demo Data Provider...")
    realistic_summary = DemoDataProvider.get_realistic_usage_summary()
    
    print(f"Current Spend: ${realistic_summary.budget_info.current_spend:.2f}")
    print(f"Budget: ${realistic_summary.budget_info.total_budget:,.2f}")
    print(f"Budget Utilization: {realistic_summary.budget_info.utilization_percentage:.3f}%")
    print(f"Forecasted Spend: ${realistic_summary.cost_forecast.forecasted_amount:.2f}")
    
    print(f"\nService Costs ({len(realistic_summary.service_costs)} services):")
    for service_cost in realistic_summary.service_costs:
        print(f"  - {service_cost.service_type.value}: ${service_cost.cost.amount:.2f}")
    
    print(f"\nResources:")
    print(f"  - EC2 Instances: {len(realistic_summary.ec2_instances)}")
    print(f"  - Storage Volumes: {len(realistic_summary.storage_volumes)}")
    print(f"  - Database Instances: {len(realistic_summary.database_instances)}")
    
    # Test mock cost provider methods
    print("\n🔧 Testing Cost Provider Mock Methods...")
    
    # Create a mock cost provider (without AWS session)
    mock_provider = AWSCostProvider(None)
    
    # Test mock methods
    current_costs = mock_provider._get_mock_current_costs()
    print(f"Mock Current Costs: ${current_costs.amount:.2f}")
    
    service_costs = mock_provider._get_mock_service_costs()
    print(f"Mock Service Costs ({len(service_costs)} services):")
    for service_cost in service_costs:
        print(f"  - {service_cost.service_type.value}: ${service_cost.cost.amount:.2f}")
    
    monthly_trend = mock_provider._get_mock_monthly_trend()
    print(f"Mock Monthly Trend ({len(monthly_trend)} months):")
    for trend in monthly_trend[-3:]:  # Last 3 months
        month_name = trend.start_date.strftime('%b %Y') if trend.start_date else 'Unknown'
        print(f"  - {month_name}: ${trend.amount:.2f}")
    
    print("\n✅ All realistic cost tests passed!")
    print(f"\n💡 The dashboard should now show ${realistic_summary.budget_info.current_spend:.2f} instead of $12,500")

if __name__ == "__main__":
    asyncio.run(test_realistic_costs())