"""
Audit Trail Service for Decision Management
Tracks and stores comprehensive audit trails for all approval activities
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from ..core.models import DecisionProposal, DecisionStatus, SystemEvent


class AuditEventType(Enum):
    """Types of audit events"""
    PROPOSAL_CREATED = "proposal_created"
    APPROVAL_REQUEST_SENT = "approval_request_sent"
    APPROVAL_RESPONSE_RECEIVED = "approval_response_received"
    PROPOSAL_APPROVED = "proposal_approved"
    PROPOSAL_REJECTED = "proposal_rejected"
    PROPOSAL_EXECUTED = "proposal_executed"
    PROPOSAL_EXPIRED = "proposal_expired"
    PROPOSAL_ESCALATED = "proposal_escalated"
    EMAIL_SENT = "email_sent"
    EMAIL_DELIVERED = "email_delivered"
    EMAIL_BOUNCED = "email_bounced"
    STATUS_UPDATED = "status_updated"
    DEADLINE_EXTENDED = "deadline_extended"
    APPROVER_ADDED = "approver_added"
    APPROVER_REMOVED = "approver_removed"


@dataclass
class AuditEvent:
    """Individual audit event"""
    event_id: str = field(default_factory=lambda: f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}")
    event_type: AuditEventType = AuditEventType.STATUS_UPDATED
    timestamp: datetime = field(default_factory=datetime.now)
    proposal_id: str = ""
    actor: str = ""  # Who performed the action
    actor_type: str = "user"  # user, system, agent
    action_description: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert audit event to dictionary"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "proposal_id": self.proposal_id,
            "actor": self.actor,
            "actor_type": self.actor_type,
            "action_description": self.action_description,
            "details": self.details,
            "metadata": self.metadata,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AuditEvent':
        """Create audit event from dictionary"""
        return cls(
            event_id=data["event_id"],
            event_type=AuditEventType(data["event_type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            proposal_id=data["proposal_id"],
            actor=data["actor"],
            actor_type=data.get("actor_type", "user"),
            action_description=data["action_description"],
            details=data.get("details", {}),
            metadata=data.get("metadata", {}),
            ip_address=data.get("ip_address"),
            user_agent=data.get("user_agent")
        )


@dataclass
class AuditTrail:
    """Complete audit trail for a proposal"""
    proposal_id: str
    events: List[AuditEvent] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    
    def add_event(self, event: AuditEvent) -> None:
        """Add event to audit trail"""
        self.events.append(event)
        self.last_updated = datetime.now()
    
    def get_events_by_type(self, event_type: AuditEventType) -> List[AuditEvent]:
        """Get events by type"""
        return [event for event in self.events if event.event_type == event_type]
    
    def get_events_by_actor(self, actor: str) -> List[AuditEvent]:
        """Get events by actor"""
        return [event for event in self.events if event.actor == actor]
    
    def get_events_in_timeframe(self, start_time: datetime, end_time: datetime) -> List[AuditEvent]:
        """Get events within timeframe"""
        return [
            event for event in self.events 
            if start_time <= event.timestamp <= end_time
        ]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert audit trail to dictionary"""
        return {
            "proposal_id": self.proposal_id,
            "events": [event.to_dict() for event in self.events],
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "total_events": len(self.events)
        }


