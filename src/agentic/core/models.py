"""
Core data models for agentic AI system
Agent communication, state management, and decision proposals
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from enum import Enum
import uuid
import json


class MessageType(Enum):
    """Types of messages between agents"""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    COMMAND = "command"
    EVENT = "event"
    ERROR = "error"
    HEARTBEAT = "heartbeat"


class AgentStatus(Enum):
    """Agent operational status"""
    INITIALIZING = "initializing"
    ACTIVE = "active"
    BUSY = "busy"
    IDLE = "idle"
    ERROR = "error"
    SHUTTING_DOWN = "shutting_down"
    OFFLINE = "offline"


class DecisionStatus(Enum):
    """Status of decision proposals"""
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowStatus(Enum):
    """Status of workflow execution"""
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RiskLevel(Enum):
    """Risk levels for decisions and actions"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AgentMessage:
    """Message structure for inter-agent communication"""
    sender: str
    recipient: str
    message_type: MessageType
    content: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    priority: str = "normal"  # low, normal, high, critical, emergency
    requires_response: bool = False
    response_timeout: Optional[int] = None  # seconds
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for serialization"""
        return {
            "sender": self.sender,
            "recipient": self.recipient,
            "message_type": self.message_type.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id,
            "priority": self.priority,
            "requires_response": self.requires_response,
            "response_timeout": self.response_timeout,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentMessage':
        """Create message from dictionary"""
        return cls(
            sender=data["sender"],
            recipient=data["recipient"],
            message_type=MessageType(data["message_type"]),
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            correlation_id=data["correlation_id"],
            priority=data.get("priority", "normal"),
            requires_response=data.get("requires_response", False),
            response_timeout=data.get("response_timeout"),
            metadata=data.get("metadata", {})
        )


@dataclass
class AgentState:
    """Current state of an agent"""
    agent_id: str
    status: AgentStatus
    current_task: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.now)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    error_count: int = 0
    last_error: Optional[str] = None
    uptime_seconds: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    
    def update_performance(self, metrics: Dict[str, float]) -> None:
        """Update performance metrics"""
        self.performance_metrics.update(metrics)
        self.last_updated = datetime.now()
    
    def record_error(self, error_message: str) -> None:
        """Record an error occurrence"""
        self.error_count += 1
        self.last_error = error_message
        self.last_updated = datetime.now()
    
    def is_healthy(self) -> bool:
        """Check if agent is in healthy state"""
        return (
            self.status in [AgentStatus.ACTIVE, AgentStatus.IDLE] and
            self.error_count < 10 and  # Threshold for error tolerance
            self.cpu_usage_percent < 90 and
            self.memory_usage_mb < 1000  # 1GB threshold
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert agent state to dictionary for serialization"""
        return {
            "agent_id": self.agent_id,
            "status": self.status.value,  # Convert enum to string value
            "current_task": self.current_task,
            "context": self.context,
            "last_updated": self.last_updated.isoformat(),
            "performance_metrics": self.performance_metrics,
            "error_count": self.error_count,
            "last_error": self.last_error,
            "uptime_seconds": self.uptime_seconds,
            "memory_usage_mb": self.memory_usage_mb,
            "cpu_usage_percent": self.cpu_usage_percent
        }


@dataclass
class AgentCapability:
    """Capability definition for an agent"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    required_permissions: List[str] = field(default_factory=list)
    execution_time_estimate: Optional[int] = None  # seconds
    resource_requirements: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input against schema (simplified validation)"""
        # In a real implementation, use jsonschema or similar
        required_fields = self.input_schema.get("required", [])
        return all(field in input_data for field in required_fields)


@dataclass
class AgentConfiguration:
    """Configuration for an agent"""
    agent_id: str
    agent_type: str
    capabilities: List[AgentCapability]
    dependencies: List[str] = field(default_factory=list)
    resource_limits: Dict[str, Any] = field(default_factory=dict)
    security_context: Dict[str, Any] = field(default_factory=dict)
    initialization_params: Dict[str, Any] = field(default_factory=dict)
    health_check_interval: int = 30  # seconds
    max_concurrent_tasks: int = 5
    retry_policy: Dict[str, Any] = field(default_factory=dict)
    
    def get_capability(self, name: str) -> Optional[AgentCapability]:
        """Get capability by name"""
        for capability in self.capabilities:
            if capability.name == name:
                return capability
        return None


@dataclass
class DecisionImpactAnalysis:
    """Analysis of decision impact"""
    cost_impact: float
    risk_assessment: RiskLevel
    affected_resources: List[str]
    timeline_impact: str
    rollback_plan: Optional[str] = None
    success_metrics: List[str] = field(default_factory=list)
    stakeholder_impact: Dict[str, str] = field(default_factory=dict)
    compliance_considerations: List[str] = field(default_factory=list)
    
    def get_impact_summary(self) -> str:
        """Get summary of impact analysis"""
        return f"Cost: ${self.cost_impact:.2f}, Risk: {self.risk_assessment.value}, Resources: {len(self.affected_resources)}"


