#!/usr/bin/env python3
"""
Test the real AWS usage analyzer
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

async def test_real_usage():
    """Test real usage analyzer"""
    try:
        print("🔍 Testing Real AWS Usage Analyzer")
        print("=" * 50)
        
        # Import required modules
        from src.infrastructure.real_usage_analyzer import RealUsageAnalyzer
        from src.infrastructure.aws_session_factory import AWSSessionFactory
        from config import Config
        
        # Create AWS session
        session_factory = AWSSessionFactory(Config)
        aws_session = session_factory.create_session()
        
        # Get account info
        sts = aws_session.client('sts')
        identity = sts.get_caller_identity()
        
        print(f"🔐 AWS Account: {identity['Account']}")
        print(f"🌍 Region: {aws_session.region_name}")
        print(f"👤 User ARN: {identity['Arn']}")
        
        # Test real usage analyzer
        print(f"\n🔍 Analyzing Real AWS Usage...")
        usage_analyzer = RealUsageAnalyzer(aws_session, Config)
        
        # Get current costs from real usage
        current_costs = await usage_analyzer.get_current_costs()
        print(f"✅ Real Current Cost: ${current_costs.amount:.2f}")
        print(f"   Source: {current_costs.service_name}")
        
        # Get service breakdown from real usage
        service_costs = await usage_analyzer.get_service_costs()
        print(f"\n📋 Real Service Breakdown ({len(service_costs)} services):")
        print("-" * 70)
        
        total_service_cost = 0
        for service_cost in service_costs:
            service_name = service_cost.cost.service_name
            amount = service_cost.cost.amount
            service_type = service_cost.service_type.value
            usage_qty = service_cost.cost.usage_quantity
            total_service_cost += amount
            
            print(f"  • {service_name:<45} ${amount:>8.3f} ({usage_qty} units)")
        
        print("-" * 70)
        print(f"  Total Service Costs: ${total_service_cost:.3f}")
        print(f"  Matches Current Cost: {'✅' if abs(total_service_cost - current_costs.amount) < 0.01 else '❌'}")
        
        # Get monthly trend from real usage
        monthly_trend = await usage_analyzer.get_monthly_trend(6)
        print(f"\n📈 Real Usage Trend ({len(monthly_trend)} months):")
        print("-" * 40)
        
        for trend_data in monthly_trend:
            month_str = trend_data.start_date.strftime('%b %Y')
            print(f"  {month_str:<12} ${trend_data.amount:>8.2f}")
        
        # Test internal usage analysis
        print(f"\n🔍 Detailed Real Usage Analysis...")
        real_usage = await usage_analyzer._get_real_aws_usage()
        
        if real_usage:
            print(f"✅ Found real usage data for {len(real_usage)} services:")
            for service_name, usage_data in real_usage.items():
                estimated_cost = usage_data.get('estimated_cost', 0)
                usage_quantity = usage_data.get('usage_quantity', 0)
                print(f"  • {service_name}: ${estimated_cost:.3f} ({usage_quantity} units)")
        else:
            print("⚠️  No real usage data found - using fallback billing data")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing real usage: {e}")
        logger.error(f"Error in test_real_usage: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Vismaya - Real AWS Usage Analyzer Test")
    print("=" * 50)
    
    try:
        success = asyncio.run(test_real_usage())
        
        if success:
            print("\n✅ Real usage analyzer test completed successfully!")
            print("💡 The system now analyzes your actual AWS resources.")
            print("🎯 Your dashboard will show real usage data, not demo data.")
            return 0
        else:
            print("\n❌ Real usage analyzer test failed!")
            return 1
            
    except KeyboardInterrupt:
        print("\n⏹️  Test cancelled by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())