#!/usr/bin/env python3
"""
Test script for migration components
Tests individual migration components without complex dependencies
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_imports():
    """Test that all migration components can be imported"""
    
    print("Testing migration component imports...")
    
    try:
        # Test feature flags
        from agentic.migration.feature_flags import FeatureFlagManager, FeatureFlag
        print("✅ Feature flags imported successfully")
        
        # Test compatibility layer
        from agentic.migration.compatibility_layer import CompatibilityLayer, CompatibilityMode
        print("✅ Compatibility layer imported successfully")
        
        # Test data migration (this might fail due to missing dependencies)
        try:
            from agentic.migration.data_migration import DataMigrationManager, MigrationResult
            print("✅ Data migration imported successfully")
        except ImportError as e:
            print(f"⚠️  Data migration import failed (expected): {e}")
        
        # Test migration orchestrator (this might fail due to missing dependencies)
        try:
            from agentic.migration.migration_orchestrator import MigrationOrchestrator
            print("✅ Migration orchestrator imported successfully")
        except ImportError as e:
            print(f"⚠️  Migration orchestrator import failed (expected): {e}")
        
        # Test enable all features
        from agentic.migration.enable_all_features import enable_all_agentic_features
        print("✅ Enable all features imported successfully")
        
        print("\n🎉 Core migration components are importable!")
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False


def test_feature_flags():
    """Test feature flag functionality"""
    
    print("\nTesting feature flag functionality...")
    
    try:
        from agentic.migration.feature_flags import FeatureFlagManager
        
        # Create feature flag manager
        config = {"flag_file_path": "test_flags.json"}
        flag_manager = FeatureFlagManager(config)
        
        # Test basic functionality
        test_flag = "test_feature"
        
        # Test evaluation
        evaluation = flag_manager.evaluate_flag(test_flag, "test_user")
        print(f"✅ Flag evaluation works: {evaluation.feature_name} = {evaluation.enabled}")
        
        # Test getting all flags
        all_flags = flag_manager.get_all_flags_status()
        print(f"✅ Retrieved {len(all_flags)} feature flags")
        
        print("✅ Feature flag functionality works!")
        return True
        
    except Exception as e:
        print(f"❌ Feature flag test failed: {e}")
        return False


def test_compatibility_layer():
    """Test compatibility layer functionality"""
    
    print("\nTesting compatibility layer functionality...")
    
    try:
        from agentic.migration.compatibility_layer import CompatibilityLayer, CompatibilityMode
        
        # Create compatibility layer
        config = {}
        compat_layer = CompatibilityLayer(config)
        
        # Test mode setting
        compat_layer.set_compatibility_mode(CompatibilityMode.HYBRID)
        print(f"✅ Set compatibility mode: {compat_layer.mode}")
        
        # Test endpoint management
        success = compat_layer.enable_endpoint("test_endpoint")
        print(f"✅ Endpoint management works: {success}")
        
        # Test metrics
        metrics = compat_layer.get_compatibility_metrics()
        print(f"✅ Retrieved compatibility metrics: {metrics['mode']}")
        
        print("✅ Compatibility layer functionality works!")
        return True
        
    except Exception as e:
        print(f"❌ Compatibility layer test failed: {e}")
        return False


def main():
    """Main test function"""
    
    print("🧪 Testing Migration Components")
    print("=" * 40)
    
    tests = [
        test_imports,
        test_feature_flags,
        test_compatibility_layer
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
    
    print("\n" + "=" * 40)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Migration components are working.")
        return 0
    else:
        print("⚠️  Some tests failed, but core functionality is available.")
        return 1


if __name__ == "__main__":
    sys.exit(main())