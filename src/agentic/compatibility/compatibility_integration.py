"""
Compatibility Integration Layer
Integrates backward compatibility manager with existing system components
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from .backward_compatibility_manager import BackwardCompatibilityManager
from ..agents.user_interface_agent import UserInterfaceAgent
from ..agents.cost_management_agent import CostManagementAgent
from ..agents.forecasting_agent import ForecastingAgent
from ..core.interfaces import IStrandsFramework, IMCPServer


class CompatibilityIntegration:
    """
    Integration layer that ensures seamless backward compatibility
    while enabling enhanced agentic capabilities
    """
    
    def __init__(self, 
                 strands_framework: Optional[IStrandsFramework] = None,
                 mcp_server: Optional[IMCPServer] = None,
                 config: Optional[Dict[str, Any]] = None):
        self.strands_framework = strands_framework
        self.mcp_server = mcp_server
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize agents
        self.ui_agent = None
        self.cost_agent = None
        self.forecasting_agent = None
        self.compatibility_manager = None
        
        # Integration state
        self.integration_active = False
        self.compatibility_status = {}
        self.enhanced_features_enabled = True
        
    async def initialize(self) -> bool:
        """Initialize the compatibility integration layer"""
        try:
            self.logger.info("Initializing compatibility integration layer")
            
            # Initialize agents
            await self._initialize_agents()
            
            # Initialize compatibility manager
            await self._initialize_compatibility_manager()
            
            # Setup integration hooks
            await self._setup_integration_hooks()
            
            # Validate integration
            validation_result = await self._validate_integration()
            
            if validation_result:
                self.integration_active = True
                self.logger.info("Compatibility integration layer initialized successfully")
                return True
            else:
                self.logger.error("Compatibility integration validation failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Error initializing compatibility integration: {e}")
            return False
    
    async def _initialize_agents(self) -> None:
        """Initialize all required agents"""
        try:
            # Initialize User Interface Agent
            self.ui_agent = UserInterfaceAgent(
                strands_framework=self.strands_framework,
                mcp_server=self.mcp_server,
                config=self.config.get('ui_agent', {})
            )
            await self.ui_agent.initialize()
            
            # Initialize Cost Management Agent
            self.cost_agent = CostManagementAgent(
                strands_framework=self.strands_framework,
                mcp_server=self.mcp_server,
                config=self.config.get('cost_agent', {})
            )
            await self.cost_agent.initialize()
            
            # Initialize Forecasting Agent
            self.forecasting_agent = ForecastingAgent(
                strands_framework=self.strands_framework,
                mcp_server=self.mcp_server,
                config=self.config.get('forecasting_agent', {})
            )
            await self.forecasting_agent.initialize()
            
            self.logger.info("All agents initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing agents: {e}")
            raise
    
    async def _initialize_compatibility_manager(self) -> None:
        """Initialize the backward compatibility manager"""
        try:
            self.compatibility_manager = BackwardCompatibilityManager(
                ui_agent=self.ui_agent,
                cost_agent=self.cost_agent,
                forecasting_agent=self.forecasting_agent
            )
            
            self.logger.info("Compatibility manager initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing compatibility manager: {e}")
            raise
    
    async def _setup_integration_hooks(self) -> None:
        """Setup integration hooks for seamless operation"""
        try:
            # Setup agent communication hooks
            if self.mcp_server:
                # Register agents with MCP server
                await self.mcp_server.register_agent(self.ui_agent)
                await self.mcp_server.register_agent(self.cost_agent)
                await self.mcp_server.register_agent(self.forecasting_agent)
            
            # Setup Strands framework hooks
            if self.strands_framework:
                # Initialize shared context
                await self.strands_framework.initialize_shared_context({
                    'compatibility_layer': {
                        'active': True,
                        'version': '1.0.0',
                        'agents': ['ui_agent', 'cost_agent', 'forecasting_agent']
                    }
                })
            
            self.logger.info("Integration hooks setup completed")
            
        except Exception as e:
            self.logger.error(f"Error setting up integration hooks: {e}")
            raise
    
    async def _validate_integration(self) -> bool:
        """Validate that integration is working correctly"""
        try:
            validation_results = {}
            
            # Validate agent health
            validation_results['ui_agent'] = await self.ui_agent.health_check()
            validation_results['cost_agent'] = await self.cost_agent.health_check()
            validation_results['forecasting_agent'] = await self.forecasting_agent.health_check()
            
            # Validate compatibility manager
            compatibility_validation = await self.compatibility_manager.validate_compatibility()
            validation_results['compatibility_manager'] = compatibility_validation.get('overall_compatibility', False)
            
            # Check agent communication
            if self.mcp_server:
                validation_results['agent_communication'] = await self._test_agent_communication()
            else:
                validation_results['agent_communication'] = True  # Skip if no MCP server
            
            # Overall validation
            overall_success = all(validation_results.values())
            
            self.compatibility_status = {
                'validation_results': validation_results,
                'overall_success': overall_success,
                'validated_at': datetime.now().isoformat()
            }
            
            return overall_success
            
        except Exception as e:
            self.logger.error(f"Error validating integration: {e}")
            return False
    
    async def _test_agent_communication(self) -> bool:
        """Test communication between agents"""
        try:
            # Test UI agent to cost agent communication
            from ..core.models import AgentMessage, MessageType
            
            test_message = AgentMessage(
                sender=self.ui_agent.agent_id,
                recipient=self.cost_agent.agent_id,
                message_type=MessageType.REQUEST,
                content={"action": "health_check", "test": True}
            )
            
            response = await self.mcp_server.route_message(test_message)
            
            return response.message_type != MessageType.ERROR
            
        except Exception as e:
            self.logger.error(f"Error testing agent communication: {e}")
            return False
    
    async def integrate_with_dashboard(self, dashboard_instance) -> bool:
        """Integrate compatibility layer with existing dashboard"""
        try:
            self.logger.info("Integrating with dashboard instance")
            
            # Ensure dashboard compatibility
            dashboard_compatible = await self.compatibility_manager.ensure_dashboard_compatibility(dashboard_instance)
            
            if not dashboard_compatible:
                self.logger.warning("Dashboard compatibility could not be fully ensured")
                return False
            
            # Add enhanced features to dashboard
            await self._add_enhanced_dashboard_features(dashboard_instance)
            
            self.logger.info("Dashboard integration completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error integrating with dashboard: {e}")
            return False
    
    async def _add_enhanced_dashboard_features(self, dashboard_instance) -> None:
        """Add enhanced features to dashboard instance"""
        try:
            # Add AI-powered insights
            if hasattr(dashboard_instance, 'render_ai_assistant'):
                # Enhance existing AI assistant with agent capabilities
                original_ai_method = dashboard_instance.render_ai_assistant
                
                async def enhanced_ai_assistant(*args, **kwargs):
                    # Get enhanced response from UI agent
                    ui_response = await self.ui_agent.render_conversational_interface()
                    
                    # Merge with original functionality
                    original_result = original_ai_method(*args, **kwargs)
                    
                    return {
                        'original': original_result,
                        'enhanced': ui_response,
                        'mode': 'hybrid'
                    }
                
                dashboard_instance.render_ai_assistant = enhanced_ai_assistant
            
            # Add enhanced forecasting
            if hasattr(dashboard_instance, 'render_forecasting_ai_assistant'):
                original_forecast_method = dashboard_instance.render_forecasting_ai_assistant
                
                async def enhanced_forecasting_assistant(*args, **kwargs):
                    # Get enhanced response from forecasting agent
                    forecast_response = await self.forecasting_agent.render_forecasting_interface()
                    
                    # Merge with original functionality
                    original_result = original_forecast_method(*args, **kwargs)
                    
                    return {
                        'original': original_result,
                        'enhanced': forecast_response,
                        'mode': 'hybrid'
                    }
                
                dashboard_instance.render_forecasting_ai_assistant = enhanced_forecasting_assistant
            
            # Add enhanced metrics
            if hasattr(dashboard_instance, 'calculate_metrics'):
                original_metrics_method = dashboard_instance.calculate_metrics
                
                async def enhanced_calculate_metrics(*args, **kwargs):
                    # Get enhanced metrics from cost agent
                    enhanced_metrics = await self.cost_agent.calculate_cost_metrics(*args, **kwargs)
                    
                    # Merge with original metrics
                    original_metrics = original_metrics_method(*args, **kwargs)
                    
                    return {
                        **original_metrics,
                        'enhanced_insights': enhanced_metrics,
                        'ai_powered': True
                    }
                
                dashboard_instance.calculate_metrics = enhanced_calculate_metrics
            
            self.logger.info("Enhanced dashboard features added successfully")
            
        except Exception as e:
            self.logger.error(f"Error adding enhanced dashboard features: {e}")
            raise
    
    async def integrate_with_cost_service(self, cost_service_instance) -> bool:
        """Integrate compatibility layer with existing cost service"""
        try:
            self.logger.info("Integrating with cost service instance")
            
            # Ensure cost analysis compatibility
            cost_compatible = await self.compatibility_manager.ensure_cost_analysis_compatibility(cost_service_instance)
            
            if not cost_compatible:
                self.logger.warning("Cost service compatibility could not be fully ensured")
                return False
            
            self.logger.info("Cost service integration completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error integrating with cost service: {e}")
            return False
    
    async def integrate_with_forecasting_service(self, forecasting_service_instance) -> bool:
        """Integrate compatibility layer with existing forecasting service"""
        try:
            self.logger.info("Integrating with forecasting service instance")
            
            # Ensure forecasting compatibility with enhancements
            forecasting_compatible = await self.compatibility_manager.ensure_forecasting_compatibility(forecasting_service_instance)
            
            if not forecasting_compatible:
                self.logger.warning("Forecasting service compatibility could not be fully ensured")
                return False
            
            self.logger.info("Forecasting service integration completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error integrating with forecasting service: {e}")
            return False
    
    async def get_integration_status(self) -> Dict[str, Any]:
        """Get current integration status"""
        try:
            status = {
                'integration_active': self.integration_active,
                'enhanced_features_enabled': self.enhanced_features_enabled,
                'compatibility_status': self.compatibility_status,
                'agent_status': {
                    'ui_agent': await self.ui_agent.get_state() if self.ui_agent else None,
                    'cost_agent': await self.cost_agent.get_state() if self.cost_agent else None,
                    'forecasting_agent': await self.forecasting_agent.get_state() if self.forecasting_agent else None
                },
                'compatibility_manager_status': await self.compatibility_manager.get_compatibility_status() if self.compatibility_manager else None,
                'last_updated': datetime.now().isoformat()
            }
            
            return status
            
        except Exception as e:
            self.logger.error(f"Error getting integration status: {e}")
            return {
                'integration_active': False,
                'error': str(e),
                'last_updated': datetime.now().isoformat()
            }
    
    async def enable_enhanced_features(self) -> bool:
        """Enable enhanced agentic features"""
        try:
            self.enhanced_features_enabled = True
            
            # Enable enhanced features in compatibility manager
            if self.compatibility_manager:
                self.compatibility_manager.enable_compatibility_layer()
            
            self.logger.info("Enhanced features enabled")
            return True
            
        except Exception as e:
            self.logger.error(f"Error enabling enhanced features: {e}")
            return False
    
    async def disable_enhanced_features(self) -> bool:
        """Disable enhanced agentic features (fallback to original functionality)"""
        try:
            self.enhanced_features_enabled = False
            
            # Disable enhanced features in compatibility manager
            if self.compatibility_manager:
                self.compatibility_manager.disable_compatibility_layer()
            
            self.logger.info("Enhanced features disabled - using original functionality")
            return True
            
        except Exception as e:
            self.logger.error(f"Error disabling enhanced features: {e}")
            return False
    
    async def shutdown(self) -> None:
        """Shutdown the compatibility integration layer"""
        try:
            self.logger.info("Shutting down compatibility integration layer")
            
            # Shutdown agents
            if self.ui_agent:
                await self.ui_agent.shutdown()
            
            if self.cost_agent:
                await self.cost_agent.shutdown()
            
            if self.forecasting_agent:
                await self.forecasting_agent.shutdown()
            
            # Mark integration as inactive
            self.integration_active = False
            
            self.logger.info("Compatibility integration layer shutdown completed")
            
        except Exception as e:
            self.logger.error(f"Error shutting down compatibility integration: {e}")
    
    def is_integration_active(self) -> bool:
        """Check if integration is active"""
        return self.integration_active
    
    def are_enhanced_features_enabled(self) -> bool:
        """Check if enhanced features are enabled"""
        return self.enhanced_features_enabled