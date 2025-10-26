"""
Agentic System Factory
Factory class for initializing and managing the complete agentic AI system
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from .core.interfaces import IStrandsFramework, IMCPServer, IMemoryStore, ISecurityManager
from .core.models import SystemEvent, AgentConfiguration
from .strands.framework import StrandsFramework
from .strands.memory_store import DynamoDBMemoryStore
from .communication.mcp_server import MCPAgentServer
from .communication.security_manager import SecurityManager
from .agents.orchestrator_agent import OrchestratorAgent


class AgenticSystemFactory:
    """
    Factory for creating and managing the complete agentic AI system
    Handles initialization, configuration, and lifecycle management
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # System components
        self.memory_store: Optional[IMemoryStore] = None
        self.security_manager: Optional[ISecurityManager] = None
        self.strands_framework: Optional[IStrandsFramework] = None
        self.mcp_server: Optional[IMCPServer] = None
        self.orchestrator: Optional[OrchestratorAgent] = None
        
        # System state
        self.initialized = False
        self.agents: Dict[str, Any] = {}
        self.system_start_time = None
    
    async def initialize_system(self) -> bool:
        """Initialize the complete agentic AI system"""
        try:
            self.logger.info("Initializing Agentic AI System...")
            self.system_start_time = datetime.now()
            
            # Step 1: Initialize Memory Store
            await self._initialize_memory_store()
            
            # Step 2: Initialize Security Manager
            await self._initialize_security_manager()
            
            # Step 3: Initialize Strands Framework
            await self._initialize_strands_framework()
            
            # Step 4: Initialize MCP Server
            await self._initialize_mcp_server()
            
            # Step 5: Initialize Orchestrator Agent
            await self._initialize_orchestrator()
            
            # Step 6: Start system services
            await self._start_system_services()
            
            self.initialized = True
            self.logger.info("Agentic AI System initialized successfully")
            
            # Broadcast system startup event
            await self._broadcast_system_event("system_started", {
                "initialization_time": self.system_start_time.isoformat(),
                "components_initialized": [
                    "memory_store", "security_manager", "strands_framework", 
                    "mcp_server", "orchestrator"
                ]
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing agentic system: {e}")
            await self._cleanup_on_failure()
            return False
    
    async def shutdown_system(self) -> bool:
        """Gracefully shutdown the agentic AI system"""
        try:
            self.logger.info("Shutting down Agentic AI System...")
            
            # Broadcast shutdown event
            await self._broadcast_system_event("system_shutdown", {
                "shutdown_time": datetime.now().isoformat(),
                "uptime_seconds": (datetime.now() - self.system_start_time).total_seconds() if self.system_start_time else 0
            })
            
            # Shutdown orchestrator
            if self.orchestrator:
                await self.orchestrator.shutdown()
            
            # Shutdown MCP server
            if self.mcp_server:
                await self.mcp_server.stop_server()
            
            # Cleanup components
            self.initialized = False
            self.agents.clear()
            
            self.logger.info("Agentic AI System shutdown completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Error shutting down agentic system: {e}")
            return False
    
    async def add_agent(self, agent_type: str, agent_config: Dict[str, Any]) -> bool:
        """Add a new agent to the system"""
        try:
            if not self.initialized:
                raise RuntimeError("System not initialized")
            
            # Create agent based on type
            agent = await self._create_agent(agent_type, agent_config)
            
            if not agent:
                return False
            
            # Initialize agent
            if not await agent.initialize():
                return False
            
            # Register with orchestrator
            if self.orchestrator:
                await self.orchestrator.register_agent(agent)
            
            # Store agent reference
            self.agents[agent.agent_id] = agent
            
            self.logger.info(f"Added agent {agent.agent_id} of type {agent_type}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding agent: {e}")
            return False
    
    async def remove_agent(self, agent_id: str) -> bool:
        """Remove an agent from the system"""
        try:
            if agent_id not in self.agents:
                return False
            
            agent = self.agents[agent_id]
            
            # Unregister from orchestrator
            if self.orchestrator:
                await self.orchestrator.unregister_agent(agent_id)
            
            # Shutdown agent
            await agent.shutdown()
            
            # Remove from registry
            del self.agents[agent_id]
            
            self.logger.info(f"Removed agent {agent_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error removing agent: {e}")
            return False
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        try:
            status = {
                "initialized": self.initialized,
                "uptime_seconds": (datetime.now() - self.system_start_time).total_seconds() if self.system_start_time else 0,
                "components": {
                    "memory_store": self.memory_store is not None,
                    "security_manager": self.security_manager is not None,
                    "strands_framework": self.strands_framework is not None,
                    "mcp_server": self.mcp_server is not None,
                    "orchestrator": self.orchestrator is not None
                },
                "agents": {
                    "count": len(self.agents),
                    "agent_ids": list(self.agents.keys())
                }
            }
            
            # Get orchestrator status if available
            if self.orchestrator:
                orchestrator_status = await self.orchestrator.execute_action("get_system_status", {})
                status["orchestrator_status"] = orchestrator_status.get("result", {})
            
            # Get MCP server stats if available
            if hasattr(self.mcp_server, 'get_server_stats'):
                status["mcp_server_stats"] = self.mcp_server.get_server_stats()
            
            # Get Strands framework stats if available
            if hasattr(self.strands_framework, 'get_framework_stats'):
                status["strands_stats"] = self.strands_framework.get_framework_stats()
            
            return status
            
        except Exception as e:
            self.logger.error(f"Error getting system status: {e}")
            return {"error": str(e)}
    
    async def _initialize_memory_store(self) -> None:
        """Initialize memory store component"""
        try:
            memory_config = self.config.get("memory_store", {})
            memory_config.update({
                "aws_region": self.config.get("aws_region", "us-east-1"),
                "table_prefix": self.config.get("table_prefix", "vismaya-agentic")
            })
            
            self.memory_store = DynamoDBMemoryStore(memory_config)
            self.logger.info("Memory store initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing memory store: {e}")
            raise
    
    async def _initialize_security_manager(self) -> None:
        """Initialize security manager component"""
        try:
            security_config = self.config.get("security", {})
            self.security_manager = SecurityManager(security_config)
            self.logger.info("Security manager initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing security manager: {e}")
            raise
    
    async def _initialize_strands_framework(self) -> None:
        """Initialize Strands framework component"""
        try:
            strands_config = self.config.get("strands", {})
            self.strands_framework = StrandsFramework(self.memory_store, strands_config)
            
            if not await self.strands_framework.initialize(strands_config):
                raise RuntimeError("Failed to initialize Strands framework")
            
            self.logger.info("Strands framework initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing Strands framework: {e}")
            raise
    
    async def _initialize_mcp_server(self) -> None:
        """Initialize MCP server component"""
        try:
            self.mcp_server = MCPAgentServer(self.security_manager)
            
            mcp_port = self.config.get("mcp_server", {}).get("port", 8000)
            if not await self.mcp_server.start_server(mcp_port):
                raise RuntimeError("Failed to start MCP server")
            
            self.logger.info(f"MCP server initialized on port {mcp_port}")
            
        except Exception as e:
            self.logger.error(f"Error initializing MCP server: {e}")
            raise
    
    async def _initialize_orchestrator(self) -> None:
        """Initialize orchestrator agent"""
        try:
            orchestrator_config = self.config.get("orchestrator", {})
            self.orchestrator = OrchestratorAgent(
                config=orchestrator_config,
                strands_framework=self.strands_framework,
                mcp_server=self.mcp_server
            )
            
            if not await self.orchestrator.initialize():
                raise RuntimeError("Failed to initialize orchestrator agent")
            
            self.agents["orchestrator"] = self.orchestrator
            self.logger.info("Orchestrator agent initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing orchestrator: {e}")
            raise
    
    async def _start_system_services(self) -> None:
        """Start background system services"""
        try:
            # Start system monitoring
            asyncio.create_task(self._system_monitoring_loop())
            
            # Start health checks
            asyncio.create_task(self._health_check_loop())
            
            self.logger.info("System services started")
            
        except Exception as e:
            self.logger.error(f"Error starting system services: {e}")
            raise
    
    async def _create_agent(self, agent_type: str, agent_config: Dict[str, Any]) -> Optional[Any]:
        """Create agent instance based on type"""
        try:
            # This is where you would add logic to create different types of agents
            # For now, we only have the orchestrator implemented
            
            if agent_type == "orchestrator":
                return OrchestratorAgent(
                    config=agent_config,
                    strands_framework=self.strands_framework,
                    mcp_server=self.mcp_server
                )
            else:
                self.logger.error(f"Unknown agent type: {agent_type}")
                return None
            
        except Exception as e:
            self.logger.error(f"Error creating agent of type {agent_type}: {e}")
            return None
    
    async def _broadcast_system_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Broadcast system event"""
        try:
            if self.mcp_server:
                event = SystemEvent(
                    event_type=event_type,
                    source="system_factory",
                    data=data,
                    severity="info"
                )
                await self.mcp_server.broadcast_system_event(event)
            
        except Exception as e:
            self.logger.error(f"Error broadcasting system event: {e}")
    
    async def _cleanup_on_failure(self) -> None:
        """Cleanup resources on initialization failure"""
        try:
            if self.mcp_server:
                await self.mcp_server.stop_server()
            
            self.memory_store = None
            self.security_manager = None
            self.strands_framework = None
            self.mcp_server = None
            self.orchestrator = None
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    async def _system_monitoring_loop(self) -> None:
        """Background system monitoring loop"""
        while self.initialized:
            try:
                await asyncio.sleep(60)  # Monitor every minute
                
                # Check system health
                if self.orchestrator:
                    health_status = await self.orchestrator.monitor_system_health()
                    
                    # Log system health
                    healthy_agents = sum(1 for healthy in health_status.values() if healthy)
                    total_agents = len(health_status)
                    
                    self.logger.info(f"System health: {healthy_agents}/{total_agents} agents healthy")
                
            except Exception as e:
                self.logger.error(f"Error in system monitoring: {e}")
    
    async def _health_check_loop(self) -> None:
        """Background health check loop"""
        while self.initialized:
            try:
                await asyncio.sleep(30)  # Health check every 30 seconds
                
                # Check all agents
                for agent_id, agent in self.agents.items():
                    try:
                        is_healthy = await agent.health_check()
                        if not is_healthy:
                            self.logger.warning(f"Agent {agent_id} failed health check")
                    except Exception as e:
                        self.logger.error(f"Error checking health of agent {agent_id}: {e}")
                
            except Exception as e:
                self.logger.error(f"Error in health check loop: {e}")


# Convenience function for creating and initializing the system
async def create_agentic_system(config: Dict[str, Any]) -> AgenticSystemFactory:
    """
    Convenience function to create and initialize the agentic AI system
    
    Args:
        config: System configuration dictionary
        
    Returns:
        Initialized AgenticSystemFactory instance
    """
    factory = AgenticSystemFactory(config)
    
    if await factory.initialize_system():
        return factory
    else:
        raise RuntimeError("Failed to initialize agentic AI system")


# Default configuration template
DEFAULT_CONFIG = {
    "aws_region": "us-east-1",
    "table_prefix": "vismaya-agentic",
    "memory_store": {
        "aws_region": "us-east-1",
        "table_prefix": "vismaya-agentic"
    },
    "security": {
        "jwt_secret": None,  # Will be auto-generated
        "jwt_algorithm": "HS256",
        "token_expiry_hours": 24,
        "encryption_key_file": ".encryption_key"
    },
    "strands": {
        "sync_interval_seconds": 60
    },
    "mcp_server": {
        "port": 8000
    },
    "orchestrator": {
        "health_check_interval": 30
    }
}