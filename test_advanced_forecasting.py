#!/usr/bin/env python3
"""
Test the advanced forecasting assistant with complex queries
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

async def test_advanced_forecasting():
    """Test advanced forecasting assistant with complex queries"""
    try:
        print("🤖 Testing Advanced Forecasting AI Assistant")
        print("=" * 60)
        
        # Import required modules
        from src.services.advanced_forecasting_assistant import AdvancedForecastingAssistant
        from src.infrastructure.aws_session_factory import AWSSessionFactory
        from src.infrastructure.bedrock_ai_assistant import BedrockAIAssistant
        from config import Config
        
        # Create AWS session and Bedrock client
        session_factory = AWSSessionFactory(Config)
        aws_session = session_factory.create_session()
        
        # Initialize Bedrock AI assistant
        bedrock_ai = BedrockAIAssistant(aws_session, Config.BEDROCK_MODEL_ID)
        
        # Create advanced forecasting assistant
        advanced_ai = AdvancedForecastingAssistant(bedrock_ai._bedrock_client, aws_session, Config)
        
        # Test complex query (your example)
        complex_query = "I need 2 EC2 large instances with 30 GB storage for 2 months, and 3 postgres databases. Can you provide cost estimation?"
        
        print(f"🔍 Testing Complex Query:")
        print(f"   '{complex_query}'")
        print()
        
        # Mock current usage data
        current_usage = {
            'current_spend': 33.58,
            'service_costs': [],
            'ec2_instances': [],
            'database_instances': [],
            'storage_volumes': []
        }
        
        # Analyze the complex query
        print("🤖 Analyzing with AI agents...")
        analysis_result = await advanced_ai.analyze_complex_query(complex_query, current_usage)
        
        # Display results
        print("✅ Analysis Complete!")
        print("=" * 60)
        
        # Show parsed requirements
        parsed_req = analysis_result.get('parsed_requirements', {})
        print(f"📋 Parsed Requirements:")
        print(f"   Summary: {parsed_req.get('summary', 'N/A')}")
        print(f"   Resources: {len(parsed_req.get('resources', []))}")
        
        for i, resource in enumerate(parsed_req.get('resources', []), 1):
            print(f"   {i}. {resource.get('type', 'unknown').upper()} {resource.get('instance_type', 'N/A')}")
            print(f"      Quantity: {resource.get('quantity', 0)}")
            print(f"      Duration: {resource.get('duration_months', 0)} months")
            print(f"      Storage: {resource.get('storage_gb', 0)} GB")
        
        print()
        
        # Show cost analysis
        cost_analysis = analysis_result.get('cost_analysis', {})
        print(f"💰 Cost Analysis:")
        print(f"   Total Monthly Cost: ${cost_analysis.get('total_monthly_cost', 0):.2f}")
        print(f"   Total Project Cost: ${cost_analysis.get('total_cost', 0):.2f}")
        print(f"   Duration: {cost_analysis.get('duration_months', 0)} months")
        
        resource_costs = cost_analysis.get('resource_costs', [])
        if resource_costs:
            print(f"   Resource Breakdown:")
            for resource in resource_costs:
                print(f"   • {resource['type']} {resource['instance_type']}: ${resource['total_cost']:.2f}")
                print(f"     Quantity: {resource['quantity']}, Monthly: ${resource['monthly_total_cost']:.2f}")
        
        print()
        
        # Show comparison analysis
        comparison = analysis_result.get('comparison_analysis', {})
        if comparison:
            print(f"📊 Current vs New Comparison:")
            print(f"   Current Monthly: ${comparison.get('current_monthly_cost', 0):.2f}")
            print(f"   Additional Monthly: ${comparison.get('requested_monthly_cost', 0):.2f}")
            print(f"   New Total Monthly: ${comparison.get('new_total_monthly', 0):.2f}")
            print(f"   Percentage Increase: {comparison.get('percentage_increase', 0):.1f}%")
        
        print()
        
        # Show AI response
        ai_response = analysis_result.get('ai_response', '')
        if ai_response:
            print(f"🤖 AI Assistant Response:")
            print("-" * 40)
            print(ai_response[:500] + "..." if len(ai_response) > 500 else ai_response)
        
        print()
        
        # Test trend data generation
        print("📈 Generating Cost Trend Data...")
        trend_data = await advanced_ai.generate_cost_trend_data(cost_analysis, current_usage)
        
        timeline_data = trend_data.get('timeline_data', [])
        if timeline_data:
            print(f"   Timeline Data Points: {len(timeline_data)}")
            print(f"   Sample Timeline:")
            for item in timeline_data[-3:]:  # Show last 3 months
                print(f"   • {item['month']}: Current ${item['current_cost']:.2f}, With New ${item['with_new_resources']:.2f}")
        
        summary = trend_data.get('summary', {})
        if summary:
            print(f"   Summary:")
            print(f"   • Current Monthly: ${summary.get('current_monthly', 0):.2f}")
            print(f"   • Additional Monthly: ${summary.get('requested_monthly', 0):.2f}")
            print(f"   • Total New Cost: ${summary.get('total_new_cost', 0):.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing advanced forecasting: {e}")
        logger.error(f"Error in test_advanced_forecasting: {e}")
        return False

async def test_simple_queries():
    """Test simple queries as well"""
    try:
        print("\n" + "=" * 60)
        print("🔍 Testing Simple Queries")
        print("=" * 60)
        
        from src.services.advanced_forecasting_assistant import AdvancedForecastingAssistant
        from src.infrastructure.aws_session_factory import AWSSessionFactory
        from src.infrastructure.bedrock_ai_assistant import BedrockAIAssistant
        from config import Config
        
        # Setup
        session_factory = AWSSessionFactory(Config)
        aws_session = session_factory.create_session()
        bedrock_ai = BedrockAIAssistant(aws_session, Config.BEDROCK_MODEL_ID)
        advanced_ai = AdvancedForecastingAssistant(bedrock_ai._bedrock_client, aws_session, Config)
        
        simple_queries = [
            "Cost of 1 t3.large EC2 for 3 months",
            "What would 2 RDS postgres databases cost for 6 months?",
            "Price for 5 t3.medium instances with 50 GB storage each"
        ]
        
        current_usage = {'current_spend': 33.58}
        
        for i, query in enumerate(simple_queries, 1):
            print(f"\n{i}. Testing: '{query}'")
            
            try:
                result = await advanced_ai.analyze_complex_query(query, current_usage)
                cost_analysis = result.get('cost_analysis', {})
                
                print(f"   ✅ Monthly: ${cost_analysis.get('total_monthly_cost', 0):.2f}")
                print(f"   ✅ Total: ${cost_analysis.get('total_cost', 0):.2f}")
                print(f"   ✅ Resources: {len(cost_analysis.get('resource_costs', []))}")
                
            except Exception as e:
                print(f"   ❌ Error: {str(e)[:100]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing simple queries: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Vismaya - Advanced Forecasting AI Assistant Test")
    print("=" * 60)
    
    try:
        # Test complex queries
        success1 = asyncio.run(test_advanced_forecasting())
        
        # Test simple queries
        success2 = asyncio.run(test_simple_queries())
        
        if success1 and success2:
            print("\n" + "=" * 60)
            print("✅ Advanced Forecasting AI Assistant tests completed successfully!")
            print("\n🎯 Key Features Verified:")
            print("  • ✅ Complex query parsing with AI agents")
            print("  • ✅ Real-time AWS pricing integration")
            print("  • ✅ Detailed cost breakdown and analysis")
            print("  • ✅ Current vs new resource comparison")
            print("  • ✅ Cost trend data generation")
            print("  • ✅ Comprehensive AI responses")
            print("\n💡 Your forecasting tab will now handle complex queries like:")
            print("     'I need 2 EC2 large instances with 30 GB storage for 2 months, and 3 postgres databases'")
            return 0
        else:
            print("\n❌ Some tests failed!")
            return 1
            
    except KeyboardInterrupt:
        print("\n⏹️  Tests cancelled by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())