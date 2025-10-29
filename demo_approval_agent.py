"""
Demonstration of Approval Agent functionality
Shows the key features implemented in task 6
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import only what we need to avoid syntax errors in other files
from agentic.core.models import DecisionProposal, DecisionStatus, RiskLevel, DecisionImpactAnalysis
from agentic.services.email_notification_service import EmailNotificationService, EmailRecipient
from agentic.services.audit_trail_service import AuditTrailService, AuditEventType
from agentic.services.real_time_notification_service import RealTimeNotificationService, NotificationChannel


async def demo_approval_system():
    """Demonstrate the approval system functionality"""
    print("🚀 Vismaya DemandOps - Approval Agent Demo")
    print("=" * 50)
    
    # Initialize services
    print("\n1. Initializing Services...")
    
    # Email service (mocked for demo)
    email_config = {
        "sender_email": "noreply@vismaya-demandops.com",
        "sender_name": "Vismaya DemandOps",
        "base_url": "https://vismaya-demandops.com",
        "secret_key": "demo-secret-key"
    }
    email_service = EmailNotificationService(email_config)
    print("✅ Email notification service initialized")
    
    # Audit trail service
    audit_service = AuditTrailService()
    print("✅ Audit trail service initialized")
    
    # Real-time notification service
    notification_service = RealTimeNotificationService({
        "enable_websocket": False  # Disable for demo
    })
    print("✅ Real-time notification service initialized")
    
    # Demo stakeholders
    stakeholders = [
        EmailRecipient(
            email="ceo@vismaya-demandops.com",
            name="Chief Executive Officer",
            role="ceo",
            approval_authority={"max_cost": float('inf'), "all_decisions": True}
        ),
        EmailRecipient(
            email="finops@vismaya-demandops.com",
            name="FinOps Lead",
            role="finops_lead",
            approval_authority={"max_cost": 5000, "cost_decisions": True}
        )
    ]
    
    print("\n2. Creating Decision Proposal...")
    
    # Create a decision proposal
    proposal = DecisionProposal(
        title="Optimize EC2 Instance Types",
        description="Switch from t3.large to t3.medium instances to reduce costs by 30%",
        created_by="cost_optimization_agent",
        estimated_cost_impact=2500.0,
        risk_level=RiskLevel.MEDIUM,
        required_approvers=["finops_lead", "cto"],
        approval_deadline=datetime.now() + timedelta(hours=24),
        execution_plan={
            "type": "cost_optimization",
            "expected_savings": 2500,
            "affected_instances": ["i-1234567890abcdef0", "i-0987654321fedcba0"],
            "rollback_plan": "Revert to original instance types within 1 hour"
        }
    )
    
    print(f"✅ Created proposal: {proposal.title}")
    print(f"   - Proposal ID: {proposal.proposal_id}")
    print(f"   - Cost Impact: ${proposal.estimated_cost_impact:,.2f}")
    print(f"   - Risk Level: {proposal.risk_level.value}")
    print(f"   - Required Approvers: {', '.join(proposal.required_approvers)}")
    
    # Record proposal creation in audit trail
    await audit_service.record_proposal_created(
        proposal=proposal,
        actor=proposal.created_by
    )
    print("✅ Proposal creation recorded in audit trail")
    
    print("\n3. Generating Email Approval Request...")
    
    # Generate authentication tokens for email approval
    approve_token = email_service._generate_auth_token(
        proposal.proposal_id, "finops@vismaya-demandops.com", "approve"
    )
    reject_token = email_service._generate_auth_token(
        proposal.proposal_id, "finops@vismaya-demandops.com", "reject"
    )
    
    print("✅ Generated secure authentication tokens")
    print(f"   - Approve token length: {len(approve_token)} characters")
    print(f"   - Reject token length: {len(reject_token)} characters")
    
    # Validate token (simulate email click)
    print("\n4. Simulating Email-based Approval...")
    
    token_validation = email_service.validate_auth_token(approve_token)
    if token_validation["valid"]:
        print("✅ Token validation successful")
        print(f"   - Proposal ID: {token_validation['proposal_id']}")
        print(f"   - Approver: {token_validation['approver_email']}")
        print(f"   - Decision: {token_validation['decision']}")
    else:
        print("❌ Token validation failed")
    
    # Process approval response
    proposal.add_approval_response("finops_lead", "approved", "Cost savings look good")
    
    # Record approval response in audit trail
    await audit_service.record_approval_response(
        proposal_id=proposal.proposal_id,
        approver="finops_lead",
        decision="approved",
        comments="Cost savings look good",
        response_method="email"
    )
    print("✅ Approval response recorded in audit trail")
    
    # Update proposal status
    old_status = proposal.status
    if proposal.is_approved():
        proposal.status = DecisionStatus.APPROVED
        
        # Record status change
        await audit_service.record_proposal_status_change(
            proposal=proposal,
            old_status=old_status,
            new_status=proposal.status,
            actor="finops_lead",
            reason="Sufficient approvals received"
        )
        print("✅ Proposal approved and status updated")
    
    print("\n5. Audit Trail Summary...")
    
    # Get audit trail
    audit_trail = await audit_service.get_audit_trail(proposal.proposal_id)
    if audit_trail:
        print(f"✅ Audit trail contains {len(audit_trail.events)} events:")
        for i, event in enumerate(audit_trail.events, 1):
            print(f"   {i}. {event.event_type.value} by {event.actor} at {event.timestamp.strftime('%H:%M:%S')}")
            print(f"      {event.action_description}")
    
    # Generate approval timeline
    timeline = await audit_service.get_approval_timeline(proposal.proposal_id)
    print(f"\n✅ Approval timeline generated with {len(timeline)} events")
    
    print("\n6. Real-time Notification Demo...")
    
    # Subscribe to notifications (simulate dashboard user)
    await notification_service.subscribe(
        subscriber_id="dashboard_user",
        channels=[NotificationChannel.DASHBOARD],
        proposal_filters={"min_cost_impact": 1000}
    )
    print("✅ Subscribed to real-time notifications")
    
    # Send status change notification
    await notification_service.notify_proposal_status_change(
        proposal=proposal,
        old_status=old_status,
        new_status=proposal.status,
        actor="finops_lead"
    )
    print("✅ Real-time notification sent")
    
    # Get notification history
    notifications = await notification_service.get_notification_history(
        proposal_id=proposal.proposal_id
    )
    print(f"✅ Notification history: {len(notifications)} notifications")
    
    print("\n7. Email Template Preview...")
    
    # Show email template variables
    template_vars = {
        "recipient_name": "FinOps Lead",
        "proposal_title": proposal.title,
        "proposal_description": proposal.description,
        "estimated_cost_impact": f"${proposal.estimated_cost_impact:,.2f}",
        "risk_level": proposal.risk_level.value.title(),
        "created_by": proposal.created_by,
        "approval_deadline": proposal.approval_deadline.strftime("%B %d, %Y at %I:%M %p"),
        "approve_url": f"https://vismaya-demandops.com/api/approval/respond?token={approve_token[:20]}...",
        "reject_url": f"https://vismaya-demandops.com/api/approval/respond?token={reject_token[:20]}...",
        "view_url": f"https://vismaya-demandops.com/dashboard/proposals/{proposal.proposal_id}",
        "proposal_id": proposal.proposal_id
    }
    
    print("✅ Email template variables prepared:")
    for key, value in template_vars.items():
        if len(str(value)) > 50:
            print(f"   - {key}: {str(value)[:47]}...")
        else:
            print(f"   - {key}: {value}")
    
    print("\n8. System Statistics...")
    
    # Get delivery stats
    delivery_stats = await notification_service.get_delivery_stats()
    print("✅ Notification delivery statistics:")
    print(f"   - Total sent: {delivery_stats['total_sent']}")
    print(f"   - Success rate: {delivery_stats['success_rate']:.1f}%")
    print(f"   - Active subscriptions: {delivery_stats['active_subscriptions']}")
    
    # Generate audit report
    audit_report = await audit_service.generate_audit_report(
        proposal_ids=[proposal.proposal_id],
        include_metrics=True
    )
    print("✅ Audit report generated:")
    print(f"   - Total events: {audit_report['summary']['total_events']}")
    print(f"   - Event types: {list(audit_report['summary']['events_by_type'].keys())}")
    
    print("\n" + "=" * 50)
    print("🎉 Approval Agent Demo Complete!")
    print("\nKey Features Demonstrated:")
    print("✅ Decision proposal creation and management")
    print("✅ Email-based approval with secure tokens")
    print("✅ Comprehensive audit trail tracking")
    print("✅ Real-time notification system")
    print("✅ Status tracking and workflow management")
    print("✅ Email template system with one-click approval")
    print("✅ Multi-stakeholder approval workflows")
    print("✅ Security and authentication for email responses")


if __name__ == "__main__":
    asyncio.run(demo_approval_system())