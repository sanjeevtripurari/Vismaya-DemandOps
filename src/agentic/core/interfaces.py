"""
Core agentic AI interfaces and abstract base classes
Following Interface Segregation Principle for agent architecture
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union, Callable
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from .models import (
    AgentMessage, AgentState, DecisionProposal, WorkflowDefinition,
    AgentCapability, AgentConfiguration, SystemEvent, MultiAgentTask,
    TaskResult, ConversationContext, DecisionContext
)


class IAgentCore(ABC):
    """Base interface for all agents in the agentic system"""
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize agent with required dependencies"""
        pass
    
    @abstractmethod
    async def process_message(self, message: AgentMessage) -> AgentMessage:
        """Process incoming message and return response"""
        pass
    
    @abstractmethod
    async def execute_action(self, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute specific agent action"""
        pass
    
    @abstractmethod
    async def get_state(self) -> AgentState:
        """Get current agent state"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Perform agent health check"""
        pass
    
    @abstractmethod
    async def shutdown(self) -> bool:
        """Gracefully shutdown agent"""
        pass
    
    @property
    @abstractmethod
    def agent_id(self) -> str:
        """Get unique agent identifier"""
        pass
    
    @property
    @abstractmethod
    def capabilities(self) -> List[AgentCapability]:
        """Get agent capabilities"""
        pass


class IOrchestrator(IAgentCore):
    """Interface for the orchestrator agent - central coordinator"""
    
    @abstractmethod
    async def route_request(self, request: Dict[str, Any]) -> str:
        """Route request to appropriate agent"""
        pass
    
    @abstractmethod
    async def coordinate_workflow(self, workflow_id: str, steps: List[Dict]) -> Dict[str, Any]:
        """Coordinate multi-agent workflow"""
        pass
    
    @abstractmethod
    async def monitor_system_health(self) -> Dict[str, bool]:
        """Monitor health of all agents"""
        pass
    
    @abstractmethod
    async def register_agent(self, agent: IAgentCore) -> bool:
        """Register new agent with orchestrator"""
        pass
    
    @abstractmethod
    async def unregister_agent(self, agent_id: str) -> bool:
        """Unregister agent from orchestrator"""
        pass
    
    @abstractmethod
    async def get_agent_registry(self) -> Dict[str, AgentConfiguration]:
        """Get registry of all agents"""
        pass


class ISpecializedAgent(IAgentCore):
    """Interface for specialized domain agents"""
    
    @abstractmethod
    async def analyze_domain_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze domain-specific data"""
        pass
    
    @abstractmethod
    async def generate_recommendations(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate domain-specific recommendations"""
        pass
    
    @abstractmethod
    async def create_decision_proposal(self, recommendation: Dict[str, Any]) -> DecisionProposal:
        """Create decision proposal from recommendation"""
        pass
    
    @property
    @abstractmethod
    def domain(self) -> str:
        """Get agent domain (cost, resource, forecasting, etc.)"""
        pass


class IApprovalAgent(IAgentCore):
    """Interface for approval agent - manages decision workflows"""
    
    @abstractmethod
    async def create_proposal(self, proposal_data: Dict[str, Any]) -> DecisionProposal:
        """Create new decision proposal"""
        pass
    
    @abstractmethod
    async def send_approval_request(self, proposal: DecisionProposal) -> bool:
        """Send approval request to stakeholders"""
        pass
    
    @abstractmethod
    async def process_approval_response(self, proposal_id: str, approver: str, decision: str) -> bool:
        """Process approval/rejection response"""
        pass
    
    @abstractmethod
    async def get_pending_proposals(self, approver_id: Optional[str] = None) -> List[DecisionProposal]:
        """Get pending decision proposals"""
        pass
    
    @abstractmethod
    async def get_proposal_status(self, proposal_id: str) -> Dict[str, Any]:
        """Get status of specific proposal"""
        pass
    
    @abstractmethod
    async def execute_approved_proposal(self, proposal_id: str) -> bool:
        """Execute approved decision proposal"""
        pass


class IMCPServer(ABC):
    """Interface for Model Context Protocol server - agent communication"""
    
    @abstractmethod
    async def start_server(self, port: int = 8000) -> bool:
        """Start MCP server"""
        pass
    
    @abstractmethod
    async def stop_server(self) -> bool:
        """Stop MCP server"""
        pass
    
    @abstractmethod
    async def route_message(self, message: AgentMessage) -> AgentMessage:
        """Route message between agents with security validation"""
        pass
    
    @abstractmethod
    async def broadcast_system_event(self, event: SystemEvent) -> List[AgentMessage]:
        """Broadcast system-wide events to relevant agents"""
        pass
    
    @abstractmethod
    async def coordinate_multi_agent_task(self, task: MultiAgentTask) -> TaskResult:
        """Coordinate complex tasks requiring multiple agents"""
        pass
    
    @abstractmethod
    async def register_agent(self, agent: IAgentCore) -> bool:
        """Register agent with MCP server"""
        pass
    
    @abstractmethod
    async def unregister_agent(self, agent_id: str) -> bool:
        """Unregister agent from MCP server"""
        pass
    
    @abstractmethod
    async def get_agent_status(self, agent_id: str) -> Dict[str, Any]:
        """Get status of specific agent"""
        pass


class IStrandsFramework(ABC):
    """Interface for Strands framework - context and memory management"""
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize Strands framework"""
        pass
    
    @abstractmethod
    async def get_shared_context(self, context_keys: List[str]) -> Dict[str, Any]:
        """Retrieve shared context across agents"""
        pass
    
    @abstractmethod
    async def update_context(self, agent_id: str, context_updates: Dict[str, Any]) -> bool:
        """Update agent-specific context"""
        pass
    
    @abstractmethod
    async def create_conversation_thread(self, participants: List[str]) -> str:
        """Create new conversation thread between agents"""
        pass
    
    @abstractmethod
    async def get_conversation_history(self, thread_id: str, limit: int = 50) -> List[AgentMessage]:
        """Get conversation history for context"""
        pass
    
    @abstractmethod
    async def store_conversation_message(self, thread_id: str, message: AgentMessage) -> bool:
        """Store conversation message with full context"""
        pass
    
    @abstractmethod
    async def get_decision_context(self, decision_id: str) -> DecisionContext:
        """Get context for specific decision proposal"""
        pass
    
    @abstractmethod
    async def store_decision_history(self, decision: DecisionProposal) -> bool:
        """Store decision proposal and approval history"""
        pass
    
    @abstractmethod
    async def query_similar_decisions(self, current_decision: DecisionProposal) -> List[DecisionProposal]:
        """Find similar past decisions for context"""
        pass


class IContextManager(ABC):
    """Interface for context management within Strands framework"""
    
    @abstractmethod
    async def get_global_context(self) -> Dict[str, Any]:
        """Get global system context"""
        pass
    
    @abstractmethod
    async def get_agent_context(self, agent_id: str) -> Dict[str, Any]:
        """Get agent-specific context"""
        pass
    
    @abstractmethod
    async def update_global_context(self, updates: Dict[str, Any]) -> bool:
        """Update global system context"""
        pass
    
    @abstractmethod
    async def update_agent_context(self, agent_id: str, updates: Dict[str, Any]) -> bool:
        """Update agent-specific context"""
        pass
    
    @abstractmethod
    async def create_context_snapshot(self, context_id: str) -> str:
        """Create snapshot of current context state"""
        pass
    
    @abstractmethod
    async def restore_context_snapshot(self, snapshot_id: str) -> bool:
        """Restore context from snapshot"""
        pass
    
    @abstractmethod
    async def synchronize_context(self, agent_ids: List[str]) -> bool:
        """Synchronize context between specified agents"""
        pass


class IMemoryStore(ABC):
    """Interface for persistent memory storage"""
    
    @abstractmethod
    async def store_conversation(self, thread_id: str, message: AgentMessage) -> bool:
        """Store conversation message with full context"""
        pass
    
    @abstractmethod
    async def retrieve_conversation_history(self, thread_id: str, limit: int = 50) -> List[AgentMessage]:
        """Retrieve conversation history for context"""
        pass
    
    @abstractmethod
    async def store_agent_state(self, agent_id: str, state: AgentState) -> bool:
        """Store agent state"""
        pass
    
    @abstractmethod
    async def retrieve_agent_state(self, agent_id: str) -> Optional[AgentState]:
        """Retrieve agent state"""
        pass
    
    @abstractmethod
    async def store_decision_proposal(self, proposal: DecisionProposal) -> bool:
        """Store decision proposal"""
        pass
    
    @abstractmethod
    async def retrieve_decision_proposal(self, proposal_id: str) -> Optional[DecisionProposal]:
        """Retrieve decision proposal"""
        pass
    
    @abstractmethod
    async def query_decisions_by_criteria(self, criteria: Dict[str, Any]) -> List[DecisionProposal]:
        """Query decisions by specific criteria"""
        pass
    
    @abstractmethod
    async def store_system_event(self, event: SystemEvent) -> bool:
        """Store system event"""
        pass
    
    @abstractmethod
    async def get_system_events(self, event_type: Optional[str] = None, limit: int = 100) -> List[SystemEvent]:
        """Get system events by type"""
        pass


class ISecurityManager(ABC):
    """Interface for security and authorization management"""
    
    @abstractmethod
    async def validate_sender(self, sender: str, recipient: str) -> bool:
        """Validate if sender is authorized to communicate with recipient"""
        pass
    
    @abstractmethod
    async def validate_action(self, agent_id: str, action: str, context: Dict[str, Any]) -> bool:
        """Validate if agent is authorized to perform specific action"""
        pass
    
    @abstractmethod
    async def encrypt_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt sensitive data in agent communications"""
        pass


class IBackwardCompatibilityManager(ABC):
    """Interface for managing backward compatibility with existing functionality"""
    
    @abstractmethod
    async def ensure_dashboard_compatibility(self, dashboard_instance) -> bool:
        """Ensure dashboard instance maintains backward compatibility"""
        pass
    
    @abstractmethod
    async def ensure_cost_analysis_compatibility(self, cost_service_instance) -> bool:
        """Ensure cost analysis functionality is preserved"""
        pass
    
    @abstractmethod
    async def ensure_forecasting_compatibility(self, forecasting_service_instance) -> bool:
        """Ensure forecasting functionality is enhanced, not replaced"""
        pass
    
    @abstractmethod
    async def validate_compatibility(self) -> Dict[str, bool]:
        """Validate that all compatibility mappings are working"""
        pass
    
    @abstractmethod
    async def get_compatibility_status(self) -> Dict[str, Any]:
        """Get current compatibility status and metrics"""
        pass
    
    @abstractmethod
    async def decrypt_sensitive_data(self, encrypted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt sensitive data from agent communications"""
        pass
    
    @abstractmethod
    async def generate_auth_token(self, agent_id: str, permissions: List[str]) -> str:
        """Generate authentication token for agent"""
        pass
    
    @abstractmethod
    async def validate_auth_token(self, token: str) -> Dict[str, Any]:
        """Validate authentication token"""
        pass
    
    @abstractmethod
    async def get_agent_permissions(self, agent_id: str) -> List[str]:
        """Get permissions for specific agent"""
        pass


class IAgentErrorHandler(ABC):
    """Interface for agent error handling and recovery"""
    
    @abstractmethod
    async def handle_agent_failure(self, agent_id: str, error: Exception) -> bool:
        """Handle agent failure with appropriate recovery strategy"""
        pass
    
    @abstractmethod
    async def retry_with_backoff(self, agent_id: str, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Retry failed action with exponential backoff"""
        pass
    
    @abstractmethod
    async def escalate_error(self, agent_id: str, error: Exception, context: Dict[str, Any]) -> bool:
        """Escalate error to appropriate handlers"""
        pass
    
    @abstractmethod
    async def get_error_history(self, agent_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get error history for agent"""
        pass
    
    @abstractmethod
    async def apply_fallback_strategy(self, agent_id: str, failed_action: str) -> Dict[str, Any]:
        """Apply fallback strategy for failed action"""
        pass


class IWorkflowEngine(ABC):
    """Interface for workflow execution and management"""
    
    @abstractmethod
    async def execute_workflow(self, workflow: WorkflowDefinition) -> TaskResult:
        """Execute workflow definition"""
        pass
    
    @abstractmethod
    async def pause_workflow(self, workflow_id: str) -> bool:
        """Pause running workflow"""
        pass
    
    @abstractmethod
    async def resume_workflow(self, workflow_id: str) -> bool:
        """Resume paused workflow"""
        pass
    
    @abstractmethod
    async def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel running workflow"""
        pass
    
    @abstractmethod
    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get status of workflow execution"""
        pass
    
    @abstractmethod
    async def get_active_workflows(self) -> List[Dict[str, Any]]:
        """Get all active workflows"""
        pass
    
    @abstractmethod
    async def register_workflow_template(self, template: WorkflowDefinition) -> bool:
        """Register workflow template for reuse"""
        pass


# Agent type enumeration for registration and discovery
class AgentType(Enum):
    """Types of agents in the agentic system"""
    ORCHESTRATOR = "orchestrator"
    COST_MANAGEMENT = "cost_management"
    RESOURCE_MANAGEMENT = "resource_management"
    FORECASTING = "forecasting"
    ALERT_MANAGEMENT = "alert_management"
    USER_INTERFACE = "user_interface"
    APPROVAL = "approval"
    SECURITY = "security"
    MONITORING = "monitoring"


# Message priority levels for agent communication
class MessagePriority(Enum):
    """Priority levels for agent messages"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


