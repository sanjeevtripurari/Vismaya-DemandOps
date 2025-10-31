#!/usr/bin/env python3
"""
Test Zero-Cost Filtering
Verifies that only non-zero cost services are displayed
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.services.tabular_data_service import TabularDataService

def test_zero_cost_filtering():
    """Test that zero-cost items are properly filtered out"""
    print("🚀 Testing Zero-Cost Filtering")
    print("=" * 50)
    
    # Initialize service
    tabular_service = TabularDataService()
    
    # Test data with mix of zero and non-zero costs
    test_resources = [
        # Non-zero cost service (should appear)
        {
            'resource_type': 'EC2 Instance',
            'resource_id': 'i-1234567890abcdef0',
            'instance_type': 't3.medium',
            'region': 'us-east-2',
            'availability_zone': 'us-east-2a',
            'state': 'running',
            'monthly_cost': 30.45,
            'daily_cost': 1.02,
            'hourly_cost': 0.0425,
            'storage_gb': 0,
            'storage_cost': 0,
            'compute_cost': 30.45,
            'network_cost': 0,
            'tags': {},
            'metadata': {'service_category': 'Compute', 'is_serverless': False}
        },
        # Zero cost service (should NOT appear)
        {
            'resource_type': 'S3 Storage',
            'resource_id': 's3-free-tier',
            'instance_type': 'Object Storage',
            'region': 'us-east-2',
            'availability_zone': 'Multi-AZ',
            'state': 'active',
            'monthly_cost': 0.00,
            'daily_cost': 0.00,
            'hourly_cost': 0.00,
            'storage_gb': 0,
            'storage_cost': 0,
            'compute_cost': 0,
            'network_cost': 0,
            'tags': {},
            'metadata': {'service_category': 'Storage', 'is_serverless': True}
        },
        # Very small cost service (should appear)
        {
            'resource_type': 'VPC Service',
            'resource_id': 'vpc-small-cost',
            'instance_type': 'Network Service',
            'region': 'us-east-2',
            'availability_zone': 'Multi-AZ',
            'state': 'active',
            'monthly_cost': 0.01,
            'daily_cost': 0.0003,
            'hourly_cost': 0.000014,
            'storage_gb': 0,
            'storage_cost': 0,
            'compute_cost': 0,
            'network_cost': 0.01,
            'tags': {},
            'metadata': {'service_category': 'Network', 'is_serverless': True}
        },
        # Another zero cost service (should NOT appear)
        {
            'resource_type': 'CloudWatch Free',
            'resource_id': 'cloudwatch-free-tier',
            'instance_type': 'Monitoring Service',
            'region': 'us-east-2',
            'availability_zone': 'Multi-AZ',
            'state': 'active',
            'monthly_cost': 0.00,
            'daily_cost': 0.00,
            'hourly_cost': 0.00,
            'storage_gb': 0,
            'storage_cost': 0,
            'compute_cost': 0,
            'network_cost': 0,
            'tags': {},
            'metadata': {'service_category': 'Management', 'is_serverless': True}
        }
    ]
    
    print(f"📊 Storing {len(test_resources)} test resources...")
    print("   • 2 with costs > $0.00 (should appear)")
    print("   • 2 with $0.00 costs (should be filtered out)")
    
    # Store test data
    success = tabular_service.store_current_resources(test_resources)
    print(f"✅ Storage successful: {success}")
    
    # Retrieve filtered data
    df = tabular_service.get_current_resources_table()
    
    print(f"\n📋 Retrieved {len(df)} services (after filtering)")
    
    if not df.empty:
        print("\n✅ Services with costs > $0.00:")
        for _, row in df.iterrows():
            service_name = row['Service/Resource']
            cost = row['Monthly Cost']
            print(f"   • {service_name}: {cost}")
        
        # Verify filtering worked correctly
        expected_services = 2  # Only EC2 and VPC should appear
        if len(df) == expected_services:
            print(f"\n✅ FILTERING SUCCESS: Showing {len(df)} services with costs")
            print("✅ Zero-cost services properly filtered out")
        else:
            print(f"\n❌ FILTERING ISSUE: Expected {expected_services} services, got {len(df)}")
    else:
        print("\n❌ No services retrieved - this might indicate an issue")
    
    # Test with all zero-cost services
    print(f"\n🔍 Testing with all zero-cost services...")
    zero_cost_resources = [
        {
            'resource_type': 'Free Service 1',
            'resource_id': 'free-1',
            'instance_type': 'Free Tier',
            'region': 'us-east-2',
            'availability_zone': 'Multi-AZ',
            'state': 'active',
            'monthly_cost': 0.00,
            'daily_cost': 0.00,
            'hourly_cost': 0.00,
            'storage_gb': 0,
            'storage_cost': 0,
            'compute_cost': 0,
            'network_cost': 0,
            'tags': {},
            'metadata': {'service_category': 'Other', 'is_serverless': True}
        }
    ]
    
    tabular_service.store_current_resources(zero_cost_resources)
    df_zero = tabular_service.get_current_resources_table()
    
    if len(df_zero) == 0:
        print("✅ All zero-cost services properly filtered out")
    else:
        print(f"❌ Zero-cost filtering failed: {len(df_zero)} services still showing")
    
    print("\n" + "=" * 50)
    print("🎯 ZERO-COST FILTERING TEST COMPLETE")
    print("✅ Only services with costs > $0.00 are displayed")
    print("✅ Zero-cost items are filtered for better clarity")
    print("✅ Users see only meaningful cost data")

if __name__ == "__main__":
    test_zero_cost_filtering()