"""
Script to enable all agentic features for migration completion
Makes all changes visible as requested in task 11.1
"""

import asyncio
import logging
from typing import Dict, Any

from .feature_flags import FeatureFlagManager


async def enable_all_agentic_features(config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Enable all agentic features to make changes visible
    This completes the migration by activating all capabilities
    """
    
    if config is None:
        config = {"flag_file_path": "config/feature_flags.json"}
    
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize feature flag manager
        flag_manager = FeatureFlagManager(config)
        
        # Wait for initialization to complete
        await asyncio.sleep(0.1)
        
        # Enable all core agentic features at 100%
        core_features = [
            "agentic_cost_analysis",
            "agentic_resource_management", 
            "agentic_forecasting",
            "agentic_dashboard"
        ]
        
        # Enable governance features
        governance_features = [
            "approval_workflows",
            "real_time_decisions"
        ]
        
        # Enable AI features
        ai_features = [
            "enhanced_ai_assistant",
            "cost_optimization_recommendations",
            "predictive_alerts"
        ]
        
        # Enable advanced features
        advanced_features = [
            "multi_agent_collaboration"
        ]
        
        enabled_features = []
        failed_features = []
        
        # Enable all feature categories
        all_features = core_features + governance_features + ai_features + advanced_features
        
        for feature in all_features:
            try:
                success = await flag_manager.enable_flag(feature, 100.0)
                if success:
                    enabled_features.append(feature)
                    logger.info(f"Enabled feature: {feature}")
                else:
                    failed_features.append(feature)
                    logger.warning(f"Failed to enable feature: {feature}")
                    
            except Exception as e:
                failed_features.append(feature)
                logger.error(f"Error enabling feature {feature}: {e}")
        
        # Get final status
        final_status = flag_manager.get_all_flags_status()
        
        result = {
            "success": len(failed_features) == 0,
            "enabled_features": enabled_features,
            "failed_features": failed_features,
            "total_features": len(all_features),
            "enabled_count": len(enabled_features),
            "final_status": final_status
        }
        
        if result["success"]:
            logger.info(f"Successfully enabled all {len(enabled_features)} agentic features")
        else:
            logger.warning(f"Enabled {len(enabled_features)} features, {len(failed_features)} failed")
        
        return result
        
    except Exception as e:
        logger.error(f"Critical error enabling agentic features: {e}")
        return {
            "success": False,
            "error": str(e),
            "enabled_features": [],
            "failed_features": all_features if 'all_features' in locals() else []
        }


async def main():
    """Main function for standalone execution"""
    
    logging.basicConfig(level=logging.INFO)
    
    print("Enabling all agentic features...")
    result = await enable_all_agentic_features()
    
    if result["success"]:
        print(f"✅ Successfully enabled all {result['enabled_count']} agentic features")
        print("\nEnabled features:")
        for feature in result["enabled_features"]:
            print(f"  - {feature}")
    else:
        print(f"❌ Failed to enable some features")
        print(f"Enabled: {result['enabled_count']}")
        print(f"Failed: {len(result['failed_features'])}")
        
        if result["failed_features"]:
            print("\nFailed features:")
            for feature in result["failed_features"]:
                print(f"  - {feature}")


if __name__ == "__main__":
    asyncio.run(main())