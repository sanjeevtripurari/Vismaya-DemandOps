#!/usr/bin/env python3
"""
Demo: Cost Explorer Flag Usage
Shows how to enable/disable Cost Explorer API calls
"""

import os
from config import Config

def demo_cost_explorer_flag():
    """Demonstrate Cost Explorer flag usage"""
    print("🎯 Cost Explorer Flag Demo")
    print("=" * 50)
    
    print("\n📋 Current Configuration:")
    print(f"   ENABLE_COST_EXPLORER: {Config.ENABLE_COST_EXPLORER}")
    
    if Config.ENABLE_COST_EXPLORER:
        print("   Status: ✅ Cost Explorer API calls are ENABLED")
        print("   - Real AWS cost data will be fetched")
        print("   - API calls will incur $0.01 each")
        print("   - Requires proper AWS permissions")
    else:
        print("   Status: 🚫 Cost Explorer API calls are DISABLED")
        print("   - No API calls will be made")
        print("   - No API costs will be incurred")
        print("   - Mock/cached data will be used")
    
    print("\n🔧 How to Change the Setting:")
    print("   1. Edit your .env file:")
    print("      ENABLE_COST_EXPLORER=false  # Disable API calls")
    print("      ENABLE_COST_EXPLORER=true   # Enable API calls")
    print("   2. Restart your application")
    
    print("\n💡 Use Cases:")
    print("   🧪 Development/Testing:")
    print("      - Set ENABLE_COST_EXPLORER=false")
    print("      - Avoid API costs during development")
    print("      - Use mock data for UI testing")
    
    print("   🚀 Production:")
    print("      - Set ENABLE_COST_EXPLORER=true")
    print("      - Get real-time cost data")
    print("      - Monitor actual AWS spending")
    
    print("   💰 Cost Control:")
    print("      - Disable during high-frequency testing")
    print("      - Enable only when cost data is needed")
    print("      - Use cached data between API calls")
    
    print("\n⚠️  Important Notes:")
    print("   - Each Cost Explorer API call costs $0.01")
    print("   - The flag affects ALL Cost Explorer calls")
    print("   - Other AWS services (EC2, Bedrock) are not affected")
    print("   - Applications gracefully handle disabled state")
    
    print("\n🔍 What Gets Disabled:")
    print("   - get_current_costs() → Returns $0.00")
    print("   - get_service_costs() → Returns empty list")
    print("   - get_monthly_trend() → Returns empty list")
    print("   - All Cost Explorer API calls in:")
    print("     • src/infrastructure/aws_cost_provider.py")
    print("     • cost-monitor.py")
    print("     • aws_client.py")
    
    print("\n✅ Safe Fallbacks:")
    print("   - Applications continue to work normally")
    print("   - UI shows appropriate messages")
    print("   - No crashes or errors")
    print("   - Mock data available for testing")

if __name__ == "__main__":
    demo_cost_explorer_flag()