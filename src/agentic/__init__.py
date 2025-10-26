"""
Agentic AI System for Vismaya DemandOps
Core infrastructure for autonomous multi-agent operations
"""

from .system_factory import AgenticSystemFactory, create_agentic_system, DEFAULT_CONFIG
from .core.interfaces import (
    IAgentCore, IOrchestrator, ISpecializedAgent, IApprovalAgent,
    IMCPServer, IStrandsFramework, IContextManager, IMemoryStore,
    ISecurityManager
)
from .core.models import (
    AgentMessage, AgentState, DecisionProposal, WorkflowDefinition,
    SystemEvent, AgentCapability, AgentConfiguration
)
from .core.base_agent import BaseAgent
from .agents import OrchestratorAgent

__version__ = "1.0.0"

__all__ = [
    # Factory
    "AgenticSystemFactory",
    "create_agentic_system",
    "DEFAULT_CONFIG",
    
    # Core interfaces
    "IAgentCore",
    "IOrchestrator", 
    "ISpecializedAgent",
    "IApprovalAgent",
    "IMCPServer",
    "IStrandsFramework",
    "IContextManager",
    "IMemoryStore",
    "ISecurityManager",
    
    # Core models
    "AgentMessage",
    "AgentState",
    "DecisionProposal",
    "WorkflowDefinition",
    "SystemEvent",
    "AgentCapability",
    "AgentConfiguration",
    
    # Base classes
    "BaseAgent",
    
    # Agents
    "OrchestratorAgent"
]