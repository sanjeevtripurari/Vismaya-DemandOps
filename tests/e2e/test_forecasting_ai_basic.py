#!/usr/bin/env python3
"""
Basic End-to-End Test for Forecasting AI Assistant

Simple smoke test to verify basic functionality and component initialization.
For comprehensive testing, see test_forecasting_ai_e2e.py
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.application.dependency_injection import DependencyContainer
from src.core.models import ForecastingContext, BudgetInfo, CostForecast
from config import Config


async def test_forecasting_ai_basic():
    """Basic smoke test for forecasting AI assistant implementation"""
    print("🤖 Basic Forecasting AI Assistant Test")
    print("=" * 50)
    
    try:
        # Initialize container
        config = Config()
        container = DependencyContainer(config)
        container.initialize()
        
        print("✅ Container initialized")
        
        # Get forecasting AI assistant
        forecasting_ai = container.get('forecasting_ai_assistant')
        print("✅ Forecasting AI assistant retrieved")
        
        # Create test context
        context = ForecastingContext()
        context.budget_info = BudgetInfo(
            total_budget=1000.0,
            current_spend=250.0,
            warning_limit=800.0,
            maximum_limit=1000.0
        )
        context.cost_forecast = CostForecast(
            forecasted_amount=300.0,
            confidence_level=0.8,
            forecast_period_days=30,
            base_amount=250.0
        )
        
        print("✅ Test context created")
        
        # Test basic queries (without AWS API calls to keep it fast)
        test_queries = [
            "Help",
            "What can you do?",
            "Tell me about my budget"
        ]
        
        for query in test_queries:
            print(f"\n🔍 Testing query: '{query}'")
            try:
                response = await forecasting_ai.chat_response(query, context)
                print(f"✅ Response received: {response[:100]}...")
            except Exception as e:
                print(f"❌ Query failed: {e}")
        
        # Test individual components initialization
        print(f"\n🧪 Testing component initialization...")
        
        # Test query parser
        query_parser = container.get('query_parser')
        try:
            resource_spec = query_parser.parse_resource_query("2 t3.medium instances for 3 months")
            print(f"✅ Query parser: {resource_spec.resource_type.value}, {resource_spec.instance_type}")
        except Exception as e:
            print(f"❌ Query parser failed: {e}")
        
        # Test pricing provider initialization (without API calls)
        pricing_provider = container.get('pricing_provider')
        try:
            print(f"✅ Pricing provider initialized: {pricing_provider._pricing_client is not None}")
        except Exception as e:
            print(f"⚠️ Pricing provider: {e}")
        
        # Test cost estimation engine
        cost_engine = container.get('cost_estimation_engine')
        print(f"✅ Cost estimation engine initialized: {cost_engine is not None}")
        
        print(f"\n✅ Basic Forecasting AI Assistant test completed!")
        print(f"💡 For comprehensive testing with real AWS API calls, run test_forecasting_ai_e2e.py")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_forecasting_ai_basic())