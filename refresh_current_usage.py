#!/usr/bin/env python3
"""
Force refresh current AWS usage data
This will fetch the latest data from AWS Cost Explorer and update the cache
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

async def refresh_current_usage():
    """Refresh current usage data from AWS Cost Explorer"""
    try:
        print("🔄 Refreshing AWS Cost Data from Cost Explorer...")
        print("=" * 50)
        
        # Import required modules
        from src.application.dependency_injection import DependencyContainer
        from src.infrastructure.sqlite_repository import SQLiteRepository
        from config import Config
        
        # Initialize container and repository
        container = DependencyContainer(Config)
        container.initialize()
        repository = SQLiteRepository()
        
        # Get the usage summary use case
        usage_summary_use_case = container.get_use_case('get_usage_summary')
        
        print("📡 Fetching fresh data from AWS Cost Explorer API...")
        
        # Fetch fresh usage summary
        fresh_summary = await usage_summary_use_case.execute()
        
        if fresh_summary:
            current_spend = fresh_summary.budget_info.current_spend
            print(f"✅ Successfully fetched current AWS costs: ${current_spend:.2f}")
            
            # Show service breakdown
            if fresh_summary.service_costs:
                print(f"\n📊 Service Breakdown ({len(fresh_summary.service_costs)} services):")
                print("-" * 50)
                
                # Sort services by cost (highest first)
                sorted_services = sorted(fresh_summary.service_costs, 
                                       key=lambda x: x.cost.amount, reverse=True)
                
                total_service_cost = 0
                for service_cost in sorted_services:
                    service_name = getattr(service_cost.cost, 'service_name', service_cost.service_type.value)
                    amount = service_cost.cost.amount
                    total_service_cost += amount
                    
                    if amount > 0:  # Only show services with actual costs
                        print(f"  • {service_name:<40} ${amount:>8.3f}")
                
                print("-" * 50)
                print(f"  Total Service Costs: ${total_service_cost:.3f}")
                print(f"  Cost Explorer Total: ${current_spend:.3f}")
                
                # Check for discrepancies
                if abs(total_service_cost - current_spend) > 0.01:
                    print(f"  ⚠️  Difference: ${abs(total_service_cost - current_spend):.3f}")
                else:
                    print("  ✅ Service costs match Cost Explorer total")
            
            # Store in cache
            print(f"\n💾 Storing fresh data in cache...")
            today = datetime.now()
            await repository.store_usage_summary(today, fresh_summary)
            
            print(f"✅ Cache updated successfully!")
            print(f"\n🎯 Summary:")
            print(f"  • Current AWS Spend: ${current_spend:.2f}")
            print(f"  • Budget Limit: ${fresh_summary.budget_info.warning_limit:.2f}")
            print(f"  • Budget Usage: {fresh_summary.budget_info.utilization_percentage:.1f}%")
            print(f"  • Data Timestamp: {fresh_summary.last_updated}")
            
            return True
            
        else:
            print("❌ Failed to fetch usage summary from AWS")
            return False
            
    except Exception as e:
        print(f"❌ Error refreshing usage data: {e}")
        logger.error(f"Error in refresh_current_usage: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Vismaya - AWS Usage Data Refresh Utility")
    print("=" * 50)
    
    try:
        success = asyncio.run(refresh_current_usage())
        
        if success:
            print("\n✅ AWS usage data refresh completed successfully!")
            print("💡 The dashboard will now show the latest AWS costs.")
            return 0
        else:
            print("\n❌ Failed to refresh AWS usage data!")
            print("💡 Check your AWS credentials and permissions.")
            return 1
            
    except KeyboardInterrupt:
        print("\n⏹️  Operation cancelled by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())