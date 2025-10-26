"""
Real-time Notification Service for Approval Status Updates
Provides real-time notifications for approval status changes via WebSocket and other channels
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
try:
    import websockets
    # Use the new import path to avoid deprecation warning
    try:
        from websockets.asyncio import ServerProtocol as WebSocketServerProtocol
    except ImportError:
        # Fallback to legacy import if new one not available
        from websockets.server import WebSocketServerProtocol
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    WebSocketServerProtocol = None

from ..core.models import DecisionProposal, DecisionStatus, SystemEvent
from .audit_trail_service import AuditEvent, AuditEventType


class NotificationChannel(Enum):
    """Types of notification channels"""
    WEBSOCKET = "websocket"
    EMAIL = "email"
    DASHBOARD = "dashboard"
    MOBILE_PUSH = "mobile_push"
    SLACK = "slack"
    TEAMS = "teams"


@dataclass
class NotificationSubscription:
    """Notification subscription configuration"""
    subscriber_id: str
    channels: List[NotificationChannel]
    proposal_filters: Dict[str, Any] = field(default_factory=dict)
    event_filters: List[AuditEventType] = field(default_factory=list)
    user_roles: List[str] = field(default_factory=list)
    active: bool = True
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class RealTimeNotification:
    """Real-time notification message"""
    notification_id: str = field(default_factory=lambda: f"notif_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}")
    event_type: str = ""
    proposal_id: str = ""
    title: str = ""
    message: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    priority: str = "normal"  # low, normal, high, critical
    channels: List[NotificationChannel] = field(default_factory=list)
    target_users: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert notification to dictionary"""
        return {
            "notification_id": self.notification_id,
            "event_type": self.event_type,
            "proposal_id": self.proposal_id,
            "title": self.title,
            "message": self.message,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "priority": self.priority,
            "channels": [c.value for c in self.channels],
            "target_users": self.target_users
        }


