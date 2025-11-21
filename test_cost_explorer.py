#!/usr/bin/env python3
"""
Test Cost Explorer API Integration
Quick test to verify cost data consistency
"""

import asyncio
import sys
from datetime import datetime
from src.application.dependency_injection import DependencyContainer
from config import Config

async def test_cost_explorer():
    """Test Cost Explorer API calls for consistency"""
    print("🔍 Testing Cost Explorer API Integration...")
    
    try:
        # Initialize container
        container = DependencyContainer(Config)
        container.initialize()
        
        # Get cost provider
        cost_provider = container.get('cost_provider')
        
        print("\n📊 Fetching current costs...")
        current_costs = await cost_provider.get_current_costs()
        print(f"   Total Cost: ${current_costs.amount:.2f}")
        
        print("\n🔍 Fetching service costs...")
        service_costs = await cost_provider.get_service_costs()
        service_total = sum(sc.cost.amount for sc in service_costs)
        print(f"   Service Count: {len(service_costs)}")
        print(f"   Service Total: ${service_total:.2f}")
        
        print("\n📋 Service Breakdown:")
        for sc in service_costs:
            if sc.cost.amount > 0:
                print(f"   • {sc.cost.service_name}: ${sc.cost.amount:.2f}")
        
        print("\n✅ Cost Consistency Check:")
        difference = abs(current_costs.amount - service_total)
        if difference <= 0.01:
            print(f"   ✅ PASS: Costs match (difference: ${difference:.2f})")
        else:
            print(f"   ⚠️  WARN: Cost mismatch (difference: ${difference:.2f})")
            print(f"      Total: ${current_costs.amount:.2f}")
            print(f"      Services: ${service_total:.2f}")
        
        print(f"\n🕒 Test completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_cost_explorer())
    sys.exit(0 if success else 1)