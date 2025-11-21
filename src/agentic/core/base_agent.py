"""
Base agent implementation for the agentic AI system
Provides common functionality for all agents
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

from .interfaces import IAgentCore, IStrandsFramework, IMCPServer, IAgentErrorHandler
from .models import (
    AgentMessage, AgentState, AgentCapability, AgentConfiguration,
    MessageType, AgentStatus, SystemEvent, AgentMetrics
)


class BaseAgent(IAgentCore):
    """
    Base implementation for all agents in the agentic system
    Provides common functionality like message handling, state management, and health monitoring
    """
    
    def __init__(
        self,
        agent_id: str,
        agent_type: str,
        capabilities: List[AgentCapability],
        config: Dict[str, Any],
        strands_framework: Optional[IStrandsFramework] = None,
        mcp_server: Optional[IMCPServer] = None,
        error_handler: Optional[IAgentErrorHandler] = None
    ):
        self._agent_id = agent_id
        self._agent_type = agent_type
        self._capabilities = capabilities
        self.config = config
        self.strands_framework = strands_framework
        self.mcp_server = mcp_server
        self.error_handler = error_handler
        
        # Initialize logging
        self.logger = logging.getLogger(f"{__name__}.{agent_id}")
        
        # Agent state
        self._state = AgentState(
            agent_id=agent_id,
            status=AgentStatus.INITIALIZING
        )
        
        # Performance metrics
        self._metrics = AgentMetrics(agent_id=agent_id)
        
        # Message handling
        self.message_handlers: Dict[str, callable] = {}
        self.action_handlers: Dict[str, callable] = {}
        
        # Task management
        self.current_tasks: Dict[str, Dict[str, Any]] = {}
        self.task_queue = asyncio.Queue()
        
        # Health monitoring
        self.start_time = datetime.now()
        self.last_heartbeat = datetime.now()
        self.health_check_interval = config.get("health_check_interval", 30)
        
        # Setup default handlers
        self._setup_default_handlers()
    
    @property
    def agent_id(self) -> str:
        """Get unique agent identifier"""
        return self._agent_id
    
    @property
    def capabilities(self) -> List[AgentCapability]:
        """Get agent capabilities"""
        return self._capabilities
    
    def _setup_default_handlers(self) -> None:
        """Setup default message and action handlers"""
        # Default message handlers
        self.message_handlers.update({
            MessageType.REQUEST.value: self._handle_request,
            MessageType.RESPONSE.value: self._handle_response,
            MessageType.NOTIFICATION.value: self._handle_notification,
            MessageType.COMMAND.value: self._handle_command,
            MessageType.EVENT.value: self._handle_event,
            MessageType.ERROR.value: self._handle_error,
            MessageType.HEARTBEAT.value: self._handle_heartbeat
        })
        
        # Default action handlers
        self.action_handlers.update({
            "health_check": self._action_health_check,
            "get_state": self._action_get_state,
            "get_metrics": self._action_get_metrics,
            "get_capabilities": self._action_get_capabilities,
            "update_config": self._action_update_config
        })
    
    async def initialize(self) -> bool:
        """Initialize agent with required dependencies"""
        try:
            self.logger.info(f"Initializing agent {self.agent_id}")
            
            # Update state
            self._state.status = AgentStatus.INITIALIZING
            self._state.last_updated = datetime.now()
            
            # Initialize Strands framework connection
            if self.strands_framework:
                await self._initialize_strands_connection()
            
            # Register with MCP server
            if self.mcp_server:
                await self.mcp_server.register_agent(self)
            
            # Start background tasks
            asyncio.create_task(self._task_processing_loop())
            asyncio.create_task(self._health_monitoring_loop())
            asyncio.create_task(self._metrics_collection_loop())
            
            # Perform agent-specific initialization
            await self._agent_specific_initialization()
            
            # Update state to active
            self._state.status = AgentStatus.ACTIVE
            self._state.last_updated = datetime.now()
            
            # Store initial state
            if self.strands_framework:
                await self.strands_framework.update_context(
                    self.agent_id,
                    {"initialization_completed": datetime.now().isoformat()}
                )
            
            self.logger.info(f"Agent {self.agent_id} initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing agent {self.agent_id}: {e}")
            self._state.status = AgentStatus.ERROR
            self._state.record_error(str(e))
            return False
    
    async def process_message(self, message: AgentMessage) -> AgentMessage:
        """Process incoming message and return response"""
        try:
            self._metrics.messages_processed += 1
            start_time = datetime.now()
            
            # Update last activity
            self.last_heartbeat = datetime.now()
            
            # Get message handler
            handler = self.message_handlers.get(message.message_type.value)
            
            if not handler:
                error_msg = f"No handler for message type: {message.message_type.value}"
                self.logger.warning(error_msg)
                
                return AgentMessage(
                    sender=self.agent_id,
                    recipient=message.sender,
                    message_type=MessageType.ERROR,
                    content={"error": error_msg},
                    correlation_id=message.correlation_id
                )
            
            # Process message
            response = await handler(message)
            
            # Update metrics
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            self._update_response_time_metric(processing_time)
            
            # Store conversation if Strands is available
            if self.strands_framework and message.message_type != MessageType.HEARTBEAT:
                thread_id = message.metadata.get("thread_id")
                if not thread_id:
                    thread_id = await self.strands_framework.create_conversation_thread([message.sender, self.agent_id])
                
                await self.strands_framework.store_conversation_message(thread_id, message)
                await self.strands_framework.store_conversation_message(thread_id, response)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            self._state.record_error(str(e))
            self._metrics.error_rate = self._state.error_count / max(self._metrics.messages_processed, 1)
            
            # Use error handler if available
            if self.error_handler:
                asyncio.create_task(self.error_handler.handle_agent_failure(self.agent_id, e))
            
            return AgentMessage(
                sender=self.agent_id,
                recipient=message.sender,
                message_type=MessageType.ERROR,
                content={"error": str(e)},
                correlation_id=message.correlation_id
            )
    
    async def execute_action(self, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute specific agent action"""
        try:
            start_time = datetime.now()
            
            # Check if action is supported
            if action not in self.action_handlers:
                available_actions = list(self.action_handlers.keys())
                raise ValueError(f"Action '{action}' not supported. Available actions: {available_actions}")
            
            # Validate action capability
            capability = self._get_capability_for_action(action)
            if capability and not capability.validate_input(parameters):
                raise ValueError(f"Invalid parameters for action '{action}'")
            
            # Execute action
            handler = self.action_handlers[action]
            result = await handler(parameters)
            
            # Update metrics
            self._metrics.tasks_completed += 1
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Log successful execution
            self.logger.debug(f"Action '{action}' executed successfully in {execution_time:.2f}s")
            
            return {
                "success": True,
                "result": result,
                "execution_time_seconds": execution_time,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error executing action '{action}': {e}")
            self._metrics.tasks_failed += 1
            self._state.record_error(str(e))
            
            # Use error handler if available
            if self.error_handler:
                asyncio.create_task(self.error_handler.handle_agent_failure(self.agent_id, e))
            
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_state(self) -> AgentState:
        """Get current agent state"""
        # Update performance metrics
        uptime = (datetime.now() - self.start_time).total_seconds()
        self._state.uptime_seconds = uptime
        self._state.performance_metrics.update({
            "messages_processed": self._metrics.messages_processed,
            "tasks_completed": self._metrics.tasks_completed,
            "tasks_failed": self._metrics.tasks_failed,
            "success_rate": self._metrics.calculate_success_rate(),
            "average_response_time_ms": self._metrics.average_response_time_ms
        })
        
        return self._state
    
    async def health_check(self) -> bool:
        """Perform agent health check"""
        try:
            # Check basic health indicators
            current_time = datetime.now()
            
            # Check if agent is responsive (last heartbeat within reasonable time)
            time_since_heartbeat = (current_time - self.last_heartbeat).total_seconds()
            if time_since_heartbeat > self.health_check_interval * 2:
                self.logger.warning(f"Agent {self.agent_id} may be unresponsive")
                return False
            
            # Check error rate
            if self._metrics.error_rate > 0.5:  # More than 50% error rate
                self.logger.warning(f"Agent {self.agent_id} has high error rate: {self._metrics.error_rate:.2%}")
                return False
            
            # Check agent-specific health
            agent_health = await self._agent_specific_health_check()
            
            # Update state based on health
            if agent_health and self._state.status == AgentStatus.ERROR:
                self._state.status = AgentStatus.ACTIVE
            elif not agent_health and self._state.status == AgentStatus.ACTIVE:
                self._state.status = AgentStatus.ERROR
            
            return agent_health
            
        except Exception as e:
            self.logger.error(f"Error in health check: {e}")
            return False
    
    async def shutdown(self) -> bool:
        """Gracefully shutdown agent"""
        try:
            self.logger.info(f"Shutting down agent {self.agent_id}")
            
            # Update state
            self._state.status = AgentStatus.SHUTTING_DOWN
            self._state.last_updated = datetime.now()
            
            # Complete current tasks
            await self._complete_current_tasks()
            
            # Perform agent-specific cleanup
            await self._agent_specific_cleanup()
            
            # Unregister from MCP server
            if self.mcp_server:
                await self.mcp_server.unregister_agent(self.agent_id)
            
            # Update final state
            self._state.status = AgentStatus.OFFLINE
            self._state.last_updated = datetime.now()
            
            self.logger.info(f"Agent {self.agent_id} shutdown completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Error shutting down agent: {e}")
            return False
    
    # Abstract methods for subclasses to implement
    async def _agent_specific_initialization(self) -> None:
        """Agent-specific initialization logic"""
        pass
    
    async def _agent_specific_health_check(self) -> bool:
        """Agent-specific health check logic"""
        return True
    
    async def _agent_specific_cleanup(self) -> None:
        """Agent-specific cleanup logic"""
        pass
    
    # Default message handlers
    async def _handle_request(self, message: AgentMessage) -> AgentMessage:
        """Handle request messages"""
        # Default implementation - subclasses should override
        return AgentMessage(
            sender=self.agent_id,
            recipient=message.sender,
            message_type=MessageType.RESPONSE,
            content={"status": "request_received", "agent_type": self._agent_type},
            correlation_id=message.correlation_id
        )
    
    async def _handle_response(self, message: AgentMessage) -> AgentMessage:
        """Handle response messages"""
        # Log response and return acknowledgment
        self.logger.debug(f"Received response from {message.sender}")
        
        return AgentMessage(
            sender=self.agent_id,
            recipient=message.sender,
            message_type=MessageType.NOTIFICATION,
            content={"status": "response_acknowledged"},
            correlation_id=message.correlation_id
        )
    
    async def _handle_notification(self, message: AgentMessage) -> AgentMessage:
        """Handle notification messages"""
        self.logger.info(f"Received notification from {message.sender}: {message.content}")
        
        return AgentMessage(
            sender=self.agent_id,
            recipient=message.sender,
            message_type=MessageType.NOTIFICATION,
            content={"status": "notification_received"},
            correlation_id=message.correlation_id
        )
    
    async def _handle_command(self, message: AgentMessage) -> AgentMessage:
        """Handle command messages"""
        command = message.content.get("command")
        parameters = message.content.get("parameters", {})
        
        if command in self.action_handlers:
            result = await self.execute_action(command, parameters)
            return AgentMessage(
                sender=self.agent_id,
                recipient=message.sender,
                message_type=MessageType.RESPONSE,
                content=result,
                correlation_id=message.correlation_id
            )
        else:
            return AgentMessage(
                sender=self.agent_id,
                recipient=message.sender,
                message_type=MessageType.ERROR,
                content={"error": f"Unknown command: {command}"},
                correlation_id=message.correlation_id
            )
    
    async def _handle_event(self, message: AgentMessage) -> AgentMessage:
        """Handle event messages"""
        event_type = message.content.get("event_type")
        self.logger.info(f"Received event {event_type} from {message.sender}")
        
        # Process event based on type
        await self._process_system_event(event_type, message.content)
        
        return AgentMessage(
            sender=self.agent_id,
            recipient=message.sender,
            message_type=MessageType.NOTIFICATION,
            content={"status": "event_processed"},
            correlation_id=message.correlation_id
        )
    
    async def _handle_error(self, message: AgentMessage) -> AgentMessage:
        """Handle error messages"""
        error = message.content.get("error", "Unknown error")
        self.logger.error(f"Received error from {message.sender}: {error}")
        
        return AgentMessage(
            sender=self.agent_id,
            recipient=message.sender,
            message_type=MessageType.NOTIFICATION,
            content={"status": "error_acknowledged"},
            correlation_id=message.correlation_id
        )
    
    async def _handle_heartbeat(self, message: AgentMessage) -> AgentMessage:
        """Handle heartbeat messages"""
        self.last_heartbeat = datetime.now()
        
        return AgentMessage(
            sender=self.agent_id,
            recipient=message.sender,
            message_type=MessageType.HEARTBEAT,
            content={"status": "alive", "timestamp": self.last_heartbeat.isoformat()},
            correlation_id=message.correlation_id
        )
    
    # Default action handlers
    async def _action_health_check(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Health check action"""
        is_healthy = await self.health_check()
        state = await self.get_state()
        
        return {
            "healthy": is_healthy,
            "status": state.status.value,
            "uptime_seconds": state.uptime_seconds,
            "error_count": state.error_count,
            "last_error": state.last_error
        }
    
    async def _action_get_state(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get state action"""
        state = await self.get_state()
        
        return {
            "agent_id": state.agent_id,
            "status": state.status.value,
            "current_task": state.current_task,
            "last_updated": state.last_updated.isoformat(),
            "uptime_seconds": state.uptime_seconds,
            "performance_metrics": state.performance_metrics
        }
    
    async def _action_get_metrics(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get metrics action"""
        return {
            "messages_processed": self._metrics.messages_processed,
            "tasks_completed": self._metrics.tasks_completed,
            "tasks_failed": self._metrics.tasks_failed,
            "success_rate": self._metrics.calculate_success_rate(),
            "average_response_time_ms": self._metrics.average_response_time_ms,
            "error_rate": self._metrics.error_rate,
            "uptime_percentage": self._metrics.uptime_percentage
        }
    
    async def _action_get_capabilities(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get capabilities action"""
        return {
            "agent_id": self.agent_id,
            "agent_type": self._agent_type,
            "capabilities": [
                {
                    "name": cap.name,
                    "description": cap.description,
                    "required_permissions": cap.required_permissions
                }
                for cap in self._capabilities
            ]
        }
    
    async def _action_update_config(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Update configuration action"""
        config_updates = parameters.get("config", {})
        
        # Update configuration
        self.config.update(config_updates)
        
        return {
            "status": "configuration_updated",
            "updated_keys": list(config_updates.keys())
        }
    
    # Helper methods
    def _get_capability_for_action(self, action: str) -> Optional[AgentCapability]:
        """Get capability definition for action"""
        for capability in self._capabilities:
            if capability.name == action:
                return capability
        return None
    
    def _update_response_time_metric(self, response_time_ms: float) -> None:
        """Update average response time metric"""
        if self._metrics.average_response_time_ms == 0:
            self._metrics.average_response_time_ms = response_time_ms
        else:
            # Exponential moving average
            alpha = 0.1
            self._metrics.average_response_time_ms = (
                alpha * response_time_ms + 
                (1 - alpha) * self._metrics.average_response_time_ms
            )
    
    async def _initialize_strands_connection(self) -> None:
        """Initialize connection to Strands framework"""
        try:
            # Update agent context
            await self.strands_framework.update_context(
                self.agent_id,
                {
                    "agent_type": self._agent_type,
                    "capabilities": [cap.name for cap in self._capabilities],
                    "initialized_at": datetime.now().isoformat()
                }
            )
            
            self.logger.info(f"Connected to Strands framework")
            
        except Exception as e:
            self.logger.error(f"Error connecting to Strands framework: {e}")
            raise
    
    async def _task_processing_loop(self) -> None:
        """Background task processing loop"""
        while self._state.status != AgentStatus.OFFLINE:
            try:
                # Process tasks from queue
                task = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                
                # Execute task
                task_id = task.get("task_id", str(uuid.uuid4()))
                self._state.current_task = task_id
                
                await self._execute_background_task(task)
                
                self._state.current_task = None
                
            except asyncio.TimeoutError:
                # No tasks to process
                continue
            except Exception as e:
                self.logger.error(f"Error in task processing loop: {e}")
    
    async def _health_monitoring_loop(self) -> None:
        """Background health monitoring loop"""
        while self._state.status != AgentStatus.OFFLINE:
            try:
                await asyncio.sleep(self.health_check_interval)
                
                # Perform health check
                is_healthy = await self.health_check()
                
                # Update metrics
                self._metrics.uptime_percentage = (
                    100.0 if is_healthy else 
                    max(0.0, self._metrics.uptime_percentage - 1.0)
                )
                
            except Exception as e:
                self.logger.error(f"Error in health monitoring loop: {e}")
    
    async def _metrics_collection_loop(self) -> None:
        """Background metrics collection loop"""
        while self._state.status != AgentStatus.OFFLINE:
            try:
                await asyncio.sleep(60)  # Collect metrics every minute
                
                # Update metrics
                self._metrics.last_updated = datetime.now()
                
                # Store metrics in Strands if available
                if self.strands_framework:
                    await self.strands_framework.update_context(
                        self.agent_id,
                        {
                            "metrics": {
                                "messages_processed": self._metrics.messages_processed,
                                "tasks_completed": self._metrics.tasks_completed,
                                "success_rate": self._metrics.calculate_success_rate(),
                                "last_updated": self._metrics.last_updated.isoformat()
                            }
                        }
                    )
                
            except Exception as e:
                self.logger.error(f"Error in metrics collection loop: {e}")
    
    async def _execute_background_task(self, task: Dict[str, Any]) -> None:
        """Execute background task"""
        # Default implementation - subclasses can override
        task_type = task.get("type", "unknown")
        self.logger.debug(f"Executing background task: {task_type}")
    
    async def _process_system_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """Process system event"""
        # Default implementation - subclasses can override
        self.logger.debug(f"Processing system event: {event_type}")
    
    async def _complete_current_tasks(self) -> None:
        """Complete current tasks before shutdown"""
        # Wait for current task to complete
        if self._state.current_task:
            self.logger.info(f"Waiting for current task {self._state.current_task} to complete")
            # In a real implementation, you might want to add a timeout here
            while self._state.current_task:
                await asyncio.sleep(0.1)
        
        # Process remaining tasks in queue (with timeout)
        timeout = 30  # 30 seconds timeout
        start_time = datetime.now()
        
        while not self.task_queue.empty() and (datetime.now() - start_time).total_seconds() < timeout:
            try:
                task = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                await self._execute_background_task(task)
            except asyncio.TimeoutError:
                break
            except Exception as e:
                self.logger.error(f"Error completing task during shutdown: {e}")