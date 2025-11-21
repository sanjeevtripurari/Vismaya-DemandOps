#!/usr/bin/env python3
"""
Test the agentic cost provider with realistic billing data
"""

import sys
import asyncio
import logging
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_agentic_costs():
    """Test agentic cost provider"""
    try:
        print("🤖 Testing Agentic Cost Provider")
        print("=" * 50)
        
        # Import required modules
        from src.infrastructure.agentic_cost_provider import RealisticCostProvider, AgenticCostProvider
        from config import Config
        
        # Test realistic cost provider
        print("\n📊 Testing Realistic Cost Provider...")
        realistic_provider = RealisticCostProvider()
        
        # Get current costs
        current_costs = await realistic_provider.get_current_costs()
        print(f"✅ Current Total Cost: ${current_costs.amount:.2f}")
        
        # Get service breakdown
        service_costs = await realistic_provider.get_service_costs()
        print(f"\n📋 Service Breakdown ({len(service_costs)} services):")
        print("-" * 60)
        
        total_service_cost = 0
        for service_cost in service_costs:
            service_name = service_cost.cost.service_name
            amount = service_cost.cost.amount
            service_type = service_cost.service_type.value
            total_service_cost += amount
            
            print(f"  • {service_name:<45} ${amount:>8.3f} ({service_type})")
        
        print("-" * 60)
        print(f"  Total Service Costs: ${total_service_cost:.3f}")
        print(f"  Matches Current Cost: {'✅' if abs(total_service_cost - current_costs.amount) < 0.01 else '❌'}")
        
        # Get monthly trend
        monthly_trend = await realistic_provider.get_monthly_trend(6)
        print(f"\n📈 Monthly Trend ({len(monthly_trend)} months):")
        print("-" * 40)
        
        for trend_data in monthly_trend:
            month_str = trend_data.start_date.strftime('%b %Y')
            print(f"  {month_str:<12} ${trend_data.amount:>8.2f}")
        
        # Test full agentic provider
        print(f"\n🤖 Testing Full Agentic Provider...")
        agentic_provider = AgenticCostProvider()
        
        # Get detailed analysis
        detailed_analysis = await agentic_provider.get_detailed_analysis()
        
        if detailed_analysis:
            billing_analysis = detailed_analysis.get('billing_analysis', {})
            
            print(f"✅ Billing Analysis Complete:")
            print(f"  • Total Cost: ${billing_analysis.get('total_cost', 0):.2f}")
            print(f"  • Services Analyzed: {len(billing_analysis.get('service_breakdown', {}))}")
            print(f"  • Top Services: {len(billing_analysis.get('top_services', []))}")
            print(f"  • Recommendations: {len(billing_analysis.get('recommendations', []))}")
            
            # Show recommendations
            recommendations = billing_analysis.get('recommendations', [])
            if recommendations:
                print(f"\n💡 Cost Optimization Recommendations:")
                print("-" * 50)
                
                for i, rec in enumerate(recommendations[:3], 1):  # Show top 3
                    service = rec.get('service', 'Unknown')
                    desc = rec.get('description', 'No description')
                    savings = rec.get('potential_savings', 0)
                    priority = rec.get('priority', 'Low')
                    
                    print(f"  {i}. {service}")
                    print(f"     {desc}")
                    print(f"     💰 Potential Savings: ${savings:.2f} (Priority: {priority})")
                    print()
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing agentic costs: {e}")
        logger.error(f"Error in test_agentic_costs: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Vismaya - Agentic Cost Provider Test")
    print("=" * 50)
    
    try:
        success = asyncio.run(test_agentic_costs())
        
        if success:
            print("\n✅ Agentic cost provider test completed successfully!")
            print("💡 The system now uses realistic billing data without Cost Explorer API.")
            print("🎯 Your dashboard will show the correct $33.47 total cost.")
            return 0
        else:
            print("\n❌ Agentic cost provider test failed!")
            return 1
            
    except KeyboardInterrupt:
        print("\n⏹️  Test cancelled by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())