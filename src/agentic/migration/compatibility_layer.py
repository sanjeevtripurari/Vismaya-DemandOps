"""
Compatibility Layer for Agentic AI Mistem Migration
Maintains existing API endpoints and functionality during transition
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable, Union
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from ..core.interfaces import IAgentCore
from ..system_factory import AgenticSystemFactory


class CompatibilityMode(Enum):
    """Compatibility modes for different migration phases"""
    LEGACY_ONLY = "legacy_only"
    HYBRID = "hybrid"
    AGENTIC_PREFERRED = "agentic_preferred"
    AGENTIC_ONLY = "agentic_only"


@dataclass
class EndpointMapping:
    """Mapping between legacy and agentic endpoints"""
    legacy_endpoint: str
    agentic_agent: str
    agentic_action: str
    transformation_function: Optional[Callable] = None
    fallback_to_legacy: bool = True
    enabled: bool = True


class CompatibilityLayer:
    """
    Compatibility layer that maintains existing API endpoints while
    gradually routing requests to the agentic system
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # System references
        self.legacy_services: Dict[str, Any] = {}
        self.agentic_system: Optional[AgenticSystemFactory] = None
        
        # Compatibility configuration
        self.mode = CompatibilityMode.LEGACY_ONLY
        self.endpoint_mappings: Dict[str, EndpointMapping] = {}
        
        # Performance tracking
        self.request_metrics: Dict[str, Dict[str, Any]] = {}
        
        # Initialize endpoint mappings
        self._initialize_endpoint_mappings()
    
    def _initialize_endpoint_mappings(self) -> None:
        """Initialize mappings between legacy and agentic endpoints"""
        
        self.endpoint_mappings.update({
            # Cost Analysis Endpoints
            "get_usage_summary": EndpointMapping(
                legacy_endpoint="get_usage_summary",
                agentic_agent="cost_management",
                agentic_action="get_usage_summary",
                transformation_function=self._transform_usage_summary,
                fallback_to_legacy=True
            ),
            "get_cost_insights": EndpointMapping(
                legacy_endpoint="get_cost_insights",
                agentic_agent="cost_management",
                agentic_action="analyze_costs",
                transformation_function=self._transform_cost_insights,
                fallback_to_legacy=True
            ),
            "get_service_costs": EndpointMapping(
                legacy_endpoint="get_service_costs",
                agentic_agent="cost_management",
                agentic_action="get_service_breakdown",
                transformation_function=self._transform_service_costs,
                fallback_to_legacy=True
            ),
            
            # Resource Management Endpoints
            "get_resource_details": EndpointMapping(
                legacy_endpoint="get_resource_details",
                agentic_agent="resource_management",
                agentic_action="get_resource_inventory",
                transformation_function=self._transform_resource_details,
                fallback_to_legacy=True
            ),
            "optimize_resources": EndpointMapping(
                legacy_endpoint="optimize_resources",
                agentic_agent="resource_management",
                agentic_action="generate_optimization_recommendations",
                transformation_function=self._transform_optimization_recommendations,
                fallback_to_legacy=True
            ),
            
            # Forecasting Endpoints
            "analyze_scenario": EndpointMapping(
                legacy_endpoint="analyze_scenario",
                agentic_agent="forecasting",
                agentic_action="analyze_cost_scenario",
                transformation_function=self._transform_scenario_analysis,
                fallback_to_legacy=True
            ),
            "get_cost_forecast": EndpointMapping(
                legacy_endpoint="get_cost_forecast",
                agentic_agent="forecasting",
                agentic_action="generate_cost_forecast",
                transformation_function=self._transform_cost_forecast,
                fallback_to_legacy=True
            ),
            
            # Chat/AI Assistant Endpoints
            "handle_chat": EndpointMapping(
                legacy_endpoint="handle_chat",
                agentic_agent="user_interface",
                agentic_action="process_user_query",
                transformation_function=self._transform_chat_response,
                fallback_to_legacy=True
            ),
            
            # Dashboard Endpoints
            "get_dashboard_data": EndpointMapping(
                legacy_endpoint="get_dashboard_data",
                agentic_agent="orchestrator",
                agentic_action="get_dashboard_summary",
                transformation_function=self._transform_dashboard_data,
                fallback_to_legacy=True
            )
        })
    
    def set_legacy_services(self, services: Dict[str, Any]) -> None:
        """Set references to legacy services"""
        self.legacy_services = services
        self.logger.info(f"Registered {len(services)} legacy services")
    
    def set_agentic_system(self, agentic_system: AgenticSystemFactory) -> None:
        """Set reference to agentic system"""
        self.agentic_system = agentic_system
        self.logger.info("Registered agentic system")
    
    def set_compatibility_mode(self, mode: CompatibilityMode) -> None:
        """Set compatibility mode"""
        self.mode = mode
        self.logger.info(f"Set compatibility mode to: {mode.value}")
    
    def enable_endpoint(self, endpoint_name: str) -> bool:
        """Enable agentic routing for specific endpoint"""
        if endpoint_name in self.endpoint_mappings:
            self.endpoint_mappings[endpoint_name].enabled = True
            self.logger.info(f"Enabled agentic routing for endpoint: {endpoint_name}")
            return True
        return False
    
    def disable_endpoint(self, endpoint_name: str) -> bool:
        """Disable agentic routing for specific endpoint"""
        if endpoint_name in self.endpoint_mappings:
            self.endpoint_mappings[endpoint_name].enabled = False
            self.logger.info(f"Disabled agentic routing for endpoint: {endpoint_name}")
            return True
        return False
    
    async def route_request(self, endpoint: str, parameters: Dict[str, Any], user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Route request to appropriate system (legacy or agentic)
        based on compatibility mode and endpoint configuration
        """
        
        start_time = datetime.now()
        
        try:
            # Check if endpoint has agentic mapping
            mapping = self.endpoint_mappings.get(endpoint)
            
            # Determine routing strategy
            use_agentic = self._should_use_agentic(endpoint, mapping, user_context)
            
            if use_agentic and mapping and self.agentic_system:
                # Route to agentic system
                result = await self._route_to_agentic(mapping, parameters)
                
                # Track success
                self._track_request_metric(endpoint, "agentic", True, start_time)
                
                return result
            
            else:
                # Route to legacy system
                result = await self._route_to_legacy(endpoint, parameters)
                
                # Track success
                self._track_request_metric(endpoint, "legacy", True, start_time)
                
                return result
        
        except Exception as e:
            self.logger.error(f"Error routing request to {endpoint}: {e}")
            
            # Track failure
            self._track_request_metric(endpoint, "agentic" if use_agentic else "legacy", False, start_time)
            
            # Try fallback if agentic failed
            if use_agentic and mapping and mapping.fallback_to_legacy:
                try:
                    self.logger.info(f"Falling back to legacy for {endpoint}")
                    result = await self._route_to_legacy(endpoint, parameters)
                    
                    # Track fallback success
                    self._track_request_metric(endpoint, "legacy_fallback", True, start_time)
                    
                    return result
                
                except Exception as fallback_error:
                    self.logger.error(f"Fallback also failed for {endpoint}: {fallback_error}")
                    self._track_request_metric(endpoint, "legacy_fallback", False, start_time)
            
            # Return error response
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _should_use_agentic(self, endpoint: str, mapping: Optional[EndpointMapping], user_context: Optional[Dict[str, Any]]) -> bool:
        """Determine if request should be routed to agentic system"""
        
        # Check compatibility mode
        if self.mode == CompatibilityMode.LEGACY_ONLY:
            return False
        
        if self.mode == CompatibilityMode.AGENTIC_ONLY:
            return True
        
        # Check if endpoint mapping exists and is enabled
        if not mapping or not mapping.enabled:
            return False
        
        # Check if agentic system is available
        if not self.agentic_system:
            return False
        
        # For hybrid mode, use additional logic
        if self.mode == CompatibilityMode.HYBRID:
            # Could implement user-based rollout, A/B testing, etc.
            # For now, use simple percentage-based rollout
            rollout_percentage = self.config.get("agentic_rollout_percentage", 0)
            
            if user_context and "user_id" in user_context:
                import hashlib
                user_id = user_context["user_id"]
                hash_value = int(hashlib.md5(f"{endpoint}:{user_id}".encode()).hexdigest()[:8], 16)
                percentage = (hash_value % 100) + 1
                return percentage <= rollout_percentage
            
            return rollout_percentage >= 100
        
        # For agentic_preferred mode, prefer agentic but allow fallback
        if self.mode == CompatibilityMode.AGENTIC_PREFERRED:
            return True
        
        return False
    
    async def _route_to_agentic(self, mapping: EndpointMapping, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Route request to agentic system"""
        
        try:
            # Get orchestrator from agentic system
            orchestrator = self.agentic_system.agents.get("orchestrator")
            
            if not orchestrator:
                raise RuntimeError("Orchestrator not available")
            
            # Create agent request
            agent_request = {
                "target_agent": mapping.agentic_agent,
                "action": mapping.agentic_action,
                "parameters": parameters
            }
            
            # Route through orchestrator
            result = await orchestrator.execute_action("route_request", agent_request)
            
            if not result.get("success", False):
                raise RuntimeError(f"Agentic request failed: {result.get('error', 'Unknown error')}")
            
            # Transform result if transformation function exists
            agentic_result = result.get("result", {})
            
            if mapping.transformation_function:
                transformed_result = await mapping.transformation_function(agentic_result, parameters)
                return transformed_result
            
            return agentic_result
        
        except Exception as e:
            self.logger.error(f"Error routing to agentic system: {e}")
            raise
    
    async def _route_to_legacy(self, endpoint: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Route request to legacy system"""
        
        try:
            # Map endpoint to legacy service method
            service_mapping = {
                "get_usage_summary": ("cost_service", "get_usage_summary"),
                "get_cost_insights": ("cost_service", "get_cost_insights"),
                "get_service_costs": ("cost_service", "get_service_costs"),
                "get_resource_details": ("resource_service", "get_resource_details"),
                "optimize_resources": ("resource_service", "optimize_resources"),
                "analyze_scenario": ("forecasting_service", "analyze_scenario"),
                "get_cost_forecast": ("forecasting_service", "get_cost_forecast"),
                "handle_chat": ("ai_assistant", "handle_chat"),
                "get_dashboard_data": ("dashboard_service", "get_dashboard_data")
            }
            
            service_name, method_name = service_mapping.get(endpoint, (None, None))
            
            if not service_name or not method_name:
                raise RuntimeError(f"No legacy mapping for endpoint: {endpoint}")
            
            service = self.legacy_services.get(service_name)
            if not service:
                raise RuntimeError(f"Legacy service not available: {service_name}")
            
            method = getattr(service, method_name, None)
            if not method:
                raise RuntimeError(f"Legacy method not available: {service_name}.{method_name}")
            
            # Call legacy method
            if asyncio.iscoroutinefunction(method):
                result = await method(**parameters)
            else:
                result = method(**parameters)
            
            return result
        
        except Exception as e:
            self.logger.error(f"Error routing to legacy system: {e}")
            raise
    
    def _track_request_metric(self, endpoint: str, system: str, success: bool, start_time: datetime) -> None:
        """Track request metrics for monitoring"""
        
        if endpoint not in self.request_metrics:
            self.request_metrics[endpoint] = {
                "agentic": {"count": 0, "success": 0, "total_time": 0},
                "legacy": {"count": 0, "success": 0, "total_time": 0},
                "legacy_fallback": {"count": 0, "success": 0, "total_time": 0}
            }
        
        duration = (datetime.now() - start_time).total_seconds() * 1000  # milliseconds
        
        metrics = self.request_metrics[endpoint][system]
        metrics["count"] += 1
        metrics["total_time"] += duration
        
        if success:
            metrics["success"] += 1
    
    def get_compatibility_metrics(self) -> Dict[str, Any]:
        """Get compatibility layer metrics"""
        
        summary = {
            "mode": self.mode.value,
            "endpoints": {},
            "overall": {
                "total_requests": 0,
                "agentic_requests": 0,
                "legacy_requests": 0,
                "fallback_requests": 0,
                "success_rate": 0.0
            }
        }
        
        total_requests = 0
        total_success = 0
        
        for endpoint, metrics in self.request_metrics.items():
            endpoint_summary = {
                "agentic": {
                    "count": metrics["agentic"]["count"],
                    "success_rate": metrics["agentic"]["success"] / max(metrics["agentic"]["count"], 1),
                    "avg_response_time": metrics["agentic"]["total_time"] / max(metrics["agentic"]["count"], 1)
                },
                "legacy": {
                    "count": metrics["legacy"]["count"],
                    "success_rate": metrics["legacy"]["success"] / max(metrics["legacy"]["count"], 1),
                    "avg_response_time": metrics["legacy"]["total_time"] / max(metrics["legacy"]["count"], 1)
                },
                "fallback": {
                    "count": metrics["legacy_fallback"]["count"],
                    "success_rate": metrics["legacy_fallback"]["success"] / max(metrics["legacy_fallback"]["count"], 1),
                    "avg_response_time": metrics["legacy_fallback"]["total_time"] / max(metrics["legacy_fallback"]["count"], 1)
                }
            }
            
            summary["endpoints"][endpoint] = endpoint_summary
            
            # Update overall metrics
            endpoint_total = sum(metrics[system]["count"] for system in metrics)
            endpoint_success = sum(metrics[system]["success"] for system in metrics)
            
            total_requests += endpoint_total
            total_success += endpoint_success
            
            summary["overall"]["agentic_requests"] += metrics["agentic"]["count"]
            summary["overall"]["legacy_requests"] += metrics["legacy"]["count"]
            summary["overall"]["fallback_requests"] += metrics["legacy_fallback"]["count"]
        
        summary["overall"]["total_requests"] = total_requests
        summary["overall"]["success_rate"] = total_success / max(total_requests, 1)
        
        return summary
    
    # Transformation functions for converting between legacy and agentic formats
    async def _transform_usage_summary(self, agentic_result: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Transform agentic usage summary to legacy format"""
        # Implementation would transform the data structure
        return agentic_result
    
    async def _transform_cost_insights(self, agentic_result: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Transform agentic cost insights to legacy format"""
        return agentic_result
    
    async def _transform_service_costs(self, agentic_result: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Transform agentic service costs to legacy format"""
        return agentic_result
    
    async def _transform_resource_details(self, agentic_result: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Transform agentic resource details to legacy format"""
        return agentic_result
    
    async def _transform_optimization_recommendations(self, agentic_result: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Transform agentic optimization recommendations to legacy format"""
        return agentic_result
    
    async def _transform_scenario_analysis(self, agentic_result: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Transform agentic scenario analysis to legacy format"""
        return agentic_result
    
    async def _transform_cost_forecast(self, agentic_result: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Transform agentic cost forecast to legacy format"""
        return agentic_result
    
    async def _transform_chat_response(self, agentic_result: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Transform agentic chat response to legacy format"""
        return agentic_result
    
    async def _transform_dashboard_data(self, agentic_result: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Transform agentic dashboard data to legacy format"""
        return agentic_result


class BackwardCompatibilityManager:
    """
    Manager for maintaining backward compatibility during migration
    Ensures existing functionality continues to work
    """
    
    def __init__(self, compatibility_layer: CompatibilityLayer):
        self.compatibility_layer = compatibility_layer
        self.logger = logging.getLogger(__name__)
        
        # Compatibility checks
        self.compatibility_tests: Dict[str, Callable] = {}
        self._initialize_compatibility_tests()
    
    def _initialize_compatibility_tests(self) -> None:
        """Initialize compatibility tests"""
        
        self.compatibility_tests.update({
            "dashboard_functionality": self._test_dashboard_functionality,
            "cost_analysis": self._test_cost_analysis,
            "resource_management": self._test_resource_management,
            "forecasting": self._test_forecasting,
            "ai_assistant": self._test_ai_assistant
        })
    
    async def run_compatibility_tests(self) -> Dict[str, Any]:
        """Run all compatibility tests"""
        
        results = {
            "overall_status": "passed",
            "test_results": {},
            "timestamp": datetime.now().isoformat()
        }
        
        for test_name, test_function in self.compatibility_tests.items():
            try:
                self.logger.info(f"Running compatibility test: {test_name}")
                
                test_result = await test_function()
                results["test_results"][test_name] = {
                    "status": "passed" if test_result else "failed",
                    "details": test_result if isinstance(test_result, dict) else {}
                }
                
                if not test_result:
                    results["overall_status"] = "failed"
                
            except Exception as e:
                self.logger.error(f"Error running compatibility test {test_name}: {e}")
                results["test_results"][test_name] = {
                    "status": "error",
                    "error": str(e)
                }
                results["overall_status"] = "failed"
        
        return results
    
    async def _test_dashboard_functionality(self) -> Union[bool, Dict[str, Any]]:
        """Test dashboard functionality compatibility"""
        
        try:
            # Test key dashboard endpoints
            test_parameters = {}
            
            # Test usage summary
            usage_result = await self.compatibility_layer.route_request("get_usage_summary", test_parameters)
            if not usage_result.get("success", True):
                return False
            
            # Test cost insights
            insights_result = await self.compatibility_layer.route_request("get_cost_insights", test_parameters)
            if not insights_result.get("success", True):
                return False
            
            return {
                "usage_summary": "passed",
                "cost_insights": "passed"
            }
        
        except Exception as e:
            self.logger.error(f"Dashboard compatibility test failed: {e}")
            return False
    
    async def _test_cost_analysis(self) -> Union[bool, Dict[str, Any]]:
        """Test cost analysis compatibility"""
        
        try:
            # Test cost analysis endpoints
            test_parameters = {}
            
            service_costs_result = await self.compatibility_layer.route_request("get_service_costs", test_parameters)
            if not service_costs_result.get("success", True):
                return False
            
            return {"service_costs": "passed"}
        
        except Exception as e:
            self.logger.error(f"Cost analysis compatibility test failed: {e}")
            return False
    
    async def _test_resource_management(self) -> Union[bool, Dict[str, Any]]:
        """Test resource management compatibility"""
        
        try:
            # Test resource management endpoints
            test_parameters = {}
            
            resource_result = await self.compatibility_layer.route_request("get_resource_details", test_parameters)
            if not resource_result.get("success", True):
                return False
            
            return {"resource_details": "passed"}
        
        except Exception as e:
            self.logger.error(f"Resource management compatibility test failed: {e}")
            return False
    
    async def _test_forecasting(self) -> Union[bool, Dict[str, Any]]:
        """Test forecasting compatibility"""
        
        try:
            # Test forecasting endpoints
            test_parameters = {"additional_ec2_instances": 1, "additional_storage_gb": 100}
            
            scenario_result = await self.compatibility_layer.route_request("analyze_scenario", test_parameters)
            if not scenario_result.get("success", True):
                return False
            
            return {"scenario_analysis": "passed"}
        
        except Exception as e:
            self.logger.error(f"Forecasting compatibility test failed: {e}")
            return False
    
    async def _test_ai_assistant(self) -> Union[bool, Dict[str, Any]]:
        """Test AI assistant compatibility"""
        
        try:
            # Test AI assistant endpoints
            test_parameters = {"query": "What is my current AWS spending?"}
            
            chat_result = await self.compatibility_layer.route_request("handle_chat", test_parameters)
            if not chat_result.get("success", True):
                return False
            
            return {"chat_response": "passed"}
        
        except Exception as e:
            self.logger.error(f"AI assistant compatibility test failed: {e}")
            return False