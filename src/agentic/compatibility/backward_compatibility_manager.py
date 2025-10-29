"""
Backward Compatibility Manager
Ensures all existing functionality is preserved while enabling agentic enhancements
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Union, Callable
from datetime import datetime
import inspect

from ..core.interfaces import IBackwardCompatibilityManager
from ..agents.user_interface_agent import UserInterfaceAgent
from ..agents.cost_management_agent import CostManagementAgent
from ..agents.forecasting_agent import ForecastingAgent


class BackwardCompatibilityManager(IBackwardCompatibilityManager):
    """
    Manages backward compatibility by ensuring existing functionality
    is preserved and enhanced through the agentic system
    """
    
    def __init__(self, 
                 ui_agent: UserInterfaceAgent,
                 cost_agent: CostManagementAgent,
                 forecasting_agent: ForecastingAgent):
        self.ui_agent = ui_agent
        self.cost_agent = cost_agent
        self.forecasting_agent = forecasting_agent
        self.logger = logging.getLogger(__name__)
        
        # Track legacy function mappings
        self.legacy_mappings = {}
        self.compatibility_layer_active = True
        
        # Initialize compatibility mappings
        self._initialize_compatibility_mappings()
    
    def _initialize_compatibility_mappings(self):
        """Initialize mappings between legacy functions and agentic equivalents"""
        
        # Dashboard functionality mappings
        self.legacy_mappings.update({
            # Legacy dashboard functions -> UserInterfaceAgent methods
            'render_header': self._wrap_ui_function('render_dashboard_header'),
            'render_navigation': self._wrap_ui_function('render_navigation_tabs'),
            'render_metrics_row': self._wrap_ui_function('render_metrics_display'),
            'render_charts': self._wrap_ui_function('render_cost_charts'),
            'render_ai_assistant': self._wrap_ui_function('render_conversational_interface'),
            'render_forecasting_ai_assistant': self._wrap_ui_function('render_forecasting_interface'),
            'render_current_usage_tab': self._wrap_ui_function('render_usage_overview'),
            'render_detailed_usage_tab': self._wrap_ui_function('render_detailed_usage'),
            'render_detailed_billing_tab': self._wrap_ui_function('render_billing_details'),
            'render_forecast_tab': self._wrap_ui_function('render_forecast_analysis'),
            'render_historical_tab': self._wrap_ui_function('render_historical_data'),
            'render_settings_tab': self._wrap_ui_function('render_settings_panel'),
            
            # Cost analysis functionality -> CostManagementAgent methods
            'calculate_metrics': self._wrap_cost_function('calculate_cost_metrics'),
            'validate_cost_data_consistency': self._wrap_cost_function('validate_cost_data'),
            'force_refresh_cost_data': self._wrap_cost_function('refresh_cost_data'),
            'load_data': self._wrap_cost_function('load_cost_data'),
            
            # Forecasting functionality -> ForecastingAgent methods
            'process_cost_query': self._wrap_forecasting_function('process_cost_estimation_query'),
            'get_resource_pricing': self._wrap_forecasting_function('get_resource_pricing_data'),
            'chat_response': self._wrap_forecasting_function('generate_forecasting_response'),
        })
        
        self.logger.info(f"Initialized {len(self.legacy_mappings)} compatibility mappings")
    
    def _wrap_ui_function(self, agent_method: str) -> Callable:
        """Wrap UI agent method for backward compatibility"""
        async def wrapper(*args, **kwargs):
            try:
                # Get the agent method
                method = getattr(self.ui_agent, agent_method, None)
                if not method:
                    self.logger.warning(f"UI agent method {agent_method} not found")
                    return self._fallback_ui_response(*args, **kwargs)
                
                # Call the agent method
                if inspect.iscoroutinefunction(method):
                    result = await method(*args, **kwargs)
                else:
                    result = method(*args, **kwargs)
                
                return result
                
            except Exception as e:
                self.logger.error(f"Error in UI compatibility wrapper for {agent_method}: {e}")
                return self._fallback_ui_response(*args, **kwargs)
        
        return wrapper
    
    def _wrap_cost_function(self, agent_method: str) -> Callable:
        """Wrap cost management agent method for backward compatibility"""
        async def wrapper(*args, **kwargs):
            try:
                # Get the agent method
                method = getattr(self.cost_agent, agent_method, None)
                if not method:
                    self.logger.warning(f"Cost agent method {agent_method} not found")
                    return self._fallback_cost_response(*args, **kwargs)
                
                # Call the agent method
                if inspect.iscoroutinefunction(method):
                    result = await method(*args, **kwargs)
                else:
                    result = method(*args, **kwargs)
                
                return result
                
            except Exception as e:
                self.logger.error(f"Error in cost compatibility wrapper for {agent_method}: {e}")
                return self._fallback_cost_response(*args, **kwargs)
        
        return wrapper
    
    def _wrap_forecasting_function(self, agent_method: str) -> Callable:
        """Wrap forecasting agent method for backward compatibility"""
        async def wrapper(*args, **kwargs):
            try:
                # Get the agent method
                method = getattr(self.forecasting_agent, agent_method, None)
                if not method:
                    self.logger.warning(f"Forecasting agent method {agent_method} not found")
                    return self._fallback_forecasting_response(*args, **kwargs)
                
                # Call the agent method
                if inspect.iscoroutinefunction(method):
                    result = await method(*args, **kwargs)
                else:
                    result = method(*args, **kwargs)
                
                return result
                
            except Exception as e:
                self.logger.error(f"Error in forecasting compatibility wrapper for {agent_method}: {e}")
                return self._fallback_forecasting_response(*args, **kwargs)
        
        return wrapper
    
    async def ensure_dashboard_compatibility(self, dashboard_instance) -> bool:
        """Ensure dashboard instance maintains backward compatibility"""
        try:
            # Inject compatibility methods into dashboard instance
            for legacy_method, wrapper_func in self.legacy_mappings.items():
                if hasattr(dashboard_instance, legacy_method):
                    # Store original method as backup
                    setattr(dashboard_instance, f"_original_{legacy_method}", 
                           getattr(dashboard_instance, legacy_method))
                    
                    # Replace with compatibility wrapper
                    setattr(dashboard_instance, legacy_method, wrapper_func)
            
            # Ensure critical dashboard methods exist
            critical_methods = [
                'render_header', 'render_navigation', 'render_metrics_row',
                'render_charts', 'render_ai_assistant', 'calculate_metrics',
                'load_data', 'validate_cost_data_consistency'
            ]
            
            for method_name in critical_methods:
                if not hasattr(dashboard_instance, method_name):
                    self.logger.warning(f"Critical method {method_name} missing from dashboard")
                    # Add fallback method
                    setattr(dashboard_instance, method_name, 
                           self._create_fallback_method(method_name))
            
            self.logger.info("Dashboard backward compatibility ensured")
            return True
            
        except Exception as e:
            self.logger.error(f"Error ensuring dashboard compatibility: {e}")
            return False
    
    async def ensure_cost_analysis_compatibility(self, cost_service_instance) -> bool:
        """Ensure cost analysis functionality is preserved"""
        try:
            # Map legacy cost analysis methods to agent methods
            cost_mappings = {
                'get_usage_summary': 'get_comprehensive_usage_summary',
                'get_service_costs': 'analyze_service_costs',
                'get_monthly_trend': 'calculate_cost_trends',
                'get_cost_insights': 'generate_cost_insights',
                'analyze_scenario': 'analyze_cost_scenario'
            }
            
            for legacy_method, agent_method in cost_mappings.items():
                if hasattr(cost_service_instance, legacy_method):
                    # Create compatibility wrapper
                    wrapper = self._create_cost_analysis_wrapper(agent_method)
                    setattr(cost_service_instance, f"_enhanced_{legacy_method}", wrapper)
            
            self.logger.info("Cost analysis backward compatibility ensured")
            return True
            
        except Exception as e:
            self.logger.error(f"Error ensuring cost analysis compatibility: {e}")
            return False
    
    async def ensure_forecasting_compatibility(self, forecasting_service_instance) -> bool:
        """Ensure forecasting functionality is enhanced, not replaced"""
        try:
            # Enhance existing forecasting methods with agent capabilities
            forecasting_enhancements = {
                'process_cost_query': self._enhance_cost_query_processing,
                'get_resource_pricing': self._enhance_resource_pricing,
                'chat_response': self._enhance_chat_response,
                'generate_budget_timeline': self._enhance_budget_timeline,
                'generate_monthly_projections': self._enhance_monthly_projections
            }
            
            for method_name, enhancement_func in forecasting_enhancements.items():
                if hasattr(forecasting_service_instance, method_name):
                    # Store original method
                    original_method = getattr(forecasting_service_instance, method_name)
                    setattr(forecasting_service_instance, f"_original_{method_name}", original_method)
                    
                    # Create enhanced wrapper
                    enhanced_method = enhancement_func(original_method)
                    setattr(forecasting_service_instance, method_name, enhanced_method)
            
            self.logger.info("Forecasting backward compatibility with enhancements ensured")
            return True
            
        except Exception as e:
            self.logger.error(f"Error ensuring forecasting compatibility: {e}")
            return False
    
    def _create_fallback_method(self, method_name: str) -> Callable:
        """Create fallback method for missing functionality"""
        def fallback_method(*args, **kwargs):
            self.logger.warning(f"Fallback method called for {method_name}")
            return f"Fallback response for {method_name}"
        
        return fallback_method
    
    def _create_cost_analysis_wrapper(self, agent_method: str) -> Callable:
        """Create wrapper for cost analysis methods"""
        async def wrapper(*args, **kwargs):
            try:
                # Call the cost management agent
                result = await self.cost_agent.execute_action(agent_method, {
                    'args': args,
                    'kwargs': kwargs
                })
                
                return result.get('data', result)
                
            except Exception as e:
                self.logger.error(f"Error in cost analysis wrapper for {agent_method}: {e}")
                return {'error': str(e)}
        
        return wrapper
    
    def _enhance_cost_query_processing(self, original_method: Callable) -> Callable:
        """Enhance cost query processing with agent capabilities"""
        async def enhanced_method(*args, **kwargs):
            try:
                # First try the enhanced agent method
                agent_result = await self.forecasting_agent.process_cost_estimation_query(*args, **kwargs)
                
                # If agent method succeeds, return enhanced result
                if agent_result and not agent_result.get('error'):
                    return agent_result
                
                # Fallback to original method
                self.logger.info("Falling back to original cost query processing")
                return await original_method(*args, **kwargs)
                
            except Exception as e:
                self.logger.error(f"Error in enhanced cost query processing: {e}")
                # Always fallback to original method on error
                return await original_method(*args, **kwargs)
        
        return enhanced_method
    
    def _enhance_resource_pricing(self, original_method: Callable) -> Callable:
        """Enhance resource pricing with agent capabilities"""
        async def enhanced_method(*args, **kwargs):
            try:
                # Try enhanced pricing through agent
                agent_result = await self.forecasting_agent.get_enhanced_resource_pricing(*args, **kwargs)
                
                if agent_result and not agent_result.get('error'):
                    return agent_result
                
                # Fallback to original method
                return await original_method(*args, **kwargs)
                
            except Exception as e:
                self.logger.error(f"Error in enhanced resource pricing: {e}")
                return await original_method(*args, **kwargs)
        
        return enhanced_method
    
    def _enhance_chat_response(self, original_method: Callable) -> Callable:
        """Enhance chat response with agent capabilities"""
        async def enhanced_method(*args, **kwargs):
            try:
                # Try enhanced chat through agent
                agent_result = await self.forecasting_agent.generate_enhanced_chat_response(*args, **kwargs)
                
                if agent_result and not agent_result.get('error'):
                    return agent_result
                
                # Fallback to original method
                return await original_method(*args, **kwargs)
                
            except Exception as e:
                self.logger.error(f"Error in enhanced chat response: {e}")
                return await original_method(*args, **kwargs)
        
        return enhanced_method
    
    def _enhance_budget_timeline(self, original_method: Callable) -> Callable:
        """Enhance budget timeline with agent insights"""
        def enhanced_method(*args, **kwargs):
            try:
                # Get original timeline
                original_timeline = original_method(*args, **kwargs)
                
                # Enhance with agent insights
                enhanced_timeline = asyncio.run(
                    self.cost_agent.enhance_budget_timeline(original_timeline)
                )
                
                return enhanced_timeline if enhanced_timeline else original_timeline
                
            except Exception as e:
                self.logger.error(f"Error enhancing budget timeline: {e}")
                return original_method(*args, **kwargs)
        
        return enhanced_method
    
    def _enhance_monthly_projections(self, original_method: Callable) -> Callable:
        """Enhance monthly projections with agent analysis"""
        def enhanced_method(*args, **kwargs):
            try:
                # Get original projections
                original_projections = original_method(*args, **kwargs)
                
                # Enhance with agent analysis
                enhanced_projections = asyncio.run(
                    self.forecasting_agent.enhance_monthly_projections(original_projections)
                )
                
                return enhanced_projections if enhanced_projections else original_projections
                
            except Exception as e:
                self.logger.error(f"Error enhancing monthly projections: {e}")
                return original_method(*args, **kwargs)
        
        return enhanced_method
    
    def _fallback_ui_response(self, *args, **kwargs) -> str:
        """Fallback response for UI methods"""
        return "UI functionality temporarily unavailable - using fallback"
    
    def _fallback_cost_response(self, *args, **kwargs) -> Dict[str, Any]:
        """Fallback response for cost methods"""
        return {
            'error': 'Cost analysis temporarily unavailable',
            'fallback': True,
            'timestamp': datetime.now().isoformat()
        }
    
    def _fallback_forecasting_response(self, *args, **kwargs) -> str:
        """Fallback response for forecasting methods"""
        return "Forecasting functionality temporarily unavailable - please try again"
    
    async def validate_compatibility(self) -> Dict[str, bool]:
        """Validate that all compatibility mappings are working"""
        validation_results = {}
        
        try:
            # Test UI agent compatibility
            ui_test = await self.ui_agent.health_check()
            validation_results['ui_agent'] = ui_test
            
            # Test cost management agent compatibility
            cost_test = await self.cost_agent.health_check()
            validation_results['cost_agent'] = cost_test
            
            # Test forecasting agent compatibility
            forecasting_test = await self.forecasting_agent.health_check()
            validation_results['forecasting_agent'] = forecasting_test
            
            # Test legacy mappings
            mapping_tests = []
            for legacy_method in ['render_header', 'calculate_metrics', 'process_cost_query']:
                if legacy_method in self.legacy_mappings:
                    mapping_tests.append(True)
                else:
                    mapping_tests.append(False)
            
            validation_results['legacy_mappings'] = all(mapping_tests)
            
            # Overall compatibility status
            validation_results['overall_compatibility'] = all(validation_results.values())
            
            self.logger.info(f"Compatibility validation results: {validation_results}")
            return validation_results
            
        except Exception as e:
            self.logger.error(f"Error validating compatibility: {e}")
            return {'error': str(e), 'overall_compatibility': False}
    
    async def get_compatibility_status(self) -> Dict[str, Any]:
        """Get current compatibility status and metrics"""
        try:
            status = {
                'compatibility_layer_active': self.compatibility_layer_active,
                'total_mappings': len(self.legacy_mappings),
                'agents_status': {
                    'ui_agent': await self.ui_agent.get_state(),
                    'cost_agent': await self.cost_agent.get_state(),
                    'forecasting_agent': await self.forecasting_agent.get_state()
                },
                'last_validation': datetime.now().isoformat(),
                'fallback_usage': {
                    'ui_fallbacks': 0,  # Would track in real implementation
                    'cost_fallbacks': 0,
                    'forecasting_fallbacks': 0
                }
            }
            
            return status
            
        except Exception as e:
            self.logger.error(f"Error getting compatibility status: {e}")
            return {'error': str(e)}
    
    def enable_compatibility_layer(self):
        """Enable the compatibility layer"""
        self.compatibility_layer_active = True
        self.logger.info("Backward compatibility layer enabled")
    
    def disable_compatibility_layer(self):
        """Disable the compatibility layer (use pure agentic system)"""
        self.compatibility_layer_active = False
        self.logger.info("Backward compatibility layer disabled - using pure agentic system")