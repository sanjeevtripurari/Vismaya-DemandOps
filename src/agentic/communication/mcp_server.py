"""
Model Context Protocol (MCP) Server implementation
Secure inter-agent communication and coordination
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
import weakref

from ..core.interfaces import IMCPServer, IAgentCore, ISecurityManager
from ..core.models import (
    AgentMessage, SystemEvent, MultiAgentTask, TaskResult,
    AgentCommunicationError, AgentNotFoundError, UnauthorizedCommunicationError,
    MessageType, AgentStatus
)
from .agent_registry import AgentRegistry


class MCPAgentServer(IMCPServer):
    """
    MCP Server for secure agent communication and coordination
    Implements the Model Context Protocol for multi-agent systems
    """
    
    def __init__(self, security_manager: ISecurityManager, registry_config: Optional[Dict[str, Any]] = None):
        self.security_manager = security_manager
        self.agent_registry = AgentRegistry(registry_config or {})
        self.agents: Dict[str, IAgentCore] = {}  # Keep for backward compatibility
        self.message_handlers: Dict[str, Callable] = {}
        self.event_subscribers: Dict[str, List[str]] = {}  # event_type -> agent_ids
        self.active_tasks: Dict[str, MultiAgentTask] = {}
        self.server_running = False
        self.message_queue = asyncio.Queue()
        self.logger = logging.getLogger(__name__)
        
        # Performance tracking
        self.message_count = 0
        self.error_count = 0
        self.start_time = None
        
        # Setup default message handlers
        self._setup_default_handlers()
    
    def _setup_default_handlers(self) -> None:
        """Setup default message handlers"""
        self.message_handlers.update({
            MessageType.REQUEST.value: self._handle_request,
            MessageType.RESPONSE.value: self._handle_response,
            MessageType.NOTIFICATION.value: self._handle_notification,
            MessageType.COMMAND.value: self._handle_command,
            MessageType.EVENT.value: self._handle_event,
            MessageType.ERROR.value: self._handle_error,
            MessageType.HEARTBEAT.value: self._handle_heartbeat
        })
    
    async def start_server(self, port: int = 8000) -> bool:
        """Start MCP server"""
        try:
            self.start_time = datetime.now()
            self.server_running = True
            
            # Start agent registry
            await self.agent_registry.start_registry()
            
            # Start message processing loop
            asyncio.create_task(self._message_processing_loop())
            
            # Start health monitoring (now handled by registry)
            asyncio.create_task(self._health_monitoring_loop())
            
            self.logger.info(f"MCP Server started on port {port}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start MCP server: {e}")
            return False
    
    async def stop_server(self) -> bool:
        """Stop MCP server"""
        try:
            self.server_running = False
            
            # Notify all agents of shutdown
            shutdown_event = SystemEvent(
                event_type="server_shutdown",
                source="mcp_server",
                data={"timestamp": datetime.now().isoformat()},
                severity="warning"
            )
            await self.broadcast_system_event(shutdown_event)
            
            # Stop agent registry
            await self.agent_registry.stop_registry()
            
            # Wait for graceful shutdown
            await asyncio.sleep(1)
            
            self.logger.info("MCP Server stopped")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping MCP server: {e}")
            return False
    
    async def route_message(self, message: AgentMessage) -> AgentMessage:
        """Route message between agents with security validation"""
        try:
            self.message_count += 1
            
            # Validate sender authorization
            if not await self.security_manager.validate_sender(message.sender, message.recipient):
                raise UnauthorizedCommunicationError(
                    f"Agent {message.sender} not authorized to communicate with {message.recipient}"
                )
            
            # Check if recipient exists and is healthy
            agent_status = await self.agent_registry.get_agent_status(message.recipient)
            if not agent_status:
                raise AgentNotFoundError(f"Agent {message.recipient} not found")
            
            if not agent_status.get("is_available", False):
                raise AgentCommunicationError(f"Agent {message.recipient} is not available")
            
            # Get agent reference
            target_agent = self.agents.get(message.recipient)
            if not target_agent:
                raise AgentNotFoundError(f"Agent {message.recipient} not found in local registry")
            
            # Encrypt sensitive data if needed
            if self._contains_sensitive_data(message.content):
                message.content = await self.security_manager.encrypt_sensitive_data(message.content)
            
            # Add message to processing queue
            await self.message_queue.put(message)
            
            # Process message through target agent
            response = await target_agent.process_message(message)
            
            # Decrypt response if needed
            if self._contains_sensitive_data(response.content):
                response.content = await self.security_manager.decrypt_sensitive_data(response.content)
            
            return response
            
        except Exception as e:
            self.error_count += 1
            self.logger.error(f"Error routing message: {e}")
            
            # Return error response
            error_response = AgentMessage(
                sender="mcp_server",
                recipient=message.sender,
                message_type=MessageType.ERROR,
                content={"error": str(e), "original_message_id": message.correlation_id},
                correlation_id=message.correlation_id
            )
            return error_response
    
    async def broadcast_system_event(self, event: SystemEvent) -> List[AgentMessage]:
        """Broadcast system-wide events to relevant agents"""
        responses = []
        
        try:
            # Determine target agents
            target_agents = event.affected_agents if event.affected_agents else list(self.agents.keys())
            
            # Add event subscribers
            subscribers = self.event_subscribers.get(event.event_type, [])
            target_agents.extend(subscribers)
            target_agents = list(set(target_agents))  # Remove duplicates
            
            # Create broadcast message
            broadcast_message = AgentMessage(
                sender="mcp_server",
                recipient="broadcast",
                message_type=MessageType.EVENT,
                content=event.to_dict(),
                priority="high" if event.severity in ["error", "critical"] else "normal"
            )
            
            # Send to each target agent
            for agent_id in target_agents:
                if agent_id in self.agents:
                    try:
                        agent_message = AgentMessage(
                            sender=broadcast_message.sender,
                            recipient=agent_id,
                            message_type=broadcast_message.message_type,
                            content=broadcast_message.content,
                            correlation_id=broadcast_message.correlation_id,
                            priority=broadcast_message.priority
                        )
                        
                        response = await self.route_message(agent_message)
                        responses.append(response)
                        
                    except Exception as e:
                        self.logger.error(f"Error broadcasting to agent {agent_id}: {e}")
            
            self.logger.info(f"Broadcasted event {event.event_type} to {len(target_agents)} agents")
            
        except Exception as e:
            self.logger.error(f"Error broadcasting system event: {e}")
        
        return responses
    
    async def coordinate_multi_agent_task(self, task: MultiAgentTask) -> TaskResult:
        """Coordinate complex tasks requiring multiple agents"""
        try:
            self.active_tasks[task.task_id] = task
            start_time = datetime.now()
            
            task_result = TaskResult(
                task_id=task.task_id,
                status="running"
            )
            
            if task.coordination_strategy == "sequential":
                task_result = await self._execute_sequential_task(task)
            elif task.coordination_strategy == "parallel":
                task_result = await self._execute_parallel_task(task)
            elif task.coordination_strategy == "conditional":
                task_result = await self._execute_conditional_task(task)
            else:
                raise ValueError(f"Unknown coordination strategy: {task.coordination_strategy}")
            
            # Calculate execution time
            end_time = datetime.now()
            task_result.execution_time_seconds = (end_time - start_time).total_seconds()
            task_result.completed_at = end_time
            
            # Remove from active tasks
            self.active_tasks.pop(task.task_id, None)
            
            return task_result
            
        except Exception as e:
            self.logger.error(f"Error coordinating multi-agent task: {e}")
            return TaskResult(
                task_id=task.task_id,
                status="failure",
                errors=[str(e)]
            )
    
    async def register_agent(self, agent: IAgentCore) -> bool:
        """Register agent with MCP server"""
        try:
            agent_id = agent.agent_id
            
            # Register with agent registry (includes health check and capability indexing)
            if not await self.agent_registry.register_agent(agent):
                self.logger.error(f"Failed to register agent {agent_id} with registry")
                return False
            
            # Keep backward compatibility
            self.agents[agent_id] = agent
            
            # Broadcast agent registration event
            registration_event = SystemEvent(
                event_type="agent_registered",
                source="mcp_server",
                data={
                    "agent_id": agent_id,
                    "capabilities": [cap.name for cap in agent.capabilities]
                },
                severity="info"
            )
            await self.broadcast_system_event(registration_event)
            
            self.logger.info(f"Agent {agent_id} registered successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error registering agent: {e}")
            return False
    
    async def unregister_agent(self, agent_id: str) -> bool:
        """Unregister agent from MCP server"""
        try:
            # Unregister from agent registry
            await self.agent_registry.unregister_agent(agent_id)
            
            # Remove from local registry for backward compatibility
            if agent_id in self.agents:
                agent = self.agents.pop(agent_id)
                # Shutdown agent gracefully
                await agent.shutdown()
            
            # Broadcast agent unregistration event
            unregistration_event = SystemEvent(
                event_type="agent_unregistered",
                source="mcp_server",
                data={"agent_id": agent_id},
                severity="info"
            )
            await self.broadcast_system_event(unregistration_event)
            
            self.logger.info(f"Agent {agent_id} unregistered successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error unregistering agent: {e}")
            return False
    
    async def get_agent_status(self, agent_id: str) -> Dict[str, Any]:
        """Get status of specific agent"""
        try:
            # Get status from agent registry (includes more detailed information)
            registry_status = await self.agent_registry.get_agent_status(agent_id)
            
            if registry_status:
                return registry_status
            else:
                return {"error": f"Agent {agent_id} not found"}
            
        except Exception as e:
            self.logger.error(f"Error getting agent status: {e}")
            return {"error": str(e)}
    
    def subscribe_to_events(self, agent_id: str, event_types: List[str]) -> bool:
        """Subscribe agent to specific event types"""
        try:
            for event_type in event_types:
                if event_type not in self.event_subscribers:
                    self.event_subscribers[event_type] = []
                
                if agent_id not in self.event_subscribers[event_type]:
                    self.event_subscribers[event_type].append(agent_id)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error subscribing to events: {e}")
            return False
    
    def unsubscribe_from_events(self, agent_id: str, event_types: List[str]) -> bool:
        """Unsubscribe agent from specific event types"""
        try:
            for event_type in event_types:
                if event_type in self.event_subscribers:
                    if agent_id in self.event_subscribers[event_type]:
                        self.event_subscribers[event_type].remove(agent_id)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error unsubscribing from events: {e}")
            return False
    
    async def _message_processing_loop(self) -> None:
        """Main message processing loop"""
        while self.server_running:
            try:
                # Process messages from queue
                message = await asyncio.wait_for(self.message_queue.get(), timeout=1.0)
                
                # Handle message based on type
                handler = self.message_handlers.get(message.message_type.value)
                if handler:
                    await handler(message)
                else:
                    self.logger.warning(f"No handler for message type: {message.message_type}")
                
            except asyncio.TimeoutError:
                # No messages to process, continue
                continue
            except Exception as e:
                self.logger.error(f"Error in message processing loop: {e}")
    
    async def _health_monitoring_loop(self) -> None:
        """Health monitoring loop for all agents"""
        while self.server_running:
            try:
                unhealthy_agents = []
                
                for agent_id, agent in self.agents.items():
                    try:
                        if not await agent.health_check():
                            unhealthy_agents.append(agent_id)
                    except Exception as e:
                        self.logger.error(f"Health check failed for agent {agent_id}: {e}")
                        unhealthy_agents.append(agent_id)
                
                # Broadcast health alerts if needed
                if unhealthy_agents:
                    health_alert = SystemEvent(
                        event_type="health_alert",
                        source="mcp_server",
                        data={"unhealthy_agents": unhealthy_agents},
                        severity="warning"
                    )
                    await self.broadcast_system_event(health_alert)
                
                # Wait before next health check
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                self.logger.error(f"Error in health monitoring loop: {e}")
    
    async def _execute_sequential_task(self, task: MultiAgentTask) -> TaskResult:
        """Execute task with sequential agent coordination"""
        result = TaskResult(task_id=task.task_id, status="success")
        agent_tasks = task.get_agent_tasks()
        
        for agent_id in task.participating_agents:
            if agent_id not in agent_tasks:
                continue
            
            try:
                agent = self.agents.get(agent_id)
                if not agent:
                    result.errors.append(f"Agent {agent_id} not found")
                    continue
                
                # Execute agent-specific task
                agent_task = agent_tasks[agent_id]
                agent_result = await agent.execute_action(
                    agent_task.get("action", "process_task"),
                    agent_task.get("parameters", {})
                )
                
                result.agent_results[agent_id] = agent_result
                
            except Exception as e:
                result.errors.append(f"Error executing task for agent {agent_id}: {e}")
                result.status = "partial"
        
        if result.errors and not result.agent_results:
            result.status = "failure"
        
        return result
    
    async def _execute_parallel_task(self, task: MultiAgentTask) -> TaskResult:
        """Execute task with parallel agent coordination"""
        result = TaskResult(task_id=task.task_id, status="success")
        agent_tasks = task.get_agent_tasks()
        
        # Create tasks for parallel execution
        parallel_tasks = []
        for agent_id in task.participating_agents:
            if agent_id in agent_tasks:
                parallel_tasks.append(self._execute_agent_task(agent_id, agent_tasks[agent_id]))
        
        # Execute all tasks in parallel
        try:
            agent_results = await asyncio.gather(*parallel_tasks, return_exceptions=True)
            
            for i, agent_result in enumerate(agent_results):
                agent_id = task.participating_agents[i]
                
                if isinstance(agent_result, Exception):
                    result.errors.append(f"Error executing task for agent {agent_id}: {agent_result}")
                    result.status = "partial"
                else:
                    result.agent_results[agent_id] = agent_result
            
        except Exception as e:
            result.errors.append(f"Error in parallel execution: {e}")
            result.status = "failure"
        
        if result.errors and not result.agent_results:
            result.status = "failure"
        
        return result
    
    async def _execute_conditional_task(self, task: MultiAgentTask) -> TaskResult:
        """Execute task with conditional agent coordination"""
        # Simplified conditional logic - can be extended
        return await self._execute_sequential_task(task)
    
    async def _execute_agent_task(self, agent_id: str, agent_task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task for specific agent"""
        agent = self.agents.get(agent_id)
        if not agent:
            raise AgentNotFoundError(f"Agent {agent_id} not found")
        
        return await agent.execute_action(
            agent_task.get("action", "process_task"),
            agent_task.get("parameters", {})
        )
    
    def _contains_sensitive_data(self, content: Dict[str, Any]) -> bool:
        """Check if content contains sensitive data"""
        sensitive_keys = ["password", "token", "key", "secret", "credential"]
        
        def check_dict(d):
            if isinstance(d, dict):
                for key, value in d.items():
                    if any(sensitive_key in key.lower() for sensitive_key in sensitive_keys):
                        return True
                    if isinstance(value, (dict, list)):
                        if check_dict(value):
                            return True
            elif isinstance(d, list):
                for item in d:
                    if check_dict(item):
                        return True
            return False
        
        return check_dict(content)
    
    # Message handlers
    async def _handle_request(self, message: AgentMessage) -> None:
        """Handle request messages"""
        self.logger.debug(f"Handling request from {message.sender} to {message.recipient}")
    
    async def _handle_response(self, message: AgentMessage) -> None:
        """Handle response messages"""
        self.logger.debug(f"Handling response from {message.sender} to {message.recipient}")
    
    async def _handle_notification(self, message: AgentMessage) -> None:
        """Handle notification messages"""
        self.logger.debug(f"Handling notification from {message.sender}")
    
    async def _handle_command(self, message: AgentMessage) -> None:
        """Handle command messages"""
        self.logger.debug(f"Handling command from {message.sender}")
    
    async def _handle_event(self, message: AgentMessage) -> None:
        """Handle event messages"""
        self.logger.debug(f"Handling event from {message.sender}")
    
    async def _handle_error(self, message: AgentMessage) -> None:
        """Handle error messages"""
        self.logger.error(f"Handling error from {message.sender}: {message.content}")
    
    async def _handle_heartbeat(self, message: AgentMessage) -> None:
        """Handle heartbeat messages"""
        self.logger.debug(f"Heartbeat from {message.sender}")
    
    def get_server_stats(self) -> Dict[str, Any]:
        """Get server statistics"""
        uptime = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        registry_stats = self.agent_registry.get_registry_stats()
        
        return {
            "server_running": self.server_running,
            "uptime_seconds": uptime,
            "registered_agents": len(self.agents),
            "active_tasks": len(self.active_tasks),
            "message_count": self.message_count,
            "error_count": self.error_count,
            "error_rate": self.error_count / max(self.message_count, 1) * 100,
            "registry_stats": registry_stats
        }
    
    async def discover_agents_by_capability(self, capability_name: str, 
                                          load_balance: bool = True) -> List[str]:
        """Discover agents by capability with load balancing"""
        return await self.agent_registry.discover_agents_by_capability(capability_name, load_balance)
    
    async def discover_agents_by_type(self, agent_type: str) -> List[str]:
        """Discover agents by type"""
        return await self.agent_registry.discover_agents_by_type(agent_type)
    
    async def get_best_agent_for_capability(self, capability_name: str, 
                                          context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Get the best agent for a specific capability"""
        return await self.agent_registry.get_best_agent_for_capability(capability_name, context)
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health"""
        system_health = await self.agent_registry.get_system_health()
        return {
            "overall_status": system_health.overall_status,
            "agent_statuses": system_health.agent_statuses,
            "system_metrics": system_health.system_metrics,
            "active_alerts": system_health.active_alerts,
            "timestamp": system_health.timestamp.isoformat()
        }
    
    async def update_agent_load(self, agent_id: str, load_score: float) -> bool:
        """Update agent load score for load balancing"""
        return await self.agent_registry.update_agent_load(agent_id, load_score)
    
    async def set_agent_failover(self, agent_id: str, failover_agents: List[str]) -> bool:
        """Set failover agents for high availability"""
        return await self.agent_registry.set_agent_failover(agent_id, failover_agents)