class RealTimeNotificationService:
    """
    Real-time notification service for approval status updates
    
    Features:
    - WebSocket-based real-time notifications
    - Multi-channel notification delivery
    - Subscription management with filtering
    - Notification history and delivery tracking
    - Integration with audit trail service
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.websocket_host = self.config.get("websocket_host", "localhost")
        self.websocket_port = self.config.get("websocket_port", 8765)
        self.enable_websocket = self.config.get("enable_websocket", True)
        
        # WebSocket connections
        self.websocket_connections: Dict[str, WebSocketServerProtocol] = {}
        self.websocket_server = None
        
        # Subscriptions
        self.subscriptions: Dict[str, NotificationSubscription] = {}
        
        # Notification history
        self.notification_history: List[RealTimeNotification] = []
        self.max_history_size = self.config.get("max_history_size", 1000)
        
        # Delivery tracking
        self.delivery_stats = {
            "total_sent": 0,
            "successful_deliveries": 0,
            "failed_deliveries": 0,
            "deliveries_by_channel": {}
        }
    
    async def start_service(self) -> None:
        """Start the real-time notification service"""
        try:
            if self.enable_websocket and WEBSOCKETS_AVAILABLE:
                await self._start_websocket_server()
            elif self.enable_websocket and not WEBSOCKETS_AVAILABLE:
                self.logger.warning("WebSocket support requested but 'websockets' package not available. Install with: pip install websockets")
                self.enable_websocket = False
            
            self.logger.info("Real-time notification service started")
            
        except Exception as e:
            self.logger.error(f"Error starting notification service: {e}")
            raise
    
    async def stop_service(self) -> None:
        """Stop the real-time notification service"""
        try:
            if self.websocket_server:
                self.websocket_server.close()
                await self.websocket_server.wait_closed()
            
            # Close all WebSocket connections
            for connection in self.websocket_connections.values():
                await connection.close()
            
            self.websocket_connections.clear()
            
            self.logger.info("Real-time notification service stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping notification service: {e}")
    
    async def subscribe(
        self,
        subscriber_id: str,
        channels: List[NotificationChannel],
        proposal_filters: Dict[str, Any] = None,
        event_filters: List[AuditEventType] = None,
        user_roles: List[str] = None
    ) -> bool:
        """Subscribe to real-time notifications"""
        try:
            subscription = NotificationSubscription(
                subscriber_id=subscriber_id,
                channels=channels,
                proposal_filters=proposal_filters or {},
                event_filters=event_filters or [],
                user_roles=user_roles or []
            )
            
            self.subscriptions[subscriber_id] = subscription
            
            self.logger.info(f"User {subscriber_id} subscribed to notifications via {[c.value for c in channels]}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error subscribing user {subscriber_id}: {e}")
            return False
    
    async def unsubscribe(self, subscriber_id: str) -> bool:
        """Unsubscribe from real-time notifications"""
        try:
            if subscriber_id in self.subscriptions:
                del self.subscriptions[subscriber_id]
                
                # Close WebSocket connection if exists
                if subscriber_id in self.websocket_connections:
                    await self.websocket_connections[subscriber_id].close()
                    del self.websocket_connections[subscriber_id]
                
                self.logger.info(f"User {subscriber_id} unsubscribed from notifications")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error unsubscribing user {subscriber_id}: {e}")
            return False
    
    async def notify_proposal_status_change(
        self,
        proposal: DecisionProposal,
        old_status: DecisionStatus,
        new_status: DecisionStatus,
        actor: str,
        additional_data: Dict[str, Any] = None
    ) -> None:
        """Send notification for proposal status change"""
        try:
            # Create notification
            notification = RealTimeNotification(
                event_type="proposal_status_change",
                proposal_id=proposal.proposal_id,
                title=f"Proposal Status Updated: {proposal.title}",
                message=f"Status changed from {old_status.value} to {new_status.value} by {actor}",
                data={
                    "old_status": old_status.value,
                    "new_status": new_status.value,
                    "actor": actor,
                    "proposal_title": proposal.title,
                    "estimated_cost_impact": proposal.estimated_cost_impact,
                    "risk_level": proposal.risk_level.value,
                    "approval_summary": proposal.get_approval_summary(),
                    **(additional_data or {})
                },
                priority="high" if new_status in [DecisionStatus.APPROVED, DecisionStatus.REJECTED] else "normal",
                target_users=proposal.required_approvers + [proposal.created_by]
            )
            
            await self._send_notification(notification)
            
        except Exception as e:
            self.logger.error(f"Error notifying proposal status change: {e}")
    
    async def notify_approval_response(
        self,
        proposal: DecisionProposal,
        approver: str,
        decision: str,
        comments: Optional[str] = None,
        additional_data: Dict[str, Any] = None
    ) -> None:
        """Send notification for approval response"""
        try:
            notification = RealTimeNotification(
                event_type="approval_response",
                proposal_id=proposal.proposal_id,
                title=f"Approval Response: {proposal.title}",
                message=f"{approver} {decision} the proposal" + (f": {comments}" if comments else ""),
                data={
                    "approver": approver,
                    "decision": decision,
                    "comments": comments,
                    "proposal_title": proposal.title,
                    "approval_summary": proposal.get_approval_summary(),
                    **(additional_data or {})
                },
                priority="high",
                target_users=proposal.required_approvers + [proposal.created_by]
            )
            
            await self._send_notification(notification)
            
        except Exception as e:
            self.logger.error(f"Error notifying approval response: {e}")
    
    async def notify_proposal_deadline_approaching(
        self,
        proposal: DecisionProposal,
        hours_remaining: float,
        additional_data: Dict[str, Any] = None
    ) -> None:
        """Send notification for approaching deadline"""
        try:
            notification = RealTimeNotification(
                event_type="deadline_approaching",
                proposal_id=proposal.proposal_id,
                title=f"Deadline Approaching: {proposal.title}",
                message=f"Approval deadline in {hours_remaining:.1f} hours",
                data={
                    "hours_remaining": hours_remaining,
                    "approval_deadline": proposal.approval_deadline.isoformat() if proposal.approval_deadline else None,
                    "proposal_title": proposal.title,
                    "pending_approvers": [
                        approver for approver in proposal.required_approvers
                        if not any(r["approver"] == approver for r in proposal.approval_responses)
                    ],
                    **(additional_data or {})
                },
                priority="critical" if hours_remaining < 2 else "high",
                target_users=proposal.required_approvers
            )
            
            await self._send_notification(notification)
            
        except Exception as e:
            self.logger.error(f"Error notifying deadline approaching: {e}")
    
    async def notify_proposal_expired(
        self,
        proposal: DecisionProposal,
        additional_data: Dict[str, Any] = None
    ) -> None:
        """Send notification for expired proposal"""
        try:
            notification = RealTimeNotification(
                event_type="proposal_expired",
                proposal_id=proposal.proposal_id,
                title=f"Proposal Expired: {proposal.title}",
                message=f"Approval deadline has passed without sufficient approvals",
                data={
                    "proposal_title": proposal.title,
                    "approval_deadline": proposal.approval_deadline.isoformat() if proposal.approval_deadline else None,
                    "approval_summary": proposal.get_approval_summary(),
                    **(additional_data or {})
                },
                priority="high",
                target_users=proposal.required_approvers + [proposal.created_by]
            )
            
            await self._send_notification(notification)
            
        except Exception as e:
            self.logger.error(f"Error notifying proposal expired: {e}")
    
    async def notify_proposal_escalated(
        self,
        proposal: DecisionProposal,
        escalated_to: List[str],
        reason: str,
        additional_data: Dict[str, Any] = None
    ) -> None:
        """Send notification for proposal escalation"""
        try:
            notification = RealTimeNotification(
                event_type="proposal_escalated",
                proposal_id=proposal.proposal_id,
                title=f"Proposal Escalated: {proposal.title}",
                message=f"Escalated to {', '.join(escalated_to)} - {reason}",
                data={
                    "escalated_to": escalated_to,
                    "reason": reason,
                    "proposal_title": proposal.title,
                    "original_approvers": proposal.required_approvers,
                    **(additional_data or {})
                },
                priority="critical",
                target_users=escalated_to + proposal.required_approvers + [proposal.created_by]
            )
            
            await self._send_notification(notification)
            
        except Exception as e:
            self.logger.error(f"Error notifying proposal escalation: {e}")
    
    async def notify_audit_event(self, audit_event: AuditEvent) -> None:
        """Send notification for audit event"""
        try:
            # Only notify for significant events
            significant_events = [
                AuditEventType.PROPOSAL_CREATED,
                AuditEventType.APPROVAL_RESPONSE_RECEIVED,
                AuditEventType.PROPOSAL_APPROVED,
                AuditEventType.PROPOSAL_REJECTED,
                AuditEventType.PROPOSAL_EXECUTED,
                AuditEventType.PROPOSAL_ESCALATED
            ]
            
            if audit_event.event_type not in significant_events:
                return
            
            notification = RealTimeNotification(
                event_type=f"audit_{audit_event.event_type.value}",
                proposal_id=audit_event.proposal_id,
                title=f"Audit Event: {audit_event.event_type.value.replace('_', ' ').title()}",
                message=audit_event.action_description,
                data={
                    "audit_event_id": audit_event.event_id,
                    "actor": audit_event.actor,
                    "actor_type": audit_event.actor_type,
                    "event_details": audit_event.details
                },
                priority="normal"
            )
            
            await self._send_notification(notification)
            
        except Exception as e:
            self.logger.error(f"Error notifying audit event: {e}")
    
    async def get_notification_history(
        self,
        subscriber_id: Optional[str] = None,
        proposal_id: Optional[str] = None,
        limit: int = 50
    ) -> List[RealTimeNotification]:
        """Get notification history"""
        try:
            notifications = self.notification_history
            
            # Apply filters
            if subscriber_id:
                notifications = [n for n in notifications if subscriber_id in n.target_users]
            
            if proposal_id:
                notifications = [n for n in notifications if n.proposal_id == proposal_id]
            
            # Sort by timestamp (newest first) and apply limit
            notifications.sort(key=lambda n: n.timestamp, reverse=True)
            return notifications[:limit]
            
        except Exception as e:
            self.logger.error(f"Error getting notification history: {e}")
            return []
    
    async def get_delivery_stats(self) -> Dict[str, Any]:
        """Get notification delivery statistics"""
        return {
            "total_sent": self.delivery_stats["total_sent"],
            "successful_deliveries": self.delivery_stats["successful_deliveries"],
            "failed_deliveries": self.delivery_stats["failed_deliveries"],
            "success_rate": (
                self.delivery_stats["successful_deliveries"] / max(self.delivery_stats["total_sent"], 1)
            ) * 100,
            "deliveries_by_channel": self.delivery_stats["deliveries_by_channel"],
            "active_subscriptions": len(self.subscriptions),
            "active_websocket_connections": len(self.websocket_connections)
        }
    
    async def _send_notification(self, notification: RealTimeNotification) -> None:
        """Send notification to all relevant subscribers"""
        try:
            # Add to history
            self.notification_history.append(notification)
            if len(self.notification_history) > self.max_history_size:
                self.notification_history.pop(0)
            
            # Find relevant subscribers
            relevant_subscribers = []
            for subscriber_id, subscription in self.subscriptions.items():
                if self._should_notify_subscriber(notification, subscription):
                    relevant_subscribers.append(subscriber_id)
            
            # Send via each channel
            delivery_results = []
            
            for subscriber_id in relevant_subscribers:
                subscription = self.subscriptions[subscriber_id]
                
                for channel in subscription.channels:
                    try:
                        if channel == NotificationChannel.WEBSOCKET:
                            success = await self._send_websocket_notification(subscriber_id, notification)
                        elif channel == NotificationChannel.DASHBOARD:
                            success = await self._send_dashboard_notification(subscriber_id, notification)
                        else:
                            # Other channels not implemented yet
                            success = False
                        
                        delivery_results.append({
                            "subscriber": subscriber_id,
                            "channel": channel.value,
                            "success": success
                        })
                        
                        # Update stats
                        channel_key = channel.value
                        if channel_key not in self.delivery_stats["deliveries_by_channel"]:
                            self.delivery_stats["deliveries_by_channel"][channel_key] = {"sent": 0, "successful": 0}
                        
                        self.delivery_stats["deliveries_by_channel"][channel_key]["sent"] += 1
                        if success:
                            self.delivery_stats["deliveries_by_channel"][channel_key]["successful"] += 1
                        
                    except Exception as e:
                        self.logger.error(f"Error sending notification via {channel.value} to {subscriber_id}: {e}")
                        delivery_results.append({
                            "subscriber": subscriber_id,
                            "channel": channel.value,
                            "success": False,
                            "error": str(e)
                        })
            
            # Update overall stats
            self.delivery_stats["total_sent"] += len(delivery_results)
            self.delivery_stats["successful_deliveries"] += sum(1 for r in delivery_results if r["success"])
            self.delivery_stats["failed_deliveries"] += sum(1 for r in delivery_results if not r["success"])
            
            self.logger.debug(f"Sent notification {notification.notification_id} to {len(relevant_subscribers)} subscribers")
            
        except Exception as e:
            self.logger.error(f"Error sending notification: {e}")
    
    def _should_notify_subscriber(self, notification: RealTimeNotification, subscription: NotificationSubscription) -> bool:
        """Check if subscriber should receive notification"""
        try:
            if not subscription.active:
                return False
            
            # Check if subscriber is in target users
            if notification.target_users and subscription.subscriber_id not in notification.target_users:
                return False
            
            # Check event filters
            if subscription.event_filters:
                event_type_enum = None
                try:
                    # Convert notification event type to audit event type
                    if notification.event_type == "proposal_status_change":
                        event_type_enum = AuditEventType.STATUS_UPDATED
                    elif notification.event_type == "approval_response":
                        event_type_enum = AuditEventType.APPROVAL_RESPONSE_RECEIVED
                    elif notification.event_type.startswith("audit_"):
                        event_type_enum = AuditEventType(notification.event_type.replace("audit_", ""))
                except ValueError:
                    pass
                
                if event_type_enum and event_type_enum not in subscription.event_filters:
                    return False
            
            # Check proposal filters
            if subscription.proposal_filters:
                # Apply proposal-specific filters (e.g., cost threshold, risk level)
                cost_threshold = subscription.proposal_filters.get("min_cost_impact")
                if cost_threshold and notification.data.get("estimated_cost_impact", 0) < cost_threshold:
                    return False
                
                risk_levels = subscription.proposal_filters.get("risk_levels")
                if risk_levels and notification.data.get("risk_level") not in risk_levels:
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking subscriber notification criteria: {e}")
            return False
    
    async def _send_websocket_notification(self, subscriber_id: str, notification: RealTimeNotification) -> bool:
        """Send notification via WebSocket"""
        try:
            connection = self.websocket_connections.get(subscriber_id)
            if not connection:
                return False
            
            message = json.dumps(notification.to_dict())
            await connection.send(message)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending WebSocket notification to {subscriber_id}: {e}")
            # Remove broken connection
            if subscriber_id in self.websocket_connections:
                del self.websocket_connections[subscriber_id]
            return False
    
    async def _send_dashboard_notification(self, subscriber_id: str, notification: RealTimeNotification) -> bool:
        """Send notification to dashboard (placeholder implementation)"""
        try:
            # In a real implementation, this would update the dashboard state
            # For now, just log the notification
            self.logger.info(f"Dashboard notification for {subscriber_id}: {notification.title}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending dashboard notification to {subscriber_id}: {e}")
            return False
    
    async def _start_websocket_server(self) -> None:
        """Start WebSocket server for real-time notifications"""
        if not WEBSOCKETS_AVAILABLE:
            raise ImportError("websockets package is required for WebSocket server. Install with: pip install websockets")
        
        try:
            async def handle_websocket_connection(websocket: WebSocketServerProtocol, path: str):
                try:
                    # Wait for authentication message
                    auth_message = await websocket.recv()
                    auth_data = json.loads(auth_message)
                    
                    subscriber_id = auth_data.get("subscriber_id")
                    if not subscriber_id:
                        await websocket.close(code=4001, reason="Missing subscriber_id")
                        return
                    
                    # Store connection
                    self.websocket_connections[subscriber_id] = websocket
                    
                    self.logger.info(f"WebSocket connection established for {subscriber_id}")
                    
                    # Send confirmation
                    await websocket.send(json.dumps({
                        "type": "connection_established",
                        "subscriber_id": subscriber_id,
                        "timestamp": datetime.now().isoformat()
                    }))
                    
                    # Keep connection alive
                    try:
                        async for message in websocket:
                            # Handle incoming messages (e.g., ping/pong)
                            data = json.loads(message)
                            if data.get("type") == "ping":
                                await websocket.send(json.dumps({"type": "pong"}))
                    except websockets.exceptions.ConnectionClosed:
                        pass
                    
                except Exception as e:
                    self.logger.error(f"Error in WebSocket connection: {e}")
                finally:
                    # Clean up connection
                    if subscriber_id in self.websocket_connections:
                        del self.websocket_connections[subscriber_id]
                    self.logger.info(f"WebSocket connection closed for {subscriber_id}")
            
            # Start WebSocket server
            self.websocket_server = await websockets.serve(
                handle_websocket_connection,
                self.websocket_host,
                self.websocket_port
            )
            
            self.logger.info(f"WebSocket server started on {self.websocket_host}:{self.websocket_port}")
            
        except Exception as e:
            self.logger.error(f"Error starting WebSocket server: {e}")
            raise