@dataclass
class ApprovalRule:
    """Rules for decision approval"""
    rule_id: str
    condition: str  # JSON logic expression or simple condition
    required_approvers: List[str]
    approval_threshold: int = 1  # number of approvals needed
    auto_approve_conditions: Optional[Dict[str, Any]] = None
    escalation_rules: List[Dict[str, Any]] = field(default_factory=list)
    timeout_hours: int = 24
    
    def matches_decision(self, decision: 'DecisionProposal') -> bool:
        """Check if rule applies to decision (simplified logic)"""
        # In real implementation, use proper condition evaluation
        if "cost_threshold" in self.condition:
            threshold = float(self.condition.split(":")[-1])
            return decision.estimated_cost_impact >= threshold
        return True


@dataclass
class DecisionProposal:
    """Decision proposal requiring approval"""
    proposal_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    impact_analysis: Optional[DecisionImpactAnalysis] = None
    recommendations: List[str] = field(default_factory=list)
    required_approvers: List[str] = field(default_factory=list)
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    status: DecisionStatus = DecisionStatus.DRAFT
    approval_deadline: Optional[datetime] = None
    estimated_cost_impact: float = 0.0
    risk_level: RiskLevel = RiskLevel.LOW
    approval_responses: List[Dict[str, Any]] = field(default_factory=list)
    execution_plan: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_approval_response(self, approver: str, decision: str, comments: Optional[str] = None) -> None:
        """Add approval response"""
        response = {
            "approver": approver,
            "decision": decision,  # approved, rejected, needs_info
            "comments": comments,
            "timestamp": datetime.now().isoformat()
        }
        self.approval_responses.append(response)
    
    def is_approved(self) -> bool:
        """Check if proposal is approved"""
        approved_count = sum(1 for response in self.approval_responses if response["decision"] == "approved")
        return approved_count >= len(self.required_approvers)
    
    def is_rejected(self) -> bool:
        """Check if proposal is rejected"""
        return any(response["decision"] == "rejected" for response in self.approval_responses)
    
    def is_expired(self) -> bool:
        """Check if approval deadline has passed"""
        if self.approval_deadline is None:
            return False
        return datetime.now() > self.approval_deadline
    
    def get_approval_summary(self) -> Dict[str, Any]:
        """Get summary of approval status"""
        approved = sum(1 for r in self.approval_responses if r["decision"] == "approved")
        rejected = sum(1 for r in self.approval_responses if r["decision"] == "rejected")
        pending = len(self.required_approvers) - len(self.approval_responses)
        
        return {
            "approved": approved,
            "rejected": rejected,
            "pending": pending,
            "total_required": len(self.required_approvers),
            "is_approved": self.is_approved(),
            "is_rejected": self.is_rejected(),
            "is_expired": self.is_expired()
        }


@dataclass
class WorkflowStep:
    """Individual step in a workflow"""
    step_id: str
    agent_id: str
    action: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    timeout_seconds: int = 300
    retry_policy: Dict[str, Any] = field(default_factory=dict)
    condition: Optional[str] = None  # Conditional execution
    on_success: Optional[str] = None  # Next step on success
    on_failure: Optional[str] = None  # Next step on failure
    
    def can_execute(self, completed_steps: List[str]) -> bool:
        """Check if step can be executed based on dependencies"""
        return all(dep in completed_steps for dep in self.dependencies)


@dataclass
class WorkflowDefinition:
    """Definition of a multi-agent workflow"""
    workflow_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    steps: List[WorkflowStep] = field(default_factory=list)
    triggers: List[Dict[str, Any]] = field(default_factory=list)
    success_criteria: Dict[str, Any] = field(default_factory=dict)
    failure_handling: Dict[str, Any] = field(default_factory=dict)
    timeout_minutes: int = 60
    max_retries: int = 3
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    
    def get_initial_steps(self) -> List[WorkflowStep]:
        """Get steps that can be executed initially (no dependencies)"""
        return [step for step in self.steps if not step.dependencies]
    
    def get_next_steps(self, completed_steps: List[str]) -> List[WorkflowStep]:
        """Get steps that can be executed next"""
        return [step for step in self.steps 
                if step.step_id not in completed_steps and step.can_execute(completed_steps)]


@dataclass
class SystemEvent:
    """System-wide event for broadcasting"""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = ""
    source: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    severity: str = "info"  # debug, info, warning, error, critical
    affected_agents: List[str] = field(default_factory=list)
    requires_action: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "source": self.source,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "severity": self.severity,
            "affected_agents": self.affected_agents,
            "requires_action": self.requires_action
        }


@dataclass
class MultiAgentTask:
    """Task requiring coordination between multiple agents"""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    participating_agents: List[str] = field(default_factory=list)
    coordination_strategy: str = "sequential"  # sequential, parallel, conditional
    task_data: Dict[str, Any] = field(default_factory=dict)
    timeout_minutes: int = 30
    priority: str = "normal"
    created_at: datetime = field(default_factory=datetime.now)
    
    def get_agent_tasks(self) -> Dict[str, Dict[str, Any]]:
        """Get individual tasks for each agent"""
        return self.task_data.get("agent_tasks", {})


