#!/usr/bin/env python3
"""
Test script to verify cost fetching fixes
"""

import asyncio
import sys
import os
sys.path.append('.')

from src.infrastructure.aws_cost_provider import AWSCostProvider
from src.infrastructure.aws_session_factory import AWSSessionFactory
from config import Config

async def test_cost_provider():
    print("🧪 Testing Cost Provider Fixes")
    print("=" * 50)
    
    try:
        # Create session factory
        session_factory = AWSSessionFactory(Config)
        session = session_factory.create_session()
        
        # Create cost provider
        cost_provider = AWSCostProvider(session)
        
        print("✅ Cost provider initialized")
        
        # Test current costs
        print("\n📊 Testing current costs...")
        current_costs = await cost_provider.get_current_costs()
        print(f"Current costs: ${current_costs.amount:.2f}")
        
        # Test service costs
        print("\n🔧 Testing service costs...")
        service_costs = await cost_provider.get_service_costs()
        print(f"Service costs count: {len(service_costs)}")
        
        for service_cost in service_costs:
            print(f"  - {service_cost.service_type.value}: ${service_cost.cost.amount:.2f}")
        
        # Test monthly trend
        print("\n📈 Testing monthly trend...")
        monthly_trend = await cost_provider.get_monthly_trend()
        print(f"Monthly trend data points: {len(monthly_trend)}")
        
        for trend in monthly_trend[-3:]:  # Show last 3 months
            print(f"  - {trend.start_date.strftime('%Y-%m') if trend.start_date else 'Unknown'}: ${trend.amount:.2f}")
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_cost_provider())