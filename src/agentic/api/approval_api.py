"""
Approval API Endpoints
REST API endpoints for handling email-based approval responses
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from flask import Flask, request, jsonify, redirect, render_template_string
import json

from ..services.email_notification_service import EmailNotificationService
from ..agents.approval_agent import ApprovalAgent


class ApprovalAPI:
    """
    REST API endpoints for approval system
    
    Handles:
    - Email-based approval responses (one-click approve/reject)
    - Approval status queries
    - Proposal management endpoints
    """
    
    def __init__(self, approval_agent: ApprovalAgent, email_service: EmailNotificationService):
        self.approval_agent = approval_agent
        self.email_service = email_service
        self.logger = logging.getLogger(__name__)
        
        # Flask app for API endpoints
        self.app = Flask(__name__)
        self._setup_routes()
    
    def _setup_routes(self) -> None:
        """Setup Flask routes for approval API"""
        
        @self.app.route('/api/approval/respond', methods=['GET'])
        def handle_email_approval_response():
            """Handle email-based approval response (one-click approve/reject)"""
            return asyncio.run(self._handle_email_approval_response())
        
        @self.app.route('/api/approval/status/<proposal_id>', methods=['GET'])
        def get_proposal_status(proposal_id: str):
            """Get proposal status"""
            return asyncio.run(self._get_proposal_status(proposal_id))
        
        @self.app.route('/api/approval/pending', methods=['GET'])
        def get_pending_proposals():
            """Get pending proposals for approver"""
            return asyncio.run(self._get_pending_proposals())
        
        @self.app.route('/api/approval/history/<proposal_id>', methods=['GET'])
        def get_approval_history(proposal_id: str):
            """Get approval history for proposal"""
            return asyncio.run(self._get_approval_history(proposal_id))
    
    async def _handle_email_approval_response(self) -> Dict[str, Any]:
        """Handle email-based approval response"""
        try:
            # Get token from query parameters
            token = request.args.get('token')
            if not token:
                return self._render_error_page("Missing authentication token")
            
            # Validate token
            token_data = self.email_service.validate_auth_token(token)
            if not token_data.get('valid'):
                return self._render_error_page(f"Invalid token: {token_data.get('error')}")
            
            # Extract token information
            proposal_id = token_data['proposal_id']
            approver_email = token_data['approver_email']
            decision = token_data['decision']
            
            # Process approval response
            success = await self.approval_agent.process_approval_response(
                proposal_id=proposal_id,
                approver=approver_email,
                decision=decision
            )
            
            if success:
                # Get updated proposal status
                proposal_status = await self.approval_agent.get_proposal_status(proposal_id)
                
                return self._render_success_page(
                    decision=decision,
                    proposal_title=proposal_status.get('title', 'Unknown'),
                    proposal_id=proposal_id,
                    approver_email=approver_email
                )
            else:
                return self._render_error_page("Failed to process approval response")
            
        except Exception as e:
            self.logger.error(f"Error handling email approval response: {e}")
            return self._render_error_page(f"Internal error: {str(e)}")
    
    async def _get_proposal_status(self, proposal_id: str) -> Dict[str, Any]:
        """Get proposal status"""
        try:
            status = await self.approval_agent.get_proposal_status(proposal_id)
            
            return {
                "success": True,
                "proposal_id": proposal_id,
                "status": status
            }
            
        except Exception as e:
            self.logger.error(f"Error getting proposal status: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _get_pending_proposals(self) -> Dict[str, Any]:
        """Get pending proposals for approver"""
        try:
            approver_id = request.args.get('approver_id')
            
            proposals = await self.approval_agent.get_pending_proposals(approver_id)
            
            # Convert proposals to JSON-serializable format
            proposals_data = []
            for proposal in proposals:
                proposals_data.append({
                    "proposal_id": proposal.proposal_id,
                    "title": proposal.title,
                    "description": proposal.description,
                    "created_by": proposal.created_by,
                    "created_at": proposal.created_at.isoformat(),
                    "approval_deadline": proposal.approval_deadline.isoformat() if proposal.approval_deadline else None,
                    "estimated_cost_impact": proposal.estimated_cost_impact,
                    "risk_level": proposal.risk_level.value,
                    "status": proposal.status.value,
                    "approval_summary": proposal.get_approval_summary()
                })
            
            return {
                "success": True,
                "approver_id": approver_id,
                "pending_proposals": proposals_data,
                "total_count": len(proposals_data)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting pending proposals: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _get_approval_history(self, proposal_id: str) -> Dict[str, Any]:
        """Get approval history for proposal"""
        try:
            # Get proposal from approval agent
            proposal = self.approval_agent.proposals.get(proposal_id)
            if not proposal:
                return {
                    "success": False,
                    "error": "Proposal not found"
                }
            
            return {
                "success": True,
                "proposal_id": proposal_id,
                "approval_history": proposal.approval_responses,
                "approval_summary": proposal.get_approval_summary(),
                "required_approvers": proposal.required_approvers,
                "current_status": proposal.status.value
            }
            
        except Exception as e:
            self.logger.error(f"Error getting approval history: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _render_success_page(self, decision: str, proposal_title: str, proposal_id: str, approver_email: str) -> str:
        """Render success page for email approval"""
        template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Approval {{ decision.title() }} - Vismaya DemandOps</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 50px auto; padding: 20px; }
        .success-container { background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 8px; padding: 30px; text-align: center; }
        .success-icon { font-size: 48px; margin-bottom: 20px; }
        .success-title { color: #155724; font-size: 24px; margin-bottom: 15px; }
        .success-message { color: #155724; font-size: 16px; margin-bottom: 20px; }
        .proposal-details { background-color: white; padding: 20px; border-radius: 5px; margin: 20px 0; text-align: left; }
        .btn { display: inline-block; padding: 12px 30px; margin: 10px; text-decoration: none; border-radius: 5px; font-weight: bold; background-color: #007bff; color: white; }
        .footer { margin-top: 30px; font-size: 12px; color: #666; }
    </style>
</head>
<body>
    <div class="success-container">
        <div class="success-icon">✅</div>
        <h1 class="success-title">Approval {{ decision.title() }} Successfully</h1>
        <p class="success-message">Your decision has been recorded and all stakeholders have been notified.</p>
        
        <div class="proposal-details">
            <h3>Proposal Details</h3>
            <p><strong>Title:</strong> {{ proposal_title }}</p>
            <p><strong>Proposal ID:</strong> {{ proposal_id }}</p>
            <p><strong>Your Decision:</strong> {{ decision.title() }}</p>
            <p><strong>Processed At:</strong> {{ datetime.now().strftime('%B %d, %Y at %I:%M %p') }}</p>
            <p><strong>Approver:</strong> {{ approver_email }}</p>
        </div>
        
        <a href="{{ dashboard_url }}" class="btn">View Dashboard</a>
        
        <div class="footer">
            <p>Thank you for using Vismaya DemandOps Decision Management System.</p>
        </div>
    </div>
</body>
</html>
        """
        
        return render_template_string(
            template,
            decision=decision,
            proposal_title=proposal_title,
            proposal_id=proposal_id,
            approver_email=approver_email,
            dashboard_url=f"{self.email_service.base_url}/dashboard",
            datetime=datetime
        )
    
    def _render_error_page(self, error_message: str) -> str:
        """Render error page for email approval"""
        template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Approval Error - Vismaya DemandOps</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 50px auto; padding: 20px; }
        .error-container { background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 8px; padding: 30px; text-align: center; }
        .error-icon { font-size: 48px; margin-bottom: 20px; }
        .error-title { color: #721c24; font-size: 24px; margin-bottom: 15px; }
        .error-message { color: #721c24; font-size: 16px; margin-bottom: 20px; }
        .btn { display: inline-block; padding: 12px 30px; margin: 10px; text-decoration: none; border-radius: 5px; font-weight: bold; background-color: #007bff; color: white; }
        .footer { margin-top: 30px; font-size: 12px; color: #666; }
    </style>
</head>
<body>
    <div class="error-container">
        <div class="error-icon">❌</div>
        <h1 class="error-title">Approval Processing Error</h1>
        <p class="error-message">{{ error_message }}</p>
        
        <p>Please try again or contact support if the problem persists.</p>
        
        <a href="{{ dashboard_url }}" class="btn">Go to Dashboard</a>
        
        <div class="footer">
            <p>Vismaya DemandOps Decision Management System</p>
        </div>
    </div>
</body>
</html>
        """
        
        return render_template_string(
            template,
            error_message=error_message,
            dashboard_url=f"{self.email_service.base_url}/dashboard"
        )
    
    def get_flask_app(self) -> Flask:
        """Get Flask app for integration with main application"""
        return self.app