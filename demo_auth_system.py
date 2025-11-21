#!/usr/bin/env python3
"""
Demonstration of the role-based access control system
"""

import asyncio
import logging
from src.agentic.auth.dashboard_integration import demo_authentication_system

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

if __name__ == "__main__":
    print("🚀 Starting Vismaya DemandOps Authentication System Demo")
    print("=" * 60)
    
    try:
        asyncio.run(demo_authentication_system())
    except KeyboardInterrupt:
        print("\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"❌ Demo failed with error: {e}")
        logging.error(f"Demo error: {e}")
    
    print("\n🎉 Demo completed!")