"""
Backward Compatibility Layer for Agentic AI System
Ensures all existing functionality is preserved through agent interfaces
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import json

from ..core.interfaces import IAgentCore
from ..agents.user_interface_agent import UserInterfaceAgent
from ..agents.cost_management_agent import CostManagementAgent
from ..agents.forecasting_agent import ForecastingAgent
from ...core.models import UsageSummary, BudgetInfo, CostForecast
from ...services.forecasting_ai_assistant import ForecastingAIAssistant


class BackwardCompatibilityLayer:
    """
    Backward compatibility layer that preserves all existing functionality
    while routing through the new agentic system
    """
    
    def __init__(
        self,
        user_interface_agent: UserInterfaceAgent,
        cost_management_agent: CostManagementAgent,
        forecasting_agent: ForecastingAgent,
        forecasting_ai_assistant: ForecastingAIAssistant
    ):
        self.ui_agent = user_interface_agent
        self.cost_agent = cost_management_agent
        self.forecasting_agent = forecasting_agent
        self.forecasting_ai = forecasting_ai_assistant
        
        self.logger = logging.getLogger(__name__)
        
        # Track compatibility mode
        self.compatibility_mode = True
        self.legacy_endpoints_active = True
        
        # Cache for performance
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes
        
        self.logger.info("Backward compatibility layer initialized")
    
    async def initialize(self) -> bool:
        """Initialize the compatibility layer"""
        try:
            # Ensure all agents are initialized
            agents_to_init = [
                self.ui_agent,
                self.cost_agent,
                self.forecasting_agent
            ]
            
            for agent in agents_to_init:
                if not await agent.initialize():
                    self.logger.error(f"Failed to initialize agent: {agent.agent_id}")
                    return False
            
            self.logger.info("All agents initialized successfully for backward compatibility")
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing backward compatibility layer: {e}")
            return False
    
    # Dashboard Functionality Preservation
    async def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Preserve existing dashboard data retrieval functionality
        Routes through UserInterfaceAgent while maintaining exact same interface
        """
        try:
            # Route through UI agent to get dashboard data
            dashboard_request = {
                "action": "get_dashboard_data",
                "include_metrics": True,
                "include_charts": True,
                "include_alerts": True
            }
            
            result = await self.ui_agent.execute_action("get_dashboard_data", dashboard_request)
            
            if result.get("success"):
                return result.get("result", {})
            else:
                self.logger.error(f"Dashboard data retrieval failed: {result.get('error')}")
                return self._get_fallback_dashboard_data()
                
        except Exception as e:
            self.logger.error(f"Error getting dashboard data: {e}")
            return self._get_fallback_dashboard_data()
    
    async def render_dashboard_metrics(self, usage_summary: UsageSummary) -> Dict[str, Any]:
        """
        Preserve existing dashboard metrics rendering
        Enhanced through UserInterfaceAgent while maintaining compatibility
        """
        try:
            # Route through UI agent for enhanced metrics
            metrics_request = {
                "action": "render_metrics",
                "usage_summary": usage_summary.dict() if hasattr(usage_summary, 'dict') else usage_summary.__dict__,
                "format": "dashboard_compatible"
            }
            
            result = await self.ui_agent.execute_action("render_dashboard_metrics", metrics_request)
            
            if result.get("success"):
                return result.get("result", {})
            else:
                # Fallback to original calculation
                return self._calculate_legacy_metrics(usage_summary)
                
        except Exception as e:
            self.logger.error(f"Error rendering dashboard metrics: {e}")
            return self._calculate_legacy_metrics(usage_summary)
    
    async def handle_chat_interaction(self, message: str, context: Dict[str, Any] = None) -> str:
        """
        Preserve existing chat functionality through UserInterfaceAgent
        Maintains exact same interface while adding agentic capabilities
        """
        try:
            # Route through UI agent for enhanced chat handling
            chat_request = {
                "message": message,
                "context": context or {},
                "compatibility_mode": True,
                "preserve_format": True
            }
            
            result = await self.ui_agent.execute_action("handle_chat", chat_request)
            
            if result.get("success"):
                return result.get("result", {}).get("response", "I'm having trouble processing your request.")
            else:
                return f"I'm having trouble processing your request: {result.get('error', 'Unknown error')}"
                
        except Exception as e:
            self.logger.error(f"Error handling chat interaction: {e}")
            return f"I'm having trouble processing your request: {str(e)}"
    
    # Cost Analysis Functionality Preservation
    async def get_cost_analysis(self, time_period: str = "current_month") -> Dict[str, Any]:
        """
        Preserve existing cost analysis functionality
        Enhanced through CostManagementAgent while maintaining compatibility
        """
        try:
            # Route through cost management agent
            analysis_request = {
                "time_period": time_period,
                "include_breakdown": True,
                "include_trends": True,
                "compatibility_format": True
            }
            
            result = await self.cost_agent.execute_action("analyze_costs", analysis_request)
            
            if result.get("success"):
                return result.get("result", {})
            else:
                self.logger.error(f"Cost analysis failed: {result.get('error')}")
                return self._get_fallback_cost_analysis()
                
        except Exception as e:
            self.logger.error(f"Error getting cost analysis: {e}")
            return self._get_fallback_cost_analysis()
    
    async def get_budget_status(self, budget_info: BudgetInfo) -> Dict[str, Any]:
        """
        Preserve existing budget status functionality
        Enhanced through CostManagementAgent
        """
        try:
            # Route through cost management agent
            budget_request = {
                "budget_info": budget_info.dict() if hasattr(budget_info, 'dict') else budget_info.__dict__,
                "include_alerts": True,
                "include_recommendations": True
            }
            
            result = await self.cost_agent.execute_action("analyze_budget_status", budget_request)
            
            if result.get("success"):
                return result.get("result", {})
            else:
                return self._get_legacy_budget_status(budget_info)
                
        except Exception as e:
            self.logger.error(f"Error getting budget status: {e}")
            return self._get_legacy_budget_status(budget_info)
    
    async def get_cost_optimization_recommendations(self, usage_summary: UsageSummary) -> List[Dict[str, Any]]:
        """
        Preserve existing cost optimization functionality
        Enhanced through CostManagementAgent
        """
        try:
            # Route through cost management agent
            optimization_request = {
                "usage_summary": usage_summary.dict() if hasattr(usage_summary, 'dict') else usage_summary.__dict__,
                "include_impact_analysis": True,
                "compatibility_format": True
            }
            
            result = await self.cost_agent.execute_action("generate_optimization_recommendations", optimization_request)
            
            if result.get("success"):
                return result.get("result", {}).get("recommendations", [])
            else:
                return self._get_legacy_optimization_recommendations(usage_summary)
                
        except Exception as e:
            self.logger.error(f"Error getting optimization recommendations: {e}")
            return self._get_legacy_optimization_recommendations(usage_summary)
    
    # Forecasting Functionality Enhancement
    async def get_cost_forecast(self, historical_data: List[Dict[str, Any]], time_horizon: int = 6) -> CostForecast:
        """
        Enhance existing forecasting functionality through ForecastingAgent
        Maintains compatibility while adding advanced AI capabilities
        """
        try:
            # Route through forecasting agent for enhanced predictions
            forecast_request = {
                "historical_data": historical_data,
                "time_horizon_months": time_horizon,
                "include_scenarios": True,
                "include_confidence_intervals": True,
                "compatibility_mode": True
            }
            
            result = await self.forecasting_agent.execute_action("generate_cost_forecast", forecast_request)
            
            if result.get("success"):
                forecast_data = result.get("result", {})
                return self._convert_to_cost_forecast(forecast_data)
            else:
                return self._get_legacy_cost_forecast(historical_data, time_horizon)
                
        except Exception as e:
            self.logger.error(f"Error getting cost forecast: {e}")
            return self._get_legacy_cost_forecast(historical_data, time_horizon)
    
    async def process_forecasting_query(self, query: str, context: Dict[str, Any] = None) -> str:
        """
        Enhance existing forecasting AI assistant functionality
        Maintains exact same interface while adding advanced capabilities
        """
        try:
            # Use enhanced forecasting AI assistant
            from ...core.models import ForecastingContext
            
            # Create forecasting context
            forecasting_context = ForecastingContext()
            if context:
                if 'usage_summary' in context:
                    forecasting_context.current_usage = context['usage_summary']
                if 'budget_info' in context:
                    forecasting_context.budget_info = context['budget_info']
                if 'cost_forecast' in context:
                    forecasting_context.cost_forecast = context['cost_forecast']
            
            # Process through enhanced AI assistant
            response = await self.forecasting_ai.chat_response(query, forecasting_context)
            return response
            
        except Exception as e:
            self.logger.error(f"Error processing forecasting query: {e}")
            return f"I'm having trouble processing your forecasting request: {str(e)}"
    
    async def get_resource_cost_estimate(self, resource_spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance existing resource cost estimation
        Routes through ForecastingAgent for improved accuracy
        """
        try:
            # Route through forecasting agent
            estimation_request = {
                "resource_specification": resource_spec,
                "include_alternatives": True,
                "include_budget_impact": True,
                "compatibility_format": True
            }
            
            result = await self.forecasting_agent.execute_action("estimate_resource_cost", estimation_request)
            
            if result.get("success"):
                return result.get("result", {})
            else:
                return self._get_legacy_cost_estimate(resource_spec)
                
        except Exception as e:
            self.logger.error(f"Error getting resource cost estimate: {e}")
            return self._get_legacy_cost_estimate(resource_spec)
    
    # UI Component Preservation
    async def render_modern_dashboard_components(self, component_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Preserve existing modern dashboard components
        Enhanced through UserInterfaceAgent
        """
        try:
            # Route through UI agent for enhanced rendering
            render_request = {
                "component_type": component_type,
                "data": data,
                "preserve_styling": True,
                "compatibility_mode": True
            }
            
            result = await self.ui_agent.execute_action("render_dashboard_component", render_request)
            
            if result.get("success"):
                return result.get("result", {})
            else:
                return self._get_legacy_component_render(component_type, data)
                
        except Exception as e:
            self.logger.error(f"Error rendering dashboard component: {e}")
            return self._get_legacy_component_render(component_type, data)
    
    async def handle_conversational_ai_interaction(self, message: str, mode: str = "assistant") -> Dict[str, Any]:
        """
        Preserve existing conversational AI functionality
        Enhanced through UserInterfaceAgent
        """
        try:
            # Route through UI agent for enhanced conversational capabilities
            conversation_request = {
                "message": message,
                "mode": mode,
                "preserve_format": True,
                "include_context": True
            }
            
            result = await self.ui_agent.execute_action("handle_conversational_interaction", conversation_request)
            
            if result.get("success"):
                return result.get("result", {})
            else:
                return self._get_legacy_conversation_response(message, mode)
                
        except Exception as e:
            self.logger.error(f"Error handling conversational AI interaction: {e}")
            return self._get_legacy_conversation_response(message, mode)
    
    # Fallback Methods for Legacy Compatibility
    def _get_fallback_dashboard_data(self) -> Dict[str, Any]:
        """Fallback dashboard data when agents are unavailable"""
        return {
            "metrics": {
                "current_spend": 0.0,
                "budget_utilization": 0.0,
                "forecast": 0.0,
                "trending": "stable"
            },
            "charts": {
                "monthly_trend": [],
                "service_breakdown": []
            },
            "alerts": [],
            "status": "fallback_mode"
        }
    
    def _calculate_legacy_metrics(self, usage_summary: UsageSummary) -> Dict[str, Any]:
        """Calculate metrics using legacy method"""
        try:
            current_spend = usage_summary.budget_info.current_spend if usage_summary.budget_info else 0.0
            budget = usage_summary.budget_info.warning_limit if usage_summary.budget_info else 1000.0
            budget_pct = (current_spend / budget * 100) if budget > 0 else 0.0
            forecast = usage_summary.cost_forecast.forecasted_amount if usage_summary.cost_forecast else current_spend
            
            return {
                "current_spend": current_spend,
                "budget": budget,
                "budget_pct": budget_pct,
                "forecast": forecast,
                "trending": "up" if forecast > current_spend else "stable",
                "has_resources": len(usage_summary.ec2_instances) > 0 if hasattr(usage_summary, 'ec2_instances') else False
            }
        except Exception as e:
            self.logger.error(f"Error calculating legacy metrics: {e}")
            return self._get_fallback_dashboard_data()["metrics"]
    
    def _get_fallback_cost_analysis(self) -> Dict[str, Any]:
        """Fallback cost analysis"""
        return {
            "total_cost": 0.0,
            "service_breakdown": [],
            "trends": [],
            "recommendations": [],
            "status": "fallback_mode"
        }
    
    def _get_legacy_budget_status(self, budget_info: BudgetInfo) -> Dict[str, Any]:
        """Legacy budget status calculation"""
        try:
            utilization = budget_info.utilization_percentage
            status = "healthy"
            
            if utilization > 90:
                status = "critical"
            elif utilization > 80:
                status = "warning"
            elif utilization > 70:
                status = "caution"
            
            return {
                "status": status,
                "utilization_percentage": utilization,
                "current_spend": budget_info.current_spend,
                "warning_limit": budget_info.warning_limit,
                "maximum_limit": budget_info.maximum_limit,
                "alerts": []
            }
        except Exception as e:
            self.logger.error(f"Error calculating legacy budget status: {e}")
            return {"status": "unknown", "utilization_percentage": 0.0}
    
    def _get_legacy_optimization_recommendations(self, usage_summary: UsageSummary) -> List[Dict[str, Any]]:
        """Legacy optimization recommendations"""
        recommendations = []
        
        try:
            # Basic recommendations based on usage summary
            if hasattr(usage_summary, 'ec2_instances') and usage_summary.ec2_instances:
                stopped_instances = [i for i in usage_summary.ec2_instances if i.state.value == "stopped"]
                if stopped_instances:
                    recommendations.append({
                        "type": "terminate_stopped_instances",
                        "title": "Terminate Stopped Instances",
                        "description": f"You have {len(stopped_instances)} stopped instances that are still incurring costs",
                        "potential_savings": len(stopped_instances) * 50,  # Rough estimate
                        "priority": "high"
                    })
            
            if hasattr(usage_summary, 'storage_volumes') and usage_summary.storage_volumes:
                unattached_volumes = [v for v in usage_summary.storage_volumes if not v.attached_instance]
                if unattached_volumes:
                    recommendations.append({
                        "type": "cleanup_unattached_volumes",
                        "title": "Clean Up Unattached Volumes",
                        "description": f"You have {len(unattached_volumes)} unattached EBS volumes",
                        "potential_savings": len(unattached_volumes) * 10,  # Rough estimate
                        "priority": "medium"
                    })
            
        except Exception as e:
            self.logger.error(f"Error generating legacy optimization recommendations: {e}")
        
        return recommendations
    
    def _get_legacy_cost_forecast(self, historical_data: List[Dict[str, Any]], time_horizon: int) -> CostForecast:
        """Legacy cost forecast calculation"""
        try:
            # Simple linear projection
            if not historical_data:
                return CostForecast(
                    base_amount=0.0,
                    forecasted_amount=0.0,
                    confidence_level=0.5,
                    trend_factor=1.0
                )
            
            # Calculate simple trend
            recent_costs = [d.get('cost', 0) for d in historical_data[-3:]]
            if len(recent_costs) >= 2:
                trend = (recent_costs[-1] - recent_costs[0]) / len(recent_costs)
                base_amount = recent_costs[-1]
                forecasted_amount = base_amount + (trend * time_horizon)
            else:
                base_amount = recent_costs[0] if recent_costs else 0.0
                forecasted_amount = base_amount
            
            return CostForecast(
                base_amount=base_amount,
                forecasted_amount=max(0, forecasted_amount),
                confidence_level=0.7,
                trend_factor=forecasted_amount / base_amount if base_amount > 0 else 1.0
            )
            
        except Exception as e:
            self.logger.error(f"Error generating legacy cost forecast: {e}")
            return CostForecast(
                base_amount=0.0,
                forecasted_amount=0.0,
                confidence_level=0.5,
                trend_factor=1.0
            )
    
    def _get_legacy_cost_estimate(self, resource_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Legacy cost estimation"""
        # Simple cost estimation based on resource type
        resource_type = resource_spec.get('resource_type', 'unknown')
        quantity = resource_spec.get('quantity', 1)
        
        # Basic cost estimates (rough approximations)
        base_costs = {
            'ec2': 50.0,  # per instance per month
            'rds': 100.0,  # per instance per month
            'ebs': 0.10,  # per GB per month
            's3': 0.023,  # per GB per month
            'lambda': 0.20  # per million requests
        }
        
        base_cost = base_costs.get(resource_type, 25.0)
        total_cost = base_cost * quantity
        
        return {
            "total_cost": total_cost,
            "monthly_cost": total_cost,
            "resource_type": resource_type,
            "quantity": quantity,
            "confidence": "low",
            "method": "legacy_estimation"
        }
    
    def _get_legacy_component_render(self, component_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Legacy component rendering"""
        return {
            "component_type": component_type,
            "rendered": True,
            "data": data,
            "method": "legacy_render"
        }
    
    def _get_legacy_conversation_response(self, message: str, mode: str) -> Dict[str, Any]:
        """Legacy conversation response"""
        return {
            "response": f"I understand you're asking about: {message}. I'm currently in compatibility mode.",
            "mode": mode,
            "method": "legacy_response"
        }
    
    def _convert_to_cost_forecast(self, forecast_data: Dict[str, Any]) -> CostForecast:
        """Convert agent response to CostForecast object"""
        try:
            return CostForecast(
                base_amount=forecast_data.get('base_amount', 0.0),
                forecasted_amount=forecast_data.get('forecasted_amount', 0.0),
                confidence_level=forecast_data.get('confidence_level', 0.7),
                trend_factor=forecast_data.get('trend_factor', 1.0),
                monthly_growth_rate=forecast_data.get('monthly_growth_rate', 0.0)
            )
        except Exception as e:
            self.logger.error(f"Error converting to CostForecast: {e}")
            return CostForecast(
                base_amount=0.0,
                forecasted_amount=0.0,
                confidence_level=0.5,
                trend_factor=1.0
            )
    
    # Compatibility Status Methods
    def get_compatibility_status(self) -> Dict[str, Any]:
        """Get current compatibility layer status"""
        return {
            "compatibility_mode": self.compatibility_mode,
            "legacy_endpoints_active": self.legacy_endpoints_active,
            "agents_status": {
                "ui_agent": self.ui_agent.agent_id if self.ui_agent else None,
                "cost_agent": self.cost_agent.agent_id if self.cost_agent else None,
                "forecasting_agent": self.forecasting_agent.agent_id if self.forecasting_agent else None
            },
            "cache_size": len(self._cache),
            "initialized": True
        }
    
    def enable_full_agentic_mode(self):
        """Disable compatibility mode and enable full agentic capabilities"""
        self.compatibility_mode = False
        self.legacy_endpoints_active = False
        self.logger.info("Switched to full agentic mode - compatibility layer disabled")
    
    def enable_compatibility_mode(self):
        """Re-enable compatibility mode"""
        self.compatibility_mode = True
        self.legacy_endpoints_active = True
        self.logger.info("Compatibility mode re-enabled")