#!/usr/bin/env python3
"""
Test the specific query: "need 3 ec2 large instance each with 20gb storage and 3 elastic ip estimate the cost"
"""

import sys
import asyncio
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def test_specific_query():
    """Test the specific query that's not working"""
    try:
        print("🔍 Testing Specific Query")
        print("=" * 50)
        
        # Import required modules
        from src.services.advanced_forecasting_assistant import AdvancedForecastingAssistant
        from src.infrastructure.aws_session_factory import AWSSessionFactory
        from src.infrastructure.bedrock_ai_assistant import BedrockAIAssistant
        from config import Config
        
        # Setup
        session_factory = AWSSessionFactory(Config)
        aws_session = session_factory.create_session()
        bedrock_ai = BedrockAIAssistant(aws_session, Config.BEDROCK_MODEL_ID)
        advanced_ai = AdvancedForecastingAssistant(bedrock_ai._bedrock_client, aws_session, Config)
        
        # Test the exact query
        query = "need 3 ec2 large instance each with 20gb storage and 3 elastic ip estimate the cost"
        
        print(f"Query: '{query}'")
        print()
        
        # Mock current usage
        current_usage = {'current_spend': 33.58}
        
        # Analyze the query
        print("🤖 Analyzing with advanced AI...")
        result = await advanced_ai.analyze_complex_query(query, current_usage)
        
        # Show results
        print("✅ Analysis Results:")
        print("=" * 50)
        
        # Parsed requirements
        parsed = result.get('parsed_requirements', {})
        print(f"📋 Parsed Requirements:")
        print(f"   Summary: {parsed.get('summary', 'N/A')}")
        
        resources = parsed.get('resources', [])
        print(f"   Resources Found: {len(resources)}")
        
        for i, resource in enumerate(resources, 1):
            print(f"   {i}. {resource.get('type', 'unknown').upper()}")
            print(f"      Instance Type: {resource.get('instance_type', 'N/A')}")
            print(f"      Quantity: {resource.get('quantity', 0)}")
            print(f"      Storage: {resource.get('storage_gb', 0)} GB")
            print(f"      Duration: {resource.get('duration_months', 1)} months")
        
        print()
        
        # Cost analysis
        cost_analysis = result.get('cost_analysis', {})
        print(f"💰 Cost Analysis:")
        print(f"   Monthly Cost: ${cost_analysis.get('total_monthly_cost', 0):.2f}")
        print(f"   Total Cost: ${cost_analysis.get('total_cost', 0):.2f}")
        
        resource_costs = cost_analysis.get('resource_costs', [])
        if resource_costs:
            print(f"   Detailed Breakdown:")
            for resource in resource_costs:
                print(f"   • {resource['type']} {resource['instance_type']}")
                print(f"     Quantity: {resource['quantity']}")
                print(f"     Monthly: ${resource['monthly_total_cost']:.2f}")
                print(f"     Total: ${resource['total_cost']:.2f}")
                print(f"     Compute: ${resource.get('monthly_compute_cost', 0):.2f}/month")
                print(f"     Storage: ${resource.get('monthly_storage_cost', 0):.2f}/month")
        
        print()
        
        # AI Response
        ai_response = result.get('ai_response', '')
        print(f"🤖 AI Response:")
        print("-" * 30)
        print(ai_response[:800] + "..." if len(ai_response) > 800 else ai_response)
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Testing Specific Query That Should Work")
    
    try:
        success = asyncio.run(test_specific_query())
        
        if success:
            print("\n✅ Query analysis completed!")
            print("💡 This should be the response shown in the dashboard.")
        else:
            print("\n❌ Query analysis failed!")
        
        return 0 if success else 1
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())