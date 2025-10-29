"""
Integration Example
Demonstrates how to integrate backward compatibility with existing dashboard
"""

import asyncio
import logging
from typing import Dict, Any

from .compatibility_integration import CompatibilityIntegration


class BackwardCompatibilityDemo:
    """
    Demonstration of backward compatibility integration
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.integration = None
    
    async def demonstrate_integration(self) -> Dict[str, Any]:
        """Demonstrate the backward compatibility integration"""
        try:
            self.logger.info("Starting backward compatibility demonstration")
            
            # Initialize compatibility integration
            self.integration = CompatibilityIntegration(config={
                'ui_agent': {'personalization_enabled': True},
                'cost_agent': {'anomaly_threshold_percentage': 15.0},
                'forecasting_agent': {'forecast_horizon_days': 90}
            })
            
            # Initialize the integration layer
            init_success = await self.integration.initialize()
            if not init_success:
                return {'success': False, 'error': 'Integration initialization failed'}
            
            # Simulate existing dashboard instance
            mock_dashboard = MockDashboard()
            
            # Integrate with dashboard
            dashboard_integration = await self.integration.integrate_with_dashboard(mock_dashboard)
            
            # Test enhanced functionality
            enhanced_results = await self._test_enhanced_functionality(mock_dashboard)
            
            # Test backward compatibility
            compatibility_results = await self._test_backward_compatibility(mock_dashboard)
            
            # Get integration status
            status = await self.integration.get_integration_status()
            
            return {
                'success': True,
                'dashboard_integration': dashboard_integration,
                'enhanced_results': enhanced_results,
                'compatibility_results': compatibility_results,
                'integration_status': status
            }
            
        except Exception as e:
            self.logger.error(f"Error in demonstration: {e}")
            return {'success': False, 'error': str(e)}
        
        finally:
            if self.integration:
                await self.integration.shutdown()
    
    async def _test_enhanced_functionality(self, dashboard) -> Dict[str, Any]:
        """Test enhanced functionality"""
        try:
            results = {}
            
            # Test enhanced metrics
            if hasattr(dashboard, 'calculate_metrics'):
                enhanced_metrics = await dashboard.calculate_metrics()
                results['enhanced_metrics'] = enhanced_metrics.get('ai_powered', False)
            
            # Test enhanced AI assistant
            if hasattr(dashboard, 'render_ai_assistant'):
                ai_response = await dashboard.render_ai_assistant()
                results['enhanced_ai'] = 'enhanced' in ai_response
            
            # Test enhanced forecasting
            if hasattr(dashboard, 'render_forecasting_ai_assistant'):
                forecast_response = await dashboard.render_forecasting_ai_assistant()
                results['enhanced_forecasting'] = 'enhanced' in forecast_response
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error testing enhanced functionality: {e}")
            return {'error': str(e)}
    
    async def _test_backward_compatibility(self, dashboard) -> Dict[str, Any]:
        """Test backward compatibility"""
        try:
            results = {}
            
            # Test that original methods still work
            original_methods = [
                'render_header', 'render_navigation', 'render_metrics_row',
                'render_charts', 'calculate_metrics', 'load_data'
            ]
            
            for method_name in original_methods:
                if hasattr(dashboard, method_name):
                    try:
                        method = getattr(dashboard, method_name)
                        if asyncio.iscoroutinefunction(method):
                            result = await method()
                        else:
                            result = method()
                        results[method_name] = 'success'
                    except Exception as e:
                        results[method_name] = f'error: {str(e)}'
                else:
                    results[method_name] = 'method_not_found'
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error testing backward compatibility: {e}")
            return {'error': str(e)}


class MockDashboard:
    """Mock dashboard class to simulate existing dashboard functionality"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def render_header(self):
        """Mock render header method"""
        return "Dashboard Header"
    
    def render_navigation(self):
        """Mock render navigation method"""
        return ["Tab1", "Tab2", "Tab3"]
    
    def render_metrics_row(self):
        """Mock render metrics method"""
        return {
            'current_spend': 1000,
            'budget_pct': 75,
            'forecast': 1200
        }
    
    def render_charts(self):
        """Mock render charts method"""
        return {
            'monthly_trend': 'chart_data',
            'service_breakdown': 'chart_data'
        }
    
    def calculate_metrics(self):
        """Mock calculate metrics method"""
        return {
            'current_spend': 1000,
            'budget': 1500,
            'budget_pct': 66.7,
            'forecast': 1200,
            'trending': 'up'
        }
    
    def load_data(self):
        """Mock load data method"""
        return {'data_loaded': True}
    
    def render_ai_assistant(self):
        """Mock AI assistant method"""
        return "AI Assistant Response"
    
    def render_forecasting_ai_assistant(self):
        """Mock forecasting AI assistant method"""
        return "Forecasting AI Response"


async def run_demonstration():
    """Run the backward compatibility demonstration"""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    demo = BackwardCompatibilityDemo()
    results = await demo.demonstrate_integration()
    
    print("=== Backward Compatibility Demonstration Results ===")
    print(f"Success: {results.get('success', False)}")
    
    if results.get('success'):
        print(f"Dashboard Integration: {results.get('dashboard_integration', False)}")
        print(f"Enhanced Results: {results.get('enhanced_results', {})}")
        print(f"Compatibility Results: {results.get('compatibility_results', {})}")
        print(f"Integration Status: {results.get('integration_status', {}).get('integration_active', False)}")
    else:
        print(f"Error: {results.get('error', 'Unknown error')}")
    
    print("=== Demonstration Complete ===")


if __name__ == "__main__":
    asyncio.run(run_demonstration())