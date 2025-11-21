"""
Email Notification Service for Approval Requests
Integrates with AWS SES for sending approval request emails with one-click functionality
"""

import asyncio
import logging
import json
import base64
import hmac
import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from ..core.models import DecisionProposal, DecisionStatus


@dataclass
class EmailTemplate:
    """Email template configuration"""
    template_id: str
    subject_template: str
    html_template: str
    text_template: str
    required_variables: List[str]


@dataclass
class EmailRecipient:
    """Email recipient information"""
    email: str
    name: str
    role: str
    approval_authority: Dict[str, Any]


class EmailNotificationService:
    """
    Email notification service for approval requests
    
    Features:
    - AWS SES integration for reliable email delivery
    - Secure one-click approve/reject functionality
    - Email template management
    - Authentication token generation and validation
    - Delivery status tracking
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # AWS SES configuration
        self.ses_region = self.config.get("ses_region", "us-east-1")
        self.sender_email = self.config.get("sender_email", "noreply@vismaya-demandops.com")
        self.sender_name = self.config.get("sender_name", "Vismaya DemandOps")
        self.base_url = self.config.get("base_url", "https://vismaya-demandops.com")
        
        # Security configuration
        self.secret_key = self.config.get("secret_key", "default-secret-key-change-in-production")
        self.token_expiry_hours = self.config.get("token_expiry_hours", 72)
        
        # Initialize SES client
        self.ses_client = None
        self._initialize_ses_client()
        
        # Email templates
        self.templates = self._load_email_templates()
        
        # Delivery tracking
        self.delivery_status: Dict[str, Dict[str, Any]] = {}
    
    def _initialize_ses_client(self) -> None:
        """Initialize AWS SES client"""
        try:
            # Try to initialize SES client
            self.ses_client = boto3.client('ses', region_name=self.ses_region)
            
            # Test SES connectivity
            self.ses_client.get_send_quota()
            self.logger.info("AWS SES client initialized successfully")
            
        except NoCredentialsError:
            self.logger.warning("AWS credentials not found. Email functionality will be limited.")
            self.ses_client = None
        except ClientError as e:
            self.logger.error(f"Error initializing SES client: {e}")
            self.ses_client = None
        except Exception as e:
            self.logger.error(f"Unexpected error initializing SES: {e}")
            self.ses_client = None
    
    def _load_email_templates(self) -> Dict[str, EmailTemplate]:
        """Load email templates"""
        templates = {}
        
        # Approval request template
        templates["approval_request"] = EmailTemplate(
            template_id="approval_request",
            subject_template="[Action Required] Approval Request: {proposal_title}",
            html_template=self._get_approval_request_html_template(),
            text_template=self._get_approval_request_text_template(),
            required_variables=[
                "recipient_name", "proposal_title", "proposal_description",
                "estimated_cost_impact", "risk_level", "created_by",
                "approval_deadline", "approve_url", "reject_url", "view_url"
            ]
        )
        
        # Approval status update template
        templates["status_update"] = EmailTemplate(
            template_id="status_update",
            subject_template="[Update] Decision Status: {proposal_title}",
            html_template=self._get_status_update_html_template(),
            text_template=self._get_status_update_text_template(),
            required_variables=[
                "recipient_name", "proposal_title", "status_update",
                "approver_name", "decision", "view_url"
            ]
        )
        
        # Execution notification template
        templates["execution_notification"] = EmailTemplate(
            template_id="execution_notification",
            subject_template="[Completed] Decision Executed: {proposal_title}",
            html_template=self._get_execution_notification_html_template(),
            text_template=self._get_execution_notification_text_template(),
            required_variables=[
                "recipient_name", "proposal_title", "execution_result",
                "execution_success", "view_url"
            ]
        )
        
        return templates
    
    async def send_approval_request(
        self,
        proposal: DecisionProposal,
        recipients: List[EmailRecipient]
    ) -> Dict[str, Any]:
        """Send approval request emails to stakeholders"""
        try:
            if not self.ses_client:
                self.logger.error("SES client not available. Cannot send emails.")
                return {"success": False, "error": "Email service not available"}
            
            results = []
            
            for recipient in recipients:
                try:
                    # Generate authentication tokens
                    approve_token = self._generate_auth_token(
                        proposal.proposal_id, recipient.email, "approve"
                    )
                    reject_token = self._generate_auth_token(
                        proposal.proposal_id, recipient.email, "reject"
                    )
                    
                    # Generate action URLs
                    approve_url = f"{self.base_url}/api/approval/respond?token={approve_token}"
                    reject_url = f"{self.base_url}/api/approval/respond?token={reject_token}"
                    view_url = f"{self.base_url}/dashboard/proposals/{proposal.proposal_id}"
                    
                    # Prepare template variables
                    template_vars = {
                        "recipient_name": recipient.name,
                        "proposal_title": proposal.title,
                        "proposal_description": proposal.description,
                        "estimated_cost_impact": f"${proposal.estimated_cost_impact:,.2f}",
                        "risk_level": proposal.risk_level.value.title(),
                        "created_by": proposal.created_by,
                        "approval_deadline": proposal.approval_deadline.strftime("%B %d, %Y at %I:%M %p") if proposal.approval_deadline else "Not specified",
                        "approve_url": approve_url,
                        "reject_url": reject_url,
                        "view_url": view_url,
                        "proposal_id": proposal.proposal_id
                    }
                    
                    # Send email
                    result = await self._send_email(
                        recipient=recipient,
                        template_id="approval_request",
                        template_vars=template_vars
                    )
                    
                    results.append({
                        "recipient": recipient.email,
                        "success": result.get("success", False),
                        "message_id": result.get("message_id"),
                        "error": result.get("error")
                    })
                    
                except Exception as e:
                    self.logger.error(f"Error sending approval request to {recipient.email}: {e}")
                    results.append({
                        "recipient": recipient.email,
                        "success": False,
                        "error": str(e)
                    })
            
            # Track delivery
            self.delivery_status[proposal.proposal_id] = {
                "sent_at": datetime.now().isoformat(),
                "recipients": results,
                "proposal_title": proposal.title
            }
            
            successful_sends = sum(1 for r in results if r["success"])
            
            return {
                "success": successful_sends > 0,
                "total_recipients": len(recipients),
                "successful_sends": successful_sends,
                "results": results
            }
            
        except Exception as e:
            self.logger.error(f"Error sending approval requests: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_status_update(
        self,
        proposal: DecisionProposal,
        approver_name: str,
        decision: str,
        recipients: List[EmailRecipient]
    ) -> Dict[str, Any]:
        """Send status update notification"""
        try:
            if not self.ses_client:
                return {"success": False, "error": "Email service not available"}
            
            results = []
            
            for recipient in recipients:
                try:
                    # Generate view URL
                    view_url = f"{self.base_url}/dashboard/proposals/{proposal.proposal_id}"
                    
                    # Prepare template variables
                    template_vars = {
                        "recipient_name": recipient.name,
                        "proposal_title": proposal.title,
                        "status_update": f"Decision {decision} by {approver_name}",
                        "approver_name": approver_name,
                        "decision": decision.title(),
                        "view_url": view_url,
                        "proposal_id": proposal.proposal_id
                    }
                    
                    # Send email
                    result = await self._send_email(
                        recipient=recipient,
                        template_id="status_update",
                        template_vars=template_vars
                    )
                    
                    results.append({
                        "recipient": recipient.email,
                        "success": result.get("success", False),
                        "message_id": result.get("message_id"),
                        "error": result.get("error")
                    })
                    
                except Exception as e:
                    self.logger.error(f"Error sending status update to {recipient.email}: {e}")
                    results.append({
                        "recipient": recipient.email,
                        "success": False,
                        "error": str(e)
                    })
            
            successful_sends = sum(1 for r in results if r["success"])
            
            return {
                "success": successful_sends > 0,
                "total_recipients": len(recipients),
                "successful_sends": successful_sends,
                "results": results
            }
            
        except Exception as e:
            self.logger.error(f"Error sending status updates: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_execution_notification(
        self,
        proposal: DecisionProposal,
        execution_result: Dict[str, Any],
        recipients: List[EmailRecipient]
    ) -> Dict[str, Any]:
        """Send execution notification"""
        try:
            if not self.ses_client:
                return {"success": False, "error": "Email service not available"}
            
            results = []
            
            for recipient in recipients:
                try:
                    # Generate view URL
                    view_url = f"{self.base_url}/dashboard/proposals/{proposal.proposal_id}"
                    
                    # Prepare template variables
                    template_vars = {
                        "recipient_name": recipient.name,
                        "proposal_title": proposal.title,
                        "execution_result": execution_result.get("result", "Execution completed"),
                        "execution_success": "successfully" if execution_result.get("success") else "with errors",
                        "view_url": view_url,
                        "proposal_id": proposal.proposal_id
                    }
                    
                    # Send email
                    result = await self._send_email(
                        recipient=recipient,
                        template_id="execution_notification",
                        template_vars=template_vars
                    )
                    
                    results.append({
                        "recipient": recipient.email,
                        "success": result.get("success", False),
                        "message_id": result.get("message_id"),
                        "error": result.get("error")
                    })
                    
                except Exception as e:
                    self.logger.error(f"Error sending execution notification to {recipient.email}: {e}")
                    results.append({
                        "recipient": recipient.email,
                        "success": False,
                        "error": str(e)
                    })
            
            successful_sends = sum(1 for r in results if r["success"])
            
            return {
                "success": successful_sends > 0,
                "total_recipients": len(recipients),
                "successful_sends": successful_sends,
                "results": results
            }
            
        except Exception as e:
            self.logger.error(f"Error sending execution notifications: {e}")
            return {"success": False, "error": str(e)}
    
    def validate_auth_token(self, token: str) -> Dict[str, Any]:
        """Validate authentication token for email-based approval"""
        try:
            # Decode token
            decoded_data = base64.urlsafe_b64decode(token.encode()).decode()
            token_data = json.loads(decoded_data)
            
            # Extract components
            proposal_id = token_data.get("proposal_id")
            approver_email = token_data.get("approver_email")
            decision = token_data.get("decision")
            expires_at = datetime.fromisoformat(token_data.get("expires_at"))
            signature = token_data.get("signature")
            
            # Check expiration
            if datetime.now() > expires_at:
                return {"valid": False, "error": "Token expired"}
            
            # Verify signature
            expected_signature = self._generate_signature(proposal_id, approver_email, decision, expires_at)
            if not hmac.compare_digest(signature, expected_signature):
                return {"valid": False, "error": "Invalid token signature"}
            
            return {
                "valid": True,
                "proposal_id": proposal_id,
                "approver_email": approver_email,
                "decision": decision,
                "expires_at": expires_at
            }
            
        except Exception as e:
            self.logger.error(f"Error validating auth token: {e}")
            return {"valid": False, "error": "Invalid token format"}
    
    def get_delivery_status(self, proposal_id: str) -> Optional[Dict[str, Any]]:
        """Get email delivery status for proposal"""
        return self.delivery_status.get(proposal_id)
    
    async def _send_email(
        self,
        recipient: EmailRecipient,
        template_id: str,
        template_vars: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send individual email using SES"""
        try:
            template = self.templates.get(template_id)
            if not template:
                raise ValueError(f"Template {template_id} not found")
            
            # Validate required variables
            missing_vars = [var for var in template.required_variables if var not in template_vars]
            if missing_vars:
                raise ValueError(f"Missing template variables: {missing_vars}")
            
            # Render templates
            subject = template.subject_template.format(**template_vars)
            html_body = template.html_template.format(**template_vars)
            text_body = template.text_template.format(**template_vars)
            
            # Send email via SES
            response = self.ses_client.send_email(
                Source=f"{self.sender_name} <{self.sender_email}>",
                Destination={
                    'ToAddresses': [recipient.email]
                },
                Message={
                    'Subject': {
                        'Data': subject,
                        'Charset': 'UTF-8'
                    },
                    'Body': {
                        'Html': {
                            'Data': html_body,
                            'Charset': 'UTF-8'
                        },
                        'Text': {
                            'Data': text_body,
                            'Charset': 'UTF-8'
                        }
                    }
                }
            )
            
            message_id = response.get('MessageId')
            self.logger.info(f"Email sent successfully to {recipient.email}, MessageId: {message_id}")
            
            return {
                "success": True,
                "message_id": message_id,
                "recipient": recipient.email
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            self.logger.error(f"SES error sending email to {recipient.email}: {error_code} - {error_message}")
            
            return {
                "success": False,
                "error": f"SES error: {error_code} - {error_message}",
                "recipient": recipient.email
            }
            
        except Exception as e:
            self.logger.error(f"Error sending email to {recipient.email}: {e}")
            return {
                "success": False,
                "error": str(e),
                "recipient": recipient.email
            }
    
    def _generate_auth_token(self, proposal_id: str, approver_email: str, decision: str) -> str:
        """Generate secure authentication token for email-based approval"""
        try:
            expires_at = datetime.now() + timedelta(hours=self.token_expiry_hours)
            
            # Generate signature
            signature = self._generate_signature(proposal_id, approver_email, decision, expires_at)
            
            # Create token data
            token_data = {
                "proposal_id": proposal_id,
                "approver_email": approver_email,
                "decision": decision,
                "expires_at": expires_at.isoformat(),
                "signature": signature
            }
            
            # Encode token
            token_json = json.dumps(token_data)
            token = base64.urlsafe_b64encode(token_json.encode()).decode()
            
            return token
            
        except Exception as e:
            self.logger.error(f"Error generating auth token: {e}")
            raise
    
    def _generate_signature(self, proposal_id: str, approver_email: str, decision: str, expires_at: datetime) -> str:
        """Generate HMAC signature for token validation"""
        message = f"{proposal_id}:{approver_email}:{decision}:{expires_at.isoformat()}"
        signature = hmac.new(
            self.secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _get_approval_request_html_template(self) -> str:
        """Get HTML template for approval requests"""
        return """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Approval Request</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #2c3e50; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
        .content {{ background-color: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px; }}
        .proposal-details {{ background-color: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #3498db; }}
        .action-buttons {{ text-align: center; margin: 30px 0; }}
        .btn {{ display: inline-block; padding: 12px 30px; margin: 0 10px; text-decoration: none; border-radius: 5px; font-weight: bold; }}
        .btn-approve {{ background-color: #27ae60; color: white; }}
        .btn-reject {{ background-color: #e74c3c; color: white; }}
        .btn-view {{ background-color: #3498db; color: white; }}
        .footer {{ text-align: center; margin-top: 30px; font-size: 12px; color: #666; }}
        .risk-high {{ color: #e74c3c; font-weight: bold; }}
        .risk-medium {{ color: #f39c12; font-weight: bold; }}
        .risk-low {{ color: #27ae60; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔔 Approval Request</h1>
        <p>Vismaya DemandOps - Decision Management System</p>
    </div>
    
    <div class="content">
        <p>Dear {recipient_name},</p>
        
        <p>A new decision proposal requires your approval. Please review the details below and take action.</p>
        
        <div class="proposal-details">
            <h3>📋 Proposal Details</h3>
            <p><strong>Title:</strong> {proposal_title}</p>
            <p><strong>Description:</strong> {proposal_description}</p>
            <p><strong>Created by:</strong> {created_by}</p>
            <p><strong>Estimated Cost Impact:</strong> {estimated_cost_impact}</p>
            <p><strong>Risk Level:</strong> <span class="risk-{risk_level}">{risk_level}</span></p>
            <p><strong>Approval Deadline:</strong> {approval_deadline}</p>
            <p><strong>Proposal ID:</strong> {proposal_id}</p>
        </div>
        
        <div class="action-buttons">
            <a href="{approve_url}" class="btn btn-approve">✅ Approve</a>
            <a href="{reject_url}" class="btn btn-reject">❌ Reject</a>
            <a href="{view_url}" class="btn btn-view">👁️ View Details</a>
        </div>
        
        <p><strong>Important:</strong> This approval request will expire on {approval_deadline}. Please take action before the deadline.</p>
        
        <p>If you have any questions about this proposal, please contact the proposal creator or visit the dashboard for more details.</p>
    </div>
    
    <div class="footer">
        <p>This is an automated message from Vismaya DemandOps Decision Management System.</p>
        <p>Please do not reply to this email.</p>
    </div>
</body>
</html>
        """
    
    def _get_approval_request_text_template(self) -> str:
        """Get text template for approval requests"""
        return """
APPROVAL REQUEST - Vismaya DemandOps

Dear {recipient_name},

A new decision proposal requires your approval. Please review the details below and take action.

PROPOSAL DETAILS:
- Title: {proposal_title}
- Description: {proposal_description}
- Created by: {created_by}
- Estimated Cost Impact: {estimated_cost_impact}
- Risk Level: {risk_level}
- Approval Deadline: {approval_deadline}
- Proposal ID: {proposal_id}

ACTIONS:
- Approve: {approve_url}
- Reject: {reject_url}
- View Details: {view_url}

IMPORTANT: This approval request will expire on {approval_deadline}. Please take action before the deadline.

If you have any questions about this proposal, please contact the proposal creator or visit the dashboard for more details.

---
This is an automated message from Vismaya DemandOps Decision Management System.
Please do not reply to this email.
        """
    
    def _get_status_update_html_template(self) -> str:
        """Get HTML template for status updates"""
        return """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Decision Status Update</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #34495e; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
        .content {{ background-color: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px; }}
        .status-update {{ background-color: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #f39c12; }}
        .btn {{ display: inline-block; padding: 12px 30px; margin: 10px 0; text-decoration: none; border-radius: 5px; font-weight: bold; background-color: #3498db; color: white; }}
        .footer {{ text-align: center; margin-top: 30px; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📢 Decision Status Update</h1>
        <p>Vismaya DemandOps - Decision Management System</p>
    </div>
    
    <div class="content">
        <p>Dear {recipient_name},</p>
        
        <p>There has been an update to a decision proposal you're involved with.</p>
        
        <div class="status-update">
            <h3>📋 Status Update</h3>
            <p><strong>Proposal:</strong> {proposal_title}</p>
            <p><strong>Update:</strong> {status_update}</p>
            <p><strong>Action by:</strong> {approver_name}</p>
            <p><strong>Decision:</strong> {decision}</p>
            <p><strong>Proposal ID:</strong> {proposal_id}</p>
        </div>
        
        <div style="text-align: center;">
            <a href="{view_url}" class="btn">👁️ View Full Details</a>
        </div>
        
        <p>You can view the complete proposal details and approval history by clicking the link above.</p>
    </div>
    
    <div class="footer">
        <p>This is an automated message from Vismaya DemandOps Decision Management System.</p>
        <p>Please do not reply to this email.</p>
    </div>
</body>
</html>
        """
    
    def _get_status_update_text_template(self) -> str:
        """Get text template for status updates"""
        return """
DECISION STATUS UPDATE - Vismaya DemandOps

Dear {recipient_name},

There has been an update to a decision proposal you're involved with.

STATUS UPDATE:
- Proposal: {proposal_title}
- Update: {status_update}
- Action by: {approver_name}
- Decision: {decision}
- Proposal ID: {proposal_id}

View Full Details: {view_url}

You can view the complete proposal details and approval history by visiting the link above.

---
This is an automated message from Vismaya DemandOps Decision Management System.
Please do not reply to this email.
        """
    
    def _get_execution_notification_html_template(self) -> str:
        """Get HTML template for execution notifications"""
        return """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Decision Executed</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #27ae60; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
        .content {{ background-color: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px; }}
        .execution-details {{ background-color: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #27ae60; }}
        .btn {{ display: inline-block; padding: 12px 30px; margin: 10px 0; text-decoration: none; border-radius: 5px; font-weight: bold; background-color: #3498db; color: white; }}
        .footer {{ text-align: center; margin-top: 30px; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>✅ Decision Executed</h1>
        <p>Vismaya DemandOps - Decision Management System</p>
    </div>
    
    <div class="content">
        <p>Dear {recipient_name},</p>
        
        <p>A decision proposal has been executed {execution_success}.</p>
        
        <div class="execution-details">
            <h3>📋 Execution Details</h3>
            <p><strong>Proposal:</strong> {proposal_title}</p>
            <p><strong>Result:</strong> {execution_result}</p>
            <p><strong>Status:</strong> Executed {execution_success}</p>
            <p><strong>Proposal ID:</strong> {proposal_id}</p>
        </div>
        
        <div style="text-align: center;">
            <a href="{view_url}" class="btn">👁️ View Full Details</a>
        </div>
        
        <p>You can view the complete execution details and results by clicking the link above.</p>
    </div>
    
    <div class="footer">
        <p>This is an automated message from Vismaya DemandOps Decision Management System.</p>
        <p>Please do not reply to this email.</p>
    </div>
</body>
</html>
        """
    
    def _get_execution_notification_text_template(self) -> str:
        """Get text template for execution notifications"""
        return """
DECISION EXECUTED - Vismaya DemandOps

Dear {recipient_name},

A decision proposal has been executed {execution_success}.

EXECUTION DETAILS:
- Proposal: {proposal_title}
- Result: {execution_result}
- Status: Executed {execution_success}
- Proposal ID: {proposal_id}

View Full Details: {view_url}

You can view the complete execution details and results by visiting the link above.

---
This is an automated message from Vismaya DemandOps Decision Management System.
Please do not reply to this email.
        """