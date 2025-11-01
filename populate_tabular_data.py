#!/usr/bin/env python3
"""
Populate Tabular Data
Collects real AWS data and populates the tabular database
Run this before viewing the dashboard to see actual data
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import asyncio
from src.services.enhanced_data_collector import EnhancedDataCollector
from src.services.tabular_data_service import TabularDataService
from src.application.dependency_injection import DependencyContainer
from config import Config

async def populate_real_data():
    """Populate database with real AWS data"""
    print("🚀 Populating Tabular Database with Real AWS Data")
    print("=" * 60)
    
    try:
        # Initialize services
        print("🔧 Initializing services...")
        container = DependencyContainer(Config)
        container.initialize()
        
        tabular_service = TabularDataService()
        aws_session = container._services.get('session_factory').create_session()
        data_collector = EnhancedDataCollector(aws_session, Config)
        
        print("✅ Services initialized successfully")
        
        # Collect real AWS data
        print("\n🔍 Collecting real AWS service data...")
        result = await data_collector.collect_and_store_current_usage()
        
        print(f"✅ Data collection successful!")
        print(f"📊 Total services collected: {result['total_resources']}")
        print(f"💰 Total monthly cost: ${result['total_cost']:.2f}")
        
        # Verify data is in database
        current_df = tabular_service.get_current_resources_table()
        print(f"\n📋 Services stored in database: {len(current_df)} rows")
        
        if len(current_df) > 0:
            print("\n✅ Real AWS services with costs:")
            print("-" * 80)
            for _, row in current_df.iterrows():
                service_name = row['Service/Resource']
                cost = row['Monthly Cost']
                category = row.get('Category', 'Unknown')
                billing_model = row.get('Billing Model', 'Unknown')
                print(f"   • {service_name:<30} {cost:>10} ({category}, {billing_model})")
            
            print(f"\n📊 Total services with costs: {len(current_df)}")
            monthly_costs = current_df['Monthly Cost'].str.replace('$', '').str.replace(',', '').astype(float)
            print(f"💰 Total monthly cost: ${monthly_costs.sum():.2f}")
        
        print("\n" + "=" * 60)
        print("🎯 DATABASE POPULATION COMPLETE")
        print("✅ Real AWS data stored in SQLite database")
        print("✅ Ready to view in Streamlit dashboard")
        print("\n💡 Next steps:")
        print("   1. Run: streamlit run dashboard.py")
        print("   2. Navigate to '📋 Tabular View' tab")
        print("   3. View your comprehensive AWS service data")
        
    except Exception as e:
        print(f"❌ Failed to populate data: {e}")
        print("\nThis could be due to:")
        print("   • AWS credentials not configured")
        print("   • Network connectivity issues") 
        print("   • AWS service permissions")
        print("\n💡 Please ensure your AWS credentials are properly configured")
        print("   and try running the script again.")

if __name__ == "__main__":
    asyncio.run(populate_real_data())