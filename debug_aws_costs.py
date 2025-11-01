#!/usr/bin/env python3
"""
Debug AWS costs to understand why Cost Explorer returns $0
"""

import sys
import asyncio
import logging
from pathlib import Path
from datetime import datetime, timedelta
import boto3

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def debug_aws_costs():
    """Debug AWS costs with different date ranges"""
    try:
        print("🔍 AWS Cost Explorer Debug Utility")
        print("=" * 50)
        
        # Import required modules
        from config import Config
        from src.infrastructure.aws_session_factory import AWSSessionFactory
        
        # Create AWS session
        session_factory = AWSSessionFactory(Config)
        session = session_factory.create_session()
        
        # Get account info
        sts = session.client('sts')
        identity = sts.get_caller_identity()
        
        print(f"🔐 AWS Account: {identity['Account']}")
        print(f"🌍 Region: {session.region_name}")
        print(f"👤 User ARN: {identity['Arn']}")
        
        # Initialize Cost Explorer
        ce = session.client('ce')
        
        # Test different date ranges
        now = datetime.now()
        
        date_ranges = [
            {
                'name': 'Current Month (Oct 2025)',
                'start': '2025-10-01',
                'end': '2025-11-01'
            },
            {
                'name': 'Last 30 Days',
                'start': (now - timedelta(days=30)).strftime('%Y-%m-%d'),
                'end': now.strftime('%Y-%m-%d')
            },
            {
                'name': 'Last 7 Days',
                'start': (now - timedelta(days=7)).strftime('%Y-%m-%d'),
                'end': now.strftime('%Y-%m-%d')
            },
            {
                'name': 'Yesterday',
                'start': (now - timedelta(days=1)).strftime('%Y-%m-%d'),
                'end': now.strftime('%Y-%m-%d')
            },
            {
                'name': 'September 2025',
                'start': '2025-09-01',
                'end': '2025-10-01'
            }
        ]
        
        for date_range in date_ranges:
            print(f"\n📅 Testing: {date_range['name']}")
            print(f"   Range: {date_range['start']} to {date_range['end']}")
            
            try:
                # Get total costs
                response = ce.get_cost_and_usage(
                    TimePeriod={
                        'Start': date_range['start'],
                        'End': date_range['end']
                    },
                    Granularity='MONTHLY',
                    Metrics=['BlendedCost']
                )
                
                if response['ResultsByTime']:
                    total_cost = float(response['ResultsByTime'][0]['Total']['BlendedCost']['Amount'])
                    print(f"   💰 Total Cost: ${total_cost:.3f}")
                    
                    if total_cost > 0:
                        # Get service breakdown for this period
                        service_response = ce.get_cost_and_usage(
                            TimePeriod={
                                'Start': date_range['start'],
                                'End': date_range['end']
                            },
                            Granularity='MONTHLY',
                            Metrics=['BlendedCost'],
                            GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
                        )
                        
                        if service_response['ResultsByTime'] and service_response['ResultsByTime'][0].get('Groups'):
                            print(f"   📊 Top Services:")
                            groups = service_response['ResultsByTime'][0]['Groups']
                            # Sort by cost
                            sorted_groups = sorted(groups, key=lambda x: float(x['Metrics']['BlendedCost']['Amount']), reverse=True)
                            
                            for i, group in enumerate(sorted_groups[:5]):  # Top 5
                                service_name = group['Keys'][0]
                                cost = float(group['Metrics']['BlendedCost']['Amount'])
                                if cost > 0:
                                    print(f"      {i+1}. {service_name:<40} ${cost:>8.3f}")
                else:
                    print(f"   💰 Total Cost: $0.000 (No data)")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        # Check billing period
        print(f"\n📊 Checking Billing Preferences...")
        try:
            # Try to get billing info (might need different permissions)
            billing = session.client('ce')  # Cost Explorer can show billing periods
            
            # Get dimension values to see what's available
            dimensions_response = ce.get_dimension_values(
                TimePeriod={
                    'Start': '2025-10-01',
                    'End': '2025-11-01'
                },
                Dimension='SERVICE'
            )
            
            print(f"   📋 Available Services in Oct 2025: {len(dimensions_response['DimensionValues'])}")
            for dim in dimensions_response['DimensionValues'][:10]:  # Show first 10
                print(f"      • {dim['Value']}")
            
        except Exception as e:
            print(f"   ⚠️  Could not get billing info: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in debug: {e}")
        return False

def main():
    """Main function"""
    try:
        success = asyncio.run(debug_aws_costs())
        
        if success:
            print("\n✅ Debug completed!")
            print("\n💡 If all costs show $0.00, this could mean:")
            print("   • You're looking at the wrong AWS account")
            print("   • The costs are in a different region")
            print("   • The billing data hasn't been processed yet")
            print("   • You need different IAM permissions")
            return 0
        else:
            print("\n❌ Debug failed!")
            return 1
            
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())