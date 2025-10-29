#!/usr/bin/env python3
"""
Demo script for Real-time Decision Tracking and Approval Interface
Showcases the implementation of task 8.2
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List

from src.services.real_time_decision_service import RealTimeDecisionService, DecisionUpdate
from src.agentic.core.models import DecisionProposal, DecisionStatus, RiskLevel

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DecisionTrackingDemo:
    """Demo class for real-time decision tracking"""
    
    def __init__(self):
        self.service = RealTimeDecisionService()
        self.updates_received = []
        
    def setup_real_time_updates(self):
        """Setup real-time update handling"""
        def update_handler(update: DecisionUpdate):
            self.updates_received.append(update)
            logger.info(f"📢 Real-time update: {update.update_type} for decision {update.decision_id}")
            
            # Display update details
            if update.update_type == "decision_created":
                logger.info(f"   📋 New decision: {update.data.get('title')}")
                logger.info(f"   💰 Cost impact: ${update.data.get('cost_impact', 0):,.2f}")
                logger.info(f"   ⚠️ Risk level: {update.data.get('risk_level', 'unknown')}")
            
            elif update.update_type == "status_change":
                old_status = update.data.get('old_status')
                new_status = update.data.get('new_status')
                logger.info(f"   🔄 Status changed: {old_status} → {new_status}")
                
                if update.data.get('approver'):
                    logger.info(f"   👤 By: {update.data.get('approver')}")
            
            elif update.update_type == "approval_response":
                approver = update.data.get('approver')
                decision = update.data.get('decision')
                logger.info(f"   ✅ {approver} {decision} the decision")
                
                if update.data.get('comments'):
                    logger.info(f"   💬 Comments: {update.data.get('comments')}")
        
        # Subscribe to updates
        self.service.subscribe_to_updates("demo_subscriber", update_handler)
        logger.info("🔔 Subscribed to real-time updates")
    
    async def demo_decision_creation(self):
        """Demo decision creation with real-time updates"""
        logger.info("\n" + "="*60)
        logger.info("🚀 DEMO: Decision Creation with Real-time Updates")
        logger.info("="*60)
        
        # Create multiple decisions with different priorities
        decisions_data = [
            {
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
                'title': 'Migrate to Reserved Instances',
                'description': 'Convert on-demand EC2 instances to reserved instances for cost savings',
                'cost_impact': 2500.00,
                'risk_level': 'high',
                'required_approvers': ['ceo', 'cto', 'finops_lead'],
                'deadline': datetime.now() + timedelta(days=1),
                'recommendations': [
                    'Analyze usage patterns for 3 months',
                    'Calculate ROI and payback period',
                    'Ensure commitment aligns with business plans'
                ]
            }
        ]
        
        created_decisions = []
        for decision_data in decisions_data:
            logger.info(f"\n📋 Creating decision: {decision_data['title']}")
            decision = await self.service.create_decision(decision_data)
            created_decisions.append(decision)
            
            # Small delay to see real-time updates
            await asyncio.sleep(0.5)
        
        logger.info(f"\n✅ Created {len(created_decisions)} decisions")
        return created_decisions
    
    async def demo_approval_workflow(self, decisions: List[DecisionProposal]):
        """Demo approval workflow with real-time status updates"""
        logger.info("\n" + "="*60)
        logger.info("👥 DEMO: Approval Workflow with Real-time Status Updates")
        logger.info("="*60)
        
        # Process approvals for different decisions
        for decision in decisions:
            logger.info(f"\n🔍 Processing approvals for: {decision.title}")
            logger.info(f"   Required approvers: {decision.required_approvers}")
            
            # Simulate approval responses
            if 'finops_lead' in decision.required_approvers:
                logger.info("   💼 FinOps Lead reviewing...")
                await asyncio.sleep(1)
                
                success = await self.service.process_approval(
                    decision.proposal_id, 
                    'finops_lead', 
                    'approved', 
                    f'Approved for cost savings of ${decision.estimated_cost_impact:,.2f}'
                )
                
                if success:
                    logger.info("   ✅ FinOps Lead approved")
                else:
                    logger.info("   ❌ FinOps Lead approval failed")
            
            if 'cto' in decision.required_approvers:
                logger.info("   🔧 CTO reviewing...")
                await asyncio.sleep(1)
                
                # CTO approves medium risk, but rejects high risk
                cto_decision = 'approved' if decision.risk_level != RiskLevel.HIGH else 'rejected'
                cto_comment = 'Technical review completed' if cto_decision == 'approved' else 'Too risky for current infrastructure'
                
                success = await self.service.process_approval(
                    decision.proposal_id, 
                    'cto', 
                    cto_decision, 
                    cto_comment
                )
                
                if success:
                    logger.info(f"   {'✅' if cto_decision == 'approved' else '❌'} CTO {cto_decision}")
                else:
                    logger.info("   ❌ CTO response failed")
            
            if 'ceo' in decision.required_approvers:
                logger.info("   👑 CEO reviewing...")
                await asyncio.sleep(1)
                
                success = await self.service.process_approval(
                    decision.proposal_id, 
                    'ceo', 
                    'approved', 
                    'Strategic decision approved for cost optimization'
                )
                
                if success:
                    logger.info("   ✅ CEO approved")
                else:
                    logger.info("   ❌ CEO approval failed")
            
            # Small delay between decisions
            await asyncio.sleep(1)
    
    def demo_decision_metrics(self):
        """Demo decision metrics and analytics"""
        logger.info("\n" + "="*60)
        logger.info("📊 DEMO: Decision Metrics and Analytics")
        logger.info("="*60)
        
        # Get current metrics
        metrics = self.service.get_decision_metrics()
        
        logger.info("📈 Current Decision Metrics:")
        logger.info(f"   📋 Total decisions: {metrics['total_decisions']}")
        logger.info(f"   ⏳ Pending decisions: {metrics['pending_decisions']}")
        logger.info(f"   ✅ Approved decisions: {metrics['approved_decisions']}")
        logger.info(f"   ❌ Rejected decisions: {metrics['rejected_decisions']}")
        logger.info(f"   📊 Approval rate: {metrics['approval_rate']:.1f}%")
        logger.info(f"   ⏱️ Avg approval time: {metrics['avg_approval_time_hours']:.1f} hours")
        
        # Get active decisions
        active_decisions = self.service.get_active_decisions()
        logger.info(f"\n📋 Active Decisions ({len(active_decisions)}):")
        for decision in active_decisions:
            logger.info(f"   • {decision.title} - {decision.status.value} - ${decision.estimated_cost_impact:,.2f}")
        
        # Get decision history
        history = self.service.get_decision_history()
        logger.info(f"\n📚 Decision History ({len(history)}):")
        for decision in history[-5:]:  # Show last 5
            logger.info(f"   • {decision.title} - {decision.status.value} - ${decision.estimated_cost_impact:,.2f}")
    
    def demo_audit_trail(self):
        """Demo audit trail functionality"""
        logger.info("\n" + "="*60)
        logger.info("🔍 DEMO: Audit Trail and Decision History")
        logger.info("="*60)
        
        # Show all decisions with their approval responses
        all_decisions = list(self.service.active_decisions.values()) + self.service.decision_history
        
        for decision in all_decisions:
            logger.info(f"\n📋 Decision: {decision.title}")
            logger.info(f"   ID: {decision.proposal_id}")
            logger.info(f"   Status: {decision.status.value}")
            logger.info(f"   Created: {decision.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"   Cost Impact: ${decision.estimated_cost_impact:,.2f}")
            logger.info(f"   Risk Level: {decision.risk_level.value}")
            
            if decision.approval_responses:
                logger.info("   📝 Approval Responses:")
                for response in decision.approval_responses:
                    timestamp = datetime.fromisoformat(response['timestamp']) if isinstance(response['timestamp'], str) else response['timestamp']
                    logger.info(f"      • {response['approver']}: {response['decision']} at {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
                    if response.get('comments'):
                        logger.info(f"        💬 \"{response['comments']}\"")
            else:
                logger.info("   📝 No approval responses yet")
            
            # Show approval summary
            summary = decision.get_approval_summary()
            logger.info(f"   📊 Approval Summary: {summary['approved']}/{summary['total_required']} approved")
    
    def demo_real_time_notifications(self):
        """Demo real-time notifications summary"""
        logger.info("\n" + "="*60)
        logger.info("🔔 DEMO: Real-time Notifications Summary")
        logger.info("="*60)
        
        logger.info(f"📢 Total real-time updates received: {len(self.updates_received)}")
        
        # Group updates by type
        update_types = {}
        for update in self.updates_received:
            update_type = update.update_type
            if update_type not in update_types:
                update_types[update_type] = 0
            update_types[update_type] += 1
        
        logger.info("📊 Update types breakdown:")
        for update_type, count in update_types.items():
            logger.info(f"   • {update_type}: {count}")
        
        # Show recent updates
        logger.info("\n📋 Recent updates (last 5):")
        for update in self.updates_received[-5:]:
            timestamp = update.timestamp.strftime('%H:%M:%S')
            logger.info(f"   • {timestamp} - {update.update_type} for {update.decision_id}")
    
    async def run_complete_demo(self):
        """Run the complete demo"""
        logger.info("🎬 Starting Real-time Decision Tracking Demo")
        logger.info("=" * 80)
        
        # Setup real-time updates
        self.setup_real_time_updates()
        
        # Start the service
        await self.service.start_service()
        logger.info("🚀 Real-time decision service started")
        
        try:
            # Demo 1: Decision creation
            decisions = await self.demo_decision_creation()
            
            # Demo 2: Approval workflow
            await self.demo_approval_workflow(decisions)
            
            # Demo 3: Metrics and analytics
            self.demo_decision_metrics()
            
            # Demo 4: Audit trail
            self.demo_audit_trail()
            
            # Demo 5: Real-time notifications
            self.demo_real_time_notifications()
            
            logger.info("\n" + "="*80)
            logger.info("🎉 Demo completed successfully!")
            logger.info("✅ All real-time decision tracking features demonstrated")
            logger.info("="*80)
            
        finally:
            # Stop the service
            await self.service.stop_service()
            logger.info("🛑 Real-time decision service stopped")


async def main():
    """Main demo function"""
    demo = DecisionTrackingDemo()
    await demo.run_complete_demo()


if __name__ == "__main__":
    asyncio.run(main())