class AuditTrailService:
    """
    Audit trail service for comprehensive tracking of approval activities
    
    Features:
    - Complete audit trail for all proposal activities
    - Real-time event tracking and storage
    - Audit trail querying and reporting
    - Compliance and security logging
    - Performance metrics and analytics
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.retention_days = self.config.get("retention_days", 2555)  # 7 years default
        self.enable_real_time_notifications = self.config.get("enable_real_time_notifications", True)
        self.enable_compliance_logging = self.config.get("enable_compliance_logging", True)
        
        # In-memory storage (in production, use persistent storage)
        self.audit_trails: Dict[str, AuditTrail] = {}
        self.event_subscribers: List[callable] = []
        
        # Performance metrics
        self.metrics = {
            "total_events": 0,
            "events_by_type": {},
            "events_by_actor": {},
            "average_response_time": 0.0
        }
    
    async def record_proposal_created(
        self,
        proposal: DecisionProposal,
        actor: str = "system",
        additional_details: Dict[str, Any] = None
    ) -> None:
        """Record proposal creation event"""
        try:
            event = AuditEvent(
                event_type=AuditEventType.PROPOSAL_CREATED,
                proposal_id=proposal.proposal_id,
                actor=actor,
                actor_type="system" if actor == "system" else "user",
                action_description=f"Proposal '{proposal.title}' created",
                details={
                    "title": proposal.title,
                    "description": proposal.description,
                    "created_by": proposal.created_by,
                    "estimated_cost_impact": proposal.estimated_cost_impact,
                    "risk_level": proposal.risk_level.value,
                    "required_approvers": proposal.required_approvers,
                    "approval_deadline": proposal.approval_deadline.isoformat() if proposal.approval_deadline else None,
                    **(additional_details or {})
                }
            )
            
            await self._record_event(event)
            
        except Exception as e:
            self.logger.error(f"Error recording proposal creation: {e}")
    
    async def record_approval_request_sent(
        self,
        proposal: DecisionProposal,
        recipients: List[str],
        email_success: bool = False,
        actor: str = "system",
        additional_details: Dict[str, Any] = None
    ) -> None:
        """Record approval request sent event"""
        try:
            event = AuditEvent(
                event_type=AuditEventType.APPROVAL_REQUEST_SENT,
                proposal_id=proposal.proposal_id,
                actor=actor,
                actor_type="system",
                action_description=f"Approval request sent to {len(recipients)} recipients",
                details={
                    "recipients": recipients,
                    "email_success": email_success,
                    "approval_deadline": proposal.approval_deadline.isoformat() if proposal.approval_deadline else None,
                    **(additional_details or {})
                }
            )
            
            await self._record_event(event)
            
        except Exception as e:
            self.logger.error(f"Error recording approval request sent: {e}")
    
    async def record_approval_response(
        self,
        proposal_id: str,
        approver: str,
        decision: str,
        comments: Optional[str] = None,
        response_method: str = "email",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        additional_details: Dict[str, Any] = None
    ) -> None:
        """Record approval response event"""
        try:
            event = AuditEvent(
                event_type=AuditEventType.APPROVAL_RESPONSE_RECEIVED,
                proposal_id=proposal_id,
                actor=approver,
                actor_type="user",
                action_description=f"Approval response: {decision}",
                details={
                    "decision": decision,
                    "comments": comments,
                    "response_method": response_method,
                    **(additional_details or {})
                },
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            await self._record_event(event)
            
        except Exception as e:
            self.logger.error(f"Error recording approval response: {e}")
    
    async def record_proposal_status_change(
        self,
        proposal: DecisionProposal,
        old_status: DecisionStatus,
        new_status: DecisionStatus,
        actor: str = "system",
        reason: Optional[str] = None,
        additional_details: Dict[str, Any] = None
    ) -> None:
        """Record proposal status change event"""
        try:
            # Determine event type based on new status
            if new_status == DecisionStatus.APPROVED:
                event_type = AuditEventType.PROPOSAL_APPROVED
                action_description = f"Proposal approved"
            elif new_status == DecisionStatus.REJECTED:
                event_type = AuditEventType.PROPOSAL_REJECTED
                action_description = f"Proposal rejected"
            elif new_status == DecisionStatus.EXECUTED:
                event_type = AuditEventType.PROPOSAL_EXECUTED
                action_description = f"Proposal executed"
            elif new_status == DecisionStatus.CANCELLED:
                event_type = AuditEventType.PROPOSAL_EXPIRED
                action_description = f"Proposal expired/cancelled"
            else:
                event_type = AuditEventType.STATUS_UPDATED
                action_description = f"Status changed from {old_status.value} to {new_status.value}"
            
            event = AuditEvent(
                event_type=event_type,
                proposal_id=proposal.proposal_id,
                actor=actor,
                actor_type="system" if actor == "system" else "user",
                action_description=action_description,
                details={
                    "old_status": old_status.value,
                    "new_status": new_status.value,
                    "reason": reason,
                    "approval_summary": proposal.get_approval_summary(),
                    **(additional_details or {})
                }
            )
            
            await self._record_event(event)
            
        except Exception as e:
            self.logger.error(f"Error recording status change: {e}")
    
    async def record_proposal_execution(
        self,
        proposal: DecisionProposal,
        execution_result: Dict[str, Any],
        actor: str = "system",
        additional_details: Dict[str, Any] = None
    ) -> None:
        """Record proposal execution event"""
        try:
            event = AuditEvent(
                event_type=AuditEventType.PROPOSAL_EXECUTED,
                proposal_id=proposal.proposal_id,
                actor=actor,
                actor_type="system",
                action_description=f"Proposal executed {'successfully' if execution_result.get('success') else 'with errors'}",
                details={
                    "execution_success": execution_result.get("success", False),
                    "execution_result": execution_result.get("result", ""),
                    "execution_time": execution_result.get("execution_time_seconds", 0),
                    **(additional_details or {})
                }
            )
            
            await self._record_event(event)
            
        except Exception as e:
            self.logger.error(f"Error recording proposal execution: {e}")
    
    async def record_email_event(
        self,
        proposal_id: str,
        event_type: AuditEventType,
        recipient: str,
        email_details: Dict[str, Any],
        actor: str = "system"
    ) -> None:
        """Record email-related event"""
        try:
            event = AuditEvent(
                event_type=event_type,
                proposal_id=proposal_id,
                actor=actor,
                actor_type="system",
                action_description=f"Email {event_type.value.replace('email_', '')} to {recipient}",
                details={
                    "recipient": recipient,
                    "message_id": email_details.get("message_id"),
                    "email_type": email_details.get("email_type"),
                    "success": email_details.get("success", False),
                    "error": email_details.get("error")
                }
            )
            
            await self._record_event(event)
            
        except Exception as e:
            self.logger.error(f"Error recording email event: {e}")
    
    async def record_escalation(
        self,
        proposal_id: str,
        escalated_to: List[str],
        reason: str,
        actor: str = "system",
        additional_details: Dict[str, Any] = None
    ) -> None:
        """Record proposal escalation event"""
        try:
            event = AuditEvent(
                event_type=AuditEventType.PROPOSAL_ESCALATED,
                proposal_id=proposal_id,
                actor=actor,
                actor_type="system",
                action_description=f"Proposal escalated to {', '.join(escalated_to)}",
                details={
                    "escalated_to": escalated_to,
                    "reason": reason,
                    **(additional_details or {})
                }
            )
            
            await self._record_event(event)
            
        except Exception as e:
            self.logger.error(f"Error recording escalation: {e}")
    
    async def get_audit_trail(self, proposal_id: str) -> Optional[AuditTrail]:
        """Get complete audit trail for proposal"""
        return self.audit_trails.get(proposal_id)
    
    async def get_audit_events(
        self,
        proposal_id: str,
        event_type: Optional[AuditEventType] = None,
        actor: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AuditEvent]:
        """Get filtered audit events"""
        try:
            audit_trail = self.audit_trails.get(proposal_id)
            if not audit_trail:
                return []
            
            events = audit_trail.events
            
            # Apply filters
            if event_type:
                events = [e for e in events if e.event_type == event_type]
            
            if actor:
                events = [e for e in events if e.actor == actor]
            
            if start_time:
                events = [e for e in events if e.timestamp >= start_time]
            
            if end_time:
                events = [e for e in events if e.timestamp <= end_time]
            
            # Sort by timestamp (newest first) and apply limit
            events.sort(key=lambda e: e.timestamp, reverse=True)
            return events[:limit]
            
        except Exception as e:
            self.logger.error(f"Error getting audit events: {e}")
            return []
    
    async def get_approval_timeline(self, proposal_id: str) -> List[Dict[str, Any]]:
        """Get approval timeline for proposal"""
        try:
            events = await self.get_audit_events(proposal_id)
            
            timeline = []
            for event in events:
                timeline.append({
                    "timestamp": event.timestamp.isoformat(),
                    "event_type": event.event_type.value,
                    "actor": event.actor,
                    "description": event.action_description,
                    "details": event.details
                })
            
            return timeline
            
        except Exception as e:
            self.logger.error(f"Error getting approval timeline: {e}")
            return []
    
    async def generate_audit_report(
        self,
        proposal_ids: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        include_metrics: bool = True
    ) -> Dict[str, Any]:
        """Generate comprehensive audit report"""
        try:
            report = {
                "generated_at": datetime.now().isoformat(),
                "report_period": {
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None
                },
                "proposals": [],
                "summary": {
                    "total_proposals": 0,
                    "total_events": 0,
                    "events_by_type": {},
                    "approval_metrics": {}
                }
            }
            
            # Filter proposals
            proposals_to_include = proposal_ids or list(self.audit_trails.keys())
            
            total_events = 0
            events_by_type = {}
            
            for proposal_id in proposals_to_include:
                audit_trail = self.audit_trails.get(proposal_id)
                if not audit_trail:
                    continue
                
                # Filter events by date range
                events = audit_trail.events
                if start_date or end_date:
                    events = [
                        e for e in events
                        if (not start_date or e.timestamp >= start_date) and
                           (not end_date or e.timestamp <= end_date)
                    ]
                
                if not events:
                    continue
                
                # Add proposal to report
                proposal_data = {
                    "proposal_id": proposal_id,
                    "total_events": len(events),
                    "first_event": events[0].timestamp.isoformat() if events else None,
                    "last_event": events[-1].timestamp.isoformat() if events else None,
                    "events": [event.to_dict() for event in events]
                }
                
                report["proposals"].append(proposal_data)
                
                # Update summary
                total_events += len(events)
                for event in events:
                    event_type = event.event_type.value
                    events_by_type[event_type] = events_by_type.get(event_type, 0) + 1
            
            # Update report summary
            report["summary"]["total_proposals"] = len(report["proposals"])
            report["summary"]["total_events"] = total_events
            report["summary"]["events_by_type"] = events_by_type
            
            # Add metrics if requested
            if include_metrics:
                report["summary"]["approval_metrics"] = await self._calculate_approval_metrics(proposals_to_include)
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating audit report: {e}")
            return {"error": str(e)}
    
    def subscribe_to_events(self, callback: callable) -> None:
        """Subscribe to real-time audit events"""
        self.event_subscribers.append(callback)
    
    def unsubscribe_from_events(self, callback: callable) -> None:
        """Unsubscribe from real-time audit events"""
        if callback in self.event_subscribers:
            self.event_subscribers.remove(callback)
    
    async def _record_event(self, event: AuditEvent) -> None:
        """Record audit event"""
        try:
            # Get or create audit trail
            if event.proposal_id not in self.audit_trails:
                self.audit_trails[event.proposal_id] = AuditTrail(proposal_id=event.proposal_id)
            
            # Add event to audit trail
            self.audit_trails[event.proposal_id].add_event(event)
            
            # Update metrics
            self.metrics["total_events"] += 1
            event_type = event.event_type.value
            self.metrics["events_by_type"][event_type] = self.metrics["events_by_type"].get(event_type, 0) + 1
            self.metrics["events_by_actor"][event.actor] = self.metrics["events_by_actor"].get(event.actor, 0) + 1
            
            # Notify subscribers
            if self.enable_real_time_notifications:
                await self._notify_subscribers(event)
            
            # Log for compliance if enabled
            if self.enable_compliance_logging:
                self.logger.info(f"AUDIT: {event.event_type.value} - {event.action_description} - Actor: {event.actor} - Proposal: {event.proposal_id}")
            
        except Exception as e:
            self.logger.error(f"Error recording audit event: {e}")
    
    async def _notify_subscribers(self, event: AuditEvent) -> None:
        """Notify event subscribers"""
        try:
            for callback in self.event_subscribers:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(event)
                    else:
                        callback(event)
                except Exception as e:
                    self.logger.error(f"Error notifying subscriber: {e}")
        except Exception as e:
            self.logger.error(f"Error in subscriber notification: {e}")
    
    async def _calculate_approval_metrics(self, proposal_ids: List[str]) -> Dict[str, Any]:
        """Calculate approval metrics for proposals"""
        try:
            metrics = {
                "average_approval_time_hours": 0.0,
                "approval_rate": 0.0,
                "rejection_rate": 0.0,
                "expiration_rate": 0.0,
                "most_active_approvers": {},
                "response_times_by_approver": {}
            }
            
            total_proposals = 0
            approved_count = 0
            rejected_count = 0
            expired_count = 0
            approval_times = []
            approver_activity = {}
            approver_response_times = {}
            
            for proposal_id in proposal_ids:
                audit_trail = self.audit_trails.get(proposal_id)
                if not audit_trail:
                    continue
                
                total_proposals += 1
                
                # Find creation and final decision events
                creation_event = None
                final_decision_event = None
                
                for event in audit_trail.events:
                    if event.event_type == AuditEventType.PROPOSAL_CREATED:
                        creation_event = event
                    elif event.event_type in [AuditEventType.PROPOSAL_APPROVED, AuditEventType.PROPOSAL_REJECTED, AuditEventType.PROPOSAL_EXPIRED]:
                        final_decision_event = event
                
                # Calculate approval time
                if creation_event and final_decision_event:
                    approval_time = (final_decision_event.timestamp - creation_event.timestamp).total_seconds() / 3600
                    approval_times.append(approval_time)
                
                # Count outcomes
                if final_decision_event:
                    if final_decision_event.event_type == AuditEventType.PROPOSAL_APPROVED:
                        approved_count += 1
                    elif final_decision_event.event_type == AuditEventType.PROPOSAL_REJECTED:
                        rejected_count += 1
                    elif final_decision_event.event_type == AuditEventType.PROPOSAL_EXPIRED:
                        expired_count += 1
                
                # Track approver activity
                for event in audit_trail.events:
                    if event.event_type == AuditEventType.APPROVAL_RESPONSE_RECEIVED:
                        approver = event.actor
                        approver_activity[approver] = approver_activity.get(approver, 0) + 1
                        
                        # Calculate response time
                        if creation_event:
                            response_time = (event.timestamp - creation_event.timestamp).total_seconds() / 3600
                            if approver not in approver_response_times:
                                approver_response_times[approver] = []
                            approver_response_times[approver].append(response_time)
            
            # Calculate metrics
            if total_proposals > 0:
                metrics["approval_rate"] = (approved_count / total_proposals) * 100
                metrics["rejection_rate"] = (rejected_count / total_proposals) * 100
                metrics["expiration_rate"] = (expired_count / total_proposals) * 100
            
            if approval_times:
                metrics["average_approval_time_hours"] = sum(approval_times) / len(approval_times)
            
            metrics["most_active_approvers"] = dict(sorted(approver_activity.items(), key=lambda x: x[1], reverse=True)[:10])
            
            # Calculate average response times by approver
            for approver, times in approver_response_times.items():
                metrics["response_times_by_approver"][approver] = sum(times) / len(times)
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error calculating approval metrics: {e}")
            return {}
    
    async def cleanup_old_records(self) -> int:
        """Clean up old audit records based on retention policy"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            cleaned_count = 0
            
            for proposal_id, audit_trail in list(self.audit_trails.items()):
                # Remove old events
                original_count = len(audit_trail.events)
                audit_trail.events = [
                    event for event in audit_trail.events
                    if event.timestamp > cutoff_date
                ]
                
                cleaned_count += original_count - len(audit_trail.events)
                
                # Remove empty audit trails
                if not audit_trail.events:
                    del self.audit_trails[proposal_id]
            
            self.logger.info(f"Cleaned up {cleaned_count} old audit records")
            return cleaned_count
            
        except Exception as e:
            self.logger.error(f"Error cleaning up old records: {e}")
            return 0