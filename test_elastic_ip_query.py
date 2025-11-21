#!/usr/bin/env python3
"""
Test Elastic IP Query
Tests the exact query: "need 2 ec2 instance large, with 20 gb and 1 elastic ip, and 3 postgres"
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import asyncio
from src.services.advanced_forecasting_assistant import AdvancedForecastingAssistant
from src.infrastructure.bedrock_ai_assistant import BedrockAIAssistant
from src.application.dependency_injection import DependencyContainer
from config import Config

async def test_elastic_ip_query():
    """Test the exact query with Elastic IP"""
    print("🚀 Testing Elastic IP Query")
    print("=" * 60)
    
    # Initialize services
    container = DependencyContainer(Config)
    container.initialize()
    
    aws_session = container._services.get('session_factory').create_session()
    bedrock_ai = container._services.get('ai_assistant')
    
    # Create advanced AI assistant
    advanced_ai = AdvancedForecastingAssistant(bedrock_ai._bedrock_client, aws_session, Config)
    
    # Test the exact query
    query = "need 2 ec2 instance large, with 20 gb and 1 elastic ip, and 3 postgres"
    current_usage = {'current_spend': 33.62}
    
    print(f"🔍 Testing Query: '{query}'")
    print()
    
    try:
        # Analyze the query
        result = await advanced_ai.analyze_complex_query(query, current_usage)
        
        print("✅ Analysis Complete!")
        print("=" * 60)
        
        # Show AI response
        ai_response = result.get('ai_response', '')
        if ai_response:
            print("🤖 AI Response:")
            print("-" * 40)
            print(ai_response[:500] + "..." if len(ai_response) > 500 else ai_response)
            print()
        
        # Show cost analysis
        cost_analysis = result.get('cost_analysis', {})
        resource_costs = cost_analysis.get('resource_costs', [])
        
        print("💰 Detailed Cost Breakdown:")
        print("-" * 60)
        
        if resource_costs:
            total_monthly = 0
            total_cost = 0
            
            for i, resource in enumerate(resource_costs, 1):
                print(f"{i}. {resource.get('type', 'Unknown')} {resource.get('instance_type', '')}")
                print(f"   Quantity: {resource.get('quantity', 0)}")
                print(f"   Duration: {resource.get('duration_months', 0)} months")
                print(f"   Storage: {resource.get('storage_gb', 0)} GB")
                print(f"   Hourly Rate: ${resource.get('hourly_rate', 0):.4f}")
                print(f"   Monthly Cost: ${resource.get('monthly_total_cost', 0):.2f}")
                print(f"   Total Cost: ${resource.get('total_cost', 0):.2f}")
                print()
                
                total_monthly += resource.get('monthly_total_cost', 0)
                total_cost += resource.get('total_cost', 0)
            
            print("📊 Summary:")
            print(f"   Total Monthly Cost: ${total_monthly:.2f}")
            print(f"   Total Project Cost: ${total_cost:.2f}")
            print(f"   Resources: {len(resource_costs)}")
            
            # Check if Elastic IP is included
            elastic_ip_found = any(r.get('type') == 'Elastic IP' for r in resource_costs)
            if elastic_ip_found:
                print("✅ Elastic IP detected and costed!")
            else:
                print("❌ Elastic IP NOT detected!")
        else:
            print("❌ No resource costs calculated")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 Test Complete")

if __name__ == "__main__":
    asyncio.run(test_elastic_ip_query())