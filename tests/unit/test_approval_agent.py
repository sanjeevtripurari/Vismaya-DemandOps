"""
Unit tests for Approval Agent
Tests the core functionality of the approval agent and decision management system
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock

from src.agentic.agents.approval_agent import ApprovalAgent
from src.agentic.core.models import DecisionProposal, DecisionStatus, RiskLevel


class TestApprovalAgent:
    """Test cases for ApprovalAgent"""
    
    @pytest.fixture
    def mock_strands_framework(self):
        """Mock Strands framework"""
        mock = AsyncMock()
        mock.store_decision_history = AsyncMock(return_value=True)
        mock.update_context = AsyncMock(return_value=True)
        return mock
    
    @pytest.fixture
    def mock_mcp_server(self):
        """Mock MCP server"""
        mock = AsyncMock()
        mock.register_agent = AsyncMock(return_value=True)
        mock.broadcast_system_event = AsyncMock(return_value=[])
        return mock
    
    @pytest.fixture
    def approval_agent_config(self):
        """Configuration for approval agent"""
        return {
            "default_approval_timeout_hours": 24,
            "auto_escalation_enabled": True,
            "escalation_timeout_hours": 48,
            "stakeholders": {
                "ceo": {
                    "email": "ceo@test.com",
                    "name": "Chief Executive Officer",
                    "approval_authority": {"max_cost": float('inf'), "all_decisions": True}
                },
                "finops_lead": {
                    "email": "finops@test.com",
                    "name": "FinOps Lead", 
                    "approval_authority": {"max_cost": 5000, "cost_decisions": True}
                }
            },
            "email_config": {
                "sender_email": "test@test.com",
                "base_url": "https://test.com"
            }
        }
    
    @pytest.fixture
    async def approval_agent(self, approval_agent_config, mock_strands_framework, mock_mcp_server):
        """Create approval agent instance"""
        agent = ApprovalAgent(
            config=approval_agent_config,
            strands_framework=mock_strands_framework,
            mcp_server=mock_mcp_server
        )
        
        # Mock the email service to avoid AWS SES calls
        agent.email_service.ses_client = None
        agent.email_service.send_approval_request = AsyncMock(return_value={"success": True, "total_recipients": 1, "successful_sends": 1})
        agent.email_service.send_status_update = AsyncMock(return_value={"success": True})
        agent.email_service.send_execution_notification = AsyncMock(return_value={"success": True})
        
        # Mock notification service
        agent.notification_service.start_service = AsyncMock()
        agent.notification_service.notify_proposal_status_change = AsyncMock()
        agent.notification_service.notify_approval_response = AsyncMock()
        
        await agent.initialize()
        return agent
    
    @pytest.mark.asyncio
    async def test_create_proposal(self, approval_agent):
        """Test creating a decision proposal"""
        proposal_data = {
            "title": "Test Proposal",
            "description": "This is a test proposal",
            "created_by": "test_user",
            "estimated_cost_impact": 1500.0,
            "risk_level": "medium",
            "recommendations": ["Implement cost optimization"],
            "execution_plan": {"type": "cost_optimization", "expected_savings": 1500}
        }
        
        proposal = await approval_agent.create_proposal(proposal_data)
        
        assert proposal is not None
        assert proposal.title == "Test Proposal"
        assert proposal.description == "This is a test proposal"
        assert proposal.created_by == "test_user"
        assert proposal.estimated_cost_impact == 1500.0
        assert proposal.risk_level == RiskLevel.MEDIUM
        assert proposal.status == DecisionStatus.PENDING
        assert len(proposal.required_approvers) > 0
        assert proposal.approval_deadline is not None
    
    @pytest.mark.asyncio
    async def test_send_approval_request(self, approval_agent):
        """Test sending approval request"""
        # Create a proposal first
        proposal_data = {
            "title": "Test Proposal",
            "description": "Test description",
            "created_by": "test_user",
            "estimated_cost_impact": 1000.0,
            "risk_level": "low"
        }
        
        proposal = await approval_agent.create_proposal(proposal_data)
        
        # Send approval request
        success = await approval_agent.send_approval_request(proposal)
        
        assert success is True
        assert proposal.status == DecisionStatus.PENDING
        
        # Verify email service was called
        approval_agent.email_service.send_approval_request.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_approval_response(self, approval_agent):
        """Test processing approval response"""
        # Create a proposal
        proposal_data = {
            "title": "Test Proposal",
            "description": "Test description", 
            "created_by": "test_user",
            "estimated_cost_impact": 500.0,
            "risk_level": "low"
        }
        
        proposal = await approval_agent.create_proposal(proposal_data)
        proposal_id = proposal.proposal_id
        
        # Process approval response
        success = await approval_agent.process_approval_response(
            proposal_id=proposal_id,
            approver="finops_lead",
            decision="approved"
        )
        
        assert success is True
        
        # Check proposal status
        updated_proposal = approval_agent.proposals[proposal_id]
        assert len(updated_proposal.approval_responses) == 1
        assert updated_proposal.approval_responses[0]["decision"] == "approved"
        assert updated_proposal.approval_responses[0]["approver"] == "finops_lead"
    
    @pytest.mark.asyncio
    async def test_get_pending_proposals(self, approval_agent):
        """Test getting pending proposals"""
        # Create multiple proposals
        for i in range(3):
            proposal_data = {
                "title": f"Test Proposal {i}",
                "description": f"Test description {i}",
                "created_by": "test_user",
                "estimated_cost_impact": 500.0 + i * 100,
                "risk_level": "low"
            }
            await approval_agent.create_proposal(proposal_data)
        
        # Get pending proposals
        pending_proposals = await approval_agent.get_pending_proposals()
        
        assert len(pending_proposals) == 3
        for proposal in pending_proposals:
            assert proposal.status == DecisionStatus.PENDING
        
        # Get pending proposals for specific approver
        finops_proposals = await approval_agent.get_pending_proposals("finops_lead")
        assert len(finops_proposals) == 3  # All should require finops_lead approval
    
    @pytest.mark.asyncio
    async def test_proposal_approval_workflow(self, approval_agent):
        """Test complete approval workflow"""
        # Create proposal
        proposal_data = {
            "title": "Complete Workflow Test",
            "description": "Testing complete approval workflow",
            "created_by": "test_user",
            "estimated_cost_impact": 800.0,
            "risk_level": "low"
        }
        
        proposal = await approval_agent.create_proposal(proposal_data)
        proposal_id = proposal.proposal_id
        
        # Send approval request
        await approval_agent.send_approval_request(proposal)
        
        # Process approval
        await approval_agent.process_approval_response(
            proposal_id=proposal_id,
            approver="finops_lead",
            decision="approved"
        )
        
        # Check if proposal is approved
        updated_proposal = approval_agent.proposals[proposal_id]
        assert updated_proposal.is_approved()
        assert updated_proposal.status == DecisionStatus.APPROVED
        
        # Execute proposal
        success = await approval_agent.execute_approved_proposal(proposal_id)
        assert success is True
        
        # Check final status
        final_proposal = approval_agent.proposals[proposal_id]
        assert final_proposal.status == DecisionStatus.EXECUTED
    
    @pytest.mark.asyncio
    async def test_proposal_rejection(self, approval_agent):
        """Test proposal rejection"""
        # Create proposal
        proposal_data = {
            "title": "Rejection Test",
            "description": "Testing proposal rejection",
            "created_by": "test_user",
            "estimated_cost_impact": 1200.0,
            "risk_level": "medium"
        }
        
        proposal = await approval_agent.create_proposal(proposal_data)
        proposal_id = proposal.proposal_id
        
        # Process rejection
        await approval_agent.process_approval_response(
            proposal_id=proposal_id,
            approver="finops_lead",
            decision="rejected"
        )
        
        # Check proposal status
        updated_proposal = approval_agent.proposals[proposal_id]
        assert updated_proposal.is_rejected()
        assert updated_proposal.status == DecisionStatus.REJECTED
    
    @pytest.mark.asyncio
    async def test_get_proposal_status(self, approval_agent):
        """Test getting proposal status"""
        # Create proposal
        proposal_data = {
            "title": "Status Test",
            "description": "Testing status retrieval",
            "created_by": "test_user",
            "estimated_cost_impact": 600.0,
            "risk_level": "low"
        }
        
        proposal = await approval_agent.create_proposal(proposal_data)
        proposal_id = proposal.proposal_id
        
        # Get status
        status = await approval_agent.get_proposal_status(proposal_id)
        
        assert status["proposal_id"] == proposal_id
        assert status["title"] == "Status Test"
        assert status["status"] == DecisionStatus.PENDING.value
        assert "approval_summary" in status
        assert "estimated_cost_impact" in status
    
    @pytest.mark.asyncio
    async def test_invalid_proposal_id(self, approval_agent):
        """Test handling invalid proposal ID"""
        # Try to process approval for non-existent proposal
        success = await approval_agent.process_approval_response(
            proposal_id="invalid_id",
            approver="finops_lead",
            decision="approved"
        )
        
        assert success is False
        
        # Try to get status for non-existent proposal
        status = await approval_agent.get_proposal_status("invalid_id")
        assert "error" in status
    
    @pytest.mark.asyncio
    async def test_unauthorized_approver(self, approval_agent):
        """Test handling unauthorized approver"""
        # Create proposal
        proposal_data = {
            "title": "Unauthorized Test",
            "description": "Testing unauthorized approver",
            "created_by": "test_user",
            "estimated_cost_impact": 500.0,
            "risk_level": "low"
        }
        
        proposal = await approval_agent.create_proposal(proposal_data)
        proposal_id = proposal.proposal_id
        
        # Try to approve with unauthorized user
        success = await approval_agent.process_approval_response(
            proposal_id=proposal_id,
            approver="unauthorized_user",
            decision="approved"
        )
        
        assert success is False
    
    @pytest.mark.asyncio
    async def test_action_handlers(self, approval_agent):
        """Test action handlers"""
        # Test create_proposal action
        result = await approval_agent.execute_action("create_proposal", {
            "title": "Action Test",
            "description": "Testing action handler",
            "created_by": "test_user",
            "estimated_cost_impact": 400.0,
            "risk_level": "low"
        })
        
        assert result["success"] is True
        assert "proposal" in result
        
        proposal_id = result["proposal"]["proposal_id"]
        
        # Test get_proposal_status action
        result = await approval_agent.execute_action("get_proposal_status", {
            "proposal_id": proposal_id
        })
        
        assert result["success"] is True
        assert "status" in result
        
        # Test get_pending_proposals action
        result = await approval_agent.execute_action("get_pending_proposals", {})
        
        assert result["success"] is True
        assert "proposals" in result
        assert len(result["proposals"]) > 0


if __name__ == "__main__":
    pytest.main([__file__])