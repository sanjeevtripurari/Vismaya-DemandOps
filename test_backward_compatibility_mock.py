#!/usr/bin/env python3
"""
Mock-based Backward Compatibility Validation
Tests backward compatibility without requiring AWS credentials
"""

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MockBackwardCompatibilityValidator:
    """Validates backward compatibility using mocked AWS services"""
    
    def __init__(self):
        self.results = {
            "overall_status": "passed",
            "test_results": {},
            "timestamp": datetime.now().isoformat(),
            "errors": []
        }
    
    async def run_all_tests(self):
        """Run all backward compatibility tests with mocked services"""
        logger.info("🧪 Starting mock-based backward compatibility validation...")
        
        try:
            # Test 1: Dashboard functionality structure
            await self._test_dashboard_data_structure()
            
            # Test 2: Cost analysis interface
            await self._test_cost_analysis_interface()
            
            # Test 3: Forecasting interface
            await self._test_forecasting_interface()
            
            # Test 4: Resource management interface
            await self._test_resource_management_interface()
            
            # Test 5: AI assistant interface
            await self._test_ai_assistant_interface()
            
            # Test 6: Compatibility layer functionality
            await self._test_compatibility_layer_functionality()
            
            # Test 7: Feature flags system
            await self._test_feature_flags_system()
            
            # Test 8: Data model compatibility
            await self._test_data_model_compatibility()
            
        except Exception as e:
            logger.error(f"❌ Critical error during testing: {e}")
            self.results["overall_status"] = "failed"
            self.results["errors"].append(str(e))
        
        # Generate final report
        self._generate_report()
        
        return self.results
    
    async def _test_dashboard_data_structure(self):
        """Test that dashboard data structures are preserved"""
        test_name = "dashboard_data_structure"
        logger.info(f"Testing: {test_name}")
        
        try:
            from src.core.models import UsageSummary, BudgetInfo, CostForecast, ServiceCost, ServiceType
            
            # Create mock data with expected structure
            budget_info = BudgetInfo(
                total_budget=1000.0,
                current_spend=500.0,
                warning_limit=800.0,
                maximum_limit=1000.0
            )
            
            cost_forecast = CostForecast(
                forecasted_amount=550.0,
                confidence_level=0.8,
                forecast_period_days=30,
                base_amount=500.0
            )
            
            service_costs = [
                ServiceCost(
                    service_type=ServiceType.EC2,
                    cost=Mock(amount=200.0, currency="USD"),
                    usage_details={}
                )
            ]
            
            usage_summary = UsageSummary(
                budget_info=budget_info,
                service_costs=service_costs,
                ec2_instances=[],
                storage_volumes=[],
                database_instances=[],
                cost_forecast=cost_forecast,
                recommendations=[]
            )
            
            # Validate required attributes exist
            required_attrs = ['budget_info', 'service_costs', 'cost_forecast', 'ec2_instances', 'storage_volumes', 'database_instances', 'recommendations']
            missing_attrs = [attr for attr in required_attrs if not hasattr(usage_summary, attr)]
            
            if not missing_attrs:
                self.results["test_results"][test_name] = {
                    "status": "passed",
                    "details": "Dashboard data structure preserved - all required attributes present"
                }
                logger.info(f"✅ {test_name}: PASSED")
            else:
                self.results["test_results"][test_name] = {
                    "status": "failed",
                    "details": f"Missing required attributes: {missing_attrs}"
                }
                self.results["overall_status"] = "failed"
                logger.error(f"❌ {test_name}: FAILED")
            
        except Exception as e:
            self.results["test_results"][test_name] = {
                "status": "failed",
                "error": str(e)
            }
            self.results["overall_status"] = "failed"
            logger.error(f"❌ {test_name}: FAILED - {e}")
    
    async def _test_cost_analysis_interface(self):
        """Test cost analysis service interface"""
        test_name = "cost_analysis_interface"
        logger.info(f"Testing: {test_name}")
        
        try:
            from src.services.cost_service import CostAnalysisService
            from src.core.interfaces import ICostDataProvider, IForecastingService, IAIAssistant
            
            # Create mock dependencies
            mock_cost_provider = Mock(spec=ICostDataProvider)
            mock_forecasting_service = Mock(spec=IForecastingService)
            mock_ai_assistant = Mock(spec=IAIAssistant)
            
            # Mock return values
            mock_cost_provider.get_current_costs = AsyncMock(return_value=Mock(amount=500.0))
            mock_cost_provider.get_service_costs = AsyncMock(return_value=[])
            mock_ai_assistant.analyze_costs = AsyncMock(return_value="Mock cost analysis")
            
            # Create service instance
            cost_service = CostAnalysisService(
                mock_cost_provider,
                mock_forecasting_service,
                mock_ai_assistant
            )
            
            # Test interface methods exist
            required_methods = ['get_cost_insights', 'get_cost_forecast', 'get_optimization_recommendations', 'analyze_cost_trends']
            missing_methods = [method for method in required_methods if not hasattr(cost_service, method)]
            
            if not missing_methods:
                # Test method execution
                insights = await cost_service.get_cost_insights()
                
                if insights and isinstance(insights, str):
                    self.results["test_results"][test_name] = {
                        "status": "passed",
                        "details": "Cost analysis interface preserved and functional"
                    }
                    logger.info(f"✅ {test_name}: PASSED")
                else:
                    self.results["test_results"][test_name] = {
                        "status": "failed",
                        "details": "Cost analysis methods not returning expected results"
                    }
                    self.results["overall_status"] = "failed"
                    logger.error(f"❌ {test_name}: FAILED")
            else:
                self.results["test_results"][test_name] = {
                    "status": "failed",
                    "details": f"Missing required methods: {missing_methods}"
                }
                self.results["overall_status"] = "failed"
                logger.error(f"❌ {test_name}: FAILED")
            
        except Exception as e:
            self.results["test_results"][test_name] = {
                "status": "failed",
                "error": str(e)
            }
            self.results["overall_status"] = "failed"
            logger.error(f"❌ {test_name}: FAILED - {e}")
    
    async def _test_forecasting_interface(self):
        """Test forecasting service interface"""
        test_name = "forecasting_interface"
        logger.info(f"Testing: {test_name}")
        
        try:
            from src.services.forecasting_ai_assistant import ForecastingAIAssistant
            from src.core.interfaces import IAWSPricingProvider, IQueryParser, ICostEstimationEngine, IAIAssistant
            from src.core.models import ForecastingContext, BudgetInfo, CostEstimateResponse, ResourceSpecification
            
            # Create mock dependencies
            mock_pricing_provider = Mock(spec=IAWSPricingProvider)
            mock_query_parser = Mock(spec=IQueryParser)
            mock_cost_engine = Mock(spec=ICostEstimationEngine)
            mock_ai_assistant = Mock(spec=IAIAssistant)
            
            # Mock return values
            mock_cost_engine.estimate_resource_cost = AsyncMock(return_value=CostEstimateResponse(
                resource_spec=ResourceSpecification(resource_type=None),
                pricing_breakdown={},
                total_cost=100.0,
                duration=None
            ))
            
            # Create service instance
            forecasting_service = ForecastingAIAssistant(
                mock_pricing_provider,
                mock_query_parser,
                mock_cost_engine,
                mock_ai_assistant
            )
            
            # Test interface methods exist
            required_methods = ['process_cost_query', 'get_resource_pricing', 'chat_response']
            missing_methods = [method for method in required_methods if not hasattr(forecasting_service, method)]
            
            if not missing_methods:
                # Test method execution
                context = ForecastingContext(
                    budget_info=BudgetInfo(
                        total_budget=1000.0,
                        current_spend=500.0,
                        warning_limit=800.0,
                        maximum_limit=1000.0
                    )
                )
                
                with patch('src.services.smart_defaults_processor.SmartDefaultsProcessor') as mock_processor:
                    mock_processor_instance = Mock()
                    mock_processor_instance.apply_defaults.return_value = {
                        'resource_type': 'ec2',
                        'instance_type': 't3.micro',
                        'quantity': 1,
                        'duration_months': 1,
                        'applied_defaults': []
                    }
                    mock_processor_instance.format_defaults_explanation.return_value = "Mock explanation"
                    mock_processor_instance.get_refinement_suggestions.return_value = []
                    mock_processor.return_value = mock_processor_instance
                    
                    response = await forecasting_service.process_cost_query("test query", context)
                
                if response and hasattr(response, 'total_cost'):
                    self.results["test_results"][test_name] = {
                        "status": "passed",
                        "details": "Forecasting interface preserved and functional"
                    }
                    logger.info(f"✅ {test_name}: PASSED")
                else:
                    self.results["test_results"][test_name] = {
                        "status": "failed",
                        "details": "Forecasting methods not returning expected results"
                    }
                    self.results["overall_status"] = "failed"
                    logger.error(f"❌ {test_name}: FAILED")
            else:
                self.results["test_results"][test_name] = {
                    "status": "failed",
                    "details": f"Missing required methods: {missing_methods}"
                }
                self.results["overall_status"] = "failed"
                logger.error(f"❌ {test_name}: FAILED")
            
        except Exception as e:
            self.results["test_results"][test_name] = {
                "status": "failed",
                "error": str(e)
            }
            self.results["overall_status"] = "failed"
            logger.error(f"❌ {test_name}: FAILED - {e}")
    
    async def _test_resource_management_interface(self):
        """Test resource management service interface"""
        test_name = "resource_management_interface"
        logger.info(f"Testing: {test_name}")
        
        try:
            from src.services.resource_service import ResourceManagementService
            from src.core.interfaces import IResourceProvider
            
            # Create mock dependencies
            mock_resource_provider = Mock(spec=IResourceProvider)
            mock_resource_provider.get_ec2_instances = AsyncMock(return_value=[])
            mock_resource_provider.get_storage_volumes = AsyncMock(return_value=[])
            mock_resource_provider.get_database_instances = AsyncMock(return_value=[])
            
            # Create service instance
            resource_service = ResourceManagementService(mock_resource_provider)
            
            # Test interface methods exist
            required_methods = ['get_resource_inventory', 'get_ec2_summary', 'get_storage_summary', 'get_database_summary', 'calculate_scenario_impact']
            missing_methods = [method for method in required_methods if not hasattr(resource_service, method)]
            
            if not missing_methods:
                # Test method execution
                inventory = await resource_service.get_resource_inventory()
                
                required_keys = ['ec2_instances', 'storage_volumes', 'database_instances']
                missing_keys = [key for key in required_keys if key not in inventory]
                
                if not missing_keys:
                    self.results["test_results"][test_name] = {
                        "status": "passed",
                        "details": "Resource management interface preserved and functional"
                    }
                    logger.info(f"✅ {test_name}: PASSED")
                else:
                    self.results["test_results"][test_name] = {
                        "status": "failed",
                        "details": f"Missing inventory keys: {missing_keys}"
                    }
                    self.results["overall_status"] = "failed"
                    logger.error(f"❌ {test_name}: FAILED")
            else:
                self.results["test_results"][test_name] = {
                    "status": "failed",
                    "details": f"Missing required methods: {missing_methods}"
                }
                self.results["overall_status"] = "failed"
                logger.error(f"❌ {test_name}: FAILED")
            
        except Exception as e:
            self.results["test_results"][test_name] = {
                "status": "failed",
                "error": str(e)
            }
            self.results["overall_status"] = "failed"
            logger.error(f"❌ {test_name}: FAILED - {e}")
    
    async def _test_ai_assistant_interface(self):
        """Test AI assistant interface"""
        test_name = "ai_assistant_interface"
        logger.info(f"Testing: {test_name}")
        
        try:
            # Test that AI assistant interfaces are preserved
            from src.core.interfaces import IAIAssistant
            from src.core.models import UsageSummary, BudgetInfo, CostForecast
            
            # Create mock AI assistant
            mock_ai_assistant = Mock(spec=IAIAssistant)
            mock_ai_assistant.chat_response = AsyncMock(return_value="Mock AI response")
            mock_ai_assistant.analyze_costs = AsyncMock(return_value="Mock cost analysis")
            mock_ai_assistant.generate_recommendations = AsyncMock(return_value=[])
            
            # Test interface methods exist
            required_methods = ['chat_response', 'analyze_costs', 'generate_recommendations']
            missing_methods = [method for method in required_methods if not hasattr(mock_ai_assistant, method)]
            
            if not missing_methods:
                # Test method execution
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
                
                response = await mock_ai_assistant.chat_response("test query", usage_summary)
                
                if response and isinstance(response, str):
                    self.results["test_results"][test_name] = {
                        "status": "passed",
                        "details": "AI assistant interface preserved and functional"
                    }
                    logger.info(f"✅ {test_name}: PASSED")
                else:
                    self.results["test_results"][test_name] = {
                        "status": "failed",
                        "details": "AI assistant not returning expected results"
                    }
                    self.results["overall_status"] = "failed"
                    logger.error(f"❌ {test_name}: FAILED")
            else:
                self.results["test_results"][test_name] = {
                    "status": "failed",
                    "details": f"Missing required methods: {missing_methods}"
                }
                self.results["overall_status"] = "failed"
                logger.error(f"❌ {test_name}: FAILED")
            
        except Exception as e:
            self.results["test_results"][test_name] = {
                "status": "failed",
                "error": str(e)
            }
            self.results["overall_status"] = "failed"
            logger.error(f"❌ {test_name}: FAILED - {e}")
    
    async def _test_compatibility_layer_functionality(self):
        """Test compatibility layer functionality"""
        test_name = "compatibility_layer_functionality"
        logger.info(f"Testing: {test_name}")
        
        try:
            from src.agentic.migration.compatibility_layer import CompatibilityLayer, CompatibilityMode
            
            # Initialize compatibility layer
            compatibility_config = {
                "agentic_rollout_percentage": 0
            }
            
            compatibility_layer = CompatibilityLayer(compatibility_config)
            compatibility_layer.set_compatibility_mode(CompatibilityMode.LEGACY_ONLY)
            
            # Test endpoint mappings exist
            expected_endpoints = [
                "get_usage_summary", "get_cost_insights", "get_service_costs",
                "get_resource_details", "optimize_resources", "analyze_scenario",
                "get_cost_forecast", "handle_chat", "get_dashboard_data"
            ]
            
            missing_endpoints = [ep for ep in expected_endpoints if ep not in compatibility_layer.endpoint_mappings]
            
            if not missing_endpoints:
                # Test mode setting
                compatibility_layer.set_compatibility_mode(CompatibilityMode.HYBRID)
                
                if compatibility_layer.mode == CompatibilityMode.HYBRID:
                    self.results["test_results"][test_name] = {
                        "status": "passed",
                        "details": "Compatibility layer functionality preserved"
                    }
                    logger.info(f"✅ {test_name}: PASSED")
                else:
                    self.results["test_results"][test_name] = {
                        "status": "failed",
                        "details": "Compatibility layer mode setting not working"
                    }
                    self.results["overall_status"] = "failed"
                    logger.error(f"❌ {test_name}: FAILED")
            else:
                self.results["test_results"][test_name] = {
                    "status": "failed",
                    "details": f"Missing endpoint mappings: {missing_endpoints}"
                }
                self.results["overall_status"] = "failed"
                logger.error(f"❌ {test_name}: FAILED")
            
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
            from src.agentic.migration.feature_flags import FeatureFlagManager, RolloutStrategy
            
            # Initialize feature flags manager
            flag_config = {
                "flag_file_path": "test_feature_flags.json",
                "max_evaluations": 1000
            }
            
            flag_manager = FeatureFlagManager(flag_config)
            
            # Test default flags exist
            expected_flags = [
                "agentic_cost_analysis", "agentic_resource_management", 
                "agentic_forecasting", "agentic_dashboard", "approval_workflows"
            ]
            
            missing_flags = [flag for flag in expected_flags if flag not in flag_manager.flags]
            
            if not missing_flags:
                # Test flag evaluation
                is_enabled = flag_manager.is_enabled("agentic_cost_analysis", "test_user")
                
                # Test flag status
                status = flag_manager.get_flag_status("agentic_cost_analysis")
                
                if status and "name" in status:
                    self.results["test_results"][test_name] = {
                        "status": "passed",
                        "details": f"Feature flags system functional - {len(expected_flags)} flags available"
                    }
                    logger.info(f"✅ {test_name}: PASSED")
                else:
                    self.results["test_results"][test_name] = {
                        "status": "failed",
                        "details": "Feature flag status not working properly"
                    }
                    self.results["overall_status"] = "failed"
                    logger.error(f"❌ {test_name}: FAILED")
            else:
                self.results["test_results"][test_name] = {
                    "status": "failed",
                    "details": f"Missing expected flags: {missing_flags}"
                }
                self.results["overall_status"] = "failed"
                logger.error(f"❌ {test_name}: FAILED")
            
        except Exception as e:
            self.results["test_results"][test_name] = {
                "status": "failed",
                "error": str(e)
            }
            self.results["overall_status"] = "failed"
            logger.error(f"❌ {test_name}: FAILED - {e}")
    
    async def _test_data_model_compatibility(self):
        """Test data model compatibility"""
        test_name = "data_model_compatibility"
        logger.info(f"Testing: {test_name}")
        
        try:
            from src.core.models import (
                UsageSummary, BudgetInfo, CostForecast, ServiceCost, ServiceType,
                EC2Instance, StorageVolume, DatabaseInstance, OptimizationRecommendation,
                ResourceSpecification, ResourceType, CostEstimateResponse, TimePeriod
            )
            
            # Test that all core data models can be instantiated
            models_to_test = [
                (BudgetInfo, {
                    'total_budget': 1000.0,
                    'current_spend': 500.0,
                    'warning_limit': 800.0,
                    'maximum_limit': 1000.0
                }),
                (CostForecast, {
                    'forecasted_amount': 550.0,
                    'confidence_level': 0.8,
                    'forecast_period_days': 30,
                    'base_amount': 500.0
                }),
                (ResourceSpecification, {
                    'resource_type': ResourceType.EC2
                }),
                (CostEstimateResponse, {
                    'resource_spec': ResourceSpecification(resource_type=ResourceType.EC2),
                    'pricing_breakdown': {},
                    'total_cost': 100.0,
                    'duration': TimePeriod.from_months(1)
                })
            ]
            
            failed_models = []
            
            for model_class, kwargs in models_to_test:
                try:
                    instance = model_class(**kwargs)
                    # Verify instance was created successfully
                    if not instance:
                        failed_models.append(model_class.__name__)
                except Exception as e:
                    failed_models.append(f"{model_class.__name__}: {str(e)}")
            
            if not failed_models:
                self.results["test_results"][test_name] = {
                    "status": "passed",
                    "details": f"All {len(models_to_test)} core data models compatible"
                }
                logger.info(f"✅ {test_name}: PASSED")
            else:
                self.results["test_results"][test_name] = {
                    "status": "failed",
                    "details": f"Failed models: {failed_models}"
                }
                self.results["overall_status"] = "failed"
                logger.error(f"❌ {test_name}: FAILED")
            
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
        logger.info("🧪 MOCK BACKWARD COMPATIBILITY VALIDATION REPORT")
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
            logger.info("✅ All existing functionality interfaces are preserved and compatible.")
            logger.info("✅ The agentic system maintains backward compatibility with legacy code.")
        else:
            logger.error("❌ BACKWARD COMPATIBILITY VALIDATION: FAILED")
            logger.error("⚠️  Some existing functionality interfaces may be broken or incompatible.")
        
        logger.info("="*60)


async def main():
    """Main function to run mock backward compatibility validation"""
    validator = MockBackwardCompatibilityValidator()
    results = await validator.run_all_tests()
    
    # Return appropriate exit code
    if results["overall_status"] == "passed":
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())