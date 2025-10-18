#!/usr/bin/env python3
"""
Test API Cost Tracking
"""

import asyncio
import sys
sys.path.append('.')

from src.services.api_cost_tracker import api_cost_tracker
from src.application.dependency_injection import DependencyContainer
from config import Config

async def test_cost_tracking():
    print("💰 Testing API Cost Tracking")
    print("=" * 50)
    
    # Reset tracker
    api_cost_tracker.reset_session()
    
    try:
        # Initialize container
        container = DependencyContainer(Config)
        container.initialize()
        
        print("✅ Application initialized")
        
        # Test Cost Explorer calls
        print("\n📊 Testing Cost Explorer API tracking...")
        usage_summary_use_case = container.get_use_case('get_usage_summary')
        usage_summary = await usage_summary_use_case.execute()
        
        print(f"✅ Retrieved usage summary: ${usage_summary.budget_info.current_spend:.2f}")
        
        # Test AI Assistant calls
        print("\n🤖 Testing Bedrock API tracking...")
        chat_use_case = container.get_use_case('handle_chat')
        response = await chat_use_case.execute("What is my current spending?")
        
        print(f"✅ AI Response: {response[:100]}...")
        
        # Get tracking summary
        print("\n💰 API Cost Tracking Summary:")
        summary = api_cost_tracker.get_session_summary()
        
        print(f"   Total Cost: ${summary['total_cost']:.6f}")
        print(f"   Total Calls: {summary['total_calls']}")
        print(f"   Session Duration: {summary['session_duration']:.1f} seconds")
        print(f"   Cost per Minute: ${summary['cost_per_minute']:.6f}")
        
        print("\n📋 Service Breakdown:")
        for service_name, service in summary['services'].items():
            print(f"   {service_name}:")
            print(f"     - Calls: {service.total_calls}")
            print(f"     - Cost: ${service.total_cost:.6f}")
            
            if service_name == 'Bedrock' and 'total_input_tokens' in service.details:
                print(f"     - Input Tokens: {service.details['total_input_tokens']:,}")
                print(f"     - Output Tokens: {service.details['total_output_tokens']:,}")
        
        # Monthly forecast
        print("\n📈 Monthly Cost Forecast:")
        forecast = api_cost_tracker.estimate_monthly_cost(1.0)
        print(f"   Estimated Monthly Cost: ${forecast['estimated_monthly_cost']:.4f}")
        print(f"   Estimated Daily Cost: ${forecast['estimated_daily_cost']:.6f}")
        
        print("\n✅ Cost tracking test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_cost_tracking())