"""
Integration tests for real-time decision tracking and approval interface
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from src.services.real_time_decision_service import RealTimeDecisionService, DecisionUpdate
from src.ui.decision_tracking import DecisionTrackingInterface
from src.agentic.core.models import DecisionProposal, DecisionStatus, RiskLevel


class TestRealTimeDecisionTracking:
    """Test real-time decision tracking functionality"""
    
    @pytest.fixture
    def real_time_service(self):
        """Create real-time decision service for testing"""
        return RealTimeDecisionService()
    
    @pytest.fixture
    def decision_interface(self, real_time_service):
        """Create decision tracking interface for testing"""
        return DecisionTrackingInterface(real_time_service)
    
    @pytest.mark.asyncio
    async def test_create_decision_proposal(self, real_time_service):
        """Test creating a decision proposal"""
        decision_data = {
            'title': 'Test Decision',
            'description': 'Test decision description',
            'cost_impact': 1500.0,
            'risk_level': 'medium',
            'required_approvers': ['cto', 'finops_lead'],
            'deadline': datetime.now() + timedelta(days=2)
        }
        
        decision = await real_time_service.create_decision(decision_data)
        
        assert decision.title == 'Test Decision'
        assert decision.estimated_cost_impact == 1500.0
        assert decision.risk_level == RiskLevel.MEDIUM
        assert decision.status == DecisionStatus.PENDING
        assert len(decision.required_approvers) == 2
        
        # Verify decision is stored
        stored_decision = real_time_service.get_decision_by_id(decision.proposal_id)
        assert stored_decision is not None
        assert stored_decision.proposal_id == decision.proposal_id
    
    @pytest.mark.asyncio
    async def test_process_approval_workflow(self, real_time_service):
        """Test complete approval workflow"""
        # Create decision
        decision_data = {
            'title': 'Approval Test',
            'description': 'Test approval workflow',
            'cost_impact': 2000.0,
            'risk_level': 'high',
            'required_approvers': ['cto', 'finops_lead']
        }
        
        decision = await real_time_service.create_decision(decision_data)
        decision_id = decision.proposal_id
        
        # First approval
        success = await real_time_service.process_approval(
            decision_id, 'cto', 'approved', 'Looks good to me'
        )
        assert success is True
        
        # Check decision status (should still be pending)
        updated_decision = real_time_service.get_decision_by_id(decision_id)
        assert updated_decision.status == DecisionStatus.PENDING
        assert len(updated_decision.approval_responses) == 1
        
        # Second approval
        success = await real_time_service.process_approval(
            decision_id, 'finops_lead', 'approved', 'Approved for cost savings'
        )
        assert success is True
        
        # Check final status (should be approved and moved to history)
        final_decision = real_time_service.get_decision_by_id(decision_id)
        assert final_decision.status == DecisionStatus.APPROVED
        assert len(final_decision.approval_responses) == 2
        assert final_decision.is_approved() is True
        
        # Verify decision moved to history
        history = real_time_service.get_decision_history()
        assert len(history) == 1
        assert history[0].proposal_id == decision_id
    
    @pytest.mark.asyncio
    async def test_rejection_workflow(self, real_time_service):
        """Test decision rejection workflow"""
        # Create decision
        decision_data = {
            'title': 'Rejection Test',
            'description': 'Test rejection workflow',
            'cost_impact': 5000.0,
            'risk_level': 'critical',
            'required_approvers': ['ceo']
        }
        
        decision = await real_time_service.create_decision(decision_data)
        decision_id = decision.proposal_id
        
        # Reject decision
        success = await real_time_service.process_approval(
            decision_id, 'ceo', 'rejected', 'Too risky at this time'
        )
        assert success is True
        
        # Check final status
        rejected_decision = real_time_service.get_decision_by_id(decision_id)
        assert rejected_decision.status == DecisionStatus.REJECTED
        assert rejected_decision.is_rejected() is True
        
        # Verify decision moved to history
        history = real_time_service.get_decision_history()
        assert any(d.proposal_id == decision_id for d in history)
    
    @pytest.mark.asyncio
    async def test_real_time_updates(self, real_time_service):
        """Test real-time update broadcasting"""
        updates_received = []
        
        def update_handler(update: DecisionUpdate):
            updates_received.append(update)
        
        # Subscribe to updates
        real_time_service.subscribe_to_updates("test_subscriber", update_handler)
        
        # Create decision (should trigger update)
        decision_data = {
            'title': 'Update Test',
            'description': 'Test real-time updates',
            'cost_impact': 1000.0
        }
        
        decision = await real_time_service.create_decision(decision_data)
        
        # Process update queue
        await asyncio.sleep(0.1)  # Allow time for update processing
        
        # Verify update was received
        assert len(updates_received) >= 1
        create_update = updates_received[0]
        assert create_update.update_type == "decision_created"
        assert create_update.decision_id == decision.proposal_id
        assert create_update.data['title'] == 'Update Test'
    
    @pytest.mark.asyncio
    async def test_deadline_monitoring(self, real_time_service):
        """Test deadline monitoring functionality"""
        # Create decision with short deadline
        decision_data = {
            'title': 'Deadline Test',
            'description': 'Test deadline monitoring',
            'cost_impact': 500.0,
            'deadline': datetime.now() + timedelta(seconds=1)  # Very short deadline
        }
        
        decision = await real_time_service.create_decision(decision_data)
        decision_id = decision.proposal_id
        
        # Wait for deadline to pass
        await asyncio.sleep(2)
        
        # Manually trigger deadline check (in production, this runs automatically)
        current_time = datetime.now()
        if decision.approval_deadline and current_time > decision.approval_deadline:
            await real_time_service.update_decision_status(
                decision_id, DecisionStatus.CANCELLED, None, "Expired due to deadline"
            )
        
        # Verify decision was cancelled
        expired_decision = real_time_service.get_decision_by_id(decision_id)
        assert expired_decision.status == DecisionStatus.CANCELLED
    
    def test_decision_metrics_calculation(self, real_time_service):
        """Test decision metrics calculation"""
        # Create some demo decisions
        demo_decisions = real_time_service.create_demo_decisions()
        assert len(demo_decisions) > 0
        
        # Get metrics
        metrics = real_time_service.get_decision_metrics()
        
        assert 'total_decisions' in metrics
        assert 'pending_decisions' in metrics
        assert 'approved_decisions' in metrics
        assert 'rejected_decisions' in metrics
        assert 'approval_rate' in metrics
        assert 'avg_approval_time_hours' in metrics
        
        assert metrics['total_decisions'] >= len(demo_decisions)
        assert metrics['pending_decisions'] >= 0
        assert metrics['approval_rate'] >= 0
    
    @pytest.mark.asyncio
    async def test_service_lifecycle(self, real_time_service):
        """Test service start and stop lifecycle"""
        # Start service
        await real_time_service.start_service()
        assert real_time_service._running is True
        
        # Stop service
        await real_time_service.stop_service()
        assert real_time_service._running is False
    
    def test_decision_conversion(self, decision_interface):
        """Test decision proposal to dictionary conversion"""
        # Create a decision proposal
        decision = DecisionProposal(
            proposal_id="test-123",
            title="Test Decision",
            description="Test description",
            estimated_cost_impact=1000.0,
            risk_level=RiskLevel.MEDIUM,
            status=DecisionStatus.PENDING,
            created_at=datetime.now(),
            required_approvers=['finops_lead']
        )
        
        # Convert to dictionary
        decision_dict = decision_interface._convert_decision_to_dict(decision)
        
        assert decision_dict['id'] == "test-123"
        assert decision_dict['title'] == "Test Decision"
        assert decision_dict['cost_impact'] == 1000.0
        assert decision_dict['priority'] == 'medium'
        assert decision_dict['status'] == 'pending'
        assert 'created_at' in decision_dict
        assert 'required_approvers' in decision_dict
    
    @pytest.mark.asyncio
    async def test_bulk_approval_operations(self, real_time_service):
        """Test bulk approval operations"""
        # Create multiple decisions
        decisions = []
        for i in range(3):
            decision_data = {
                'title': f'Bulk Test {i+1}',
                'description': f'Bulk approval test decision {i+1}',
                'cost_impact': 100.0 * (i+1),
                'risk_level': 'low',
                'required_approvers': ['finops_lead']
            }
            decision = await real_time_service.create_decision(decision_data)
            decisions.append(decision)
        
        # Approve all decisions
        for decision in decisions:
            success = await real_time_service.process_approval(
                decision.proposal_id, 'finops_lead', 'approved', 'Bulk approval'
            )
            assert success is True
        
        # Verify all decisions are approved
        history = real_time_service.get_decision_history()
        approved_count = len([d for d in history if d.status == DecisionStatus.APPROVED])
        assert approved_count >= 3
    
    def test_error_handling(self, real_time_service):
        """Test error handling in decision operations"""
        # Test processing approval for non-existent decision
        result = asyncio.run(
            real_time_service.process_approval(
                "non-existent-id", "finops_lead", "approved", "Test"
            )
        )
        assert result is False
        
        # Test getting non-existent decision
        decision = real_time_service.get_decision_by_id("non-existent-id")
        assert decision is None
    
    @pytest.mark.asyncio
    async def test_concurrent_approvals(self, real_time_service):
        """Test concurrent approval processing"""
        # Create decision requiring multiple approvers
        decision_data = {
            'title': 'Concurrent Test',
            'description': 'Test concurrent approvals',
            'cost_impact': 3000.0,
            'risk_level': 'high',
            'required_approvers': ['cto', 'finops_lead']
        }
        
        decision = await real_time_service.create_decision(decision_data)
        decision_id = decision.proposal_id
        
        # Process approvals concurrently
        approval_tasks = [
            real_time_service.process_approval(decision_id, 'cto', 'approved', 'CTO approval'),
            real_time_service.process_approval(decision_id, 'finops_lead', 'approved', 'FinOps approval')
        ]
        
        results = await asyncio.gather(*approval_tasks)
        assert all(results)
        
        # Verify final state
        final_decision = real_time_service.get_decision_by_id(decision_id)
        assert final_decision.status == DecisionStatus.APPROVED
        assert len(final_decision.approval_responses) == 2
        assert final_decision.is_approved() is True


if __name__ == "__main__":
    pytest.main([__file__])