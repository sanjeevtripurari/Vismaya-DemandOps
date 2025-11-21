"""
Unit tests for real-time decision service
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock

from src.services.real_time_decision_service import RealTimeDecisionService, DecisionUpdate
from src.agentic.core.models import DecisionProposal, DecisionStatus, RiskLevel


class TestRealTimeDecisionService:
    """Test real-time decision service functionality"""
    
    @pytest.fixture
    def service(self):
        """Create real-time decision service for testing"""
        return RealTimeDecisionService()
    
    @pytest.mark.asyncio
    async def test_create_decision_proposal(self, service):
        """Test creating a decision proposal"""
        decision_data = {
            'title': 'Test Decision',
            'description': 'Test decision description',
            'cost_impact': 1500.0,
            'risk_level': 'medium',
            'required_approvers': ['cto', 'finops_lead'],
            'deadline': datetime.now() + timedelta(days=2)
        }
        
        decision = await service.create_decision(decision_data)
        
        assert decision.title == 'Test Decision'
        assert decision.estimated_cost_impact == 1500.0
        assert decision.risk_level == RiskLevel.MEDIUM
        assert decision.status == DecisionStatus.PENDING
        assert len(decision.required_approvers) == 2
        
        # Verify decision is stored
        stored_decision = service.get_decision_by_id(decision.proposal_id)
        assert stored_decision is not None
        assert stored_decision.proposal_id == decision.proposal_id
    
    @pytest.mark.asyncio
    async def test_process_approval_workflow(self, service):
        """Test complete approval workflow"""
        # Create decision
        decision_data = {
            'title': 'Approval Test',
            'description': 'Test approval workflow',
            'cost_impact': 2000.0,
            'risk_level': 'high',
            'required_approvers': ['cto', 'finops_lead']
        }
        
        decision = await service.create_decision(decision_data)
        decision_id = decision.proposal_id
        
        # First approval
        success = await service.process_approval(
            decision_id, 'cto', 'approved', 'Looks good to me'
        )
        assert success is True
        
        # Check decision status (should still be pending)
        updated_decision = service.get_decision_by_id(decision_id)
        assert updated_decision.status == DecisionStatus.PENDING
        assert len(updated_decision.approval_responses) == 1
        
        # Second approval
        success = await service.process_approval(
            decision_id, 'finops_lead', 'approved', 'Approved for cost savings'
        )
        assert success is True
        
        # Check final status (should be approved and moved to history)
        final_decision = service.get_decision_by_id(decision_id)
        assert final_decision.status == DecisionStatus.APPROVED
        assert len(final_decision.approval_responses) == 2
        assert final_decision.is_approved() is True
        
        # Verify decision moved to history
        history = service.get_decision_history()
        assert len(history) == 1
        assert history[0].proposal_id == decision_id
    
    @pytest.mark.asyncio
    async def test_rejection_workflow(self, service):
        """Test decision rejection workflow"""
        # Create decision
        decision_data = {
            'title': 'Rejection Test',
            'description': 'Test rejection workflow',
            'cost_impact': 5000.0,
            'risk_level': 'critical',
            'required_approvers': ['ceo']
        }
        
        decision = await service.create_decision(decision_data)
        decision_id = decision.proposal_id
        
        # Reject decision
        success = await service.process_approval(
            decision_id, 'ceo', 'rejected', 'Too risky at this time'
        )
        assert success is True
        
        # Check final status
        rejected_decision = service.get_decision_by_id(decision_id)
        assert rejected_decision.status == DecisionStatus.REJECTED
        assert rejected_decision.is_rejected() is True
        
        # Verify decision moved to history
        history = service.get_decision_history()
        assert any(d.proposal_id == decision_id for d in history)
    
    @pytest.mark.asyncio
    async def test_real_time_updates(self, service):
        """Test real-time update broadcasting"""
        updates_received = []
        
        def update_handler(update: DecisionUpdate):
            updates_received.append(update)
        
        # Subscribe to updates
        service.subscribe_to_updates("test_subscriber", update_handler)
        
        # Create decision (should trigger update)
        decision_data = {
            'title': 'Update Test',
            'description': 'Test real-time updates',
            'cost_impact': 1000.0
        }
        
        decision = await service.create_decision(decision_data)
        
        # Verify update was queued
        assert len(service.update_queue) >= 1
        create_update = service.update_queue[0]
        assert create_update.update_type == "decision_created"
        assert create_update.decision_id == decision.proposal_id
        assert create_update.data['title'] == 'Update Test'
    
    def test_decision_metrics_calculation(self, service):
        """Test decision metrics calculation"""
        # Create some demo decisions
        demo_decisions = service.create_demo_decisions()
        assert len(demo_decisions) > 0
        
        # Get metrics
        metrics = service.get_decision_metrics()
        
        assert 'total_decisions' in metrics
        assert 'pending_decisions' in metrics
        assert 'approved_decisions' in metrics
        assert 'rejected_decisions' in metrics
        assert 'approval_rate' in metrics
        assert 'avg_approval_time_hours' in metrics
        
        assert metrics['total_decisions'] >= len(demo_decisions)
        assert metrics['pending_decisions'] >= 0
        assert metrics['approval_rate'] >= 0
    
    def test_get_active_decisions(self, service):
        """Test getting active decisions"""
        # Create demo decisions
        demo_decisions = service.create_demo_decisions()
        
        # Get all active decisions
        active_decisions = service.get_active_decisions()
        assert len(active_decisions) == len(demo_decisions)
        
        # Get decisions for specific approver
        finops_decisions = service.get_active_decisions('finops_lead')
        assert len(finops_decisions) > 0
        
        # Verify all returned decisions require the specified approver
        for decision in finops_decisions:
            assert 'finops_lead' in decision.required_approvers
    
    def test_subscription_management(self, service):
        """Test subscription management"""
        callback = Mock()
        
        # Subscribe
        service.subscribe_to_updates("test_sub", callback)
        assert "test_sub" in service.subscribers
        
        # Unsubscribe
        service.unsubscribe_from_updates("test_sub")
        assert "test_sub" not in service.subscribers
    
    def test_error_handling(self, service):
        """Test error handling in decision operations"""
        # Test processing approval for non-existent decision
        result = asyncio.run(
            service.process_approval(
                "non-existent-id", "finops_lead", "approved", "Test"
            )
        )
        assert result is False
        
        # Test getting non-existent decision
        decision = service.get_decision_by_id("non-existent-id")
        assert decision is None
    
    @pytest.mark.asyncio
    async def test_update_decision_status(self, service):
        """Test updating decision status"""
        # Create decision
        decision_data = {
            'title': 'Status Test',
            'description': 'Test status updates',
            'cost_impact': 500.0
        }
        
        decision = await service.create_decision(decision_data)
        decision_id = decision.proposal_id
        
        # Update status
        success = await service.update_decision_status(
            decision_id, DecisionStatus.APPROVED, 'test_user', 'Manual approval'
        )
        assert success is True
        
        # Verify status change
        updated_decision = service.get_decision_by_id(decision_id)
        assert updated_decision.status == DecisionStatus.APPROVED
        
        # Verify decision moved to history
        history = service.get_decision_history()
        assert any(d.proposal_id == decision_id for d in history)
    
    def test_decision_history_management(self, service):
        """Test decision history management"""
        # Create and complete multiple decisions
        for i in range(5):
            decision_data = {
                'title': f'History Test {i+1}',
                'description': f'Test decision {i+1}',
                'cost_impact': 100.0 * (i+1)
            }
            decision = asyncio.run(service.create_decision(decision_data))
            
            # Move to history by updating status
            asyncio.run(service.update_decision_status(
                decision.proposal_id, DecisionStatus.APPROVED, 'test_user', 'Test approval'
            ))
        
        # Get history
        history = service.get_decision_history()
        assert len(history) == 5
        
        # Test limited history
        limited_history = service.get_decision_history(limit=3)
        assert len(limited_history) == 3
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, service):
        """Test concurrent decision operations"""
        # Create multiple decisions concurrently
        decision_tasks = []
        for i in range(3):
            decision_data = {
                'title': f'Concurrent Test {i+1}',
                'description': f'Concurrent decision {i+1}',
                'cost_impact': 200.0 * (i+1)
            }
            task = service.create_decision(decision_data)
            decision_tasks.append(task)
        
        # Wait for all decisions to be created
        decisions = await asyncio.gather(*decision_tasks)
        assert len(decisions) == 3
        
        # Verify all decisions are stored
        active_decisions = service.get_active_decisions()
        assert len(active_decisions) >= 3


if __name__ == "__main__":
    pytest.main([__file__])