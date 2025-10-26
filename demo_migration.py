#!/usr/bin/env python3
"""
Demo script for Agentic AI System Migration
Demonstrates the complete migration process from legacy to agentic architecture
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from agentic.migration import (
    MigrationOrchestrator,
    enable_all_agentic_features
)
from agentic.system_factory import AgenticSystemFactory
from agentic.strands.memory_store import DynamoDBMemoryStore


class MockLegacyService:
    """Mock legacy service for demonstration"""
    
    def __init__(self, name: str):
        self.name = name
    
    async def get_usage_summary(self, **kwargs):
        return {
            "success": True,
            "data": {
                "current_spend": 1500.0,
                "budget_limit": 2500.0,
                "utilization": 60.0
            }
        }
    
    def get_cost_insights(self, **kwargs):
        return {
            "success": True,
            "insights": ["EC2 costs are trending upward", "Consider reserved instances"]
        }


async def demo_migration():
    """Demonstrate the complete migration process"""
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    
    print("🚀 Starting Agentic AI System Migration Demo")
    print("=" * 50)
    
    try:
        # 1. Setup mock legacy services
        print("\n📋 Step 1: Setting up legacy services...")
        legacy_services = {
            "cost_service": MockLegacyService("cost_service"),
            "resource_service": MockLegacyService("resource_service"),
            "forecasting_service": MockLegacyService("forecasting_service"),
            "ai_assistant": MockLegacyService("ai_assistant"),
            "dashboard_service": MockLegacyService("dashboard_service")
        }
        print(f"✅ Initialized {len(legacy_services)} legacy services")
        
        # 2. Initialize agentic system (mock for demo)
        print("\n🤖 Step 2: Initializing agentic system...")
        config = {
            "aws_region": "us-east-1",
            "environment": "demo",
            "bedrock_model_id": "anthropic.claude-3-sonnet-20240229-v1:0"
        }
        
        class MockAgenticSystem:
            def __init__(self, config):
                self.config = config
                self.agents = {
                    "orchestrator": "MockOrchestratorAgent",
                    "cost_management": "MockCostManagementAgent",
                    "resource_management": "MockResourceManagementAgent",
                    "forecasting": "MockForecastingAgent",
                    "alert_management": "MockAlertManagementAgent",
                    "user_interface": "MockUserInterfaceAgent",
                    "approval": "MockApprovalAgent"
                }
            
            async def initialize_all_agents(self):
                return True
        
        agentic_system = MockAgenticSystem(config)
        await agentic_system.initialize_all_agents()
        print(f"✅ Initialized agentic system with {len(agentic_system.agents)} agents")
        
        # 3. Setup memory store (mock for demo)
        print("\n💾 Step 3: Setting up memory store...")
        
        class MockMemoryStore:
            def __init__(self, config):
                self.config = config
            
            async def initialize(self):
                return True
            
            async def update_context(self, agent_id, context):
                return True
            
            async def get_context(self, agent_id, keys):
                return {"test_key": "test_value"}
            
            async def store_decision_proposal(self, proposal):
                return True
        
        memory_store = MockMemoryStore(config)
        await memory_store.initialize()
        print("✅ Memory store initialized (mock)")
        
        # 4. Initialize migration orchestrator
        print("\n🎯 Step 4: Initializing migration orchestrator...")
        migration_config = {
            "migration_log_path": "logs/migration.log",
            "flag_file_path": "config/feature_flags.json",
            "agentic_rollout_percentage": 50
        }
        
        orchestrator = MigrationOrchestrator(migration_config)
        await orchestrator.initialize(legacy_services, agentic_system, memory_store)
        print("✅ Migration orchestrator initialized")
        
        # 5. Start migration process
        print("\n🔄 Step 5: Starting migration process...")
        print("This will execute all migration phases:")
        print("  - Preparation")
        print("  - Data Migration") 
        print("  - Feature Enablement")
        print("  - Compatibility Testing")
        print("  - Gradual Rollout")
        print("  - Finalization")
        
        migration_result = await orchestrator.start_migration()
        
        if migration_result["success"]:
            print(f"\n✅ Migration completed successfully!")
            print(f"   Duration: {migration_result['duration_seconds']:.2f} seconds")
            print(f"   Completed phases: {len(migration_result['completed_phases'])}")
            
            # Show completed phases
            print("\n📊 Completed phases:")
            for phase in migration_result["completed_phases"]:
                print(f"   ✅ {phase}")
                
        else:
            print(f"\n❌ Migration failed!")
            print(f"   Failed phase: {migration_result.get('failed_phase', 'Unknown')}")
            print(f"   Error: {migration_result.get('error', 'Unknown error')}")
            print(f"   Completed phases: {migration_result.get('completed_phases', [])}")
        
        # 6. Enable all features (as requested in task)
        print("\n🎛️  Step 6: Enabling all agentic features...")
        feature_result = await enable_all_agentic_features(migration_config)
        
        if feature_result["success"]:
            print(f"✅ All {feature_result['enabled_count']} agentic features enabled")
            print("\n🔧 Enabled features:")
            for feature in feature_result["enabled_features"]:
                print(f"   ✅ {feature}")
        else:
            print(f"❌ Failed to enable some features")
            print(f"   Enabled: {feature_result.get('enabled_count', 0)}")
            print(f"   Failed: {len(feature_result.get('failed_features', []))}")
        
        # 7. Show final migration status
        print("\n📈 Step 7: Final migration status...")
        final_status = orchestrator.get_migration_status()
        
        print(f"   Current phase: {final_status.get('current_phase', 'Completed')}")
        print(f"   Completed phases: {len(final_status.get('completed_phases', []))}")
        
        # Show compatibility metrics
        compatibility_metrics = final_status.get('compatibility_metrics', {})
        if compatibility_metrics:
            overall = compatibility_metrics.get('overall', {})
            print(f"   Total requests: {overall.get('total_requests', 0)}")
            print(f"   Agentic requests: {overall.get('agentic_requests', 0)}")
            print(f"   Success rate: {overall.get('success_rate', 0):.2%}")
        
        print("\n🎉 Migration demo completed!")
        print("=" * 50)
        
        return migration_result
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"\n❌ Demo failed: {e}")
        return {"success": False, "error": str(e)}


async def main():
    """Main function"""
    
    print("Agentic AI System Migration Demo")
    print("This demo shows the complete migration process")
    print("from legacy system to agentic architecture.\n")
    
    # Run the demo
    result = await demo_migration()
    
    # Exit with appropriate code
    sys.exit(0 if result.get("success", False) else 1)


if __name__ == "__main__":
    asyncio.run(main())