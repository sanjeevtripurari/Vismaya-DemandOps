"""
Forecasting Agent
Autonomous agent for advanced predictive analytics, cost forecasting, and capacity planning
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import numpy as np

from ..core.base_agent import BaseAgent
from ..core.interfaces import ISpecializedAgent, IStrandsFramework, IMCPServer
from ..core.models import (
    AgentCapability, DecisionProposal, AgentMessage, MessageType,
    SystemEvent, SystemEventType
)


class ForecastingAgent(BaseAgent, ISpecializedAgent):
    """
    Specialized agent for advanced forecasting with enhanced capabilities:
    - Machine learning-based cost prediction models
    - Scenario analysis and what-if modeling
    - Capacity planning and growth trend analysis with decision proposals
    """
    
    def __init__(
        self,
        strands_framework: Optional[IStrandsFramework] = None,
        mcp_server: Optional[IMCPServer] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        # Define agent capabilities
        capabilities = [
            AgentCapability(
                name="generate_cost_forecast",
                description="Generate cost forecasts using machine learning models",
                input_schema={
                    "type": "object",
                    "properties": {
                        "historical_data": {"type": "array"},
                        "forecast_period": {"type": "string"},
                        "confidence_level": {"type": "number", "default": 0.95},
                        "include_seasonality": {"type": "boolean", "default": True}
                    }
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "forecast": {"type": "array"},
                        "confidence_intervals": {"type": "object"},
                        "model_accuracy": {"type": "number"},
                        "trend_analysis": {"type": "object"}
                    }
                },
                required_permissions=["cost:GetCostAndUsage", "sagemaker:InvokeEndpoint"]
            ),
            AgentCapability(
                name="perform_scenario_analysis",
                description="Perform what-if scenario analysis for cost planning",
                input_schema={
                    "type": "object",
                    "properties": {
                        "base_scenario": {"type": "object"},
                        "scenarios": {"type": "array"},
                        "variables": {"type": "array"}
                    }
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "scenario_results": {"type": "array"},
                        "best_case": {"type": "object"},
                        "worst_case": {"type": "object"},
                        "recommendations": {"type": "array"}
                    }
                },
                required_permissions=["cost:GetCostAndUsage"]
            ),
            AgentCapability(
                name="analyze_capacity_planning",
                description="Analyze capacity planning requirements and growth trends",
                input_schema={
                    "type": "object",
                    "properties": {
                        "usage_data": {"type": "array"},
                        "growth_assumptions": {"type": "object"},
                        "capacity_constraints": {"type": "object"}
                    }
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "capacity_forecast": {"type": "object"},
                        "scaling_recommendations": {"type": "array"},
                        "cost_implications": {"type": "object"}
                    }
                },
                required_permissions=["cloudwatch:GetMetricStatistics", "cost:GetCostAndUsage"]
            ),
            AgentCapability(
                name="detect_forecast_anomalies",
                description="Detect anomalies in forecast patterns and trends",
                input_schema={
                    "type": "object",
                    "properties": {
                        "forecast_data": {"type": "array"},
                        "actual_data": {"type": "array"},
                        "sensitivity": {"type": "number", "default": 0.1}
                    }
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "anomalies": {"type": "array"},
                        "model_drift": {"type": "number"},
                        "recalibration_needed": {"type": "boolean"}
                    }
                },
                required_permissions=["cost:GetCostAndUsage"]
            )
        ]
        
        # Default configuration
        default_config = {
            "forecast_horizon_days": 90,
            "model_retrain_frequency_days": 7,
            "confidence_level": 0.95,
            "seasonality_detection": True,
            "trend_detection_sensitivity": 0.05,
            "scenario_analysis_enabled": True,
            "capacity_planning_enabled": True,
            "ml_models": {
                "primary": "linear_regression",
                "fallback": "moving_average",
                "ensemble": True
            }
        }
        
        if config:
            default_config.update(config)
        
        super().__init__(
            agent_id="forecasting_agent",
            agent_type="forecasting",
            capabilities=capabilities,
            config=default_config,
            strands_framework=strands_framework,
            mcp_server=mcp_server
        )
        
        # Forecasting specific state
        self.forecast_models = {}
        self.historical_data_cache = {}
        self.forecast_cache = {}
        self.model_performance_metrics = {}
        self.scenario_templates = {}
        
        # Setup specialized handlers
        self._setup_forecasting_handlers()
    
    @property
    def domain(self) -> str:
        """Get agent domain"""
        return "forecasting"
    
    def _setup_forecasting_handlers(self) -> None:
        """Setup forecasting specific message and action handlers"""
        # Add specialized action handlers
        self.action_handlers.update({
            "generate_cost_forecast": self._action_generate_cost_forecast,
            "perform_scenario_analysis": self._action_perform_scenario_analysis,
            "analyze_capacity_planning": self._action_analyze_capacity_planning,
            "detect_forecast_anomalies": self._action_detect_forecast_anomalies,
            "update_forecast_models": self._action_update_forecast_models,
            "get_forecast_accuracy": self._action_get_forecast_accuracy,
            "create_scenario_template": self._action_create_scenario_template
        })
        
        # Add specialized message handlers
        self.message_handlers.update({
            "forecast_request": self._handle_forecast_request,
            "model_update_required": self._handle_model_update_required,
            "capacity_alert": self._handle_capacity_alert
        })
    
    async def _agent_specific_initialization(self) -> None:
        """Initialize forecasting specific components"""
        try:
            self.logger.info("Initializing forecasting agent components")
            
            # Initialize ML models
            await self._initialize_forecast_models()
            
            # Initialize scenario templates
            await self._initialize_scenario_templates()
            
            # Load historical data
            await self._load_historical_data()
            
            # Start background tasks
            asyncio.create_task(self._model_training_loop())
            asyncio.create_task(self._forecast_generation_loop())
            asyncio.create_task(self._model_performance_monitoring_loop())
            
            self.logger.info("Forecasting agent initialization completed")
            
        except Exception as e:
            self.logger.error(f"Error in forecasting agent initialization: {e}")
            raise
    
    async def analyze_domain_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze forecasting domain data"""
        try:
            historical_data = data.get("historical_data", [])
            forecast_period = data.get("forecast_period", "30_days")
            include_trends = data.get("include_trends", True)
            
            # Generate forecast
            forecast_result = await self._generate_ml_forecast(historical_data, forecast_period)
            
            # Analyze trends
            trend_analysis = await self._analyze_trends(historical_data) if include_trends else {}
            
            # Detect seasonality
            seasonality_analysis = await self._detect_seasonality(historical_data)
            
            # Calculate forecast accuracy
            accuracy_metrics = await self._calculate_forecast_accuracy(historical_data)
            
            return {
                "forecast": forecast_result,
                "trend_analysis": trend_analysis,
                "seasonality_analysis": seasonality_analysis,
                "accuracy_metrics": accuracy_metrics,
                "timestamp": datetime.now().isoformat(),
                "data_points": len(historical_data)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing forecasting domain data: {e}")
            raise
    
    async def generate_recommendations(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate forecasting-based recommendations"""
        try:
            forecast_data = context.get("forecast_data", {})
            budget_constraints = context.get("budget_constraints", {})
            capacity_data = context.get("capacity_data", {})
            
            recommendations = []
            
            # Generate budget-based recommendations
            budget_recs = await self._generate_budget_forecast_recommendations(forecast_data, budget_constraints)
            recommendations.extend(budget_recs)
            
            # Generate capacity planning recommendations
            capacity_recs = await self._generate_capacity_recommendations(forecast_data, capacity_data)
            recommendations.extend(capacity_recs)
            
            # Generate trend-based recommendations
            trend_recs = await self._generate_trend_recommendations(forecast_data)
            recommendations.extend(trend_recs)
            
            # Generate scenario-based recommendations
            scenario_recs = await self._generate_scenario_recommendations(forecast_data)
            recommendations.extend(scenario_recs)
            
            # Sort by potential impact and confidence
            recommendations.sort(key=lambda x: (x.get("confidence_score", 0), x.get("potential_impact", 0)), reverse=True)
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error generating recommendations: {e}")
            return []
    
    async def create_decision_proposal(self, recommendation: Dict[str, Any]) -> DecisionProposal:
        """Create decision proposal from forecasting recommendation"""
        try:
            # Calculate impact analysis
            impact_analysis = await self._calculate_forecasting_recommendation_impact(recommendation)
            
            # Determine required approvers based on forecast confidence and impact
            required_approvers = self._determine_required_approvers(impact_analysis, recommendation)
            
            # Create proposal
            proposal = DecisionProposal(
                proposal_id=f"forecast_rec_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                title=recommendation.get("title", "Forecasting-Based Recommendation"),
                description=recommendation.get("description", ""),
                impact_analysis=impact_analysis,
                recommendations=[recommendation.get("action", "")],
                required_approvers=required_approvers,
                created_by=self.agent_id,
                created_at=datetime.now(),
                status="pending",
                approval_deadline=datetime.now() + timedelta(days=10),
                estimated_cost_impact=impact_analysis.get("cost_impact", 0),
                risk_level=recommendation.get("risk_level", "medium")
            )
            
            # Store proposal in memory
            if self.strands_framework:
                await self.strands_framework.store_decision_history(proposal)
            
            return proposal
            
        except Exception as e:
            self.logger.error(f"Error creating decision proposal: {e}")
            raise   
 # Action handlers
    async def _action_generate_cost_forecast(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate cost forecast action"""
        try:
            historical_data = parameters.get("historical_data", [])
            forecast_period = parameters.get("forecast_period", "30_days")
            confidence_level = parameters.get("confidence_level", self.config.get("confidence_level", 0.95))
            include_seasonality = parameters.get("include_seasonality", True)
            
            # Generate forecast
            forecast_result = await self._generate_ml_forecast(historical_data, forecast_period, confidence_level, include_seasonality)
            
            # Calculate confidence intervals
            confidence_intervals = await self._calculate_confidence_intervals(forecast_result, confidence_level)
            
            # Analyze model accuracy
            model_accuracy = await self._calculate_model_accuracy(historical_data, forecast_result)
            
            # Perform trend analysis
            trend_analysis = await self._analyze_trends(historical_data)
            
            return {
                "success": True,
                "forecast": forecast_result,
                "confidence_intervals": confidence_intervals,
                "model_accuracy": model_accuracy,
                "trend_analysis": trend_analysis,
                "forecast_period": forecast_period,
                "confidence_level": confidence_level
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _action_perform_scenario_analysis(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Perform scenario analysis action"""
        try:
            base_scenario = parameters.get("base_scenario", {})
            scenarios = parameters.get("scenarios", [])
            variables = parameters.get("variables", [])
            
            # Perform scenario analysis
            scenario_results = await self._perform_scenario_analysis(base_scenario, scenarios, variables)
            
            # Identify best and worst case scenarios
            best_case = max(scenario_results, key=lambda x: x.get("outcome_score", 0)) if scenario_results else {}
            worst_case = min(scenario_results, key=lambda x: x.get("outcome_score", 0)) if scenario_results else {}
            
            # Generate recommendations based on scenarios
            recommendations = await self._generate_scenario_based_recommendations(scenario_results)
            
            return {
                "success": True,
                "scenario_results": scenario_results,
                "best_case": best_case,
                "worst_case": worst_case,
                "recommendations": recommendations,
                "scenarios_analyzed": len(scenarios)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _action_analyze_capacity_planning(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze capacity planning action"""
        try:
            usage_data = parameters.get("usage_data", [])
            growth_assumptions = parameters.get("growth_assumptions", {})
            capacity_constraints = parameters.get("capacity_constraints", {})
            
            # Perform capacity analysis
            capacity_forecast = await self._analyze_capacity_requirements(usage_data, growth_assumptions)
            
            # Generate scaling recommendations
            scaling_recommendations = await self._generate_scaling_recommendations(capacity_forecast, capacity_constraints)
            
            # Calculate cost implications
            cost_implications = await self._calculate_capacity_cost_implications(capacity_forecast, scaling_recommendations)
            
            return {
                "success": True,
                "capacity_forecast": capacity_forecast,
                "scaling_recommendations": scaling_recommendations,
                "cost_implications": cost_implications,
                "analysis_period": growth_assumptions.get("period", "12_months")
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _action_detect_forecast_anomalies(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Detect forecast anomalies action"""
        try:
            forecast_data = parameters.get("forecast_data", [])
            actual_data = parameters.get("actual_data", [])
            sensitivity = parameters.get("sensitivity", 0.1)
            
            # Detect anomalies
            anomalies = await self._detect_forecast_anomalies(forecast_data, actual_data, sensitivity)
            
            # Calculate model drift
            model_drift = await self._calculate_model_drift(forecast_data, actual_data)
            
            # Determine if recalibration is needed
            recalibration_needed = model_drift > 0.15  # 15% drift threshold
            
            return {
                "success": True,
                "anomalies": anomalies,
                "anomaly_count": len(anomalies),
                "model_drift": model_drift,
                "recalibration_needed": recalibration_needed,
                "sensitivity_used": sensitivity
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _action_update_forecast_models(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Update forecast models action"""
        try:
            model_type = parameters.get("model_type", "all")
            training_data = parameters.get("training_data", [])
            force_retrain = parameters.get("force_retrain", False)
            
            # Update models
            updated_models = await self._update_forecast_models(model_type, training_data, force_retrain)
            
            # Calculate new performance metrics
            performance_metrics = await self._calculate_model_performance(updated_models)
            
            return {
                "success": True,
                "updated_models": updated_models,
                "performance_metrics": performance_metrics,
                "retrain_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _action_get_forecast_accuracy(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get forecast accuracy action"""
        try:
            model_name = parameters.get("model_name", "primary")
            time_period = parameters.get("time_period", "30_days")
            
            # Get accuracy metrics
            accuracy_metrics = self.model_performance_metrics.get(model_name, {})
            
            # Get recent forecast performance
            recent_performance = await self._get_recent_forecast_performance(model_name, time_period)
            
            return {
                "success": True,
                "accuracy_metrics": accuracy_metrics,
                "recent_performance": recent_performance,
                "model_name": model_name,
                "evaluation_period": time_period
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _action_create_scenario_template(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Create scenario template action"""
        try:
            template_name = parameters.get("template_name")
            template_config = parameters.get("template_config", {})
            
            if not template_name:
                return {"success": False, "error": "template_name is required"}
            
            # Create scenario template
            self.scenario_templates[template_name] = {
                "config": template_config,
                "created_at": datetime.now().isoformat(),
                "created_by": self.agent_id
            }
            
            # Store in Strands framework
            if self.strands_framework:
                await self.strands_framework.update_context(
                    self.agent_id,
                    {"scenario_templates": self.scenario_templates}
                )
            
            return {
                "success": True,
                "template_name": template_name,
                "template_created": True
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # Message handlers
    async def _handle_forecast_request(self, message: AgentMessage) -> AgentMessage:
        """Handle forecast request messages"""
        try:
            request_data = message.content
            forecast_type = request_data.get("forecast_type", "cost")
            
            # Process forecast request
            if forecast_type == "cost":
                result = await self._action_generate_cost_forecast(request_data)
            elif forecast_type == "capacity":
                result = await self._action_analyze_capacity_planning(request_data)
            else:
                result = {"success": False, "error": f"Unknown forecast type: {forecast_type}"}
            
            return AgentMessage(
                sender=self.agent_id,
                recipient=message.sender,
                message_type=MessageType.RESPONSE,
                content=result,
                correlation_id=message.correlation_id
            )
            
        except Exception as e:
            self.logger.error(f"Error handling forecast request: {e}")
            return AgentMessage(
                sender=self.agent_id,
                recipient=message.sender,
                message_type=MessageType.ERROR,
                content={"error": str(e)},
                correlation_id=message.correlation_id
            )
    
    async def _handle_model_update_required(self, message: AgentMessage) -> AgentMessage:
        """Handle model update required messages"""
        try:
            update_data = message.content
            model_type = update_data.get("model_type", "all")
            
            # Update models
            result = await self._action_update_forecast_models({
                "model_type": model_type,
                "force_retrain": True
            })
            
            return AgentMessage(
                sender=self.agent_id,
                recipient=message.sender,
                message_type=MessageType.RESPONSE,
                content=result,
                correlation_id=message.correlation_id
            )
            
        except Exception as e:
            self.logger.error(f"Error handling model update: {e}")
            return AgentMessage(
                sender=self.agent_id,
                recipient=message.sender,
                message_type=MessageType.ERROR,
                content={"error": str(e)},
                correlation_id=message.correlation_id
            )
    
    async def _handle_capacity_alert(self, message: AgentMessage) -> AgentMessage:
        """Handle capacity alert messages"""
        try:
            alert_data = message.content
            
            # Generate capacity recommendations
            recommendations = await self._generate_capacity_alert_recommendations(alert_data)
            
            # Create decision proposals for high-priority recommendations
            for rec in recommendations[:2]:  # Top 2 recommendations
                if rec.get("priority_score", 0) > 7:
                    proposal = await self.create_decision_proposal(rec)
                    
                    # Send to approval agent
                    if self.mcp_server:
                        approval_message = AgentMessage(
                            sender=self.agent_id,
                            recipient="approval_agent",
                            message_type=MessageType.REQUEST,
                            content={
                                "action": "process_proposal",
                                "proposal": proposal.__dict__,
                                "priority": "high"
                            }
                        )
                        
                        await self.mcp_server.route_message(approval_message)
            
            return AgentMessage(
                sender=self.agent_id,
                recipient=message.sender,
                message_type=MessageType.RESPONSE,
                content={
                    "status": "capacity_alert_processed",
                    "recommendations_generated": len(recommendations)
                },
                correlation_id=message.correlation_id
            )
            
        except Exception as e:
            self.logger.error(f"Error handling capacity alert: {e}")
            return AgentMessage(
                sender=self.agent_id,
                recipient=message.sender,
                message_type=MessageType.ERROR,
                content={"error": str(e)},
                correlation_id=message.correlation_id
            )
    
    # Helper methods
    async def _initialize_forecast_models(self) -> None:
        """Initialize ML forecast models"""
        try:
            # Initialize different model types
            self.forecast_models = {
                "linear_regression": {
                    "type": "linear_regression",
                    "trained": False,
                    "accuracy": 0.0,
                    "last_trained": None
                },
                "moving_average": {
                    "type": "moving_average",
                    "window_size": 7,
                    "trained": True,
                    "accuracy": 0.75,
                    "last_trained": datetime.now()
                },
                "seasonal_decomposition": {
                    "type": "seasonal_decomposition",
                    "trained": False,
                    "accuracy": 0.0,
                    "last_trained": None
                }
            }
            
            self.logger.info("Forecast models initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing forecast models: {e}")
            raise
    
    async def _initialize_scenario_templates(self) -> None:
        """Initialize scenario analysis templates"""
        try:
            self.scenario_templates = {
                "growth_scenarios": {
                    "config": {
                        "variables": ["user_growth", "usage_per_user", "service_expansion"],
                        "scenarios": [
                            {"name": "conservative", "growth_rate": 0.1},
                            {"name": "moderate", "growth_rate": 0.25},
                            {"name": "aggressive", "growth_rate": 0.5}
                        ]
                    },
                    "created_at": datetime.now().isoformat()
                },
                "cost_optimization": {
                    "config": {
                        "variables": ["reserved_instances", "spot_usage", "rightsizing"],
                        "scenarios": [
                            {"name": "minimal_optimization", "savings_rate": 0.05},
                            {"name": "moderate_optimization", "savings_rate": 0.15},
                            {"name": "aggressive_optimization", "savings_rate": 0.30}
                        ]
                    },
                    "created_at": datetime.now().isoformat()
                }
            }
            
            self.logger.info("Scenario templates initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing scenario templates: {e}")
            raise
    
    async def _load_historical_data(self) -> None:
        """Load historical data for model training"""
        try:
            # Simulate loading historical cost data
            import random
            from datetime import datetime, timedelta
            
            # Generate 90 days of historical data
            historical_data = []
            base_cost = 1000
            
            for i in range(90):
                date = datetime.now() - timedelta(days=90-i)
                
                # Add trend, seasonality, and noise
                trend = i * 2  # Slight upward trend
                seasonality = 100 * np.sin(2 * np.pi * i / 7)  # Weekly seasonality
                noise = random.uniform(-50, 50)
                
                daily_cost = base_cost + trend + seasonality + noise
                
                historical_data.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "cost": max(0, daily_cost),  # Ensure non-negative
                    "usage_metrics": {
                        "compute_hours": random.uniform(100, 500),
                        "storage_gb": random.uniform(1000, 5000),
                        "data_transfer_gb": random.uniform(50, 200)
                    }
                })
            
            self.historical_data_cache["cost_data"] = historical_data
            
            self.logger.info(f"Loaded {len(historical_data)} days of historical data")
            
        except Exception as e:
            self.logger.error(f"Error loading historical data: {e}")
            raise
    
    async def _model_training_loop(self) -> None:
        """Model training background loop"""
        retrain_frequency = self.config.get("model_retrain_frequency_days", 7)
        
        while self._state.status != "offline":
            try:
                await asyncio.sleep(retrain_frequency * 24 * 3600)  # Convert days to seconds
                
                # Retrain models
                await self._retrain_forecast_models()
                
            except Exception as e:
                self.logger.error(f"Error in model training loop: {e}")
    
    async def _forecast_generation_loop(self) -> None:
        """Forecast generation background loop"""
        while self._state.status != "offline":
            try:
                await asyncio.sleep(3600)  # Generate forecasts every hour
                
                # Generate updated forecasts
                await self._generate_periodic_forecasts()
                
            except Exception as e:
                self.logger.error(f"Error in forecast generation loop: {e}")
    
    async def _model_performance_monitoring_loop(self) -> None:
        """Model performance monitoring background loop"""
        while self._state.status != "offline":
            try:
                await asyncio.sleep(6 * 3600)  # Monitor every 6 hours
                
                # Monitor model performance
                await self._monitor_model_performance()
                
            except Exception as e:
                self.logger.error(f"Error in model performance monitoring loop: {e}")
    
    async def _generate_ml_forecast(self, historical_data: List[Dict[str, Any]], forecast_period: str, 
                                  confidence_level: float = 0.95, include_seasonality: bool = True) -> Dict[str, Any]:
        """Generate ML-based forecast"""
        try:
            if not historical_data:
                historical_data = self.historical_data_cache.get("cost_data", [])
            
            if not historical_data:
                raise ValueError("No historical data available for forecasting")
            
            # Extract time series data
            dates = [item["date"] for item in historical_data]
            values = [item["cost"] for item in historical_data]
            
            # Determine forecast horizon
            horizon_days = self._parse_forecast_period(forecast_period)
            
            # Use primary model for forecasting
            primary_model = self.config.get("ml_models", {}).get("primary", "linear_regression")
            
            if primary_model == "linear_regression":
                forecast = await self._linear_regression_forecast(values, horizon_days)
            elif primary_model == "moving_average":
                forecast = await self._moving_average_forecast(values, horizon_days)
            else:
                # Fallback to moving average
                forecast = await self._moving_average_forecast(values, horizon_days)
            
            # Add seasonality if requested
            if include_seasonality:
                forecast = await self._add_seasonality_to_forecast(forecast, historical_data)
            
            # Generate forecast dates
            last_date = datetime.strptime(dates[-1], "%Y-%m-%d")
            forecast_dates = [(last_date + timedelta(days=i+1)).strftime("%Y-%m-%d") for i in range(horizon_days)]
            
            # Combine forecast with dates
            forecast_result = [
                {"date": date, "forecasted_cost": cost, "confidence": confidence_level}
                for date, cost in zip(forecast_dates, forecast)
            ]
            
            return {
                "forecast_data": forecast_result,
                "model_used": primary_model,
                "forecast_horizon_days": horizon_days,
                "total_forecasted_cost": sum(forecast),
                "average_daily_cost": sum(forecast) / len(forecast) if forecast else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error generating ML forecast: {e}")
            raise
    
    async def _linear_regression_forecast(self, values: List[float], horizon_days: int) -> List[float]:
        """Generate forecast using linear regression"""
        try:
            # Simple linear regression implementation
            n = len(values)
            x = list(range(n))
            
            # Calculate slope and intercept
            x_mean = sum(x) / n
            y_mean = sum(values) / n
            
            numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
            denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
            
            slope = numerator / denominator if denominator != 0 else 0
            intercept = y_mean - slope * x_mean
            
            # Generate forecast
            forecast = []
            for i in range(horizon_days):
                future_x = n + i
                forecasted_value = slope * future_x + intercept
                forecast.append(max(0, forecasted_value))  # Ensure non-negative
            
            return forecast
            
        except Exception as e:
            self.logger.error(f"Error in linear regression forecast: {e}")
            return [values[-1]] * horizon_days  # Fallback to last known value
    
    async def _moving_average_forecast(self, values: List[float], horizon_days: int) -> List[float]:
        """Generate forecast using moving average"""
        try:
            window_size = min(7, len(values))  # Use 7-day window or available data
            
            if len(values) < window_size:
                # Not enough data, use simple average
                avg_value = sum(values) / len(values)
                return [avg_value] * horizon_days
            
            # Calculate moving average
            recent_values = values[-window_size:]
            moving_avg = sum(recent_values) / window_size
            
            # Simple forecast: extend moving average
            return [moving_avg] * horizon_days
            
        except Exception as e:
            self.logger.error(f"Error in moving average forecast: {e}")
            return [values[-1]] * horizon_days  # Fallback to last known value
    
    async def _add_seasonality_to_forecast(self, forecast: List[float], historical_data: List[Dict[str, Any]]) -> List[float]:
        """Add seasonality patterns to forecast"""
        try:
            # Extract historical values for seasonality analysis
            values = [item["cost"] for item in historical_data]
            
            # Simple weekly seasonality (7-day cycle)
            if len(values) >= 14:  # Need at least 2 weeks of data
                weekly_pattern = []
                for day_of_week in range(7):
                    day_values = [values[i] for i in range(day_of_week, len(values), 7)]
                    if day_values:
                        avg_for_day = sum(day_values) / len(day_values)
                        overall_avg = sum(values) / len(values)
                        seasonal_factor = avg_for_day / overall_avg if overall_avg > 0 else 1.0
                        weekly_pattern.append(seasonal_factor)
                    else:
                        weekly_pattern.append(1.0)
                
                # Apply seasonality to forecast
                seasonal_forecast = []
                for i, base_value in enumerate(forecast):
                    day_of_week = i % 7
                    seasonal_value = base_value * weekly_pattern[day_of_week]
                    seasonal_forecast.append(seasonal_value)
                
                return seasonal_forecast
            
            return forecast  # Return original forecast if not enough data for seasonality
            
        except Exception as e:
            self.logger.error(f"Error adding seasonality to forecast: {e}")
            return forecast
    
    def _parse_forecast_period(self, forecast_period: str) -> int:
        """Parse forecast period string to days"""
        period_map = {
            "7_days": 7,
            "14_days": 14,
            "30_days": 30,
            "60_days": 60,
            "90_days": 90,
            "180_days": 180,
            "365_days": 365
        }
        
        return period_map.get(forecast_period, 30)  # Default to 30 days
    
    async def _calculate_confidence_intervals(self, forecast_result: Dict[str, Any], confidence_level: float) -> Dict[str, Any]:
        """Calculate confidence intervals for forecast"""
        try:
            forecast_data = forecast_result.get("forecast_data", [])
            
            if not forecast_data:
                return {"lower_bound": [], "upper_bound": []}
            
            # Simple confidence interval calculation (±20% for demonstration)
            confidence_margin = 0.2  # 20% margin
            
            lower_bound = []
            upper_bound = []
            
            for item in forecast_data:
                forecasted_cost = item.get("forecasted_cost", 0)
                margin = forecasted_cost * confidence_margin
                
                lower_bound.append({
                    "date": item.get("date"),
                    "lower_cost": max(0, forecasted_cost - margin)
                })
                
                upper_bound.append({
                    "date": item.get("date"),
                    "upper_cost": forecasted_cost + margin
                })
            
            return {
                "lower_bound": lower_bound,
                "upper_bound": upper_bound,
                "confidence_level": confidence_level,
                "margin_percentage": confidence_margin * 100
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating confidence intervals: {e}")
            return {"lower_bound": [], "upper_bound": []}
    
    async def _calculate_model_accuracy(self, historical_data: List[Dict[str, Any]], forecast_result: Dict[str, Any]) -> float:
        """Calculate model accuracy using historical data"""
        try:
            if len(historical_data) < 14:  # Need at least 2 weeks for accuracy calculation
                return 0.0
            
            # Use last 7 days for accuracy testing
            test_data = historical_data[-7:]
            train_data = historical_data[:-7]
            
            # Generate forecast for test period
            test_forecast = await self._generate_ml_forecast(train_data, "7_days")
            
            if not test_forecast.get("forecast_data"):
                return 0.0
            
            # Calculate Mean Absolute Percentage Error (MAPE)
            actual_values = [item["cost"] for item in test_data]
            forecasted_values = [item["forecasted_cost"] for item in test_forecast["forecast_data"]]
            
            if len(actual_values) != len(forecasted_values):
                return 0.0
            
            mape_sum = 0
            valid_points = 0
            
            for actual, forecasted in zip(actual_values, forecasted_values):
                if actual > 0:  # Avoid division by zero
                    mape_sum += abs((actual - forecasted) / actual)
                    valid_points += 1
            
            if valid_points == 0:
                return 0.0
            
            mape = mape_sum / valid_points
            accuracy = max(0, 1 - mape)  # Convert MAPE to accuracy (0-1 scale)
            
            return accuracy
            
        except Exception as e:
            self.logger.error(f"Error calculating model accuracy: {e}")
            return 0.0
    
    async def _analyze_trends(self, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze trends in historical data"""
        try:
            if len(historical_data) < 7:
                return {"trend": "insufficient_data"}
            
            values = [item["cost"] for item in historical_data]
            
            # Calculate trend using linear regression
            n = len(values)
            x = list(range(n))
            
            x_mean = sum(x) / n
            y_mean = sum(values) / n
            
            numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
            denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
            
            slope = numerator / denominator if denominator != 0 else 0
            
            # Determine trend direction and strength
            if abs(slope) < 1:
                trend_direction = "stable"
                trend_strength = "weak"
            elif slope > 1:
                trend_direction = "increasing"
                trend_strength = "strong" if slope > 5 else "moderate"
            else:
                trend_direction = "decreasing"
                trend_strength = "strong" if slope < -5 else "moderate"
            
            # Calculate trend percentage
            if len(values) >= 2:
                first_period_avg = sum(values[:len(values)//2]) / (len(values)//2)
                second_period_avg = sum(values[len(values)//2:]) / (len(values) - len(values)//2)
                trend_percentage = ((second_period_avg - first_period_avg) / first_period_avg) * 100 if first_period_avg > 0 else 0
            else:
                trend_percentage = 0
            
            return {
                "trend": trend_direction,
                "strength": trend_strength,
                "slope": slope,
                "trend_percentage": trend_percentage,
                "analysis_period_days": len(values)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing trends: {e}")
            return {"trend": "error", "error": str(e)}
    
    async def _detect_seasonality(self, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect seasonality patterns in historical data"""
        try:
            if len(historical_data) < 14:  # Need at least 2 weeks
                return {"seasonality_detected": False, "reason": "insufficient_data"}
            
            values = [item["cost"] for item in historical_data]
            
            # Check for weekly seasonality (7-day cycle)
            weekly_correlation = await self._calculate_seasonal_correlation(values, 7)
            
            # Check for monthly seasonality (30-day cycle) if enough data
            monthly_correlation = 0
            if len(values) >= 60:
                monthly_correlation = await self._calculate_seasonal_correlation(values, 30)
            
            seasonality_detected = weekly_correlation > 0.3 or monthly_correlation > 0.3
            
            return {
                "seasonality_detected": seasonality_detected,
                "weekly_correlation": weekly_correlation,
                "monthly_correlation": monthly_correlation,
                "dominant_cycle": "weekly" if weekly_correlation > monthly_correlation else "monthly",
                "strength": "strong" if max(weekly_correlation, monthly_correlation) > 0.6 else "moderate"
            }
            
        except Exception as e:
            self.logger.error(f"Error detecting seasonality: {e}")
            return {"seasonality_detected": False, "error": str(e)}
    
    async def _calculate_seasonal_correlation(self, values: List[float], cycle_length: int) -> float:
        """Calculate correlation for seasonal patterns"""
        try:
            if len(values) < cycle_length * 2:
                return 0.0
            
            # Compare values at the same position in different cycles
            correlations = []
            
            for offset in range(cycle_length):
                cycle_values = [values[i] for i in range(offset, len(values), cycle_length)]
                
                if len(cycle_values) >= 2:
                    # Calculate correlation between consecutive cycles
                    for i in range(len(cycle_values) - 1):
                        if cycle_values[i] > 0 and cycle_values[i+1] > 0:
                            correlation = min(cycle_values[i], cycle_values[i+1]) / max(cycle_values[i], cycle_values[i+1])
                            correlations.append(correlation)
            
            return sum(correlations) / len(correlations) if correlations else 0.0
            
        except Exception as e:
            self.logger.error(f"Error calculating seasonal correlation: {e}")
            return 0.0
    
    async def _calculate_forecast_accuracy(self, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate overall forecast accuracy metrics"""
        try:
            # Get stored accuracy metrics for different models
            accuracy_metrics = {}
            
            for model_name, model_info in self.forecast_models.items():
                accuracy_metrics[model_name] = {
                    "accuracy": model_info.get("accuracy", 0.0),
                    "last_trained": model_info.get("last_trained"),
                    "trained": model_info.get("trained", False)
                }
            
            # Calculate ensemble accuracy if enabled
            if self.config.get("ml_models", {}).get("ensemble", False):
                individual_accuracies = [info["accuracy"] for info in accuracy_metrics.values() if info["trained"]]
                ensemble_accuracy = sum(individual_accuracies) / len(individual_accuracies) if individual_accuracies else 0.0
                accuracy_metrics["ensemble"] = {
                    "accuracy": ensemble_accuracy,
                    "component_count": len(individual_accuracies)
                }
            
            return accuracy_metrics
            
        except Exception as e:
            self.logger.error(f"Error calculating forecast accuracy: {e}")
            return {}
    
    # Additional helper methods for recommendations and other functionality would continue here...
    async def _generate_budget_forecast_recommendations(self, forecast_data: Dict[str, Any], budget_constraints: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate budget-based forecast recommendations"""
        recommendations = []
        
        forecasted_total = forecast_data.get("total_forecasted_cost", 0)
        budget_limit = budget_constraints.get("monthly_limit", 0)
        
        if forecasted_total > budget_limit:
            overage = forecasted_total - budget_limit
            recommendations.append({
                "title": "Budget Overage Forecast Alert",
                "description": f"Forecast indicates ${overage:.2f} budget overage",
                "action": "Implement cost reduction measures",
                "potential_impact": overage,
                "confidence_score": 0.8,
                "risk_level": "high",
                "priority_score": 9,
                "category": "budget_management"
            })
        
        return recommendations
    
    async def _generate_capacity_recommendations(self, forecast_data: Dict[str, Any], capacity_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate capacity planning recommendations"""
        recommendations = []
        
        recommendations.append({
            "title": "Proactive Capacity Scaling",
            "description": "Forecast indicates need for capacity scaling",
            "action": "Plan capacity increases for projected growth",
            "potential_impact": 500.0,
            "confidence_score": 0.7,
            "risk_level": "medium",
            "priority_score": 7,
            "category": "capacity_planning"
        })
        
        return recommendations
    
    async def _generate_trend_recommendations(self, forecast_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate trend-based recommendations"""
        recommendations = []
        
        recommendations.append({
            "title": "Cost Trend Optimization",
            "description": "Upward cost trend detected in forecast",
            "action": "Investigate and optimize cost drivers",
            "potential_impact": 300.0,
            "confidence_score": 0.6,
            "risk_level": "medium",
            "priority_score": 6,
            "category": "trend_analysis"
        })
        
        return recommendations
    
    async def _generate_scenario_recommendations(self, forecast_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate scenario-based recommendations"""
        recommendations = []
        
        recommendations.append({
            "title": "Scenario Planning Implementation",
            "description": "Multiple scenarios indicate need for flexible planning",
            "action": "Implement scenario-based budgeting",
            "potential_impact": 200.0,
            "confidence_score": 0.5,
            "risk_level": "low",
            "priority_score": 5,
            "category": "scenario_planning"
        })
        
        return recommendations
    
    async def _calculate_forecasting_recommendation_impact(self, recommendation: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate impact analysis for forecasting recommendation"""
        potential_impact = recommendation.get("potential_impact", 0)
        confidence_score = recommendation.get("confidence_score", 0.5)
        risk_level = recommendation.get("risk_level", "medium")
        
        return {
            "cost_impact": potential_impact,
            "confidence": confidence_score,
            "risk_assessment": risk_level,
            "forecast_horizon": "90_days",
            "implementation_timeline": "2-4 weeks",
            "success_metrics": [
                f"Achieve forecasted impact of ${potential_impact}",
                f"Maintain forecast accuracy above {confidence_score*100}%",
                "Implement proactive cost management"
            ]
        }
    
    def _determine_required_approvers(self, impact_analysis: Dict[str, Any], recommendation: Dict[str, Any]) -> List[str]:
        """Determine required approvers for forecasting recommendations"""
        cost_impact = abs(impact_analysis.get("cost_impact", 0))
        confidence = impact_analysis.get("confidence", 0.5)
        
        approvers = []
        
        if cost_impact > 1000 or confidence < 0.3:
            approvers.extend(["ceo", "cto"])
        elif cost_impact > 500 or confidence < 0.6:
            approvers.append("cto")
        else:
            approvers.append("finops_lead")
        
        return approvers
    
    # Placeholder methods for remaining functionality
    async def _perform_scenario_analysis(self, base_scenario: Dict[str, Any], scenarios: List[Dict[str, Any]], variables: List[str]) -> List[Dict[str, Any]]:
        """Perform scenario analysis"""
        return [{"scenario": "example", "outcome_score": 0.7}]
    
    async def _generate_scenario_based_recommendations(self, scenario_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate recommendations based on scenario analysis"""
        return []
    
    async def _analyze_capacity_requirements(self, usage_data: List[Dict[str, Any]], growth_assumptions: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze capacity requirements"""
        return {"capacity_needed": "moderate_increase"}
    
    async def _generate_scaling_recommendations(self, capacity_forecast: Dict[str, Any], capacity_constraints: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate scaling recommendations"""
        return []
    
    async def _calculate_capacity_cost_implications(self, capacity_forecast: Dict[str, Any], scaling_recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate cost implications of capacity changes"""
        return {"estimated_cost_increase": 500.0}
    
    async def _detect_forecast_anomalies(self, forecast_data: List[Dict[str, Any]], actual_data: List[Dict[str, Any]], sensitivity: float) -> List[Dict[str, Any]]:
        """Detect anomalies in forecast vs actual"""
        return []
    
    async def _calculate_model_drift(self, forecast_data: List[Dict[str, Any]], actual_data: List[Dict[str, Any]]) -> float:
        """Calculate model drift"""
        return 0.05
    
    async def _update_forecast_models(self, model_type: str, training_data: List[Dict[str, Any]], force_retrain: bool) -> List[str]:
        """Update forecast models"""
        return ["linear_regression"]
    
    async def _calculate_model_performance(self, updated_models: List[str]) -> Dict[str, Any]:
        """Calculate model performance metrics"""
        return {"accuracy": 0.8}
    
    async def _get_recent_forecast_performance(self, model_name: str, time_period: str) -> Dict[str, Any]:
        """Get recent forecast performance"""
        return {"recent_accuracy": 0.75}
    
    async def _generate_capacity_alert_recommendations(self, alert_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate recommendations for capacity alerts"""
        return []
    
    async def _retrain_forecast_models(self) -> None:
        """Retrain forecast models"""
        self.logger.info("Retraining forecast models")
    
    async def _generate_periodic_forecasts(self) -> None:
        """Generate periodic forecasts"""
        self.logger.info("Generating periodic forecasts")
    
    async def _monitor_model_performance(self) -> None:
        """Monitor model performance"""
        self.logger.info("Monitoring model performance")
    
    # Backward Compatibility Methods
    async def process_cost_estimation_query(self, query: str, context=None) -> Dict[str, Any]:
        """Process cost estimation query (backward compatibility method)"""
        try:
            # Enhanced processing with agent capabilities
            result = await self.execute_action('generate_cost_forecast', {
                'query': query,
                'context': context,
                'enhanced_processing': True
            })
            
            if result.get('success'):
                return result
            else:
                # Fallback to basic processing
                return {
                    'success': True,
                    'response': f"Cost estimation for: {query}",
                    'enhanced': False
                }
                
        except Exception as e:
            self.logger.error(f"Error processing cost estimation query: {e}")
            return {
                'success': False,
                'error': str(e),
                'fallback_response': "Cost estimation temporarily unavailable"
            }
    
    async def get_enhanced_resource_pricing(self, resource_spec, *args, **kwargs) -> Dict[str, Any]:
        """Get enhanced resource pricing (backward compatibility method)"""
        try:
            # Use agent capabilities for enhanced pricing
            result = await self.execute_action('analyze_capacity_planning', {
                'resource_spec': resource_spec,
                'enhanced_analysis': True
            })
            
            if result.get('success'):
                return result
            else:
                return {'error': 'Enhanced pricing unavailable'}
                
        except Exception as e:
            self.logger.error(f"Error getting enhanced resource pricing: {e}")
            return {'error': str(e)}
    
    async def generate_enhanced_chat_response(self, message: str, context=None) -> str:
        """Generate enhanced chat response (backward compatibility method)"""
        try:
            # Use agent capabilities for enhanced responses
            if 'forecast' in message.lower() or 'predict' in message.lower():
                result = await self.execute_action('generate_cost_forecast', {
                    'query': message,
                    'context': context
                })
                
                if result.get('success'):
                    return f"🤖 Enhanced Forecast: {result.get('summary', 'Forecast generated successfully')}"
            
            # Default enhanced response
            return f"🤖 Enhanced Response: I can help with advanced forecasting and cost predictions. {message}"
            
        except Exception as e:
            self.logger.error(f"Error generating enhanced chat response: {e}")
            return f"Enhanced chat response unavailable: {str(e)}"
    
    async def enhance_monthly_projections(self, original_projections: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance monthly projections with agent analysis"""
        try:
            # Add agent-generated insights to projections
            enhanced_projections = original_projections.copy()
            
            # Add ML-based confidence intervals
            if 'monthly_projections' in enhanced_projections:
                for projection in enhanced_projections['monthly_projections']:
                    # Add confidence intervals
                    projected_cost = projection.get('projected_cost', 0)
                    confidence_margin = projected_cost * 0.15  # 15% margin
                    
                    projection['confidence_interval'] = {
                        'lower_bound': max(0, projected_cost - confidence_margin),
                        'upper_bound': projected_cost + confidence_margin,
                        'confidence_level': 0.85
                    }
                    
                    # Add AI insights
                    if projected_cost > original_projections.get('warning_threshold', float('inf')):
                        projection['ai_insight'] = "🤖 High cost projection - consider optimization"
                    elif projection.get('status') == 'HEALTHY':
                        projection['ai_insight'] = "🤖 Projection within expected range"
            
            # Add trend analysis
            enhanced_projections['ai_trend_analysis'] = await self._analyze_projection_trends(original_projections)
            
            # Add scenario analysis
            enhanced_projections['scenario_analysis'] = await self._generate_projection_scenarios(original_projections)
            
            return enhanced_projections
            
        except Exception as e:
            self.logger.error(f"Error enhancing monthly projections: {e}")
            return original_projections
    
    async def _analyze_projection_trends(self, projections: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze trends in projections"""
        try:
            monthly_data = projections.get('monthly_projections', [])
            if len(monthly_data) < 2:
                return {'trend': 'insufficient_data'}
            
            # Calculate trend
            costs = [proj.get('projected_cost', 0) for proj in monthly_data]
            first_half_avg = sum(costs[:len(costs)//2]) / (len(costs)//2)
            second_half_avg = sum(costs[len(costs)//2:]) / (len(costs) - len(costs)//2)
            
            trend_percentage = ((second_half_avg - first_half_avg) / first_half_avg) * 100 if first_half_avg > 0 else 0
            
            if trend_percentage > 10:
                trend_direction = 'increasing'
                trend_strength = 'strong'
            elif trend_percentage > 5:
                trend_direction = 'increasing'
                trend_strength = 'moderate'
            elif trend_percentage < -10:
                trend_direction = 'decreasing'
                trend_strength = 'strong'
            elif trend_percentage < -5:
                trend_direction = 'decreasing'
                trend_strength = 'moderate'
            else:
                trend_direction = 'stable'
                trend_strength = 'weak'
            
            return {
                'trend_direction': trend_direction,
                'trend_strength': trend_strength,
                'trend_percentage': trend_percentage,
                'ai_recommendation': self._get_trend_recommendation(trend_direction, trend_strength)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing projection trends: {e}")
            return {'trend': 'error'}
    
    async def _generate_projection_scenarios(self, projections: Dict[str, Any]) -> Dict[str, Any]:
        """Generate scenario analysis for projections"""
        try:
            base_projection = projections.get('next_month', 0)
            
            scenarios = {
                'optimistic': {
                    'description': 'Cost optimization measures successful',
                    'projected_cost': base_projection * 0.85,
                    'probability': 0.3
                },
                'realistic': {
                    'description': 'Current trends continue',
                    'projected_cost': base_projection,
                    'probability': 0.5
                },
                'pessimistic': {
                    'description': 'Unexpected cost increases',
                    'projected_cost': base_projection * 1.2,
                    'probability': 0.2
                }
            }
            
            return {
                'scenarios': scenarios,
                'recommended_scenario': 'realistic',
                'ai_insight': '🤖 Plan for realistic scenario, prepare for pessimistic'
            }
            
        except Exception as e:
            self.logger.error(f"Error generating projection scenarios: {e}")
            return {}
    
    def _get_trend_recommendation(self, trend_direction: str, trend_strength: str) -> str:
        """Get AI recommendation based on trend analysis"""
        if trend_direction == 'increasing' and trend_strength == 'strong':
            return "🤖 Strong upward trend detected - implement cost controls immediately"
        elif trend_direction == 'increasing' and trend_strength == 'moderate':
            return "🤖 Moderate cost increase trend - monitor and optimize proactively"
        elif trend_direction == 'decreasing':
            return "🤖 Positive cost reduction trend - maintain current optimization efforts"
        else:
            return "🤖 Stable cost trend - good baseline for planning"