@dataclass
class TaskResult:
    """Result of task execution"""
    task_id: str
    status: str  # success, failure, partial, timeout
    results: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    execution_time_seconds: float = 0.0
    completed_at: datetime = field(default_factory=datetime.now)
    agent_results: Dict[str, Any] = field(default_factory=dict)  # Results from each agent
    
    def is_successful(self) -> bool:
        """Check if task completed successfully"""
        return self.status == "success"
    
    def has_errors(self) -> bool:
        """Check if task had errors"""
        return len(self.errors) > 0


@dataclass
class ConversationContext:
    """Context for agent conversations"""
    thread_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    participants: List[str] = field(default_factory=list)
    topic: Optional[str] = None
    context_data: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    
    def add_participant(self, agent_id: str) -> None:
        """Add participant to conversation"""
        if agent_id not in self.participants:
            self.participants.append(agent_id)
            self.last_activity = datetime.now()
    
    def update_activity(self) -> None:
        """Update last activity timestamp"""
        self.last_activity = datetime.now()


@dataclass
class DecisionContext:
    """Context for decision proposals"""
    decision_id: str
    related_decisions: List[str] = field(default_factory=list)
    historical_context: Dict[str, Any] = field(default_factory=dict)
    stakeholder_context: Dict[str, Any] = field(default_factory=dict)
    business_context: Dict[str, Any] = field(default_factory=dict)
    technical_context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def add_related_decision(self, decision_id: str) -> None:
        """Add related decision for context"""
        if decision_id not in self.related_decisions:
            self.related_decisions.append(decision_id)


@dataclass
class AgentMetrics:
    """Performance metrics for an agent"""
    agent_id: str
    messages_processed: int = 0
    tasks_completed: int = 0
    tasks_failed: int = 0
    average_response_time_ms: float = 0.0
    error_rate: float = 0.0
    uptime_percentage: float = 100.0
    last_updated: datetime = field(default_factory=datetime.now)
    custom_metrics: Dict[str, float] = field(default_factory=dict)
    
    def update_metrics(self, **kwargs) -> None:
        """Update metrics with new values"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.last_updated = datetime.now()
    
    def calculate_success_rate(self) -> float:
        """Calculate task success rate"""
        total_tasks = self.tasks_completed + self.tasks_failed
        if total_tasks == 0:
            return 100.0
        return (self.tasks_completed / total_tasks) * 100.0


@dataclass
class SystemHealth:
    """Overall system health status"""
    timestamp: datetime = field(default_factory=datetime.now)
    overall_status: str = "healthy"  # healthy, degraded, critical, offline
    agent_statuses: Dict[str, str] = field(default_factory=dict)
    system_metrics: Dict[str, float] = field(default_factory=dict)
    active_alerts: List[str] = field(default_factory=list)
    performance_summary: Dict[str, Any] = field(default_factory=dict)
    
    def is_healthy(self) -> bool:
        """Check if system is healthy"""
        return self.overall_status == "healthy" and len(self.active_alerts) == 0
    
    def get_unhealthy_agents(self) -> List[str]:
        """Get list of unhealthy agents"""
        return [agent_id for agent_id, status in self.agent_statuses.items() 
                if status not in ["active", "idle"]]


# Exception classes for agentic system
class AgenticSystemError(Exception):
    """Base exception for agentic system errors"""
    pass


class AgentCommunicationError(AgenticSystemError):
    """Error in agent communication"""
    pass


class AgentNotFoundError(AgenticSystemError):
    """Agent not found in registry"""
    pass


class UnauthorizedCommunicationError(AgenticSystemError):
    """Unauthorized communication attempt"""
    pass


class WorkflowExecutionError(AgenticSystemError):
    """Error in workflow execution"""
    pass


class DecisionProposalError(AgenticSystemError):
    """Error in decision proposal processing"""
    pass


class ContextSynchronizationError(AgenticSystemError):
    """Error in context synchronization"""
    pass


class MemoryStoreError(AgenticSystemError):
    """Error in memory store operations"""
    pass


# System event types for broadcasting
class SystemEventType(Enum):
    """Types of system events"""
    AGENT_STARTED = "agent_started"
    AGENT_STOPPED = "agent_stopped"
    AGENT_ERROR = "agent_error"
    DECISION_CREATED = "decision_created"
    DECISION_APPROVED = "decision_approved"
    DECISION_REJECTED = "decision_rejected"
    DECISION_EXECUTED = "decision_executed"
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_FAILED = "workflow_failed"
    SYSTEM_ALERT = "system_alert"
    BUDGET_THRESHOLD_EXCEEDED = "budget_threshold_exceeded"
    COST_ANOMALY_DETECTED = "cost_anomaly_detected"