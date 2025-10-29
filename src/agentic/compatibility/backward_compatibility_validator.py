"""
Backward Compatibility Validator
Ensures existing functionality continues to work with the agentic system
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class BackwardCompatibilityValidator:
    """
    Validates that existing functionality is preserved during agentic migration
    """
    
    def __init__(self):
        self.validation_results = {
            "dashboard_functionality": False,
            "cost_analysis": False,
            "resource_management": False,
            "forecasting": False,
            "ai_assistant": False,
            "data_models": False,
            "interfaces": False
        }
        
        self.validation_details = {}
    
    def validate_dashboard_functionality(self) -> bool:
        """Validate dashboard functionality is preserved"""
        try:
            # Check that dashboard can still load data
            from src.core.models import UsageSummary, BudgetInfo, CostForecast
            
            # Test data model creation
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
            
            usage_summary = UsageSummary(
                budget_info=budget_info,
                service_costs=[],
                ec2_instances=[],
                storage_volumes=[],
                database_instances=[],
                cost_forecast=cost_forecast,
                recommendations=[]
            )
            
            # Validate required attributes exist
            required_attrs = [
                'budget_info', 'service_costs', 'cost_forecast', 
                'ec2_instances', 'storage_volumes', 'database_instances'
            ]
            
            for attr in required_attrs:
                if not hasattr(usage_summary, attr):
                    self.validation_details["dashboard_functionality"] = f"Missing attribute: {attr}"
                    return False
            
            self.validation_results["dashboard_functionality"] = True
            self.validation_details["dashboard_functionality"] = "All dashboard data structures preserved"
            return True
            
        except Exception as e:
            self.validation_details["dashboard_functionality"] = f"Error: {str(e)}"
            return False
    
    def validate_cost_analysis(self) -> bool:
        """Validate cost analysis functionality is preserved"""
        try:
            # Check that cost service interface exists
            from src.services.cost_service import CostAnalysisService
            
            # Validate required methods exist
            required_methods = [
                'get_cost_insights', 'get_cost_forecast', 
                'get_optimization_recommendations', 'analyze_cost_trends'
            ]
            
            for method in required_methods:
                if not hasattr(CostAnalysisService, method):
                    self.validation_details["cost_analysis"] = f"Missing method: {method}"
                    return False
            
            self.validation_results["cost_analysis"] = True
            self.validation_details["cost_analysis"] = "All cost analysis methods preserved"
            return True
            
        except Exception as e:
            self.validation_details["cost_analysis"] = f"Error: {str(e)}"
            return False
    
    def validate_resource_management(self) -> bool:
        """Validate resource management functionality is preserved"""
        try:
            # Check that resource service interface exists
            from src.services.resource_service import ResourceManagementService
            
            # Validate required methods exist
            required_methods = [
                'get_resource_inventory', 'get_ec2_summary', 
                'get_storage_summary', 'get_database_summary', 'calculate_scenario_impact'
            ]
            
            for method in required_methods:
                if not hasattr(ResourceManagementService, method):
                    self.validation_details["resource_management"] = f"Missing method: {method}"
                    return False
            
            self.validation_results["resource_management"] = True
            self.validation_details["resource_management"] = "All resource management methods preserved"
            return True
            
        except Exception as e:
            self.validation_details["resource_management"] = f"Error: {str(e)}"
            return False
    
    def validate_forecasting(self) -> bool:
        """Validate forecasting functionality is preserved"""
        try:
            # Check that forecasting service interface exists
            from src.services.forecasting_ai_assistant import ForecastingAIAssistant
            
            # Validate required methods exist
            required_methods = [
                'process_cost_query', 'get_resource_pricing', 'chat_response'
            ]
            
            for method in required_methods:
                if not hasattr(ForecastingAIAssistant, method):
                    self.validation_details["forecasting"] = f"Missing method: {method}"
                    return False
            
            self.validation_results["forecasting"] = True
            self.validation_details["forecasting"] = "All forecasting methods preserved"
            return True
            
        except Exception as e:
            self.validation_details["forecasting"] = f"Error: {str(e)}"
            return False
    
    def validate_ai_assistant(self) -> bool:
        """Validate AI assistant functionality is preserved"""
        try:
            # Check that AI assistant interfaces exist
            from src.core.interfaces import IAIAssistant
            
            # Validate interface methods
            required_methods = ['chat_response', 'analyze_costs', 'generate_recommendations']
            
            # Check if interface has required methods
            interface_methods = [method for method in dir(IAIAssistant) if not method.startswith('_')]
            
            for method in required_methods:
                if method not in interface_methods:
                    self.validation_details["ai_assistant"] = f"Missing interface method: {method}"
                    return False
            
            self.validation_results["ai_assistant"] = True
            self.validation_details["ai_assistant"] = "All AI assistant interfaces preserved"
            return True
            
        except Exception as e:
            self.validation_details["ai_assistant"] = f"Error: {str(e)}"
            return False
    
    def validate_data_models(self) -> bool:
        """Validate data models are preserved"""
        try:
            # Import and test core data models
            from src.core.models import (
                UsageSummary, BudgetInfo, CostForecast, ServiceCost, ServiceType,
                EC2Instance, StorageVolume, DatabaseInstance, OptimizationRecommendation,
                ResourceSpecification, ResourceType, CostEstimateResponse, TimePeriod
            )
            
            # Test model instantiation
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
                })
            ]
            
            for model_class, kwargs in models_to_test:
                try:
                    instance = model_class(**kwargs)
                    if not instance:
                        self.validation_details["data_models"] = f"Failed to create {model_class.__name__}"
                        return False
                except Exception as e:
                    self.validation_details["data_models"] = f"Error creating {model_class.__name__}: {str(e)}"
                    return False
            
            self.validation_results["data_models"] = True
            self.validation_details["data_models"] = "All data models preserved and functional"
            return True
            
        except Exception as e:
            self.validation_details["data_models"] = f"Error: {str(e)}"
            return False
    
    def validate_interfaces(self) -> bool:
        """Validate core interfaces are preserved"""
        try:
            # Import and check core interfaces
            from src.core.interfaces import (
                ICostDataProvider, IResourceProvider, IForecastingService,
                IAIAssistant, INotificationService, IConfigurationService,
                IAuthenticationService
            )
            
            # Check that interfaces exist and have expected structure
            interfaces = [
                ICostDataProvider, IResourceProvider, IForecastingService,
                IAIAssistant, INotificationService, IConfigurationService,
                IAuthenticationService
            ]
            
            for interface in interfaces:
                if not hasattr(interface, '__abstractmethods__'):
                    self.validation_details["interfaces"] = f"Interface {interface.__name__} is not properly defined"
                    return False
            
            self.validation_results["interfaces"] = True
            self.validation_details["interfaces"] = "All core interfaces preserved"
            return True
            
        except Exception as e:
            self.validation_details["interfaces"] = f"Error: {str(e)}"
            return False
    
    def run_full_validation(self) -> Dict[str, Any]:
        """Run complete backward compatibility validation"""
        logger.info("🧪 Running backward compatibility validation...")
        
        # Run all validation checks
        validations = [
            ("Dashboard Functionality", self.validate_dashboard_functionality),
            ("Cost Analysis", self.validate_cost_analysis),
            ("Resource Management", self.validate_resource_management),
            ("Forecasting", self.validate_forecasting),
            ("AI Assistant", self.validate_ai_assistant),
            ("Data Models", self.validate_data_models),
            ("Interfaces", self.validate_interfaces)
        ]
        
        results = {
            "overall_status": "passed",
            "validations": {},
            "summary": {
                "total": len(validations),
                "passed": 0,
                "failed": 0
            },
            "timestamp": datetime.now().isoformat()
        }
        
        for validation_name, validation_func in validations:
            try:
                success = validation_func()
                results["validations"][validation_name] = {
                    "status": "passed" if success else "failed",
                    "details": self.validation_details.get(validation_name.lower().replace(" ", "_"), "")
                }
                
                if success:
                    results["summary"]["passed"] += 1
                    logger.info(f"✅ {validation_name}: PASSED")
                else:
                    results["summary"]["failed"] += 1
                    results["overall_status"] = "failed"
                    logger.error(f"❌ {validation_name}: FAILED - {self.validation_details.get(validation_name.lower().replace(' ', '_'), '')}")
                    
            except Exception as e:
                results["validations"][validation_name] = {
                    "status": "error",
                    "details": f"Validation error: {str(e)}"
                }
                results["summary"]["failed"] += 1
                results["overall_status"] = "failed"
                logger.error(f"❌ {validation_name}: ERROR - {str(e)}")
        
        # Generate summary
        logger.info(f"\n📊 Backward Compatibility Validation Summary:")
        logger.info(f"   ✅ Passed: {results['summary']['passed']}/{results['summary']['total']}")
        logger.info(f"   ❌ Failed: {results['summary']['failed']}/{results['summary']['total']}")
        logger.info(f"   🎯 Overall Status: {results['overall_status'].upper()}")
        
        if results["overall_status"] == "passed":
            logger.info("🎉 BACKWARD COMPATIBILITY: VALIDATED")
            logger.info("✅ All existing functionality is preserved and compatible with the agentic system.")
        else:
            logger.warning("⚠️ BACKWARD COMPATIBILITY: ISSUES DETECTED")
            logger.warning("Some functionality may need attention during migration.")
        
        return results


def validate_backward_compatibility() -> Dict[str, Any]:
    """
    Main function to validate backward compatibility
    Returns validation results
    """
    validator = BackwardCompatibilityValidator()
    return validator.run_full_validation()


if __name__ == "__main__":
    # Run validation if called directly
    results = validate_backward_compatibility()
    
    # Exit with appropriate code
    import sys
    if results["overall_status"] == "passed":
        sys.exit(0)
    else:
        sys.exit(1)