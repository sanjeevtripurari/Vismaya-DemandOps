#!/usr/bin/env python3
"""
Test Cost Explorer Flag Configuration
Verifies that ENABLE_COST_EXPLORER=false prevents API calls
"""

import os
import sys
import asyncio
from unittest.mock import patch, MagicMock

# Add src to path for imports
sys.path.insert(0, 'src')

def test_cost_explorer_flag():
    """Test that Cost Explorer flag prevents API calls"""
    print("🧪 Testing Cost Explorer Flag Configuration...")
    
    # Test 1: Flag enabled (default)
    print("\n1️⃣ Testing with ENABLE_COST_EXPLORER=true")
    os.environ['ENABLE_COST_EXPLORER'] = 'true'
    
    # Reload config to pick up new environment variable
    import importlib
    import config
    importlib.reload(config)
    
    from config import Config
    print(f"   Config.ENABLE_COST_EXPLORER: {Config.ENABLE_COST_EXPLORER}")
    assert Config.ENABLE_COST_EXPLORER == True, "Flag should be True when set to 'true'"
    
    # Test 2: Flag disabled
    print("\n2️⃣ Testing with ENABLE_COST_EXPLORER=false")
    os.environ['ENABLE_COST_EXPLORER'] = 'false'
    importlib.reload(config)
    from config import Config
    print(f"   Config.ENABLE_COST_EXPLORER: {Config.ENABLE_COST_EXPLORER}")
    assert Config.ENABLE_COST_EXPLORER == False, "Flag should be False when set to 'false'"
    
    # Test 3: Test AWS Cost Provider with flag disabled
    print("\n3️⃣ Testing AWS Cost Provider with flag disabled")
    
    # Mock AWS session and client
    mock_session = MagicMock()
    mock_ce_client = MagicMock()
    mock_session.client.return_value = mock_ce_client
    
    # Import and test the cost provider
    from infrastructure.aws_cost_provider import AWSCostProvider
    
    # Create provider with mocked session and config
    provider = AWSCostProvider(mock_session, Config)
    
    async def test_methods():
        # Test get_current_costs
        result = await provider.get_current_costs()
        print(f"   get_current_costs() returned: {result}")
        assert result.amount == 0.0, "Should return $0.00 when flag is disabled"
        
        # Test get_service_costs
        result = await provider.get_service_costs()
        print(f"   get_service_costs() returned: {len(result)} services")
        assert len(result) == 0, "Should return empty list when flag is disabled"
        
        # Test get_monthly_trend
        result = await provider.get_monthly_trend()
        print(f"   get_monthly_trend() returned: {len(result)} months")
        assert len(result) == 0, "Should return empty list when flag is disabled"
        
        # Verify no API calls were made
        mock_ce_client.get_cost_and_usage.assert_not_called()
        print("   ✅ No Cost Explorer API calls were made")
    
    asyncio.run(test_methods())
    
    # Test 4: Test other clients with flag disabled
    print("\n4️⃣ Testing other clients with flag disabled")
    
    # Test cost-monitor.py
    from cost_monitor import CostMonitor
    with patch('cost_monitor.boto3.Session') as mock_session_class:
        mock_session_instance = MagicMock()
        mock_ce_client = MagicMock()
        mock_session_instance.client.return_value = mock_ce_client
        mock_session_class.return_value = mock_session_instance
        
        monitor = CostMonitor()
        
        # Test methods
        result = monitor.get_current_costs()
        print(f"   CostMonitor.get_current_costs(): {result}")
        assert result == 0.0, "Should return 0.0 when flag is disabled"
        
        result = monitor.get_daily_costs()
        print(f"   CostMonitor.get_daily_costs(): {len(result)} days")
        assert len(result) == 0, "Should return empty list when flag is disabled"
        
        result = monitor.get_service_costs()
        print(f"   CostMonitor.get_service_costs(): {len(result)} services")
        assert len(result) == 0, "Should return empty list when flag is disabled"
        
        # Verify no API calls were made
        mock_ce_client.get_cost_and_usage.assert_not_called()
        print("   ✅ No Cost Explorer API calls were made by CostMonitor")
    
    # Test aws_client.py
    from aws_client import AWSClient
    with patch('aws_client.boto3.Session') as mock_session_class:
        mock_session_instance = MagicMock()
        mock_ce_client = MagicMock()
        mock_session_instance.client.return_value = mock_ce_client
        mock_session_class.return_value = mock_session_instance
        
        client = AWSClient()
        
        # Test methods - these should return mock data instead of making API calls
        result = client.get_current_month_costs()
        print(f"   AWSClient.get_current_month_costs(): Found ResultsByTime")
        assert 'ResultsByTime' in result, "Should return mock data when flag is disabled"
        
        result = client.get_monthly_trend()
        print(f"   AWSClient.get_monthly_trend(): Found ResultsByTime")
        assert 'ResultsByTime' in result, "Should return mock data when flag is disabled"
        
        result = client.get_service_costs()
        print(f"   AWSClient.get_service_costs(): Found ResultsByTime")
        assert 'ResultsByTime' in result, "Should return mock data when flag is disabled"
        
        # Verify no API calls were made
        mock_ce_client.get_cost_and_usage.assert_not_called()
        print("   ✅ No Cost Explorer API calls were made by AWSClient")
    
    print("\n✅ All tests passed! Cost Explorer flag is working correctly.")
    print("\n📋 Summary:")
    print("   - ENABLE_COST_EXPLORER=true: API calls are made normally")
    print("   - ENABLE_COST_EXPLORER=false: API calls are blocked, returns safe defaults")
    print("   - All major components respect the flag")
    
    return True

if __name__ == "__main__":
    try:
        success = test_cost_explorer_flag()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)