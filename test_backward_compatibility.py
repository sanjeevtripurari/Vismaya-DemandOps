#!/usr/bin/env python3
"""
Backward Compatibility Validation Script
Tests that existing functionality continues to work with the agentic system
"""

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.application.dependency_injection import DependencyContainer
from src.agentic.migration.compatibility_layer import CompatibilityLayer, CompatibilityMode
from src.agentic.migration.feature_flags import FeatureFlagManager
from config import Config

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class BackwardCompatibilityValidator:
    """Validates backward compatibility of existing functionality"""
    
    def __init__(self):
        self.results = {
            "overall_status": "passed",
            "test_results": {},
            "timestamp": datetime.now().isoformat(),
            "errors": []
        }
    
    async def run_all_tests(self):
        """Run all backward compatibility tests"""
        logger.info("🧪 Starting backward compatibility validation...")
        
        try:
            # Test 1: Legacy system initialization
            await self._test_legacy_system_initialization()
            
            # Test 2: Dashboard functionality
            await self._test_dashboard_functionality()
            
            # Test 3: Cost analysis features
            await self._test_cost_analysis_features()
            
            # Test 4: Forecasting capabilities
            await self._test_forecasting_capabilities()
            
            # Test 5: Resource management
            await self._test_resource_management()
            
            # Test 6: AI assistant functionality
            await self._test_ai_assistant_functionality()
            
            # Test 7: Compatibility layer
            await self._test_compatibility_layer()
            
            # Test 8: Feature flags system
            await self._test_feature_flags_system()
            
        except Exception as e:
            logger.error(f"❌ Critical error during testing: {e}")
            self.results["overall_status"] = "failed"
            self.results["errors"].append(str(e))
        
        # Generate final report
        self._generate_report()
        
        return self.results
    
    async def _test_legacy_system_initialization(self):
        """Test that legacy system initializes correctly"""
        test_name = "legacy_system_initialization"
        logger.info(f"Testing: {test_name}")
        
        try:
            # Initialize dependency container (legacy system)
            container = DependencyContainer(Config)
            container.initialize()
            
            # Test health check
            health_status = await container.health_check()
            
            if health_status.get('overall_health', False):
                self.results["test_results"][test_name] = {
                    "status": "passed",
                    "details": "Legacy system initializes and passes health check"
                }
                logger.info(f"✅ {test_name}: PASSED")
            else:
                self.results["test_results"][test_name] = {
                    "status": "warning",
                    "details": "Legacy system initializes but health check shows warnings"
                }
                logger.warning(f"⚠️ {test_name}: WARNING - Health check issues")
            
        except Exception as e:
            self.results["test_results"][test_name] = {
                "status": "failed",
                "error": str(e)
            }
            self.results["overall_status"] = "failed"
            logger.error(f"❌ {test_name}: FAILED - {e}")
    
    async def _test_dashboard_functionality(self):
        """Test dashboard functionality preservation"""
        test_name = "dashboard_functionality"
        logger.info(f"Testing: {test_name}")
        
        try:
            container = DependencyContainer(Config)
            container.initialize()
            
            # Test usage summary endpoint
            usage_summary_use_case = container.get_use_case('get_usage_summary')
            usage_summary = await usage_summary_use_case.execute()
            
            # Validate usage summary structure
            required_fields = ['budget_info', 'service_costs', 'cost_forecast']
            missing_fields = [field for field in required_fields if not hasattr(usage_summary, field)]
            
            if not missing_fields:
                self.results["test_results"][test_name] = {
                    "status": "passed",
                    "details": "Dashboard data structure preserved"
                }
                logger.info(f"✅ {test_name}: PASSED")
            else:
                self.results["test_results"][test_name] = {
                    "status": "failed",
                    "details": f"Missing required fields: {missing_fields}"
                }
                self.results["overall_status"] = "failed"
                logger.error(f"❌ {test_name}: FAILED - Missing fields")
            
        except Exception as e:
            self.results["test_results"][test_name] = {
                "status": "failed",
                "error": str(e)
            }
            self.results["overall_status"] = "failed"
            logger.error(f"❌ {test_name}: FAILED - {e}")
    
    async def _test_cost_analysis_features(self):
        """Test cost analysis features preservation"""
        test_name = "cost_analysis_features"
        logger.info(f"Testing: {test_name}")
        
        try:
            container = DependencyContainer(Config)
            container.initialize()
            
            # Test cost service
            cost_service = container.get_service('cost_service')
            
            # Test cost insights
            cost_insights = await cost_service.get_cost_insights()
            
            if cost_insights and isinstance(cost_insights, str) and len(cost_insights) > 0:
                self.results["test_results"][test_name] = {
                    "status": "passed",
                    "details": "Cost analysis features working"
                }
                logger.info(f"✅ {test_name}: PASSED")
            else:
                self.results["test_results"][test_name] = {
                    "status": "failed",
                    "details": "Cost insights not generated properly"
                }
                self.results["overall_status"] = "failed"
                logger.error(f"❌ {test_name}: FAILED - No cost insights")
            
        except Exception as e:
            self.results["test_results"][test_name] = {
                "status": "failed",
                "error": str(e)
            }
            self.results["overall_status"] = "failed"
            logger.error(f"❌ {test_name}: FAILED - {e}")
    
    async def _test_forecasting_capabilities(self):
        """Test forecasting capabilities preservation"""
        test_name = "forecasting_capabilities"
        logger.info(f"Testing: {test_name}")
        
        try:
            container = DependencyContainer(Config)
            container.initialize()
            
            # Test forecasting AI assistant
            forecasting_assistant = container.get_service('forecasting_ai_assistant')
            
            # Test cost query processing
            from src.core.models import ForecastingContext, BudgetInfo
            
            context = ForecastingContext(
                budget_info=BudgetInfo(
                    total_budget=1000.0,
                    current_spend=500.0,
                    warning_limit=800.0,
                    maximum_limit=1000.0
                )
            )
            
            # Test a simple cost query
            response = await forecasting_assistant.process_cost_query(
                "What would a t3.micro instance cost for 1 month?", 
                context
            )
            
            if response and hasattr(response, 'total_cost') and response.total_cost > 0:
                self.results["test_results"][test_name] = {
                    "status": "passed",
                    "details": f"Forecasting working - estimated cost: ${response.total_cost:.2f}"
                }
                logger.info(f"✅ {test_name}: PASSED")
            else:
                self.results["test_results"][test_name] = {
                    "status": "failed",
                    "details": "Forecasting query did not return valid cost estimate"
                }
                self.results["overall_status"] = "failed"
                logger.error(f"❌ {test_name}: FAILED - Invalid response")
            
        except Exception as e:
            self.results["test_results"][test_name] = {
                "status": "failed",
                "error": str(e)
            }
            self.results["overall_status"] = "failed"
            logger.error(f"❌ {test_name}: FAILED - {e}")
    
    async def _test_resource_management(self):
        """Test resource management features preservation"""
        test_name = "resource_management"
        logger.info(f"Testing: {test_name}")
        
        try:
            container = DependencyContainer(Config)
            container.initialize()
            
            # Test resource service
            resource_service = container.get_service('resource_service')
            
            # Test resource inventory
            inventory = await resource_service.get_resource_inventory()
            
            # Validate inventory structure
            required_keys = ['ec2_instances', 'storage_volumes', 'database_instances']
            missing_keys = [key for key in required_keys if key not in inventory]
            
            if not missing_keys:
                self.results["test_results"][test_name] = {
                    "status": "passed",
                    "details": "Resource management features preserved"
                }
                logger.info(f"✅ {test_name}: PASSED")
            else:
                self.results["test_results"][test_name] = {
                    "status": "failed",
                    "details": f"Missing inventory keys: {missing_keys}"
                }
                self.results["overall_status"] = "failed"
                logger.error(f"❌ {test_name}: FAILED - Missing keys")
            
        except Exception as e:
            self.results["test_results"][test_name] = {
                "status": "failed",
                "error": str(e)
            }
            self.results["overall_status"] = "failed"
            logger.error(f"❌ {test_name}: FAILED - {e}")
    
    async def _test_ai_assistant_functionality(self):
        """Test AI assistant functionality preservation"""
        test_name = "ai_assistant_functionality"
        logger.info(f"Testing: {test_name}")
        
        try:
            container = DependencyContainer(Config)
            container.initialize()
            
            # Test AI assistant
            ai_assistant = container.get_service('ai_assistant')
            
            # Test chat response
            from src.core.models import UsageSummary, BudgetInfo, CostForecast
            
            usage_summary = UsageSummary(
                budget_info=BudgetInfo(
                    total_budget=1000.0,
                    current_spend=500.0,
                    warning_limit=800.0,
                    maximum_limit=1000.0
                ),
                service_costs=[],
                ec2_instances=[],
                storage_volumes=[],
                database_instances=[],
                cost_forecast=CostForecast(
                    forecasted_amount=550.0,
                    confidence_level=0.8,
                    forecast_period_days=30,
                    base_amount=500.0
                ),
                recommendations=[]
            )
            
            response = await ai_assistant.chat_response("What is my current spending?", usage_summary)
            
            if response and isinstance(response, str) and len(response) > 0:
                self.results["test_results"][test_name] = {
                    "status": "passed",
                    "details": "AI assistant functionality preserved"
                }
                logger.info(f"✅ {test_name}: PASSED")
            else:
                self.results["test_results"][test_name] = {
                    "status": "failed",
                    "details": "AI assistant not responding properly"
                }
                self.results["overall_status"] = "failed"
                logger.error(f"❌ {test_name}: FAILED - No response")
            
        except Exception as e:
            self.results["test_results"][test_name] = {
                "status": "failed",
                "error": str(e)
            }
            self.results["overall_status"] = "failed"
            logger.error(f"❌ {test_name}: FAILED - {e}")
    
    async def _test_compatibility_layer(self):
        """Test compatibility layer functionality"""
        test_name = "compatibility_layer"
        logger.info(f"Testing: {test_name}")
        
        try:
            # Initialize compatibility layer
            compatibility_config = {
                "agentic_rollout_percentage": 0  # Start with 0% rollout
            }
            
            compatibility_layer = CompatibilityLayer(compatibility_config)
            compatibility_layer.set_compatibility_mode(CompatibilityMode.LEGACY_ONLY)
            
            # Set up legacy services
            container = DependencyContainer(Config)
            container.initialize()
            
            legacy_services = {
                "cost_service": container.get_service('cost_service'),
                "resource_service": container.get_service('resource_service'),
                "forecasting_service": container.get_service('forecasting_service'),
                "ai_assistant": container.get_service('ai_assistant')
            }
            
            compatibility_layer.set_legacy_services(legacy_services)
            
            # Test routing to legacy system
            result = await compatibility_layer.route_request("get_usage_summary", {})
            
            if result and not result.get("error"):
                self.results["test_results"][test_name] = {
                    "status": "passed",
                    "details": "Compatibility layer routing works"
                }
                logger.info(f"✅ {test_name}: PASSED")
            else:
                self.results["test_results"][test_name] = {
                    "status": "failed",
                    "details": f"Compatibility layer routing failed: {result.get('error', 'Unknown error')}"
                }
                self.results["overall_status"] = "failed"
                logger.error(f"❌ {test_name}: FAILED - Routing error")
            
        except Exception as e:
            self.results["test_results"][test_name] = {
                "status": "failed",
                "error": str(e)
            }
            self.results["overall_status"] = "failed"
            logger.error(f"❌ {test_name}: FAILED - {e}")
    
    async def _test_feature_flags_system(self):
        """Test feature flags system"""
        test_name = "feature_flags_system"
        logger.info(f"Testing: {test_name}")
        
        try:
            # Initialize feature flags manager
            flag_config = {
                "flag_file_path": "test_feature_flags.json",
                "max_evaluations": 1000
            }
            
            flag_manager = FeatureFlagManager(flag_config)
            
            # Test flag evaluation
            is_enabled = flag_manager.is_enabled("agentic_cost_analysis", "test_user")
            
            # Test flag status
            status = flag_manager.get_flag_status("agentic_cost_analysis")
            
            if status and "name" in status:
                self.results["test_results"][test_name] = {
                    "status": "passed",
                    "details": f"Feature flags system working - agentic_cost_analysis: {is_enabled}"
                }
                logger.info(f"✅ {test_name}: PASSED")
            else:
                self.results["test_results"][test_name] = {
                    "status": "failed",
                    "details": "Feature flags system not working properly"
                }
                self.results["overall_status"] = "failed"
                logger.error(f"❌ {test_name}: FAILED - No flag status")
            
        except Exception as e:
            self.results["test_results"][test_name] = {
                "status": "failed",
                "error": str(e)
            }
            self.results["overall_status"] = "failed"
            logger.error(f"❌ {test_name}: FAILED - {e}")
    
    def _generate_report(self):
        """Generate final compatibility report"""
        logger.info("\n" + "="*60)
        logger.info("🧪 BACKWARD COMPATIBILITY VALIDATION REPORT")
        logger.info("="*60)
        
        passed_tests = sum(1 for result in self.results["test_results"].values() if result["status"] == "passed")
        warning_tests = sum(1 for result in self.results["test_results"].values() if result["status"] == "warning")
        failed_tests = sum(1 for result in self.results["test_results"].values() if result["status"] == "failed")
        total_tests = len(self.results["test_results"])
        
        logger.info(f"📊 Test Summary:")
        logger.info(f"   ✅ Passed: {passed_tests}/{total_tests}")
        logger.info(f"   ⚠️  Warnings: {warning_tests}/{total_tests}")
        logger.info(f"   ❌ Failed: {failed_tests}/{total_tests}")
        logger.info(f"   🎯 Overall Status: {self.results['overall_status'].upper()}")
        
        logger.info(f"\n📋 Detailed Results:")
        for test_name, result in self.results["test_results"].items():
            status_emoji = {"passed": "✅", "warning": "⚠️", "failed": "❌"}[result["status"]]
            logger.info(f"   {status_emoji} {test_name}: {result['status'].upper()}")
            if "details" in result:
                logger.info(f"      {result['details']}")
            if "error" in result:
                logger.info(f"      Error: {result['error']}")
        
        if self.results["errors"]:
            logger.info(f"\n🚨 Critical Errors:")
            for error in self.results["errors"]:
                logger.info(f"   • {error}")
        
        logger.info("\n" + "="*60)
        
        if self.results["overall_status"] == "passed":
            logger.info("🎉 BACKWARD COMPATIBILITY VALIDATION: PASSED")
            logger.info("✅ All existing functionality is preserved and working correctly.")
        else:
            logger.error("❌ BACKWARD COMPATIBILITY VALIDATION: FAILED")
            logger.error("⚠️  Some existing functionality may be broken or degraded.")
        
        logger.info("="*60)


async def main():
    """Main function to run backward compatibility validation"""
    validator = BackwardCompatibilityValidator()
    results = await validator.run_all_tests()
    
    # Return appropriate exit code
    if results["overall_status"] == "passed":
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())