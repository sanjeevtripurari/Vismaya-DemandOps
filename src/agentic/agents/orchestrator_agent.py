"""
Orchestrator Agent implementation
Central coordinator for the agentic AI system
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json

from ..core.interfaces import IOrchestrator, IStrandsFramework, IMCPServer, IWorkflowEngine
from ..core.models import (
    AgentMessage, AgentState, AgentCapability, AgentConfiguration,
    MessageType, WorkflowDefinition, WorkflowStep, SystemEvent,
    MultiAgentTask, TaskResult, SystemHealth, AgentStatus, AgentMetrics
)
from ..core.base_agent import BaseAgent
from ..core.workflow_engine import WorkflowEngine


class OrchestratorAgent(BaseAgent, IOrchestrator):
    """
    Orchestrator Agent - Central coordinator for multi-agent workflows
    Manages agent registry, request routing, and system health monitoring
    """
    
    def __init__(
        self,
        config: Dict[str, Any],
        strands_framework: Optional[IStrandsFramework] = None,
        mcp_server: Optional[IMCPServer] = None
    ):
        # Define orchestrator capabilities
        capabilities = [
            AgentCapability(
                name="route_request",
                description="Route requests to appropriate agents",
                input_schema={
                    "type": "object",
                    "required": ["request_type", "content"],
                    "properties": {
                        "request_type": {"type": "string"},
                        "content": {"type": "object"}
                    }
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "target_agent": {"type": "string"},
                        "routing_decision": {"type": "object"}
                    }
                },
                required_permissions=["agent_coordination", "request_routing"]
            ),
            AgentCapability(
                name="coordinate_workflow",
                description="Coordinate multi-agent workflows",
                input_schema={
                    "type": "object",
                    "required": ["workflow_definition"],
                    "properties": {
                        "workflow_definition": {"type": "object"}
                    }
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "workflow_result": {"type": "object"}
                    }
                },
                required_permissions=["workflow_management", "agent_coordination"]
            ),
            AgentCapability(
                name="monitor_system_health",
                description="Monitor health of all agents in the system",
                input_schema={"type": "object"},
                output_schema={
                    "type": "object",
                    "properties": {
                        "system_health": {"type": "object"}
                    }
                },
                required_permissions=["system_monitoring", "health_check"]
            )
        ]
        
        super().__init__(
            agent_id="orchestrator",
            agent_type="orchestrator",
            capabilities=capabilities,
            config=config,
            strands_framework=strands_framework,
            mcp_server=mcp_server
        )
        
        # Agent registry and health tracking
        self.agent_registry: Dict[str, AgentConfiguration] = {}
        self.agent_health_status: Dict[str, bool] = {}
        self.agent_performance_metrics: Dict[str, AgentMetrics] = {}
        self.agent_last_heartbeat: Dict[str, datetime] = {}
        
        # Workflow management - Initialize workflow engine
        self.workflow_engine: Optional[IWorkflowEngine] = None
        if mcp_server:
            self.workflow_engine = WorkflowEngine(
                mcp_server=mcp_server,
                strands_framework=strands_framework,
                config=config.get("workflow_engine", {})
            )
        
        # Request routing logic with intelligent load balancing
        self.routing_rules: Dict[str, str] = {}
        self.load_balancing_state: Dict[str, int] = {}
        self.agent_response_times: Dict[str, List[float]] = {}  # Track response times for load balancing
        self.agent_failure_counts: Dict[str, int] = {}
        
        # System monitoring and health management
        self.system_health = SystemHealth()
        self.health_check_interval = config.get("health_check_interval", 30)
        self.performance_monitoring_interval = config.get("performance_monitoring_interval", 60)
        self.system_alerts: List[Dict[str, Any]] = []
        
        # Advanced routing configuration
        self.routing_strategy = config.get("routing_strategy", "round_robin")  # round_robin, least_loaded, fastest_response
        self.failover_enabled = config.get("failover_enabled", True)
        self.max_agent_failures = config.get("max_agent_failures", 3)
        
        # Setup orchestrator-specific handlers
        self._setup_orchestrator_handlers()
        
        # Load default routing rules
        self._load_default_routing_rules()
    
    def _setup_orchestrator_handlers(self) -> None:
        """Setup orchestrator-specific message and action handlers"""
        # Add orchestrator-specific action handlers
        self.action_handlers.update({
            "route_request": self._action_route_request,
            "coordinate_workflow": self._action_coordinate_workflow,
            "monitor_system_health": self._action_monitor_system_health,
            "register_agent": self._action_register_agent,
            "unregister_agent": self._action_unregister_agent,
            "get_agent_registry": self._action_get_agent_registry,
            "execute_workflow": self._action_execute_workflow,
            "get_system_status": self._action_get_system_status,
            "get_performance_metrics": self._action_get_performance_metrics,
            "get_load_balancing_status": self._action_get_load_balancing_status,
            "update_routing_rules": self._action_update_routing_rules,
            "get_workflow_templates": self._action_get_workflow_templates,
            "create_workflow_template": self._action_create_workflow_template,
            "get_routing_analytics": self._action_get_routing_analytics,
            "reset_agent_failures": self._action_reset_agent_failures,
            "update_load_balancing_strategy": self._action_update_load_balancing_strategy,
            "get_agent_capacity_status": self._action_get_agent_capacity_status,
            "simulate_routing_decision": self._action_simulate_routing_decision
        })
    
    def _load_default_routing_rules(self) -> None:
        """Load default request routing rules"""
        self.routing_rules.update({
            "cost_analysis": "cost_management",
            "budget_monitoring": "cost_management",
            "cost_optimization": "cost_management",
            "resource_monitoring": "resource_management",
            "resource_optimization": "resource_management",
            "cost_forecasting": "forecasting",
            "trend_analysis": "forecasting",
            "alert_generation": "alert_management",
            "notification_sending": "alert_management",
            "user_interaction": "user_interface",
            "response_formatting": "user_interface",
            "decision_management": "approval",
            "approval_processing": "approval"
        })
    
    async def _agent_specific_initialization(self) -> None:
        """Orchestrator-specific initialization"""
        try:
            # Start system health monitoring
            asyncio.create_task(self._system_health_monitoring_loop())
            
            # Start performance metrics collection
            asyncio.create_task(self._performance_monitoring_loop())
            
            # Start workflow management
            asyncio.create_task(self._workflow_management_loop())
            
            # Start agent heartbeat monitoring
            asyncio.create_task(self._agent_heartbeat_monitoring_loop())
            
            # Initialize system health
            self.system_health.overall_status = "healthy"
            self.system_health.timestamp = datetime.now()
            
            # Initialize workflow engine if available
            if self.workflow_engine:
                self.logger.info("Workflow engine initialized")
            
            self.logger.info("Orchestrator agent initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error in orchestrator initialization: {e}")
            raise
    
    async def route_request(self, request: Dict[str, Any]) -> str:
        """Route request to appropriate agent with intelligent load balancing"""
        try:
            request_type = request.get("request_type", "")
            content = request.get("content", {})
            priority = request.get("priority", "normal")
            context = request.get("context", {})
            
            # Analyze request for intelligent routing
            routing_analysis = await self._analyze_request_for_routing(request_type, content, context)
            
            # Determine candidate agents based on analysis
            candidate_agents = self._determine_candidate_agents(request_type, content, routing_analysis)
            
            if not candidate_agents:
                raise ValueError(f"No suitable agents found for request type: {request_type}")
            
            # Filter available agents with health and capacity checks
            available_agents = await self._filter_available_agents(candidate_agents, priority)
            
            if not available_agents:
                # Try to find alternative agents with failover
                if self.failover_enabled:
                    alternative_agents = await self._find_alternative_agents_with_fallback(request_type, routing_analysis)
                    available_agents = await self._filter_available_agents(alternative_agents, priority)
                
                if not available_agents:
                    raise ValueError(f"No available agents found for request type: {request_type}")
            
            # Select best agent using intelligent load balancing strategy
            target_agent = await self._select_best_agent_intelligent(available_agents, priority, routing_analysis)
            
            # Update load balancing state and metrics
            await self._update_load_balancing_metrics(target_agent, request_type, priority)
            
            # Record routing decision for analytics and learning
            await self._record_routing_decision_detailed(request_type, target_agent, available_agents, routing_analysis)
            
            # Log routing decision with context
            self.logger.info(f"Routed request type '{request_type}' to agent '{target_agent}' "
                           f"(strategy: {self.routing_strategy}, priority: {priority}, "
                           f"candidates: {len(candidate_agents)}, available: {len(available_agents)})")
            
            return target_agent
            
        except Exception as e:
            self.logger.error(f"Error routing request: {e}")
            # Try emergency fallback routing
            fallback_agent = await self._emergency_fallback_routing(request)
            if fallback_agent:
                self.logger.warning(f"Using emergency fallback routing to agent: {fallback_agent}")
                return fallback_agent
            raise
    
    async def coordinate_workflow(self, workflow_id: str, steps: List[Dict]) -> Dict[str, Any]:
        """Coordinate multi-agent workflow using workflow engine"""
        try:
            # Create workflow definition
            workflow_steps = []
            for step_data in steps:
                step = WorkflowStep(
                    step_id=step_data.get("step_id", f"step_{len(workflow_steps)}"),
                    agent_id=step_data.get("agent_id", ""),
                    action=step_data.get("action", ""),
                    parameters=step_data.get("parameters", {}),
                    dependencies=step_data.get("dependencies", []),
                    timeout_seconds=step_data.get("timeout_seconds", 300),
                    retry_policy=step_data.get("retry_policy", {}),
                    condition=step_data.get("condition"),
                    on_success=step_data.get("on_success"),
                    on_failure=step_data.get("on_failure")
                )
                workflow_steps.append(step)
            
            workflow = WorkflowDefinition(
                workflow_id=workflow_id,
                name=step_data.get("workflow_name", f"Workflow {workflow_id}"),
                description=step_data.get("description", ""),
                steps=workflow_steps,
                created_by=self.agent_id,
                timeout_minutes=step_data.get("timeout_minutes", 60),
                max_retries=step_data.get("max_retries", 3)
            )
            
            # Execute workflow using workflow engine
            if self.workflow_engine:
                result = await self.workflow_engine.execute_workflow(workflow)
            else:
                # Fallback to basic execution
                result = await self._execute_workflow_basic(workflow)
            
            # Update system metrics
            await self._update_workflow_metrics(workflow_id, result)
            
            return {
                "workflow_id": workflow_id,
                "status": result.status,
                "results": result.results,
                "execution_time_seconds": result.execution_time_seconds,
                "errors": result.errors,
                "agent_results": result.agent_results,
                "completed_at": result.completed_at.isoformat() if result.completed_at else None
            }
            
        except Exception as e:
            self.logger.error(f"Error coordinating workflow: {e}")
            return {
                "workflow_id": workflow_id,
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def monitor_system_health(self) -> Dict[str, bool]:
        """Monitor health of all agents with detailed performance metrics"""
        try:
            health_status = {}
            performance_summary = {}
            current_time = datetime.now()
            
            # Check health of all registered agents
            for agent_id in self.agent_registry.keys():
                try:
                    # Use MCP server to check agent health
                    if self.mcp_server:
                        agent_status = await self.mcp_server.get_agent_status(agent_id)
                        is_healthy = agent_status.get("is_healthy", False)
                        
                        # Collect performance metrics
                        if agent_id in self.agent_performance_metrics:
                            metrics = self.agent_performance_metrics[agent_id]
                            performance_summary[agent_id] = {
                                "success_rate": metrics.calculate_success_rate(),
                                "average_response_time_ms": metrics.average_response_time_ms,
                                "error_rate": metrics.error_rate,
                                "uptime_percentage": metrics.uptime_percentage,
                                "tasks_completed": metrics.tasks_completed,
                                "last_updated": metrics.last_updated.isoformat()
                            }
                    else:
                        # Fallback to stored health status
                        is_healthy = self.agent_health_status.get(agent_id, False)
                    
                    # Check heartbeat freshness
                    last_heartbeat = self.agent_last_heartbeat.get(agent_id)
                    if last_heartbeat:
                        heartbeat_age = (current_time - last_heartbeat).total_seconds()
                        if heartbeat_age > self.health_check_interval * 2:
                            is_healthy = False
                            self.logger.warning(f"Agent {agent_id} heartbeat is stale ({heartbeat_age:.1f}s)")
                    
                    health_status[agent_id] = is_healthy
                    
                    # Update failure count
                    if not is_healthy:
                        self.agent_failure_counts[agent_id] = self.agent_failure_counts.get(agent_id, 0) + 1
                    else:
                        self.agent_failure_counts[agent_id] = 0
                    
                except Exception as e:
                    self.logger.error(f"Error checking health of agent {agent_id}: {e}")
                    health_status[agent_id] = False
                    self.agent_failure_counts[agent_id] = self.agent_failure_counts.get(agent_id, 0) + 1
            
            # Update system health with detailed information
            self.system_health.agent_statuses = health_status
            self.system_health.performance_summary = performance_summary
            self.system_health.timestamp = current_time
            
            # Calculate system metrics
            total_agents = len(health_status)
            healthy_agents = sum(1 for healthy in health_status.values() if healthy)
            unhealthy_agents = total_agents - healthy_agents
            
            self.system_health.system_metrics = {
                "total_agents": total_agents,
                "healthy_agents": healthy_agents,
                "unhealthy_agents": unhealthy_agents,
                "health_percentage": (healthy_agents / max(total_agents, 1)) * 100,
                "total_requests_routed": sum(self.load_balancing_state.values()),
                "workflow_engine_active": self.workflow_engine is not None
            }
            
            # Determine overall system health
            if unhealthy_agents == 0:
                self.system_health.overall_status = "healthy"
            elif unhealthy_agents < total_agents / 2:
                self.system_health.overall_status = "degraded"
            else:
                self.system_health.overall_status = "critical"
            
            # Generate alerts for critical issues
            await self._generate_health_alerts(health_status)
            
            return health_status
            
        except Exception as e:
            self.logger.error(f"Error monitoring system health: {e}")
            return {}
    
    async def register_agent(self, agent) -> bool:
        """Register new agent with orchestrator"""
        try:
            agent_id = agent.agent_id
            
            # Create agent configuration
            config = AgentConfiguration(
                agent_id=agent_id,
                agent_type=getattr(agent, '_agent_type', 'unknown'),
                capabilities=agent.capabilities,
                initialization_params=getattr(agent, 'config', {})
            )
            
            # Register agent
            self.agent_registry[agent_id] = config
            self.agent_health_status[agent_id] = True
            
            # Update load balancing state
            self.load_balancing_state[agent_id] = 0
            
            # Broadcast registration event
            if self.mcp_server:
                event = SystemEvent(
                    event_type="agent_registered",
                    source=self.agent_id,
                    data={
                        "agent_id": agent_id,
                        "agent_type": config.agent_type,
                        "capabilities": [cap.name for cap in config.capabilities]
                    },
                    severity="info"
                )
                await self.mcp_server.broadcast_system_event(event)
            
            self.logger.info(f"Registered agent {agent_id} with orchestrator")
            return True
            
        except Exception as e:
            self.logger.error(f"Error registering agent: {e}")
            return False
    
    async def unregister_agent(self, agent_id: str) -> bool:
        """Unregister agent from orchestrator"""
        try:
            if agent_id not in self.agent_registry:
                return False
            
            # Remove from registry
            del self.agent_registry[agent_id]
            self.agent_health_status.pop(agent_id, None)
            self.load_balancing_state.pop(agent_id, None)
            
            # Broadcast unregistration event
            if self.mcp_server:
                event = SystemEvent(
                    event_type="agent_unregistered",
                    source=self.agent_id,
                    data={"agent_id": agent_id},
                    severity="info"
                )
                await self.mcp_server.broadcast_system_event(event)
            
            self.logger.info(f"Unregistered agent {agent_id} from orchestrator")
            return True
            
        except Exception as e:
            self.logger.error(f"Error unregistering agent: {e}")
            return False
    
    async def get_agent_registry(self) -> Dict[str, AgentConfiguration]:
        """Get registry of all agents"""
        return self.agent_registry.copy()
    
    # Action handlers
    async def _action_route_request(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Route request action"""
        target_agent = await self.route_request(parameters)
        
        return {
            "target_agent": target_agent,
            "routing_decision": {
                "request_type": parameters.get("request_type"),
                "timestamp": datetime.now().isoformat()
            }
        }
    
    async def _action_coordinate_workflow(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate workflow action"""
        workflow_id = parameters.get("workflow_id", f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        steps = parameters.get("steps", [])
        
        return await self.coordinate_workflow(workflow_id, steps)
    
    async def _action_monitor_system_health(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Monitor system health action"""
        health_status = await self.monitor_system_health()
        
        return {
            "system_health": {
                "overall_status": self.system_health.overall_status,
                "agent_statuses": health_status,
                "timestamp": self.system_health.timestamp.isoformat(),
                "active_alerts": self.system_health.active_alerts
            }
        }
    
    async def _action_register_agent(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Register agent action"""
        # This would typically be called internally, not via external action
        return {"error": "Agent registration should be done through MCP server"}
    
    async def _action_unregister_agent(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Unregister agent action"""
        agent_id = parameters.get("agent_id")
        if not agent_id:
            return {"error": "agent_id is required"}
        
        success = await self.unregister_agent(agent_id)
        return {"success": success}
    
    async def _action_get_agent_registry(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get agent registry action"""
        registry = await self.get_agent_registry()
        
        return {
            "agent_registry": {
                agent_id: {
                    "agent_type": config.agent_type,
                    "capabilities": [cap.name for cap in config.capabilities],
                    "health_status": self.agent_health_status.get(agent_id, False),
                    "load_count": self.load_balancing_state.get(agent_id, 0)
                }
                for agent_id, config in registry.items()
            }
        }
    
    async def _action_execute_workflow(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute workflow action"""
        workflow_definition = parameters.get("workflow_definition")
        if not workflow_definition:
            return {"error": "workflow_definition is required"}
        
        # Convert dict to WorkflowDefinition object
        workflow = WorkflowDefinition(**workflow_definition)
        result = await self._execute_workflow(workflow)
        
        return {
            "workflow_id": workflow.workflow_id,
            "status": result.status,
            "results": result.results,
            "execution_time_seconds": result.execution_time_seconds,
            "errors": result.errors
        }
    
    async def _action_get_system_status(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get comprehensive system status action"""
        workflow_count = 0
        if self.workflow_engine:
            active_workflows = await self.workflow_engine.get_active_workflows()
            workflow_count = len(active_workflows)
        
        return {
            "system_status": {
                "overall_health": self.system_health.overall_status,
                "registered_agents": len(self.agent_registry),
                "healthy_agents": sum(1 for healthy in self.agent_health_status.values() if healthy),
                "active_workflows": workflow_count,
                "total_requests_routed": sum(self.load_balancing_state.values()),
                "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
                "routing_strategy": self.routing_strategy,
                "failover_enabled": self.failover_enabled,
                "system_metrics": self.system_health.system_metrics,
                "active_alerts": len(self.system_alerts),
                "workflow_engine_available": self.workflow_engine is not None
            }
        }
    
    async def _action_get_performance_metrics(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed performance metrics for all agents"""
        agent_id = parameters.get("agent_id")
        
        if agent_id:
            # Return metrics for specific agent
            if agent_id in self.agent_performance_metrics:
                metrics = self.agent_performance_metrics[agent_id]
                return {
                    "agent_id": agent_id,
                    "metrics": {
                        "success_rate": metrics.calculate_success_rate(),
                        "average_response_time_ms": metrics.average_response_time_ms,
                        "error_rate": metrics.error_rate,
                        "uptime_percentage": metrics.uptime_percentage,
                        "tasks_completed": metrics.tasks_completed,
                        "tasks_failed": metrics.tasks_failed,
                        "messages_processed": metrics.messages_processed,
                        "last_updated": metrics.last_updated.isoformat()
                    }
                }
            else:
                return {"error": f"No metrics found for agent {agent_id}"}
        else:
            # Return metrics for all agents
            all_metrics = {}
            for agent_id, metrics in self.agent_performance_metrics.items():
                all_metrics[agent_id] = {
                    "success_rate": metrics.calculate_success_rate(),
                    "average_response_time_ms": metrics.average_response_time_ms,
                    "error_rate": metrics.error_rate,
                    "uptime_percentage": metrics.uptime_percentage,
                    "tasks_completed": metrics.tasks_completed,
                    "last_updated": metrics.last_updated.isoformat()
                }
            
            return {"agent_metrics": all_metrics}
    
    async def _action_get_load_balancing_status(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get comprehensive load balancing status and statistics"""
        total_requests = sum(self.load_balancing_state.values())
        agent_count = len(self.load_balancing_state)
        
        # Calculate load distribution statistics
        load_values = list(self.load_balancing_state.values())
        load_variance = 0.0
        if load_values:
            mean_load = sum(load_values) / len(load_values)
            load_variance = sum((x - mean_load) ** 2 for x in load_values) / len(load_values)
        
        # Get request type distribution
        request_type_stats = {}
        if hasattr(self, 'agent_request_types'):
            for agent_id, types in self.agent_request_types.items():
                for req_type, count in types.items():
                    request_type_stats[req_type] = request_type_stats.get(req_type, 0) + count
        
        # Get priority distribution
        priority_stats = {}
        if hasattr(self, 'agent_priority_distribution'):
            for agent_id, priorities in self.agent_priority_distribution.items():
                for priority, count in priorities.items():
                    priority_stats[priority] = priority_stats.get(priority, 0) + count
        
        return {
            "load_balancing": {
                "strategy": self.routing_strategy,
                "failover_enabled": self.failover_enabled,
                "max_agent_failures": self.max_agent_failures,
                "agent_loads": self.load_balancing_state.copy(),
                "agent_failures": self.agent_failure_counts.copy(),
                "total_requests": total_requests,
                "average_load": total_requests / max(agent_count, 1),
                "load_variance": load_variance,
                "most_loaded_agent": max(self.load_balancing_state, key=self.load_balancing_state.get) if self.load_balancing_state else None,
                "least_loaded_agent": min(self.load_balancing_state, key=self.load_balancing_state.get) if self.load_balancing_state else None,
                "request_type_distribution": request_type_stats,
                "priority_distribution": priority_stats,
                "routing_decisions_total": getattr(self, '_total_routing_decisions', 0),
                "timestamp": datetime.now().isoformat()
            }
        }
    
    async def _action_update_routing_rules(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Update routing rules configuration"""
        new_rules = parameters.get("routing_rules", {})
        new_strategy = parameters.get("routing_strategy")
        
        # Update routing rules
        if new_rules:
            self.routing_rules.update(new_rules)
        
        # Update routing strategy
        if new_strategy and new_strategy in ["round_robin", "least_loaded", "fastest_response"]:
            self.routing_strategy = new_strategy
        
        return {
            "status": "updated",
            "current_rules": self.routing_rules.copy(),
            "current_strategy": self.routing_strategy,
            "updated_at": datetime.now().isoformat()
        }
    
    async def _action_get_workflow_templates(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get available workflow templates"""
        if self.workflow_engine:
            return {
                "workflow_templates": {
                    template_id: {
                        "name": template.name,
                        "description": template.description,
                        "steps_count": len(template.steps),
                        "created_at": template.created_at.isoformat(),
                        "created_by": template.created_by
                    }
                    for template_id, template in self.workflow_engine.workflow_templates.items()
                }
            }
        else:
            return {"error": "Workflow engine not available"}
    
    async def _action_create_workflow_template(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Create new workflow template"""
        if not self.workflow_engine:
            return {"error": "Workflow engine not available"}
        
        template_data = parameters.get("template")
        if not template_data:
            return {"error": "Template data is required"}
        
        try:
            # Create workflow definition from template data
            workflow_steps = []
            for step_data in template_data.get("steps", []):
                step = WorkflowStep(
                    step_id=step_data.get("step_id"),
                    agent_id=step_data.get("agent_id"),
                    action=step_data.get("action"),
                    parameters=step_data.get("parameters", {}),
                    dependencies=step_data.get("dependencies", []),
                    timeout_seconds=step_data.get("timeout_seconds", 300)
                )
                workflow_steps.append(step)
            
            template = WorkflowDefinition(
                workflow_id=template_data.get("template_id", f"template_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
                name=template_data.get("name", ""),
                description=template_data.get("description", ""),
                steps=workflow_steps,
                created_by=self.agent_id
            )
            
            success = await self.workflow_engine.register_workflow_template(template)
            
            if success:
                return {
                    "status": "created",
                    "template_id": template.workflow_id,
                    "name": template.name,
                    "created_at": template.created_at.isoformat()
                }
            else:
                return {"error": "Failed to register workflow template"}
        
        except Exception as e:
            return {"error": f"Error creating workflow template: {e}"}
    
    async def _action_get_routing_analytics(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed routing analytics and patterns"""
        analytics = {
            "total_routing_decisions": getattr(self, '_total_routing_decisions', 0),
            "routing_strategy": self.routing_strategy,
            "agent_request_patterns": {},
            "request_type_success_rates": {},
            "routing_efficiency_metrics": {}
        }
        
        # Agent request patterns
        if hasattr(self, 'agent_request_types'):
            analytics["agent_request_patterns"] = dict(self.agent_request_types)
        
        # Calculate routing efficiency
        if hasattr(self, '_routing_history') and self._routing_history:
            recent_decisions = self._routing_history[-100:]  # Last 100 decisions
            
            # Calculate average candidate count
            avg_candidates = sum(d.get("candidate_count", 0) for d in recent_decisions) / len(recent_decisions)
            
            # Calculate cross-domain request percentage
            cross_domain_count = sum(1 for d in recent_decisions if d.get("routing_analysis", {}).get("cross_domain", False))
            cross_domain_percentage = (cross_domain_count / len(recent_decisions)) * 100
            
            analytics["routing_efficiency_metrics"] = {
                "average_candidates_per_request": avg_candidates,
                "cross_domain_request_percentage": cross_domain_percentage,
                "recent_decisions_analyzed": len(recent_decisions)
            }
        
        return {"routing_analytics": analytics}
    
    async def _action_reset_agent_failures(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Reset failure counts for agents"""
        agent_id = parameters.get("agent_id")
        
        if agent_id:
            if agent_id in self.agent_failure_counts:
                old_count = self.agent_failure_counts[agent_id]
                self.agent_failure_counts[agent_id] = 0
                return {
                    "status": "reset",
                    "agent_id": agent_id,
                    "previous_failure_count": old_count,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {"error": f"Agent {agent_id} not found in failure tracking"}
        else:
            # Reset all failure counts
            old_counts = dict(self.agent_failure_counts)
            self.agent_failure_counts.clear()
            return {
                "status": "reset_all",
                "previous_failure_counts": old_counts,
                "timestamp": datetime.now().isoformat()
            }
    
    async def _action_update_load_balancing_strategy(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Update load balancing strategy and configuration"""
        new_strategy = parameters.get("strategy")
        new_failover_enabled = parameters.get("failover_enabled")
        new_max_failures = parameters.get("max_agent_failures")
        
        old_config = {
            "strategy": self.routing_strategy,
            "failover_enabled": self.failover_enabled,
            "max_agent_failures": self.max_agent_failures
        }
        
        # Update strategy
        if new_strategy and new_strategy in ["round_robin", "least_loaded", "fastest_response"]:
            self.routing_strategy = new_strategy
        
        # Update failover setting
        if new_failover_enabled is not None:
            self.failover_enabled = bool(new_failover_enabled)
        
        # Update max failures threshold
        if new_max_failures is not None and isinstance(new_max_failures, int) and new_max_failures > 0:
            self.max_agent_failures = new_max_failures
        
        new_config = {
            "strategy": self.routing_strategy,
            "failover_enabled": self.failover_enabled,
            "max_agent_failures": self.max_agent_failures
        }
        
        return {
            "status": "updated",
            "old_configuration": old_config,
            "new_configuration": new_config,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _action_get_agent_capacity_status(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed capacity status for all agents"""
        capacity_status = {}
        max_load = self.config.get("max_agent_load", 100)
        
        for agent_id in self.agent_registry.keys():
            current_load = self.load_balancing_state.get(agent_id, 0)
            failure_count = self.agent_failure_counts.get(agent_id, 0)
            is_healthy = self.agent_health_status.get(agent_id, False)
            
            # Calculate capacity utilization
            utilization_percentage = (current_load / max_load) * 100 if max_load > 0 else 0
            
            # Determine capacity status
            if not is_healthy:
                status = "unhealthy"
            elif failure_count >= self.max_agent_failures:
                status = "failed"
            elif utilization_percentage >= 100:
                status = "at_capacity"
            elif utilization_percentage >= 80:
                status = "high_load"
            elif utilization_percentage >= 50:
                status = "moderate_load"
            else:
                status = "available"
            
            capacity_info = {
                "current_load": current_load,
                "max_load": max_load,
                "utilization_percentage": utilization_percentage,
                "failure_count": failure_count,
                "is_healthy": is_healthy,
                "status": status
            }
            
            # Add performance metrics if available
            if agent_id in self.agent_performance_metrics:
                metrics = self.agent_performance_metrics[agent_id]
                capacity_info.update({
                    "success_rate": metrics.calculate_success_rate(),
                    "average_response_time_ms": metrics.average_response_time_ms,
                    "error_rate": metrics.error_rate,
                    "uptime_percentage": metrics.uptime_percentage
                })
            
            capacity_status[agent_id] = capacity_info
        
        return {
            "agent_capacity_status": capacity_status,
            "system_summary": {
                "total_agents": len(capacity_status),
                "available_agents": sum(1 for info in capacity_status.values() if info["status"] == "available"),
                "high_load_agents": sum(1 for info in capacity_status.values() if info["status"] == "high_load"),
                "at_capacity_agents": sum(1 for info in capacity_status.values() if info["status"] == "at_capacity"),
                "failed_agents": sum(1 for info in capacity_status.values() if info["status"] == "failed"),
                "unhealthy_agents": sum(1 for info in capacity_status.values() if info["status"] == "unhealthy")
            },
            "timestamp": datetime.now().isoformat()
        }
    
    async def _action_simulate_routing_decision(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate routing decision without actually routing"""
        request_type = parameters.get("request_type", "")
        content = parameters.get("content", {})
        priority = parameters.get("priority", "normal")
        context = parameters.get("context", {})
        
        try:
            # Perform routing analysis
            routing_analysis = await self._analyze_request_for_routing(request_type, content, context)
            
            # Determine candidates
            candidate_agents = self._determine_candidate_agents(request_type, content, routing_analysis)
            
            # Filter available agents
            available_agents = await self._filter_available_agents(candidate_agents, priority)
            
            # Select best agent (simulation)
            selected_agent = None
            if available_agents:
                selected_agent = await self._select_best_agent_intelligent(available_agents, priority, routing_analysis)
            
            # Find alternatives if needed
            alternative_agents = []
            if not available_agents:
                alternative_agents = await self._find_alternative_agents_with_fallback(request_type, routing_analysis)
            
            return {
                "simulation_result": {
                    "request_analysis": routing_analysis,
                    "candidate_agents": candidate_agents,
                    "available_agents": available_agents,
                    "selected_agent": selected_agent,
                    "alternative_agents": alternative_agents,
                    "routing_strategy_used": self.routing_strategy,
                    "would_succeed": selected_agent is not None,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            return {
                "simulation_result": {
                    "error": str(e),
                    "would_succeed": False,
                    "timestamp": datetime.now().isoformat()
                }
            }
    
    # Helper methods
    def _determine_target_agent(self, request_type: str, content: Dict[str, Any]) -> Optional[str]:
        """Determine target agent for request"""
        # Check direct routing rules
        if request_type in self.routing_rules:
            return self.routing_rules[request_type]
        
        # Check content-based routing
        if "cost" in request_type.lower() or "budget" in request_type.lower():
            return "cost_management"
        elif "resource" in request_type.lower():
            return "resource_management"
        elif "forecast" in request_type.lower() or "predict" in request_type.lower():
            return "forecasting"
        elif "alert" in request_type.lower() or "notification" in request_type.lower():
            return "alert_management"
        elif "user" in request_type.lower() or "interface" in request_type.lower():
            return "user_interface"
        elif "approval" in request_type.lower() or "decision" in request_type.lower():
            return "approval"
        
        # Default to user interface agent for unknown requests
        return "user_interface"
    
    def _is_agent_available(self, agent_id: str) -> bool:
        """Check if agent is available"""
        return (
            agent_id in self.agent_registry and
            self.agent_health_status.get(agent_id, False)
        )
    
    def _find_alternative_agent(self, request_type: str) -> Optional[str]:
        """Find alternative agent for request type"""
        # Simple fallback logic - could be more sophisticated
        if "cost" in request_type.lower():
            alternatives = ["forecasting", "user_interface"]
        elif "resource" in request_type.lower():
            alternatives = ["cost_management", "user_interface"]
        else:
            alternatives = ["user_interface"]
        
        for alt_agent in alternatives:
            if self._is_agent_available(alt_agent):
                return alt_agent
        
        return None
    
    async def _execute_workflow(self, workflow: WorkflowDefinition) -> TaskResult:
        """Execute workflow definition"""
        try:
            start_time = datetime.now()
            self.active_workflows[workflow.workflow_id] = {
                "workflow": workflow,
                "status": "running",
                "start_time": start_time
            }
            
            result = TaskResult(
                task_id=workflow.workflow_id,
                status="running"
            )
            
            # Execute workflow steps
            completed_steps = []
            
            for step in workflow.steps:
                if step.can_execute(completed_steps):
                    try:
                        # Execute step through MCP server
                        if self.mcp_server and step.agent_id in self.agent_registry:
                            # Create agent message for step execution
                            message = AgentMessage(
                                sender=self.agent_id,
                                recipient=step.agent_id,
                                message_type=MessageType.COMMAND,
                                content={
                                    "command": step.action,
                                    "parameters": step.parameters
                                }
                            )
                            
                            response = await self.mcp_server.route_message(message)
                            
                            if response.message_type == MessageType.ERROR:
                                result.errors.append(f"Step {step.step_id} failed: {response.content.get('error')}")
                            else:
                                result.agent_results[step.agent_id] = response.content
                                completed_steps.append(step.step_id)
                        else:
                            result.errors.append(f"Agent {step.agent_id} not available for step {step.step_id}")
                    
                    except Exception as e:
                        result.errors.append(f"Error executing step {step.step_id}: {e}")
            
            # Determine final status
            if not result.errors:
                result.status = "success"
            elif completed_steps:
                result.status = "partial"
            else:
                result.status = "failed"
            
            # Calculate execution time
            end_time = datetime.now()
            result.execution_time_seconds = (end_time - start_time).total_seconds()
            result.completed_at = end_time
            
            # Update workflow status
            self.active_workflows[workflow.workflow_id]["status"] = result.status
            self.active_workflows[workflow.workflow_id]["end_time"] = end_time
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error executing workflow: {e}")
            return TaskResult(
                task_id=workflow.workflow_id,
                status="failed",
                errors=[str(e)]
            )
    
    async def _system_health_monitoring_loop(self) -> None:
        """Background system health monitoring"""
        while self._state.status != AgentStatus.OFFLINE:
            try:
                await asyncio.sleep(self.health_check_interval)
                
                # Monitor system health
                await self.monitor_system_health()
                
                # Check for critical issues
                if self.system_health.overall_status == "critical":
                    # Broadcast critical system alert
                    if self.mcp_server:
                        event = SystemEvent(
                            event_type="system_critical",
                            source=self.agent_id,
                            data={
                                "unhealthy_agents": self.system_health.get_unhealthy_agents(),
                                "timestamp": datetime.now().isoformat()
                            },
                            severity="critical",
                            requires_action=True
                        )
                        await self.mcp_server.broadcast_system_event(event)
                
            except Exception as e:
                self.logger.error(f"Error in system health monitoring: {e}")
    
    async def _workflow_management_loop(self) -> None:
        """Background workflow management"""
        while self._state.status != AgentStatus.OFFLINE:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                # Get workflow engine metrics if available
                if self.workflow_engine:
                    workflow_metrics = self.workflow_engine.get_execution_metrics()
                    
                    # Update system health with workflow metrics
                    self.system_health.system_metrics.update({
                        "workflows_executed": workflow_metrics.get("workflows_executed", 0),
                        "workflow_success_rate": workflow_metrics.get("success_rate", 0),
                        "active_workflows": workflow_metrics.get("active_workflows", 0)
                    })
                
            except Exception as e:
                self.logger.error(f"Error in workflow management: {e}")
    
    async def _performance_monitoring_loop(self) -> None:
        """Background performance monitoring for all agents"""
        while self._state.status != AgentStatus.OFFLINE:
            try:
                await asyncio.sleep(self.performance_monitoring_interval)
                
                # Collect performance metrics from all agents
                for agent_id in self.agent_registry.keys():
                    try:
                        if self.mcp_server:
                            # Request metrics from agent
                            message = AgentMessage(
                                sender=self.agent_id,
                                recipient=agent_id,
                                message_type=MessageType.COMMAND,
                                content={"command": "get_metrics", "parameters": {}},
                                requires_response=True,
                                response_timeout=10
                            )
                            
                            response = await self.mcp_server.route_message(message)
                            
                            if response.message_type != MessageType.ERROR:
                                metrics_data = response.content
                                
                                # Update stored metrics
                                if agent_id not in self.agent_performance_metrics:
                                    self.agent_performance_metrics[agent_id] = AgentMetrics(agent_id=agent_id)
                                
                                metrics = self.agent_performance_metrics[agent_id]
                                metrics.update_metrics(
                                    messages_processed=metrics_data.get("messages_processed", 0),
                                    tasks_completed=metrics_data.get("tasks_completed", 0),
                                    tasks_failed=metrics_data.get("tasks_failed", 0),
                                    average_response_time_ms=metrics_data.get("average_response_time_ms", 0),
                                    error_rate=metrics_data.get("error_rate", 0),
                                    uptime_percentage=metrics_data.get("uptime_percentage", 100)
                                )
                    
                    except Exception as e:
                        self.logger.debug(f"Could not collect metrics from agent {agent_id}: {e}")
                
            except Exception as e:
                self.logger.error(f"Error in performance monitoring: {e}")
    
    async def _agent_heartbeat_monitoring_loop(self) -> None:
        """Monitor agent heartbeats and update availability"""
        while self._state.status != AgentStatus.OFFLINE:
            try:
                await asyncio.sleep(self.health_check_interval)
                
                current_time = datetime.now()
                
                # Send heartbeat requests to all agents
                for agent_id in self.agent_registry.keys():
                    try:
                        if self.mcp_server:
                            message = AgentMessage(
                                sender=self.agent_id,
                                recipient=agent_id,
                                message_type=MessageType.HEARTBEAT,
                                content={"timestamp": current_time.isoformat()},
                                requires_response=True,
                                response_timeout=5
                            )
                            
                            response = await self.mcp_server.route_message(message)
                            
                            if response.message_type != MessageType.ERROR:
                                self.agent_last_heartbeat[agent_id] = current_time
                                self.agent_health_status[agent_id] = True
                            else:
                                self.agent_health_status[agent_id] = False
                    
                    except Exception as e:
                        self.logger.debug(f"Heartbeat failed for agent {agent_id}: {e}")
                        self.agent_health_status[agent_id] = False
                
            except Exception as e:
                self.logger.error(f"Error in heartbeat monitoring: {e}")
    
    # Enhanced intelligent routing methods
    async def _analyze_request_for_routing(self, request_type: str, content: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze request content and context for intelligent routing decisions"""
        analysis = {
            "complexity": "low",
            "domain_keywords": [],
            "required_capabilities": [],
            "estimated_processing_time": "short",
            "data_sensitivity": "normal",
            "cross_domain": False
        }
        
        # Analyze request content for keywords and complexity
        text_content = f"{request_type} {str(content)} {str(context)}".lower()
        
        # Domain keyword analysis
        domain_keywords = {
            "cost": ["cost", "budget", "spend", "billing", "price", "expense", "financial"],
            "resource": ["resource", "instance", "server", "storage", "compute", "infrastructure"],
            "forecast": ["forecast", "predict", "trend", "projection", "future", "estimate"],
            "alert": ["alert", "notification", "threshold", "warning", "alarm", "monitor"],
            "approval": ["approval", "decision", "authorize", "approve", "review", "permission"],
            "user": ["user", "interface", "dashboard", "display", "view", "interaction"]
        }
        
        for domain, keywords in domain_keywords.items():
            found_keywords = [kw for kw in keywords if kw in text_content]
            if found_keywords:
                analysis["domain_keywords"].extend([(domain, kw) for kw in found_keywords])
        
        # Complexity analysis
        complexity_indicators = {
            "high": ["complex", "detailed", "comprehensive", "analysis", "report", "multiple"],
            "medium": ["calculate", "process", "generate", "create", "update"],
            "low": ["get", "show", "display", "list", "simple"]
        }
        
        for level, indicators in complexity_indicators.items():
            if any(indicator in text_content for indicator in indicators):
                analysis["complexity"] = level
                break
        
        # Cross-domain detection
        domains_found = set(domain for domain, _ in analysis["domain_keywords"])
        if len(domains_found) > 1:
            analysis["cross_domain"] = True
            analysis["complexity"] = "high"  # Cross-domain requests are inherently complex
        
        # Estimate processing time based on complexity and content
        if analysis["complexity"] == "high" or analysis["cross_domain"]:
            analysis["estimated_processing_time"] = "long"
        elif analysis["complexity"] == "medium":
            analysis["estimated_processing_time"] = "medium"
        
        # Data sensitivity analysis
        sensitive_keywords = ["financial", "cost", "budget", "billing", "security", "private"]
        if any(keyword in text_content for keyword in sensitive_keywords):
            analysis["data_sensitivity"] = "high"
        
        return analysis
    
    def _determine_candidate_agents(self, request_type: str, content: Dict[str, Any], routing_analysis: Dict[str, Any]) -> List[str]:
        """Determine candidate agents based on intelligent analysis"""
        candidates = []
        
        # Primary routing based on request type
        if request_type in self.routing_rules:
            primary_agent = self.routing_rules[request_type]
            if primary_agent in self.agent_registry:
                candidates.append(primary_agent)
        
        # Domain-based routing using analysis
        domain_priorities = {}
        for domain, keyword in routing_analysis.get("domain_keywords", []):
            domain_priorities[domain] = domain_priorities.get(domain, 0) + 1
        
        # Sort domains by keyword frequency
        sorted_domains = sorted(domain_priorities.items(), key=lambda x: x[1], reverse=True)
        
        # Map domains to agents
        domain_agent_mapping = {
            "cost": ["cost_management", "forecasting"],
            "resource": ["resource_management", "cost_management"],
            "forecast": ["forecasting", "cost_management"],
            "alert": ["alert_management", "user_interface"],
            "approval": ["approval", "user_interface"],
            "user": ["user_interface"]
        }
        
        # Add agents based on domain analysis
        for domain, _ in sorted_domains:
            if domain in domain_agent_mapping:
                candidates.extend(domain_agent_mapping[domain])
        
        # Handle cross-domain requests
        if routing_analysis.get("cross_domain", False):
            # For cross-domain requests, prioritize orchestrator coordination
            # and include multiple domain agents
            candidates.insert(0, "user_interface")  # UI agent can coordinate display
            
            # Add all relevant domain agents
            for domain in domain_priorities.keys():
                if domain in domain_agent_mapping:
                    candidates.extend(domain_agent_mapping[domain])
        
        # Fallback content-based routing (legacy support)
        if not candidates:
            request_lower = request_type.lower()
            content_text = str(content).lower()
            
            if "cost" in request_lower or "budget" in request_lower or "cost" in content_text:
                candidates.extend(["cost_management", "forecasting"])
            elif "resource" in request_lower or "resource" in content_text:
                candidates.extend(["resource_management", "cost_management"])
            elif "forecast" in request_lower or "predict" in request_lower:
                candidates.extend(["forecasting", "cost_management"])
            elif "alert" in request_lower or "notification" in request_lower:
                candidates.extend(["alert_management", "user_interface"])
            elif "user" in request_lower or "interface" in request_lower:
                candidates.extend(["user_interface"])
            elif "approval" in request_lower or "decision" in request_lower:
                candidates.extend(["approval", "user_interface"])
        
        # Remove duplicates while preserving priority order
        seen = set()
        unique_candidates = []
        for agent in candidates:
            if agent not in seen and agent in self.agent_registry:
                seen.add(agent)
                unique_candidates.append(agent)
        
        # Add user_interface as final fallback
        if "user_interface" not in unique_candidates and "user_interface" in self.agent_registry:
            unique_candidates.append("user_interface")
        
        return unique_candidates
    
    async def _filter_available_agents(self, candidate_agents: List[str], priority: str = "normal") -> List[str]:
        """Filter agents based on availability, health, and capacity"""
        available_agents = []
        
        for agent_id in candidate_agents:
            # Basic availability check
            if not self._is_agent_available(agent_id):
                continue
            
            # Health check with failure count consideration
            failure_count = self.agent_failure_counts.get(agent_id, 0)
            if failure_count >= self.max_agent_failures:
                self.logger.warning(f"Agent {agent_id} has too many failures ({failure_count}), skipping")
                continue
            
            # Capacity check based on current load
            current_load = self.load_balancing_state.get(agent_id, 0)
            max_load = self.config.get("max_agent_load", 100)
            
            if current_load >= max_load:
                self.logger.debug(f"Agent {agent_id} is at capacity ({current_load}/{max_load}), skipping")
                continue
            
            # Performance check for high priority requests
            if priority in ["high", "critical"]:
                if agent_id in self.agent_performance_metrics:
                    metrics = self.agent_performance_metrics[agent_id]
                    if metrics.error_rate > 0.3:  # More than 30% error rate
                        self.logger.debug(f"Agent {agent_id} has high error rate ({metrics.error_rate:.1%}), skipping for high priority")
                        continue
            
            available_agents.append(agent_id)
        
        return available_agents
    
    async def _select_best_agent_intelligent(self, available_agents: List[str], priority: str = "normal", routing_analysis: Dict[str, Any] = None) -> str:
        """Select best agent using intelligent load balancing with context awareness"""
        if len(available_agents) == 1:
            return available_agents[0]
        
        # For high priority requests, use performance-based selection
        if priority in ["high", "critical"]:
            return await self._select_performance_optimized(available_agents)
        
        # For cross-domain requests, prefer agents with broader capabilities
        if routing_analysis and routing_analysis.get("cross_domain", False):
            return await self._select_for_cross_domain(available_agents)
        
        # Use configured strategy with enhancements
        if self.routing_strategy == "round_robin":
            return self._select_round_robin_enhanced(available_agents)
        elif self.routing_strategy == "least_loaded":
            return await self._select_least_loaded_enhanced(available_agents)
        elif self.routing_strategy == "fastest_response":
            return await self._select_fastest_response_enhanced(available_agents)
        else:
            # Default to enhanced round robin
            return self._select_round_robin_enhanced(available_agents)
    
    async def _select_performance_optimized(self, agents: List[str]) -> str:
        """Select agent optimized for performance (high priority requests)"""
        agent_scores = {}
        
        for agent in agents:
            score = 100.0  # Base score
            
            # Factor in success rate
            if agent in self.agent_performance_metrics:
                metrics = self.agent_performance_metrics[agent]
                score *= (metrics.calculate_success_rate() / 100.0)
                
                # Factor in response time (lower is better)
                if metrics.average_response_time_ms > 0:
                    score *= (1000.0 / max(metrics.average_response_time_ms, 100.0))
                
                # Factor in uptime
                score *= (metrics.uptime_percentage / 100.0)
            
            # Factor in current load (lower is better)
            current_load = self.load_balancing_state.get(agent, 0)
            score *= (1.0 / max(current_load + 1, 1))
            
            # Factor in failure count (lower is better)
            failure_count = self.agent_failure_counts.get(agent, 0)
            score *= (1.0 / max(failure_count + 1, 1))
            
            agent_scores[agent] = score
        
        return max(agent_scores, key=agent_scores.get)
    
    async def _select_for_cross_domain(self, agents: List[str]) -> str:
        """Select agent best suited for cross-domain requests"""
        # Prefer user_interface agent for cross-domain coordination
        if "user_interface" in agents:
            return "user_interface"
        
        # Otherwise, select the most capable agent
        return await self._select_performance_optimized(agents)
    
    def _select_round_robin_enhanced(self, agents: List[str]) -> str:
        """Enhanced round-robin selection with failure awareness"""
        # Calculate effective load including failure penalties
        agent_loads = {}
        for agent in agents:
            base_load = self.load_balancing_state.get(agent, 0)
            failure_penalty = self.agent_failure_counts.get(agent, 0) * 0.5
            agent_loads[agent] = base_load + failure_penalty
        
        # Find agents with minimum effective load
        min_load = min(agent_loads.values())
        candidates = [agent for agent, load in agent_loads.items() if load == min_load]
        
        # If multiple candidates, prefer agents with better performance
        if len(candidates) > 1:
            best_candidate = candidates[0]
            best_success_rate = 0.0
            
            for candidate in candidates:
                if candidate in self.agent_performance_metrics:
                    success_rate = self.agent_performance_metrics[candidate].calculate_success_rate()
                    if success_rate > best_success_rate:
                        best_success_rate = success_rate
                        best_candidate = candidate
            
            return best_candidate
        
        return candidates[0]
    
    async def _select_least_loaded_enhanced(self, agents: List[str]) -> str:
        """Enhanced least-loaded selection with performance weighting"""
        agent_scores = {}
        
        for agent in agents:
            # Base load score
            load_count = self.load_balancing_state.get(agent, 0)
            failure_count = self.agent_failure_counts.get(agent, 0)
            
            # Calculate weighted load
            weighted_load = load_count + (failure_count * 2.0)
            
            # Factor in performance metrics if available
            if agent in self.agent_performance_metrics:
                metrics = self.agent_performance_metrics[agent]
                
                # Adjust load based on success rate (lower success rate = higher effective load)
                success_rate = metrics.calculate_success_rate() / 100.0
                weighted_load = weighted_load / max(success_rate, 0.1)
                
                # Adjust for response time (slower agents get higher effective load)
                if metrics.average_response_time_ms > 0:
                    time_factor = metrics.average_response_time_ms / 1000.0  # Convert to seconds
                    weighted_load *= (1.0 + time_factor * 0.1)  # 10% penalty per second
            
            agent_scores[agent] = weighted_load
        
        return min(agent_scores, key=agent_scores.get)
    
    async def _select_fastest_response_enhanced(self, agents: List[str]) -> str:
        """Enhanced fastest response selection with load balancing"""
        agent_scores = {}
        
        for agent in agents:
            if agent in self.agent_performance_metrics:
                metrics = self.agent_performance_metrics[agent]
                base_response_time = metrics.average_response_time_ms
                
                # Adjust response time based on current load
                current_load = self.load_balancing_state.get(agent, 0)
                load_penalty = current_load * 50  # 50ms penalty per active request
                
                # Adjust for failure rate
                failure_count = self.agent_failure_counts.get(agent, 0)
                failure_penalty = failure_count * 100  # 100ms penalty per recent failure
                
                # Calculate effective response time
                effective_response_time = base_response_time + load_penalty + failure_penalty
                
                # Factor in success rate
                success_rate = metrics.calculate_success_rate() / 100.0
                effective_response_time = effective_response_time / max(success_rate, 0.1)
                
                agent_scores[agent] = effective_response_time
            else:
                # Unknown performance, assign high penalty
                agent_scores[agent] = 10000.0  # 10 second penalty
        
        return min(agent_scores, key=agent_scores.get)
    
    async def _find_alternative_agents_with_fallback(self, request_type: str, routing_analysis: Dict[str, Any]) -> List[str]:
        """Find alternative agents with intelligent fallback based on analysis"""
        alternatives = []
        
        # Use routing analysis to find better alternatives
        domain_keywords = routing_analysis.get("domain_keywords", [])
        complexity = routing_analysis.get("complexity", "low")
        cross_domain = routing_analysis.get("cross_domain", False)
        
        # Build fallback chains based on analysis
        if cross_domain:
            # For cross-domain requests, prioritize versatile agents
            alternatives.extend(["user_interface", "cost_management", "forecasting"])
        else:
            # Single domain fallbacks
            primary_domains = set(domain for domain, _ in domain_keywords)
            
            for domain in primary_domains:
                if domain == "cost":
                    alternatives.extend(["cost_management", "forecasting", "user_interface"])
                elif domain == "resource":
                    alternatives.extend(["resource_management", "cost_management", "user_interface"])
                elif domain == "forecast":
                    alternatives.extend(["forecasting", "cost_management", "user_interface"])
                elif domain == "alert":
                    alternatives.extend(["alert_management", "user_interface"])
                elif domain == "approval":
                    alternatives.extend(["approval", "user_interface"])
                elif domain == "user":
                    alternatives.extend(["user_interface"])
        
        # Legacy fallback for unknown request types
        if not alternatives:
            request_lower = request_type.lower()
            fallback_chains = {
                "cost": ["cost_management", "forecasting", "user_interface"],
                "resource": ["resource_management", "cost_management", "user_interface"],
                "forecast": ["forecasting", "cost_management", "user_interface"],
                "alert": ["alert_management", "user_interface"],
                "approval": ["approval", "user_interface"],
                "user": ["user_interface"]
            }
            
            for key, chain in fallback_chains.items():
                if key in request_lower:
                    alternatives.extend(chain)
                    break
        
        # Ultimate fallback
        if not alternatives:
            alternatives = ["user_interface"]
        
        # Remove duplicates and filter by registry
        seen = set()
        filtered_alternatives = []
        for agent in alternatives:
            if agent not in seen and agent in self.agent_registry:
                seen.add(agent)
                filtered_alternatives.append(agent)
        
        return filtered_alternatives
    
    async def _emergency_fallback_routing(self, request: Dict[str, Any]) -> Optional[str]:
        """Emergency fallback routing when all else fails"""
        try:
            # Try to find any healthy agent
            for agent_id in self.agent_registry.keys():
                if self.agent_health_status.get(agent_id, False):
                    failure_count = self.agent_failure_counts.get(agent_id, 0)
                    if failure_count < self.max_agent_failures * 2:  # Allow higher failure threshold in emergency
                        self.logger.warning(f"Emergency fallback routing to {agent_id}")
                        return agent_id
            
            # If no healthy agents, try the user_interface agent as last resort
            if "user_interface" in self.agent_registry:
                self.logger.critical("Using user_interface agent as last resort")
                return "user_interface"
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error in emergency fallback routing: {e}")
            return None
    
    async def _update_load_balancing_metrics(self, target_agent: str, request_type: str, priority: str) -> None:
        """Update load balancing metrics and state"""
        # Update basic load count
        self.load_balancing_state[target_agent] = self.load_balancing_state.get(target_agent, 0) + 1
        
        # Track request types per agent for learning
        if not hasattr(self, 'agent_request_types'):
            self.agent_request_types = {}
        
        if target_agent not in self.agent_request_types:
            self.agent_request_types[target_agent] = {}
        
        self.agent_request_types[target_agent][request_type] = (
            self.agent_request_types[target_agent].get(request_type, 0) + 1
        )
        
        # Track priority distribution
        if not hasattr(self, 'agent_priority_distribution'):
            self.agent_priority_distribution = {}
        
        if target_agent not in self.agent_priority_distribution:
            self.agent_priority_distribution[target_agent] = {}
        
        self.agent_priority_distribution[target_agent][priority] = (
            self.agent_priority_distribution[target_agent].get(priority, 0) + 1
        )
    
    async def _record_routing_decision_detailed(self, request_type: str, target_agent: str, available_agents: List[str], routing_analysis: Dict[str, Any]) -> None:
        """Record detailed routing decision for analytics and learning"""
        if self.strands_framework:
            decision_record = {
                "request_type": request_type,
                "target_agent": target_agent,
                "available_agents": available_agents,
                "candidate_count": len(available_agents),
                "strategy_used": self.routing_strategy,
                "routing_analysis": routing_analysis,
                "load_balancing_state": dict(self.load_balancing_state),
                "agent_failure_counts": dict(self.agent_failure_counts),
                "timestamp": datetime.now().isoformat()
            }
            
            # Store in routing analytics
            await self.strands_framework.update_context(
                self.agent_id,
                {
                    "routing_analytics": {
                        "last_decision": decision_record,
                        "total_decisions": getattr(self, '_total_routing_decisions', 0) + 1
                    }
                }
            )
            
            # Store in routing history for pattern learning
            if not hasattr(self, '_routing_history'):
                self._routing_history = []
            
            self._routing_history.append(decision_record)
            
            # Keep only last 1000 decisions for memory efficiency
            if len(self._routing_history) > 1000:
                self._routing_history = self._routing_history[-1000:]
            
            # Update total decision counter
            self._total_routing_decisions = getattr(self, '_total_routing_decisions', 0) + 1
    
    async def _generate_health_alerts(self, health_status: Dict[str, bool]) -> None:
        """Generate alerts for critical health issues"""
        current_time = datetime.now()
        new_alerts = []
        
        # Check for unhealthy agents
        for agent_id, is_healthy in health_status.items():
            if not is_healthy:
                failure_count = self.agent_failure_counts.get(agent_id, 0)
                if failure_count >= self.max_agent_failures:
                    alert = {
                        "type": "agent_critical_failure",
                        "agent_id": agent_id,
                        "failure_count": failure_count,
                        "timestamp": current_time.isoformat(),
                        "severity": "critical"
                    }
                    new_alerts.append(alert)
        
        # Check system-wide health
        healthy_count = sum(1 for healthy in health_status.values() if healthy)
        total_count = len(health_status)
        
        if total_count > 0 and healthy_count / total_count < 0.5:
            alert = {
                "type": "system_degraded",
                "healthy_agents": healthy_count,
                "total_agents": total_count,
                "timestamp": current_time.isoformat(),
                "severity": "high"
            }
            new_alerts.append(alert)
        
        # Add new alerts and broadcast critical ones
        for alert in new_alerts:
            self.system_alerts.append(alert)
            
            if alert["severity"] == "critical" and self.mcp_server:
                event = SystemEvent(
                    event_type="system_alert",
                    source=self.agent_id,
                    data=alert,
                    severity="critical",
                    requires_action=True
                )
                await self.mcp_server.broadcast_system_event(event)
        
        # Clean up old alerts (keep last 100)
        if len(self.system_alerts) > 100:
            self.system_alerts = self.system_alerts[-100:]
    
    async def _update_workflow_metrics(self, workflow_id: str, result: TaskResult) -> None:
        """Update workflow execution metrics"""
        if self.strands_framework:
            await self.strands_framework.update_context(
                self.agent_id,
                {
                    "workflow_metrics": {
                        workflow_id: {
                            "status": result.status,
                            "execution_time_seconds": result.execution_time_seconds,
                            "error_count": len(result.errors),
                            "completed_at": result.completed_at.isoformat() if result.completed_at else None
                        }
                    }
                }
            )
    
    async def _execute_workflow_basic(self, workflow: WorkflowDefinition) -> TaskResult:
        """Basic workflow execution fallback when workflow engine is not available"""
        # This is a simplified version for fallback
        result = TaskResult(
            task_id=workflow.workflow_id,
            status="success"
        )
        
        # Execute steps sequentially (simplified)
        for step in workflow.steps:
            try:
                if self.mcp_server and step.agent_id in self.agent_registry:
                    message = AgentMessage(
                        sender=self.agent_id,
                        recipient=step.agent_id,
                        message_type=MessageType.COMMAND,
                        content={
                            "command": step.action,
                            "parameters": step.parameters
                        }
                    )
                    
                    response = await self.mcp_server.route_message(message)
                    
                    if response.message_type == MessageType.ERROR:
                        result.errors.append(f"Step {step.step_id} failed: {response.content.get('error')}")
                        result.status = "partial"
                    else:
                        result.agent_results[step.agent_id] = response.content
            
            except Exception as e:
                result.errors.append(f"Error executing step {step.step_id}: {e}")
                result.status = "failed"
        
        result.completed_at = datetime.now()
        return result