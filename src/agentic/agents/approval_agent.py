"""
Approval Agent for Agentic AI System
Manages decision proposals, approval workflows, and stakeholder notifications
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import uuid
import json

from ..core.base_agent import BaseAgent
from ..core.interfaces import IApprovalAgent, IStrandsFramework, IMCPServer
from ..core.models import (
    AgentMessage, AgentCapability, DecisionProposal, DecisionStatus,
    MessageType, RiskLevel, DecisionImpactAnalysis, ApprovalRule,
    SystemEvent, AgentStatus
)
from ..services.email_notification_service import EmailNotificationService, EmailRecipient
from ..services.audit_trail_service import AuditTrailService
from ..services.real_time_notification_service import RealTimeNotificationService


class ApprovalAgent(BaseAgent, IApprovalAgent):
    """
    Approval Agent - manages decision proposals and approval workflows
    
    Key Responsibilities:
    - Create and manage decision proposals
    - Generate impact analysis and stakeholder identification
    - Orchestrate approval workflows with deadline management
    - Process approval responses and track status
    - Send notifications and manage escalations
    """
    
    def __init__(
        self,
        agent_id: str = "approval_agent",
        config: Dict[str, Any] = None,
        strands_framework: Optional[IStrandsFramework] = None,
        mcp_server: Optional[IMCPServer] = None
    ):
        # Define capabilities
        capabilities = [
            AgentCapability(
                name="create_proposal",
                description="Create new decision proposal with impact analysis",
                input_schema={
                    "type": "object",
                    "required": ["title", "description", "created_by"],
                    "properties": {
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "created_by": {"type": "string"},
                        "recommendations": {"type": "array"},
                        "estimated_cost_impact": {"type": "number"},
                        "risk_level": {"type": "string"},
                        "execution_plan": {"type": "object"}
                    }
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "proposal": {"type": "object"},
                        "proposal_id": {"type": "string"}
                    }
                },
                required_permissions=["create_decisions"]
            ),
            AgentCapability(
                name="send_approval_request",
                description="Send approval request to stakeholders",
                input_schema={
                    "type": "object",
                    "required": ["proposal_id"],
                    "properties": {
                        "proposal_id": {"type": "string"},
                        "notification_method": {"type": "string"}
                    }
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "sent": {"type": "boolean"},
                        "recipients": {"type": "array"}
                    }
                },
                required_permissions=["send_notifications"]
            ),
            AgentCapability(
                name="process_approval_response",
                description="Process approval or rejection response",
                input_schema={
                    "type": "object",
                    "required": ["proposal_id", "approver", "decision"],
                    "properties": {
                        "proposal_id": {"type": "string"},
                        "approver": {"type": "string"},
                        "decision": {"type": "string"},
                        "comments": {"type": "string"}
                    }
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "processed": {"type": "boolean"},
                        "proposal_status": {"type": "string"}
                    }
                },
                required_permissions=["process_approvals"]
            ),
            AgentCapability(
                name="get_pending_proposals",
                description="Get pending decision proposals",
                input_schema={
                    "type": "object",
                    "properties": {
                        "approver_id": {"type": "string"},
                        "status_filter": {"type": "string"}
                    }
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "proposals": {"type": "array"}
                    }
                },
                required_permissions=["view_decisions"]
            ),
            AgentCapability(
                name="execute_approved_proposal",
                description="Execute approved decision proposal",
                input_schema={
                    "type": "object",
                    "required": ["proposal_id"],
                    "properties": {
                        "proposal_id": {"type": "string"}
                    }
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "executed": {"type": "boolean"},
                        "execution_result": {"type": "object"}
                    }
                },
                required_permissions=["execute_decisions"]
            )
        ]
        
        # Initialize base agent
        super().__init__(
            agent_id=agent_id,
            agent_type="approval",
            capabilities=capabilities,
            config=config or {},
            strands_framework=strands_framework,
            mcp_server=mcp_server
        )
        
        # Approval-specific configuration
        self.default_approval_timeout_hours = config.get("default_approval_timeout_hours", 24)
        self.auto_escalation_enabled = config.get("auto_escalation_enabled", True)
        self.escalation_timeout_hours = config.get("escalation_timeout_hours", 48)
        
        # In-memory storage for proposals (in production, use persistent storage)
        self.proposals: Dict[str, DecisionProposal] = {}
        self.approval_rules: List[ApprovalRule] = []
        
        # Stakeholder configuration
        self.stakeholder_config = config.get("stakeholders", {
            "ceo": {
                "email": "ceo@company.com",
                "name": "Chief Executive Officer",
                "approval_authority": {"max_cost": float('inf'), "all_decisions": True}
            },
            "cto": {
                "email": "cto@company.com", 
                "name": "Chief Technology Officer",
                "approval_authority": {"max_cost": 10000, "technical_decisions": True}
            },
            "finops_lead": {
                "email": "finops@company.com",
                "name": "FinOps Lead",
                "approval_authority": {"max_cost": 5000, "cost_decisions": True}
            }
        })
        
        # Initialize services
        self.email_service = EmailNotificationService(config.get("email_config", {}))
        self.audit_service = AuditTrailService(config.get("audit_config", {}))
        self.notification_service = RealTimeNotificationService(config.get("notification_config", {}))
        
        # Setup approval-specific handlers
        self._setup_approval_handlers()
    
    def _setup_approval_handlers(self) -> None:
        """Setup approval-specific message and action handlers"""
        # Add approval-specific action handlers
        self.action_handlers.update({
            "create_proposal": self._action_create_proposal,
            "send_approval_request": self._action_send_approval_request,
            "process_approval_response": self._action_process_approval_response,
            "get_pending_proposals": self._action_get_pending_proposals,
            "get_proposal_status": self._action_get_proposal_status,
            "execute_approved_proposal": self._action_execute_approved_proposal,
            "generate_impact_analysis": self._action_generate_impact_analysis,
            "identify_stakeholders": self._action_identify_stakeholders,
            "check_approval_deadlines": self._action_check_approval_deadlines,
            "get_audit_trail": self._action_get_audit_trail,
            "get_approval_timeline": self._action_get_approval_timeline,
            "subscribe_to_notifications": self._action_subscribe_to_notifications,
            "get_notification_history": self._action_get_notification_history
        })
        
        # Add approval-specific message handlers
        self.message_handlers.update({
            "approval_request": self._handle_approval_request,
            "approval_response": self._handle_approval_response,
            "proposal_update": self._handle_proposal_update
        })
    
    async def _agent_specific_initialization(self) -> None:
        """Initialize approval agent specific components"""
        try:
            # Load default approval rules
            await self._load_default_approval_rules()
            
            # Start services
            await self.notification_service.start_service()
            
            # Subscribe to audit events for real-time notifications
            self.audit_service.subscribe_to_events(self.notification_service.notify_audit_event)
            
            # Start background tasks
            asyncio.create_task(self._approval_deadline_monitor())
            asyncio.create_task(self._escalation_monitor())
            
            self.logger.info("Approval agent initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error in approval agent initialization: {e}")
            raise
    
    async def _load_default_approval_rules(self) -> None:
        """Load default approval rules"""
        default_rules = [
            ApprovalRule(
                rule_id="high_cost_decisions",
                condition="cost_threshold:5000",
                required_approvers=["ceo", "cto"],
                approval_threshold=2,
                timeout_hours=48
            ),
            ApprovalRule(
                rule_id="medium_cost_decisions", 
                condition="cost_threshold:1000",
                required_approvers=["cto", "finops_lead"],
                approval_threshold=1,
                timeout_hours=24
            ),
            ApprovalRule(
                rule_id="low_cost_decisions",
                condition="cost_threshold:500",
                required_approvers=["finops_lead"],
                approval_threshold=1,
                timeout_hours=12
            ),
            ApprovalRule(
                rule_id="critical_risk_decisions",
                condition="risk_level:critical",
                required_approvers=["ceo", "cto"],
                approval_threshold=2,
                timeout_hours=24
            )
        ]
        
        self.approval_rules.extend(default_rules)
        self.logger.info(f"Loaded {len(default_rules)} default approval rules")
    
    # IApprovalAgent interface implementation
    async def create_proposal(self, proposal_data: Dict[str, Any]) -> DecisionProposal:
        """Create new decision proposal"""
        try:
            # Generate proposal ID
            proposal_id = str(uuid.uuid4())
            
            # Generate impact analysis
            impact_analysis = await self._generate_impact_analysis(proposal_data)
            
            # Identify required approvers
            required_approvers = await self._identify_stakeholders(proposal_data, impact_analysis)
            
            # Set approval deadline
            approval_deadline = datetime.now() + timedelta(hours=self.default_approval_timeout_hours)
            
            # Create proposal
            proposal = DecisionProposal(
                proposal_id=proposal_id,
                title=proposal_data.get("title", ""),
                description=proposal_data.get("description", ""),
                impact_analysis=impact_analysis,
                recommendations=proposal_data.get("recommendations", []),
                required_approvers=required_approvers,
                created_by=proposal_data.get("created_by", "system"),
                created_at=datetime.now(),
                status=DecisionStatus.PENDING,
                approval_deadline=approval_deadline,
                estimated_cost_impact=proposal_data.get("estimated_cost_impact", 0.0),
                risk_level=RiskLevel(proposal_data.get("risk_level", "low")),
                execution_plan=proposal_data.get("execution_plan", {}),
                metadata=proposal_data.get("metadata", {})
            )
            
            # Store proposal
            self.proposals[proposal_id] = proposal
            
            # Store in Strands framework if available
            if self.strands_framework:
                await self.strands_framework.store_decision_history(proposal)
            
            # Record audit event
            await self.audit_service.record_proposal_created(
                proposal=proposal,
                actor=proposal.created_by
            )
            
            self.logger.info(f"Created decision proposal {proposal_id}: {proposal.title}")
            
            return proposal
            
        except Exception as e:
            self.logger.error(f"Error creating proposal: {e}")
            raise
    
    async def send_approval_request(self, proposal: DecisionProposal) -> bool:
        """Send approval request to stakeholders"""
        try:
            # Update proposal status
            proposal.status = DecisionStatus.PENDING
            
            # Convert approver IDs to email recipients
            recipients = []
            for approver_id in proposal.required_approvers:
                stakeholder_info = self.stakeholder_config.get(approver_id)
                if stakeholder_info:
                    recipients.append(EmailRecipient(
                        email=stakeholder_info["email"],
                        name=stakeholder_info["name"],
                        role=approver_id,
                        approval_authority=stakeholder_info.get("approval_authority", {})
                    ))
            
            # Send email notifications
            email_result = await self.email_service.send_approval_request(proposal, recipients)
            
            # Record audit event
            await self.audit_service.record_approval_request_sent(
                proposal=proposal,
                recipients=[r.email for r in recipients],
                email_success=email_result.get("success", False),
                actor=self.agent_id
            )
            
            # Create notification event
            notification_event = SystemEvent(
                event_type="approval_request_sent",
                source=self.agent_id,
                data={
                    "proposal_id": proposal.proposal_id,
                    "title": proposal.title,
                    "required_approvers": proposal.required_approvers,
                    "approval_deadline": proposal.approval_deadline.isoformat() if proposal.approval_deadline else None,
                    "estimated_cost_impact": proposal.estimated_cost_impact,
                    "risk_level": proposal.risk_level.value,
                    "email_sent": email_result.get("success", False),
                    "email_recipients": len(recipients)
                },
                severity="info",
                affected_agents=proposal.required_approvers,
                requires_action=True
            )
            
            # Broadcast notification event
            if self.mcp_server:
                await self.mcp_server.broadcast_system_event(notification_event)
            
            # Log approval request
            self.logger.info(f"Sent approval request for proposal {proposal.proposal_id} to {proposal.required_approvers}")
            if email_result.get("success"):
                self.logger.info(f"Email notifications sent successfully: {email_result.get('successful_sends')}/{email_result.get('total_recipients')}")
            else:
                self.logger.warning(f"Email notification failed: {email_result.get('error')}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending approval request: {e}")
            return False
    
    async def process_approval_response(self, proposal_id: str, approver: str, decision: str) -> bool:
        """Process approval/rejection response"""
        try:
            # Get proposal
            proposal = self.proposals.get(proposal_id)
            if not proposal:
                self.logger.error(f"Proposal {proposal_id} not found")
                return False
            
            # Validate approver
            if approver not in proposal.required_approvers:
                self.logger.error(f"Approver {approver} not authorized for proposal {proposal_id}")
                return False
            
            # Check if already responded
            existing_response = next(
                (r for r in proposal.approval_responses if r["approver"] == approver),
                None
            )
            if existing_response:
                self.logger.warning(f"Approver {approver} already responded to proposal {proposal_id}")
                return False
            
            # Store old status for audit
            old_status = proposal.status
            
            # Add approval response
            proposal.add_approval_response(approver, decision)
            
            # Record audit event for approval response
            await self.audit_service.record_approval_response(
                proposal_id=proposal_id,
                approver=approver,
                decision=decision,
                response_method="email"
            )
            
            # Update proposal status based on responses
            if proposal.is_approved():
                proposal.status = DecisionStatus.APPROVED
                await self._handle_proposal_approved(proposal)
            elif proposal.is_rejected():
                proposal.status = DecisionStatus.REJECTED
                await self._handle_proposal_rejected(proposal)
            
            # Record status change if status changed
            if proposal.status != old_status:
                await self.audit_service.record_proposal_status_change(
                    proposal=proposal,
                    old_status=old_status,
                    new_status=proposal.status,
                    actor=approver,
                    reason=f"Approval response: {decision}"
                )
                
                # Send real-time notification for status change
                await self.notification_service.notify_proposal_status_change(
                    proposal=proposal,
                    old_status=old_status,
                    new_status=proposal.status,
                    actor=approver
                )
            
            # Store updated proposal
            if self.strands_framework:
                await self.strands_framework.store_decision_history(proposal)
            
            # Send approval response notification
            await self.notification_service.notify_approval_response(
                proposal=proposal,
                approver=approver,
                decision=decision
            )
            
            # Send status update notification
            await self._send_status_update_notification(proposal, approver, decision)
            
            self.logger.info(f"Processed approval response from {approver} for proposal {proposal_id}: {decision}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error processing approval response: {e}")
            return False
    
    async def get_pending_proposals(self, approver_id: Optional[str] = None) -> List[DecisionProposal]:
        """Get pending decision proposals"""
        try:
            pending_proposals = []
            
            for proposal in self.proposals.values():
                if proposal.status == DecisionStatus.PENDING:
                    if approver_id is None or approver_id in proposal.required_approvers:
                        # Check if approver hasn't responded yet
                        if approver_id is None or not any(
                            r["approver"] == approver_id for r in proposal.approval_responses
                        ):
                            pending_proposals.append(proposal)
            
            return pending_proposals
            
        except Exception as e:
            self.logger.error(f"Error getting pending proposals: {e}")
            return []
    
    async def get_proposal_status(self, proposal_id: str) -> Dict[str, Any]:
        """Get status of specific proposal"""
        try:
            proposal = self.proposals.get(proposal_id)
            if not proposal:
                return {"error": "Proposal not found"}
            
            return {
                "proposal_id": proposal.proposal_id,
                "title": proposal.title,
                "status": proposal.status.value,
                "created_at": proposal.created_at.isoformat(),
                "approval_deadline": proposal.approval_deadline.isoformat() if proposal.approval_deadline else None,
                "approval_summary": proposal.get_approval_summary(),
                "estimated_cost_impact": proposal.estimated_cost_impact,
                "risk_level": proposal.risk_level.value
            }
            
        except Exception as e:
            self.logger.error(f"Error getting proposal status: {e}")
            return {"error": str(e)}
    
    async def execute_approved_proposal(self, proposal_id: str) -> bool:
        """Execute approved decision proposal"""
        try:
            proposal = self.proposals.get(proposal_id)
            if not proposal:
                self.logger.error(f"Proposal {proposal_id} not found")
                return False
            
            if proposal.status != DecisionStatus.APPROVED:
                self.logger.error(f"Proposal {proposal_id} is not approved (status: {proposal.status.value})")
                return False
            
            # Store old status for audit
            old_status = proposal.status
            
            # Execute the proposal based on execution plan
            execution_result = await self._execute_proposal_plan(proposal)
            
            if execution_result.get("success", False):
                proposal.status = DecisionStatus.EXECUTED
                self.logger.info(f"Successfully executed proposal {proposal_id}")
            else:
                proposal.status = DecisionStatus.FAILED
                self.logger.error(f"Failed to execute proposal {proposal_id}: {execution_result.get('error')}")
            
            # Record audit events
            await self.audit_service.record_proposal_execution(
                proposal=proposal,
                execution_result=execution_result,
                actor=self.agent_id
            )
            
            await self.audit_service.record_proposal_status_change(
                proposal=proposal,
                old_status=old_status,
                new_status=proposal.status,
                actor=self.agent_id,
                reason="Proposal execution completed"
            )
            
            # Store updated proposal
            if self.strands_framework:
                await self.strands_framework.store_decision_history(proposal)
            
            # Send real-time notification
            await self.notification_service.notify_proposal_status_change(
                proposal=proposal,
                old_status=old_status,
                new_status=proposal.status,
                actor=self.agent_id,
                additional_data={"execution_result": execution_result}
            )
            
            # Send execution notification
            await self._send_execution_notification(proposal, execution_result)
            
            return execution_result.get("success", False)
            
        except Exception as e:
            self.logger.error(f"Error executing proposal: {e}")
            return False
    
    # Action handlers
    async def _action_create_proposal(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Create proposal action handler"""
        try:
            proposal = await self.create_proposal(parameters)
            
            return {
                "success": True,
                "proposal": {
                    "proposal_id": proposal.proposal_id,
                    "title": proposal.title,
                    "status": proposal.status.value,
                    "required_approvers": proposal.required_approvers,
                    "approval_deadline": proposal.approval_deadline.isoformat() if proposal.approval_deadline else None
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _action_send_approval_request(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Send approval request action handler"""
        try:
            proposal_id = parameters.get("proposal_id")
            proposal = self.proposals.get(proposal_id)
            
            if not proposal:
                return {"success": False, "error": "Proposal not found"}
            
            success = await self.send_approval_request(proposal)
            
            return {
                "success": success,
                "recipients": proposal.required_approvers if success else []
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _action_process_approval_response(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Process approval response action handler"""
        try:
            proposal_id = parameters.get("proposal_id")
            approver = parameters.get("approver")
            decision = parameters.get("decision")
            
            success = await self.process_approval_response(proposal_id, approver, decision)
            
            proposal_status = "unknown"
            if success and proposal_id in self.proposals:
                proposal_status = self.proposals[proposal_id].status.value
            
            return {
                "success": success,
                "proposal_status": proposal_status
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _action_get_pending_proposals(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get pending proposals action handler"""
        try:
            approver_id = parameters.get("approver_id")
            proposals = await self.get_pending_proposals(approver_id)
            
            return {
                "success": True,
                "proposals": [
                    {
                        "proposal_id": p.proposal_id,
                        "title": p.title,
                        "description": p.description,
                        "created_by": p.created_by,
                        "created_at": p.created_at.isoformat(),
                        "approval_deadline": p.approval_deadline.isoformat() if p.approval_deadline else None,
                        "estimated_cost_impact": p.estimated_cost_impact,
                        "risk_level": p.risk_level.value,
                        "approval_summary": p.get_approval_summary()
                    }
                    for p in proposals
                ]
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _action_get_proposal_status(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get proposal status action handler"""
        try:
            proposal_id = parameters.get("proposal_id")
            status = await self.get_proposal_status(proposal_id)
            
            return {"success": True, "status": status}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _action_execute_approved_proposal(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute approved proposal action handler"""
        try:
            proposal_id = parameters.get("proposal_id")
            success = await self.execute_approved_proposal(proposal_id)
            
            return {"success": success}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _action_generate_impact_analysis(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate impact analysis action handler"""
        try:
            impact_analysis = await self._generate_impact_analysis(parameters)
            
            return {
                "success": True,
                "impact_analysis": {
                    "cost_impact": impact_analysis.cost_impact,
                    "risk_assessment": impact_analysis.risk_assessment.value,
                    "affected_resources": impact_analysis.affected_resources,
                    "timeline_impact": impact_analysis.timeline_impact,
                    "success_metrics": impact_analysis.success_metrics
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _action_identify_stakeholders(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Identify stakeholders action handler"""
        try:
            impact_analysis = DecisionImpactAnalysis(
                cost_impact=parameters.get("estimated_cost_impact", 0.0),
                risk_assessment=RiskLevel(parameters.get("risk_level", "low")),
                affected_resources=parameters.get("affected_resources", []),
                timeline_impact=parameters.get("timeline_impact", "immediate")
            )
            
            stakeholders = await self._identify_stakeholders(parameters, impact_analysis)
            
            return {
                "success": True,
                "stakeholders": stakeholders
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _action_check_approval_deadlines(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Check approval deadlines action handler"""
        try:
            expired_proposals = []
            expiring_soon = []
            
            current_time = datetime.now()
            
            for proposal in self.proposals.values():
                if proposal.status == DecisionStatus.PENDING and proposal.approval_deadline:
                    if current_time > proposal.approval_deadline:
                        expired_proposals.append(proposal.proposal_id)
                    elif (proposal.approval_deadline - current_time).total_seconds() < 3600:  # 1 hour
                        expiring_soon.append(proposal.proposal_id)
            
            return {
                "success": True,
                "expired_proposals": expired_proposals,
                "expiring_soon": expiring_soon
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _action_get_audit_trail(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get audit trail action handler"""
        try:
            proposal_id = parameters.get("proposal_id")
            if not proposal_id:
                return {"success": False, "error": "proposal_id required"}
            
            audit_trail = await self.audit_service.get_audit_trail(proposal_id)
            if not audit_trail:
                return {"success": False, "error": "Audit trail not found"}
            
            return {
                "success": True,
                "audit_trail": audit_trail.to_dict()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _action_get_approval_timeline(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get approval timeline action handler"""
        try:
            proposal_id = parameters.get("proposal_id")
            if not proposal_id:
                return {"success": False, "error": "proposal_id required"}
            
            timeline = await self.audit_service.get_approval_timeline(proposal_id)
            
            return {
                "success": True,
                "timeline": timeline
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _action_subscribe_to_notifications(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Subscribe to notifications action handler"""
        try:
            subscriber_id = parameters.get("subscriber_id")
            channels = parameters.get("channels", ["websocket"])
            
            if not subscriber_id:
                return {"success": False, "error": "subscriber_id required"}
            
            # Convert channel strings to enums
            from ..services.real_time_notification_service import NotificationChannel
            channel_enums = []
            for channel in channels:
                try:
                    channel_enums.append(NotificationChannel(channel))
                except ValueError:
                    return {"success": False, "error": f"Invalid channel: {channel}"}
            
            success = await self.notification_service.subscribe(
                subscriber_id=subscriber_id,
                channels=channel_enums,
                proposal_filters=parameters.get("proposal_filters"),
                event_filters=parameters.get("event_filters"),
                user_roles=parameters.get("user_roles")
            )
            
            return {"success": success}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _action_get_notification_history(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get notification history action handler"""
        try:
            subscriber_id = parameters.get("subscriber_id")
            proposal_id = parameters.get("proposal_id")
            limit = parameters.get("limit", 50)
            
            notifications = await self.notification_service.get_notification_history(
                subscriber_id=subscriber_id,
                proposal_id=proposal_id,
                limit=limit
            )
            
            return {
                "success": True,
                "notifications": [n.to_dict() for n in notifications]
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # Helper methods
    async def _generate_impact_analysis(self, proposal_data: Dict[str, Any]) -> DecisionImpactAnalysis:
        """Generate impact analysis for proposal"""
        try:
            # Extract basic information
            cost_impact = proposal_data.get("estimated_cost_impact", 0.0)
            risk_level = RiskLevel(proposal_data.get("risk_level", "low"))
            affected_resources = proposal_data.get("affected_resources", [])
            
            # Determine timeline impact
            timeline_impact = "immediate"
            if cost_impact > 10000:
                timeline_impact = "long-term"
            elif cost_impact > 1000:
                timeline_impact = "medium-term"
            
            # Generate success metrics
            success_metrics = []
            if cost_impact > 0:
                success_metrics.append(f"Cost savings of ${cost_impact:.2f}")
            if "performance" in proposal_data.get("description", "").lower():
                success_metrics.append("Performance improvement measured")
            if "efficiency" in proposal_data.get("description", "").lower():
                success_metrics.append("Efficiency gains documented")
            
            # Create rollback plan
            rollback_plan = None
            if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                rollback_plan = "Automated rollback available within 1 hour of execution"
            
            return DecisionImpactAnalysis(
                cost_impact=cost_impact,
                risk_assessment=risk_level,
                affected_resources=affected_resources,
                timeline_impact=timeline_impact,
                rollback_plan=rollback_plan,
                success_metrics=success_metrics,
                stakeholder_impact={
                    "finance": "Cost impact analysis required",
                    "operations": "Resource allocation review needed",
                    "technical": "Implementation feasibility confirmed"
                },
                compliance_considerations=[
                    "Budget approval required for costs > $1000",
                    "Security review for infrastructure changes",
                    "Change management process compliance"
                ]
            )
            
        except Exception as e:
            self.logger.error(f"Error generating impact analysis: {e}")
            # Return minimal impact analysis
            return DecisionImpactAnalysis(
                cost_impact=0.0,
                risk_assessment=RiskLevel.LOW,
                affected_resources=[],
                timeline_impact="unknown"
            )
    
    async def _identify_stakeholders(self, proposal_data: Dict[str, Any], impact_analysis: DecisionImpactAnalysis) -> List[str]:
        """Identify required stakeholders for approval"""
        try:
            required_approvers = []
            
            # Apply approval rules
            for rule in self.approval_rules:
                if rule.matches_decision(DecisionProposal(
                    estimated_cost_impact=impact_analysis.cost_impact,
                    risk_level=impact_analysis.risk_assessment
                )):
                    required_approvers.extend(rule.required_approvers)
            
            # Remove duplicates while preserving order
            unique_approvers = []
            for approver in required_approvers:
                if approver not in unique_approvers:
                    unique_approvers.append(approver)
            
            # Ensure at least one approver for non-trivial decisions
            if not unique_approvers and (impact_analysis.cost_impact > 0 or impact_analysis.risk_assessment != RiskLevel.LOW):
                unique_approvers.append("finops_lead")
            
            return unique_approvers
            
        except Exception as e:
            self.logger.error(f"Error identifying stakeholders: {e}")
            return ["finops_lead"]  # Default fallback
    
    async def _execute_proposal_plan(self, proposal: DecisionProposal) -> Dict[str, Any]:
        """Execute the proposal's execution plan"""
        try:
            execution_plan = proposal.execution_plan
            
            if not execution_plan:
                return {"success": False, "error": "No execution plan defined"}
            
            # For now, simulate execution based on plan type
            plan_type = execution_plan.get("type", "generic")
            
            if plan_type == "cost_optimization":
                # Simulate cost optimization execution
                await asyncio.sleep(1)  # Simulate processing time
                return {
                    "success": True,
                    "result": "Cost optimization measures implemented",
                    "savings_achieved": execution_plan.get("expected_savings", 0)
                }
            elif plan_type == "resource_management":
                # Simulate resource management execution
                await asyncio.sleep(1)
                return {
                    "success": True,
                    "result": "Resource management changes applied",
                    "resources_affected": execution_plan.get("resources", [])
                }
            else:
                # Generic execution
                await asyncio.sleep(0.5)
                return {
                    "success": True,
                    "result": "Proposal executed successfully",
                    "execution_details": execution_plan
                }
                
        except Exception as e:
            self.logger.error(f"Error executing proposal plan: {e}")
            return {"success": False, "error": str(e)}
    
    async def _handle_proposal_approved(self, proposal: DecisionProposal) -> None:
        """Handle proposal approval"""
        try:
            # Create approval notification event
            approval_event = SystemEvent(
                event_type="decision_approved",
                source=self.agent_id,
                data={
                    "proposal_id": proposal.proposal_id,
                    "title": proposal.title,
                    "approved_by": [r["approver"] for r in proposal.approval_responses if r["decision"] == "approved"],
                    "estimated_cost_impact": proposal.estimated_cost_impact
                },
                severity="info",
                requires_action=True
            )
            
            # Broadcast approval event
            if self.mcp_server:
                await self.mcp_server.broadcast_system_event(approval_event)
            
            self.logger.info(f"Proposal {proposal.proposal_id} approved")
            
        except Exception as e:
            self.logger.error(f"Error handling proposal approval: {e}")
    
    async def _handle_proposal_rejected(self, proposal: DecisionProposal) -> None:
        """Handle proposal rejection"""
        try:
            # Create rejection notification event
            rejection_event = SystemEvent(
                event_type="decision_rejected",
                source=self.agent_id,
                data={
                    "proposal_id": proposal.proposal_id,
                    "title": proposal.title,
                    "rejected_by": [r["approver"] for r in proposal.approval_responses if r["decision"] == "rejected"],
                    "rejection_reasons": [r["comments"] for r in proposal.approval_responses if r["decision"] == "rejected" and r["comments"]]
                },
                severity="warning"
            )
            
            # Broadcast rejection event
            if self.mcp_server:
                await self.mcp_server.broadcast_system_event(rejection_event)
            
            self.logger.info(f"Proposal {proposal.proposal_id} rejected")
            
        except Exception as e:
            self.logger.error(f"Error handling proposal rejection: {e}")
    
    async def _send_status_update_notification(self, proposal: DecisionProposal, approver: str, decision: str) -> None:
        """Send status update notification"""
        try:
            # Send email notifications to all stakeholders
            recipients = []
            all_stakeholders = set(proposal.required_approvers + [proposal.created_by])
            
            for stakeholder_id in all_stakeholders:
                stakeholder_info = self.stakeholder_config.get(stakeholder_id)
                if stakeholder_info:
                    recipients.append(EmailRecipient(
                        email=stakeholder_info["email"],
                        name=stakeholder_info["name"],
                        role=stakeholder_id,
                        approval_authority=stakeholder_info.get("approval_authority", {})
                    ))
            
            # Send status update emails
            approver_name = self.stakeholder_config.get(approver, {}).get("name", approver)
            email_result = await self.email_service.send_status_update(
                proposal, approver_name, decision, recipients
            )
            
            # Create status update event
            status_event = SystemEvent(
                event_type="approval_status_update",
                source=self.agent_id,
                data={
                    "proposal_id": proposal.proposal_id,
                    "title": proposal.title,
                    "approver": approver,
                    "decision": decision,
                    "current_status": proposal.status.value,
                    "approval_summary": proposal.get_approval_summary(),
                    "email_sent": email_result.get("success", False)
                },
                severity="info"
            )
            
            # Broadcast status update
            if self.mcp_server:
                await self.mcp_server.broadcast_system_event(status_event)
            
        except Exception as e:
            self.logger.error(f"Error sending status update notification: {e}")
    
    async def _send_execution_notification(self, proposal: DecisionProposal, execution_result: Dict[str, Any]) -> None:
        """Send execution notification"""
        try:
            # Send email notifications to all stakeholders
            recipients = []
            all_stakeholders = set(proposal.required_approvers + [proposal.created_by])
            
            for stakeholder_id in all_stakeholders:
                stakeholder_info = self.stakeholder_config.get(stakeholder_id)
                if stakeholder_info:
                    recipients.append(EmailRecipient(
                        email=stakeholder_info["email"],
                        name=stakeholder_info["name"],
                        role=stakeholder_id,
                        approval_authority=stakeholder_info.get("approval_authority", {})
                    ))
            
            # Send execution notification emails
            email_result = await self.email_service.send_execution_notification(
                proposal, execution_result, recipients
            )
            
            # Create execution notification event
            execution_event = SystemEvent(
                event_type="decision_executed",
                source=self.agent_id,
                data={
                    "proposal_id": proposal.proposal_id,
                    "title": proposal.title,
                    "execution_success": execution_result.get("success", False),
                    "execution_result": execution_result.get("result", ""),
                    "final_status": proposal.status.value,
                    "email_sent": email_result.get("success", False)
                },
                severity="info" if execution_result.get("success") else "error"
            )
            
            # Broadcast execution notification
            if self.mcp_server:
                await self.mcp_server.broadcast_system_event(execution_event)
            
        except Exception as e:
            self.logger.error(f"Error sending execution notification: {e}")
    
    # Background monitoring tasks
    async def _approval_deadline_monitor(self) -> None:
        """Monitor approval deadlines and handle expired proposals"""
        while self._state.status != AgentStatus.OFFLINE:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                
                current_time = datetime.now()
                expired_proposals = []
                
                for proposal in self.proposals.values():
                    if (proposal.status == DecisionStatus.PENDING and 
                        proposal.approval_deadline and 
                        current_time > proposal.approval_deadline):
                        expired_proposals.append(proposal)
                
                # Handle expired proposals
                for proposal in expired_proposals:
                    await self._handle_expired_proposal(proposal)
                
                # Check for proposals approaching deadline
                approaching_deadline = []
                for proposal in self.proposals.values():
                    if (proposal.status == DecisionStatus.PENDING and 
                        proposal.approval_deadline):
                        time_remaining = proposal.approval_deadline - current_time
                        hours_remaining = time_remaining.total_seconds() / 3600
                        
                        # Notify if less than 24 hours remaining
                        if 0 < hours_remaining <= 24:
                            approaching_deadline.append((proposal, hours_remaining))
                
                # Send deadline approaching notifications
                for proposal, hours_remaining in approaching_deadline:
                    await self.notification_service.notify_proposal_deadline_approaching(
                        proposal=proposal,
                        hours_remaining=hours_remaining
                    )
                
            except Exception as e:
                self.logger.error(f"Error in approval deadline monitor: {e}")
    
    async def _escalation_monitor(self) -> None:
        """Monitor for escalation conditions"""
        while self._state.status != AgentStatus.OFFLINE:
            try:
                await asyncio.sleep(600)  # Check every 10 minutes
                
                if not self.auto_escalation_enabled:
                    continue
                
                current_time = datetime.now()
                
                for proposal in self.proposals.values():
                    if proposal.status == DecisionStatus.PENDING and proposal.approval_deadline:
                        # Check if proposal needs escalation (75% of deadline passed)
                        time_remaining = proposal.approval_deadline - current_time
                        total_time = proposal.approval_deadline - proposal.created_at
                        
                        if time_remaining.total_seconds() < (total_time.total_seconds() * 0.25):
                            await self._escalate_proposal(proposal)
                
            except Exception as e:
                self.logger.error(f"Error in escalation monitor: {e}")
    
    async def _handle_expired_proposal(self, proposal: DecisionProposal) -> None:
        """Handle expired proposal"""
        try:
            # Store old status for audit
            old_status = proposal.status
            
            # Update status
            proposal.status = DecisionStatus.CANCELLED
            
            # Record audit events
            await self.audit_service.record_proposal_status_change(
                proposal=proposal,
                old_status=old_status,
                new_status=proposal.status,
                actor=self.agent_id,
                reason="Approval deadline expired"
            )
            
            # Send real-time notification
            await self.notification_service.notify_proposal_expired(proposal)
            
            # Create expiration event
            expiration_event = SystemEvent(
                event_type="approval_deadline_expired",
                source=self.agent_id,
                data={
                    "proposal_id": proposal.proposal_id,
                    "title": proposal.title,
                    "expired_at": datetime.now().isoformat(),
                    "required_approvers": proposal.required_approvers,
                    "responses_received": len(proposal.approval_responses)
                },
                severity="warning",
                requires_action=True
            )
            
            # Broadcast expiration event
            if self.mcp_server:
                await self.mcp_server.broadcast_system_event(expiration_event)
            
            self.logger.warning(f"Proposal {proposal.proposal_id} expired without sufficient approvals")
            
        except Exception as e:
            self.logger.error(f"Error handling expired proposal: {e}")
    
    async def _escalate_proposal(self, proposal: DecisionProposal) -> None:
        """Escalate proposal to higher authority"""
        try:
            # Add CEO to required approvers if not already present
            if "ceo" not in proposal.required_approvers:
                original_approvers = proposal.required_approvers.copy()
                proposal.required_approvers.append("ceo")
                
                # Record audit event
                await self.audit_service.record_escalation(
                    proposal_id=proposal.proposal_id,
                    escalated_to=["ceo"],
                    reason="Approaching deadline without sufficient approvals",
                    actor=self.agent_id
                )
                
                # Send real-time notification
                await self.notification_service.notify_proposal_escalated(
                    proposal=proposal,
                    escalated_to=["ceo"],
                    reason="Approaching deadline without sufficient approvals"
                )
                
                # Create escalation event
                escalation_event = SystemEvent(
                    event_type="approval_escalated",
                    source=self.agent_id,
                    data={
                        "proposal_id": proposal.proposal_id,
                        "title": proposal.title,
                        "escalated_to": ["ceo"],
                        "original_approvers": original_approvers,
                        "time_remaining_hours": (proposal.approval_deadline - datetime.now()).total_seconds() / 3600
                    },
                    severity="warning",
                    requires_action=True
                )
                
                # Broadcast escalation event
                if self.mcp_server:
                    await self.mcp_server.broadcast_system_event(escalation_event)
                
                self.logger.info(f"Escalated proposal {proposal.proposal_id} to CEO")
            
        except Exception as e:
            self.logger.error(f"Error escalating proposal: {e}")
    
    # Message handlers
    async def _handle_approval_request(self, message: AgentMessage) -> AgentMessage:
        """Handle approval request messages"""
        try:
            proposal_data = message.content.get("proposal_data", {})
            
            # Create proposal
            proposal = await self.create_proposal(proposal_data)
            
            # Send approval request
            await self.send_approval_request(proposal)
            
            return AgentMessage(
                sender=self.agent_id,
                recipient=message.sender,
                message_type=MessageType.RESPONSE,
                content={
                    "status": "approval_request_created",
                    "proposal_id": proposal.proposal_id,
                    "required_approvers": proposal.required_approvers
                },
                correlation_id=message.correlation_id
            )
            
        except Exception as e:
            return AgentMessage(
                sender=self.agent_id,
                recipient=message.sender,
                message_type=MessageType.ERROR,
                content={"error": str(e)},
                correlation_id=message.correlation_id
            )
    
    async def _handle_approval_response(self, message: AgentMessage) -> AgentMessage:
        """Handle approval response messages"""
        try:
            proposal_id = message.content.get("proposal_id")
            approver = message.content.get("approver")
            decision = message.content.get("decision")
            
            success = await self.process_approval_response(proposal_id, approver, decision)
            
            return AgentMessage(
                sender=self.agent_id,
                recipient=message.sender,
                message_type=MessageType.RESPONSE,
                content={
                    "status": "approval_response_processed",
                    "success": success,
                    "proposal_id": proposal_id
                },
                correlation_id=message.correlation_id
            )
            
        except Exception as e:
            return AgentMessage(
                sender=self.agent_id,
                recipient=message.sender,
                message_type=MessageType.ERROR,
                content={"error": str(e)},
                correlation_id=message.correlation_id
            )
    
    async def _handle_proposal_update(self, message: AgentMessage) -> AgentMessage:
        """Handle proposal update messages"""
        try:
            proposal_id = message.content.get("proposal_id")
            updates = message.content.get("updates", {})
            
            proposal = self.proposals.get(proposal_id)
            if not proposal:
                raise ValueError(f"Proposal {proposal_id} not found")
            
            # Apply updates
            for key, value in updates.items():
                if hasattr(proposal, key):
                    setattr(proposal, key, value)
            
            # Store updated proposal
            if self.strands_framework:
                await self.strands_framework.store_decision_history(proposal)
            
            return AgentMessage(
                sender=self.agent_id,
                recipient=message.sender,
                message_type=MessageType.RESPONSE,
                content={
                    "status": "proposal_updated",
                    "proposal_id": proposal_id
                },
                correlation_id=message.correlation_id
            )
            
        except Exception as e:
            return AgentMessage(
                sender=self.agent_id,
                recipient=message.sender,
                message_type=MessageType.ERROR,
                content={"error": str(e)},
                correlation_id=message.correlation_id
            )