"""
Real-time Decision Tracking Service
Handles live updates for decision proposals and approval workflows
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
import json
import uuid
from dataclasses import dataclass, asdict

from ..agentic.core.models import DecisionProposal, DecisionStatus, RiskLevel
from ..agentic.agents.approval_agent import ApprovalAgent


@dataclass
class DecisionUpdate:
    """Real-time decision update event"""
    update_id: str
    decision_id: str
    update_type: str  # status_change, approval_response, deadline_approaching, etc.
    data: Dict[str, Any]
    timestamp: datetime
    user_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "update_id": self.update_id,
            "decision_id": self.decision_id,
            "update_type": self.update_type,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id
        }


class RealTimeDecisionService:
    """Service for real-time decision tracking and updates"""
    
    def __init__(self, approval_agent: Optional[ApprovalAgent] = None):
        self.logger = logging.getLogger(__name__)
        self.approval_agent = approval_agent
        
        # In-memory storage for demo (in production, use Redis or similar)
        self.active_decisions: Dict[str, DecisionProposal] = {}
        self.decision_history: List[DecisionProposal] = []
        self.subscribers: Dict[str, Callable] = {}
        self.update_queue: List[DecisionUpdate] = []
        
        # Real-time update configuration
        self.update_interval_seconds = 30
        self.max_history_size = 1000
        
        # Start background tasks
        self._background_tasks = []
        self._running = False
    
    async def start_service(self) -> None:
        """Start the real-time service"""
        if self._running:
            return
        
        self._running = True
        
        # Start background monitoring tasks
        self._background_tasks = [
            asyncio.create_task(self._decision_monitor()),
            asyncio.create_task(self._deadline_monitor()),
            asyncio.create_task(self._update_broadcaster())
        ]
        
        self.logger.info("Real-time decision service started")
    
    async def stop_service(self) -> None:
        """Stop the real-time service"""
        self._running = False
        
        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self._background_tasks, return_exceptions=True)
        
        self.logger.info("Real-time decision service stopped")
    
    def subscribe_to_updates(self, subscriber_id: str, callback: Callable[[DecisionUpdate], None]) -> None:
        """Subscribe to real-time decision updates"""
        self.subscribers[subscriber_id] = callback
        self.logger.info(f"Subscriber {subscriber_id} registered for decision updates")
    
    def unsubscribe_from_updates(self, subscriber_id: str) -> None:
        """Unsubscribe from real-time decision updates"""
        if subscriber_id in self.subscribers:
            del self.subscribers[subscriber_id]
            self.logger.info(f"Subscriber {subscriber_id} unregistered from decision updates")
    
    async def create_decision(self, decision_data: Dict[str, Any]) -> DecisionProposal:
        """Create a new decision proposal"""
        try:
            # Create decision proposal
            decision = DecisionProposal(
                proposal_id=decision_data.get('id', str(uuid.uuid4())),
                title=decision_data.get('title', 'Untitled Decision'),
                description=decision_data.get('description', ''),
                estimated_cost_impact=decision_data.get('cost_impact', 0.0),
                risk_level=RiskLevel(decision_data.get('risk_level', 'low')),
                status=DecisionStatus.PENDING,
                created_at=datetime.now(),
                approval_deadline=decision_data.get('deadline'),
                required_approvers=decision_data.get('required_approvers', ['finops_lead']),
                recommendations=decision_data.get('recommendations', []),
                metadata=decision_data.get('metadata', {})
            )
            
            # Store decision
            self.active_decisions[decision.proposal_id] = decision
            
            # Create update event
            update = DecisionUpdate(
                update_id=str(uuid.uuid4()),
                decision_id=decision.proposal_id,
                update_type="decision_created",
                data={
                    "title": decision.title,
                    "cost_impact": decision.estimated_cost_impact,
                    "risk_level": decision.risk_level.value,
                    "required_approvers": decision.required_approvers
                },
                timestamp=datetime.now()
            )
            
            # Queue update for broadcasting
            self.update_queue.append(update)
            
            self.logger.info(f"Created decision {decision.proposal_id}: {decision.title}")
            return decision
            
        except Exception as e:
            self.logger.error(f"Error creating decision: {e}")
            raise
    
    async def update_decision_status(self, decision_id: str, new_status: DecisionStatus, 
                                   approver: Optional[str] = None, comments: Optional[str] = None) -> bool:
        """Update decision status and broadcast update"""
        try:
            decision = self.active_decisions.get(decision_id)
            if not decision:
                self.logger.error(f"Decision {decision_id} not found")
                return False
            
            old_status = decision.status
            decision.status = new_status
            
            # Move to history if completed
            if new_status in [DecisionStatus.APPROVED, DecisionStatus.REJECTED, DecisionStatus.EXECUTED, DecisionStatus.CANCELLED]:
                self.decision_history.append(decision)
                if decision_id in self.active_decisions:
                    del self.active_decisions[decision_id]
                
                # Trim history if too large
                if len(self.decision_history) > self.max_history_size:
                    self.decision_history = self.decision_history[-self.max_history_size:]
            
            # Create update event
            update = DecisionUpdate(
                update_id=str(uuid.uuid4()),
                decision_id=decision_id,
                update_type="status_change",
                data={
                    "old_status": old_status.value,
                    "new_status": new_status.value,
                    "approver": approver,
                    "comments": comments,
                    "approval_summary": decision.get_approval_summary()
                },
                timestamp=datetime.now(),
                user_id=approver
            )
            
            # Queue update for broadcasting
            self.update_queue.append(update)
            
            self.logger.info(f"Updated decision {decision_id} status: {old_status.value} -> {new_status.value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating decision status: {e}")
            return False
    
    async def process_approval(self, decision_id: str, approver: str, decision: str, comments: Optional[str] = None) -> bool:
        """Process approval response"""
        try:
            proposal = self.active_decisions.get(decision_id)
            if not proposal:
                self.logger.error(f"Decision {decision_id} not found")
                return False
            
            # Check if approver already responded
            existing_response = next(
                (r for r in proposal.approval_responses if r["approver"] == approver),
                None
            )
            if existing_response:
                self.logger.warning(f"Approver {approver} already responded to decision {decision_id}")
                return False
            
            # Add approval response
            proposal.add_approval_response(approver, decision, comments)
            
            # Determine new status
            new_status = proposal.status
            if proposal.is_approved():
                new_status = DecisionStatus.APPROVED
            elif proposal.is_rejected():
                new_status = DecisionStatus.REJECTED
            
            # Update status if changed
            if new_status != proposal.status:
                await self.update_decision_status(decision_id, new_status, approver, comments)
            else:
                # Create approval response update
                update = DecisionUpdate(
                    update_id=str(uuid.uuid4()),
                    decision_id=decision_id,
                    update_type="approval_response",
                    data={
                        "approver": approver,
                        "decision": decision,
                        "comments": comments,
                        "approval_summary": proposal.get_approval_summary()
                    },
                    timestamp=datetime.now(),
                    user_id=approver
                )
                
                self.update_queue.append(update)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error processing approval: {e}")
            return False
    
    def get_active_decisions(self, approver_id: Optional[str] = None) -> List[DecisionProposal]:
        """Get active decisions, optionally filtered by approver"""
        decisions = list(self.active_decisions.values())
        
        if approver_id:
            decisions = [d for d in decisions if approver_id in d.required_approvers]
        
        # Sort by priority and creation time
        priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        decisions.sort(key=lambda x: (
            priority_order.get(x.risk_level.value, 2),
            x.created_at
        ))
        
        return decisions
    
    def get_decision_history(self, limit: int = 50) -> List[DecisionProposal]:
        """Get decision history"""
        return self.decision_history[-limit:] if limit else self.decision_history
    
    def get_decision_by_id(self, decision_id: str) -> Optional[DecisionProposal]:
        """Get decision by ID from active decisions or history"""
        # Check active decisions first
        if decision_id in self.active_decisions:
            return self.active_decisions[decision_id]
        
        # Check history
        for decision in self.decision_history:
            if decision.proposal_id == decision_id:
                return decision
        
        return None
    
    def get_decision_metrics(self) -> Dict[str, Any]:
        """Get decision metrics for dashboard"""
        active_decisions = list(self.active_decisions.values())
        total_decisions = len(active_decisions) + len(self.decision_history)
        
        # Calculate metrics
        pending_count = len([d for d in active_decisions if d.status == DecisionStatus.PENDING])
        approved_count = len([d for d in self.decision_history if d.status == DecisionStatus.APPROVED])
        rejected_count = len([d for d in self.decision_history if d.status == DecisionStatus.REJECTED])
        
        # Calculate approval rate
        completed_decisions = approved_count + rejected_count
        approval_rate = (approved_count / completed_decisions * 100) if completed_decisions > 0 else 0
        
        # Calculate average approval time
        approved_decisions = [d for d in self.decision_history if d.status == DecisionStatus.APPROVED]
        avg_approval_time = 0
        if approved_decisions:
            total_time = 0
            count = 0
            for decision in approved_decisions:
                if decision.approval_responses:
                    # Calculate time from creation to first approval
                    first_approval = min(
                        datetime.fromisoformat(r['timestamp']) for r in decision.approval_responses
                        if r['decision'] == 'approved'
                    )
                    approval_time = (first_approval - decision.created_at).total_seconds() / 3600
                    total_time += approval_time
                    count += 1
            
            if count > 0:
                avg_approval_time = total_time / count
        
        return {
            'total_decisions': total_decisions,
            'pending_decisions': pending_count,
            'approved_decisions': approved_count,
            'rejected_decisions': rejected_count,
            'approval_rate': approval_rate,
            'avg_approval_time_hours': avg_approval_time
        }
    
    async def _decision_monitor(self) -> None:
        """Monitor decisions for status changes"""
        while self._running:
            try:
                await asyncio.sleep(self.update_interval_seconds)
                
                # Check for decisions approaching deadline
                current_time = datetime.now()
                for decision in self.active_decisions.values():
                    if decision.approval_deadline and decision.status == DecisionStatus.PENDING:
                        time_remaining = decision.approval_deadline - current_time
                        hours_remaining = time_remaining.total_seconds() / 3600
                        
                        # Notify if less than 24 hours remaining
                        if 0 < hours_remaining <= 24:
                            update = DecisionUpdate(
                                update_id=str(uuid.uuid4()),
                                decision_id=decision.proposal_id,
                                update_type="deadline_approaching",
                                data={
                                    "hours_remaining": hours_remaining,
                                    "deadline": decision.approval_deadline.isoformat()
                                },
                                timestamp=current_time
                            )
                            self.update_queue.append(update)
                
            except Exception as e:
                self.logger.error(f"Error in decision monitor: {e}")
    
    async def _deadline_monitor(self) -> None:
        """Monitor for expired decisions"""
        while self._running:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                
                current_time = datetime.now()
                expired_decisions = []
                
                for decision in self.active_decisions.values():
                    if (decision.approval_deadline and 
                        decision.status == DecisionStatus.PENDING and
                        current_time > decision.approval_deadline):
                        expired_decisions.append(decision)
                
                # Handle expired decisions
                for decision in expired_decisions:
                    await self.update_decision_status(
                        decision.proposal_id, 
                        DecisionStatus.CANCELLED,
                        None,
                        "Expired due to deadline"
                    )
                    
                    # Create expiration update
                    update = DecisionUpdate(
                        update_id=str(uuid.uuid4()),
                        decision_id=decision.proposal_id,
                        update_type="decision_expired",
                        data={
                            "expired_at": current_time.isoformat(),
                            "deadline": decision.approval_deadline.isoformat()
                        },
                        timestamp=current_time
                    )
                    self.update_queue.append(update)
                
            except Exception as e:
                self.logger.error(f"Error in deadline monitor: {e}")
    
    async def _update_broadcaster(self) -> None:
        """Broadcast updates to subscribers"""
        while self._running:
            try:
                await asyncio.sleep(1)  # Check for updates every second
                
                # Process queued updates
                while self.update_queue:
                    update = self.update_queue.pop(0)
                    
                    # Broadcast to all subscribers
                    for subscriber_id, callback in self.subscribers.items():
                        try:
                            callback(update)
                        except Exception as e:
                            self.logger.error(f"Error broadcasting to subscriber {subscriber_id}: {e}")
                
            except Exception as e:
                self.logger.error(f"Error in update broadcaster: {e}")
    
    def create_demo_decisions(self) -> List[DecisionProposal]:
        """Create demo decisions for testing"""
        demo_decisions_data = [
            {
                'id': 'DEC-001',
                'title': 'Terminate Unused EBS Volumes',
                'description': 'Remove 5 unattached EBS volumes to reduce storage costs',
                'cost_impact': 125.00,
                'risk_level': 'low',
                'required_approvers': ['finops_lead'],
                'deadline': datetime.now() + timedelta(days=7),
                'recommendations': [
                    'Verify volumes are truly unused',
                    'Create snapshots before deletion',
                    'Monitor for any application dependencies'
                ]
            },
            {
                'id': 'DEC-002',
                'title': 'Scale Down RDS Instance',
                'description': 'Downgrade RDS instance from db.t3.large to db.t3.medium',
                'cost_impact': 450.00,
                'risk_level': 'medium',
                'required_approvers': ['cto', 'finops_lead'],
                'deadline': datetime.now() + timedelta(days=2),
                'recommendations': [
                    'Schedule during maintenance window',
                    'Monitor performance after change',
                    'Have rollback plan ready'
                ]
            },
            {
                'id': 'DEC-003',
                'title': 'Optimize EC2 Instance Types',
                'description': 'Switch from t3.large to t3.medium instances to reduce costs',
                'cost_impact': 245.50,
                'risk_level': 'low',
                'required_approvers': ['finops_lead'],
                'deadline': datetime.now() + timedelta(days=3),
                'recommendations': [
                    'Test performance with new instance type',
                    'Implement during low-traffic hours',
                    'Set up monitoring alerts'
                ]
            }
        ]
        
        created_decisions = []
        for decision_data in demo_decisions_data:
            try:
                decision = asyncio.run(self.create_decision(decision_data))
                created_decisions.append(decision)
            except Exception as e:
                self.logger.error(f"Error creating demo decision: {e}")
        
        return created_decisions