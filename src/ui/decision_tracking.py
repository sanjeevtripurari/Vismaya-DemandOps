"""
Real-time Decision Tracking and Approval Interface
Implements live status updates and approval workflows
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json
import time

from ..agentic.core.models import DecisionProposal, DecisionStatus, RiskLevel
from ..services.real_time_decision_service import RealTimeDecisionService, DecisionUpdate
from .modern_dashboard import ModernDashboardFramework


class DecisionTrackingInterface:
    """Real-time decision tracking and approval interface"""
    
    def __init__(self, real_time_service: Optional[RealTimeDecisionService] = None):
        self.dashboard = ModernDashboardFramework()
        self.real_time_service = real_time_service or RealTimeDecisionService()
        self._initialize_decision_state()
        self._setup_real_time_updates()
    
    def _initialize_decision_state(self):
        """Initialize decision tracking state"""
        if 'decisions' not in st.session_state:
            st.session_state.decisions = []
        
        if 'decision_history' not in st.session_state:
            st.session_state.decision_history = []
        
        if 'approval_responses' not in st.session_state:
            st.session_state.approval_responses = {}
        
        if 'real_time_updates' not in st.session_state:
            st.session_state.real_time_updates = True
        
        if 'last_update_time' not in st.session_state:
            st.session_state.last_update_time = datetime.now()
        
        if 'update_notifications' not in st.session_state:
            st.session_state.update_notifications = []
    
    def _setup_real_time_updates(self):
        """Setup real-time update handling"""
        # Subscribe to real-time updates
        if 'subscribed_to_updates' not in st.session_state:
            self.real_time_service.subscribe_to_updates(
                "streamlit_ui", 
                self._handle_real_time_update
            )
            st.session_state.subscribed_to_updates = True
    
    def _handle_real_time_update(self, update: DecisionUpdate):
        """Handle real-time decision updates"""
        try:
            # Add to notification queue
            st.session_state.update_notifications.append({
                'update_id': update.update_id,
                'decision_id': update.decision_id,
                'update_type': update.update_type,
                'data': update.data,
                'timestamp': update.timestamp,
                'user_id': update.user_id
            })
            
            # Keep only last 50 notifications
            if len(st.session_state.update_notifications) > 50:
                st.session_state.update_notifications = st.session_state.update_notifications[-50:]
            
            # Update last update time
            st.session_state.last_update_time = datetime.now()
            
        except Exception as e:
            st.error(f"Error handling real-time update: {e}")
    
    def render_decision_dashboard(self):
        """Render the main decision tracking dashboard"""
        self.dashboard.render_modern_header(
            "Decision Tracking & Approval",
            "Real-time monitoring of AI-generated decisions and approval workflows"
        )
        
        # Real-time status indicators
        self._render_real_time_status()
        
        # Decision metrics overview
        self._render_decision_metrics()
        
        # Main content tabs
        self.dashboard.render_modern_tabs([
            {
                'label': '📋 Pending Decisions',
                'content': self._render_pending_decisions_tab
            },
            {
                'label': '✅ Approval Interface',
                'content': self._render_approval_interface_tab
            },
            {
                'label': '📊 Decision History',
                'content': self._render_decision_history_tab
            },
            {
                'label': '📈 Analytics',
                'content': self._render_decision_analytics_tab
            }
        ])
    
    def _render_real_time_status(self):
        """Render real-time status indicators"""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Auto-refresh toggle
            auto_refresh = st.toggle(
                "🔄 Auto-refresh",
                value=st.session_state.real_time_updates,
                help="Enable real-time updates every 30 seconds"
            )
            st.session_state.real_time_updates = auto_refresh
        
        with col2:
            # Manual refresh button
            if st.button("🔄 Refresh Now", help="Manually refresh decision data"):
                self._refresh_decision_data()
                st.rerun()
        
        with col3:
            # Connection status
            connection_status = self._check_connection_status()
            status_color = "🟢" if connection_status else "🔴"
            st.markdown(f"{status_color} **Connection:** {'Online' if connection_status else 'Offline'}")
        
        with col4:
            # Last update time
            last_update = st.session_state.get('last_update_time', datetime.now())
            time_diff = datetime.now() - last_update
            seconds_ago = int(time_diff.total_seconds())
            st.markdown(f"🕒 **Last update:** {seconds_ago}s ago")
        
        # Real-time notifications
        self._render_real_time_notifications()
        
        # Auto-refresh mechanism
        if st.session_state.real_time_updates:
            # Check for updates every 5 seconds
            time.sleep(0.1)  # Small delay to prevent excessive reloading
            
            # Auto-refresh if more than 30 seconds since last update
            if (datetime.now() - st.session_state.last_update_time).total_seconds() > 30:
                self._refresh_decision_data()
                st.rerun()
    
    def _render_real_time_notifications(self):
        """Render real-time update notifications"""
        notifications = st.session_state.get('update_notifications', [])
        
        if notifications:
            # Show recent notifications
            recent_notifications = notifications[-5:]  # Last 5 notifications
            
            with st.expander(f"🔔 Recent Updates ({len(recent_notifications)})", expanded=False):
                for notification in reversed(recent_notifications):  # Show newest first
                    update_type = notification['update_type']
                    timestamp = notification['timestamp']
                    data = notification['data']
                    
                    # Format notification message
                    if update_type == "decision_created":
                        message = f"📋 New decision created: {data.get('title', 'Unknown')}"
                    elif update_type == "status_change":
                        old_status = data.get('old_status', 'unknown')
                        new_status = data.get('new_status', 'unknown')
                        message = f"🔄 Status changed: {old_status} → {new_status}"
                    elif update_type == "approval_response":
                        approver = data.get('approver', 'Unknown')
                        decision = data.get('decision', 'unknown')
                        message = f"✅ {approver} {decision} decision"
                    elif update_type == "deadline_approaching":
                        hours = data.get('hours_remaining', 0)
                        message = f"⏰ Deadline approaching: {hours:.1f} hours remaining"
                    elif update_type == "decision_expired":
                        message = f"⚠️ Decision expired"
                    else:
                        message = f"📢 {update_type.replace('_', ' ').title()}"
                    
                    # Display notification
                    time_str = timestamp.strftime('%H:%M:%S') if isinstance(timestamp, datetime) else str(timestamp)
                    st.markdown(f"**{time_str}** - {message}")
                
                # Clear notifications button
                if st.button("🗑️ Clear Notifications", key="clear_notifications"):
                    st.session_state.update_notifications = []
                    st.rerun()
    
    def _render_decision_metrics(self):
        """Render decision metrics overview"""
        try:
            # Get metrics from real-time service
            metrics_data = self.real_time_service.get_decision_metrics()
            
            # Calculate additional metrics
            decisions = st.session_state.decisions
            today_created = len([d for d in decisions if d.get('created_today', False)])
            
            metrics = [
                {
                    'label': 'Total Decisions',
                    'value': str(metrics_data['total_decisions']),
                    'icon': '📋',
                    'delta': f"+{today_created}" if today_created > 0 else None
                },
                {
                    'label': 'Pending Approval',
                    'value': str(metrics_data['pending_decisions']),
                    'icon': '⏳',
                    'color': 'warning' if metrics_data['pending_decisions'] > 0 else 'success'
                },
                {
                    'label': 'Approval Rate',
                    'value': f"{metrics_data['approval_rate']:.1f}%",
                    'icon': '✅',
                    'color': 'success' if metrics_data['approval_rate'] > 70 else 'warning'
                },
                {
                    'label': 'Avg Approval Time',
                    'value': f"{metrics_data['avg_approval_time_hours']:.1f}h" if metrics_data['avg_approval_time_hours'] > 0 else "N/A",
                    'icon': '⏱️',
                    'color': 'primary'
                }
            ]
            
            self.dashboard.render_modern_metrics_grid(metrics)
            
        except Exception as e:
            st.error(f"Error rendering decision metrics: {e}")
            # Fallback to basic metrics
            decisions = st.session_state.decisions
            basic_metrics = [
                {
                    'label': 'Active Decisions',
                    'value': str(len(decisions)),
                    'icon': '📋'
                }
            ]
            self.dashboard.render_modern_metrics_grid(basic_metrics)
    
    def _render_pending_decisions_tab(self):
        """Render pending decisions tab with live updates"""
        st.markdown("### 📋 Pending Decisions")
        
        pending_decisions = [d for d in st.session_state.decisions if d.get('status') == 'pending']
        
        if not pending_decisions:
            st.info("🎉 No pending decisions! All decisions have been processed.")
            
            # Show option to create demo decision
            if st.button("➕ Create Demo Decision", help="Create a sample decision for testing"):
                self._create_demo_decision()
                st.rerun()
            return
        
        # Sort by priority and creation time
        pending_decisions.sort(key=lambda x: (
            {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}.get(x.get('priority', 'medium'), 2),
            x.get('created_at', datetime.now())
        ))
        
        for decision in pending_decisions:
            self._render_decision_card(decision)
    
    def _render_decision_card(self, decision: Dict[str, Any]):
        """Render individual decision card with approval actions"""
        decision_id = decision.get('id', 'unknown')
        title = decision.get('title', 'Untitled Decision')
        description = decision.get('description', 'No description available')
        priority = decision.get('priority', 'medium')
        cost_impact = decision.get('cost_impact', 0)
        created_at = decision.get('created_at', datetime.now())
        deadline = decision.get('deadline')
        
        # Priority styling
        priority_config = {
            'critical': {'color': '#ef4444', 'bg': '#fee2e2', 'icon': '🚨'},
            'high': {'color': '#f59e0b', 'bg': '#fef3c7', 'icon': '⚠️'},
            'medium': {'color': '#3b82f6', 'bg': '#dbeafe', 'icon': '📋'},
            'low': {'color': '#10b981', 'bg': '#d1fae5', 'icon': '📝'}
        }
        
        config = priority_config.get(priority, priority_config['medium'])
        
        # Time remaining calculation
        time_remaining = ""
        if deadline:
            remaining = deadline - datetime.now()
            if remaining.total_seconds() > 0:
                days = remaining.days
                hours = remaining.seconds // 3600
                if days > 0:
                    time_remaining = f"{days}d {hours}h remaining"
                else:
                    time_remaining = f"{hours}h remaining"
            else:
                time_remaining = "⚠️ Overdue"
        
        # Render decision card
        with st.container():
            st.markdown(f"""
            <div class="modern-card" style="border-left: 4px solid {config['color']};">
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 1rem;">
                    <div>
                        <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                            <span style="font-size: 1.2rem;">{config['icon']}</span>
                            <h3 style="margin: 0; color: var(--text-primary);">{title}</h3>
                            <span style="
                                background: {config['bg']};
                                color: {config['color']};
                                padding: 0.25rem 0.5rem;
                                border-radius: 0.25rem;
                                font-size: 0.75rem;
                                font-weight: 600;
                                text-transform: uppercase;
                            ">{priority}</span>
                        </div>
                        <p style="color: var(--text-secondary); margin: 0;">{description}</p>
                    </div>
                    <div style="text-align: right; font-size: 0.875rem; color: var(--text-secondary);">
                        <div>ID: {decision_id}</div>
                        <div>{created_at.strftime('%Y-%m-%d %H:%M')}</div>
                        {f'<div style="color: {config["color"]}; font-weight: 600;">{time_remaining}</div>' if time_remaining else ''}
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            # Decision details
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Cost Impact", f"${cost_impact:,.2f}")
            
            with col2:
                affected_resources = decision.get('affected_resources', [])
                st.metric("Affected Resources", len(affected_resources))
            
            with col3:
                risk_level = decision.get('risk_level', 'medium')
                st.metric("Risk Level", risk_level.title())
            
            # Approval actions
            st.markdown("**Quick Actions:**")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("✅ Approve", key=f"approve_{decision_id}", type="primary"):
                    self._process_approval(decision_id, "approved", "Quick approval")
                    st.success("Decision approved!")
                    st.rerun()
            
            with col2:
                if st.button("❌ Reject", key=f"reject_{decision_id}"):
                    self._process_approval(decision_id, "rejected", "Quick rejection")
                    st.error("Decision rejected!")
                    st.rerun()
            
            with col3:
                if st.button("📝 Review", key=f"review_{decision_id}"):
                    st.session_state[f"review_mode_{decision_id}"] = True
                    st.rerun()
            
            with col4:
                if st.button("📧 Email", key=f"email_{decision_id}"):
                    self._send_approval_email(decision)
                    st.info("Approval email sent!")
            
            # Detailed review mode
            if st.session_state.get(f"review_mode_{decision_id}", False):
                with st.expander("📝 Detailed Review", expanded=True):
                    self._render_detailed_review(decision)
            
            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("---")
    
    def _render_detailed_review(self, decision: Dict[str, Any]):
        """Render detailed review interface for a decision"""
        decision_id = decision.get('id')
        
        # Impact analysis
        st.markdown("**📊 Impact Analysis:**")
        impact_analysis = decision.get('impact_analysis', {})
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Financial Impact:**")
            st.write(f"• Initial cost: ${decision.get('cost_impact', 0):,.2f}")
            st.write(f"• Monthly impact: ${impact_analysis.get('monthly_impact', 0):,.2f}")
            st.write(f"• Annual projection: ${impact_analysis.get('annual_impact', 0):,.2f}")
        
        with col2:
            st.write("**Operational Impact:**")
            operational_impact = impact_analysis.get('operational_impact', [])
            if operational_impact:
                for impact in operational_impact:
                    st.write(f"• {impact}")
            else:
                st.write("• No significant operational impact identified")
        
        # Recommendations
        recommendations = decision.get('recommendations', [])
        if recommendations:
            st.markdown("**💡 AI Recommendations:**")
            for i, rec in enumerate(recommendations, 1):
                st.write(f"{i}. {rec}")
        
        # Approval form
        st.markdown("**✍️ Approval Decision:**")
        
        approval_decision = st.radio(
            "Decision:",
            ["Approve", "Reject", "Request More Info"],
            key=f"approval_decision_{decision_id}"
        )
        
        comments = st.text_area(
            "Comments (optional):",
            placeholder="Add any comments or conditions...",
            key=f"approval_comments_{decision_id}"
        )
        
        conditions = []
        if approval_decision == "Approve":
            add_conditions = st.checkbox("Add approval conditions", key=f"add_conditions_{decision_id}")
            if add_conditions:
                condition_text = st.text_area(
                    "Approval Conditions:",
                    placeholder="List any conditions for approval...",
                    key=f"approval_conditions_{decision_id}"
                )
                if condition_text:
                    conditions = [c.strip() for c in condition_text.split('\n') if c.strip()]
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Submit Decision", key=f"submit_decision_{decision_id}", type="primary"):
                self._process_detailed_approval(
                    decision_id, 
                    approval_decision.lower().replace(" ", "_"), 
                    comments, 
                    conditions
                )
                st.success("Decision submitted successfully!")
                st.session_state[f"review_mode_{decision_id}"] = False
                st.rerun()
        
        with col2:
            if st.button("❌ Cancel Review", key=f"cancel_review_{decision_id}"):
                st.session_state[f"review_mode_{decision_id}"] = False
                st.rerun()
    
    def _render_approval_interface_tab(self):
        """Render approval interface with one-click functionality"""
        st.markdown("### ✅ Quick Approval Interface")
        
        # Bulk approval options
        pending_decisions = [d for d in st.session_state.decisions if d.get('status') == 'pending']
        
        if not pending_decisions:
            st.info("No decisions pending approval.")
            return
        
        # Bulk actions
        st.markdown("**🔄 Bulk Actions:**")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("✅ Approve All Low Risk", help="Approve all low-risk decisions"):
                low_risk_decisions = [d for d in pending_decisions if d.get('risk_level') == 'low']
                for decision in low_risk_decisions:
                    self._process_approval(decision['id'], "approved", "Bulk approval - low risk")
                st.success(f"Approved {len(low_risk_decisions)} low-risk decisions")
                st.rerun()
        
        with col2:
            if st.button("📧 Email All Pending", help="Send email notifications for all pending"):
                for decision in pending_decisions:
                    self._send_approval_email(decision)
                st.success(f"Sent {len(pending_decisions)} approval emails")
        
        with col3:
            selected_priority = st.selectbox(
                "Filter by Priority:",
                ["all", "critical", "high", "medium", "low"],
                key="priority_filter"
            )
        
        with col4:
            if st.button("🔄 Refresh Decisions"):
                self._refresh_decision_data()
                st.rerun()
        
        # Filter decisions based on priority
        if selected_priority != "all":
            filtered_decisions = [d for d in pending_decisions if d.get('priority') == selected_priority]
        else:
            filtered_decisions = pending_decisions
        
        # Quick approval grid
        if filtered_decisions:
            st.markdown(f"**📋 {len(filtered_decisions)} Decisions for Review:**")
            
            # Create approval grid
            for i in range(0, len(filtered_decisions), 2):
                col1, col2 = st.columns(2)
                
                with col1:
                    if i < len(filtered_decisions):
                        self._render_quick_approval_card(filtered_decisions[i])
                
                with col2:
                    if i + 1 < len(filtered_decisions):
                        self._render_quick_approval_card(filtered_decisions[i + 1])
        else:
            st.info(f"No {selected_priority} priority decisions found.")
    
    def _render_quick_approval_card(self, decision: Dict[str, Any]):
        """Render compact approval card for quick decisions"""
        decision_id = decision.get('id')
        title = decision.get('title', 'Untitled')
        cost_impact = decision.get('cost_impact', 0)
        priority = decision.get('priority', 'medium')
        
        priority_emoji = {
            'critical': '🚨',
            'high': '⚠️',
            'medium': '📋',
            'low': '📝'
        }.get(priority, '📋')
        
        with st.container():
            st.markdown(f"""
            <div class="modern-card" style="padding: 1rem;">
                <div style="margin-bottom: 0.5rem;">
                    <strong>{priority_emoji} {title}</strong>
                </div>
                <div style="font-size: 0.875rem; color: var(--text-secondary); margin-bottom: 1rem;">
                    Cost: ${cost_impact:,.2f} | Priority: {priority.title()}
                </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅", key=f"quick_approve_{decision_id}", help="Quick approve"):
                    self._process_approval(decision_id, "approved", "Quick approval")
                    st.rerun()
            
            with col2:
                if st.button("❌", key=f"quick_reject_{decision_id}", help="Quick reject"):
                    self._process_approval(decision_id, "rejected", "Quick rejection")
                    st.rerun()
            
            st.markdown("</div>", unsafe_allow_html=True)
    
    def _render_decision_history_tab(self):
        """Render decision history and audit trail"""
        st.markdown("### 📊 Decision History & Audit Trail")
        
        # History filters
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            date_range = st.selectbox(
                "Time Range:",
                ["Last 7 days", "Last 30 days", "Last 90 days", "All time"],
                key="history_date_range"
            )
        
        with col2:
            status_filter = st.selectbox(
                "Status:",
                ["All", "Approved", "Rejected", "Executed", "Cancelled"],
                key="history_status_filter"
            )
        
        with col3:
            priority_filter = st.selectbox(
                "Priority:",
                ["All", "Critical", "High", "Medium", "Low"],
                key="history_priority_filter"
            )
        
        with col4:
            if st.button("📥 Export History", help="Export decision history as CSV"):
                self._export_decision_history()
        
        # Get filtered history
        history = self._get_filtered_history(date_range, status_filter, priority_filter)
        
        if not history:
            st.info("No decision history found for the selected filters.")
            return
        
        # History summary
        self._render_history_summary(history)
        
        # Audit trail visualization
        self._render_audit_trail_section(history)
        
        # History table with enhanced details
        self._render_enhanced_history_table(history)
        
        # History timeline chart
        self._render_history_timeline(history)
    
    def _render_audit_trail_section(self, history: List[Dict[str, Any]]):
        """Render detailed audit trail section"""
        st.markdown("#### 🔍 Detailed Audit Trail")
        
        if not history:
            st.info("No audit trail data available.")
            return
        
        # Select decision for detailed audit trail
        decision_options = {f"{h['id']} - {h['title']}": h['id'] for h in history}
        
        if decision_options:
            selected_decision_key = st.selectbox(
                "Select decision for detailed audit trail:",
                list(decision_options.keys()),
                key="audit_trail_decision"
            )
            
            if selected_decision_key:
                selected_decision_id = decision_options[selected_decision_key]
                selected_decision = next((h for h in history if h['id'] == selected_decision_id), None)
                
                if selected_decision:
                    self._render_decision_audit_trail(selected_decision)
    
    def _render_decision_audit_trail(self, decision: Dict[str, Any]):
        """Render audit trail for a specific decision"""
        with st.container():
            st.markdown(f"**Audit Trail for Decision: {decision['title']}**")
            
            # Decision timeline
            timeline_events = []
            
            # Creation event
            timeline_events.append({
                'timestamp': decision['created_at'],
                'event': 'Decision Created',
                'actor': decision.get('created_by', 'System'),
                'details': f"Initial cost impact: ${decision['cost_impact']:,.2f}"
            })
            
            # Approval responses
            approval_responses = decision.get('approval_responses', [])
            for response in approval_responses:
                timestamp = datetime.fromisoformat(response['timestamp']) if isinstance(response['timestamp'], str) else response['timestamp']
                timeline_events.append({
                    'timestamp': timestamp,
                    'event': f"Approval Response: {response['decision'].title()}",
                    'actor': response['approver'],
                    'details': response.get('comments', 'No comments provided')
                })
            
            # Status changes
            if decision.get('approved_at'):
                timeline_events.append({
                    'timestamp': decision['approved_at'],
                    'event': 'Decision Approved',
                    'actor': 'System',
                    'details': 'All required approvals received'
                })
            
            # Sort by timestamp
            timeline_events.sort(key=lambda x: x['timestamp'])
            
            # Render timeline
            for i, event in enumerate(timeline_events):
                col1, col2 = st.columns([1, 4])
                
                with col1:
                    st.markdown(f"**{event['timestamp'].strftime('%Y-%m-%d %H:%M')}**")
                
                with col2:
                    st.markdown(f"**{event['event']}** by {event['actor']}")
                    if event['details']:
                        st.markdown(f"*{event['details']}*")
                
                if i < len(timeline_events) - 1:
                    st.markdown("---")
    
    def _render_enhanced_history_table(self, history: List[Dict[str, Any]]):
        """Render enhanced history table with more details"""
        if not history:
            return
        
        # Create enhanced dataframe
        enhanced_data = []
        for h in history:
            approval_summary = h.get('approval_summary', {})
            enhanced_data.append({
                'ID': h.get('id', ''),
                'Title': h.get('title', ''),
                'Priority': h.get('priority', '').title(),
                'Status': h.get('status', '').title(),
                'Cost Impact': h.get('cost_impact', 0),
                'Approvers': len(h.get('required_approvers', [])),
                'Responses': len(h.get('approval_responses', [])),
                'Approval Rate': f"{(approval_summary.get('approved', 0) / max(approval_summary.get('total_required', 1), 1) * 100):.0f}%",
                'Created': h.get('created_at', datetime.now()).strftime('%Y-%m-%d %H:%M'),
                'Completed': h.get('approved_at', datetime.now()).strftime('%Y-%m-%d %H:%M') if h.get('approved_at') else 'N/A'
            })
        
        df = pd.DataFrame(enhanced_data)
        
        # Render with enhanced styling
        st.markdown("#### 📋 Decision History Table")
        self.dashboard.render_interactive_data_table(df, "Enhanced Decision History")
    
    def _render_history_summary(self, history: List[Dict[str, Any]]):
        """Render history summary metrics"""
        total_decisions = len(history)
        approved = len([h for h in history if h.get('status') == 'approved'])
        rejected = len([h for h in history if h.get('status') == 'rejected'])
        approval_rate = (approved / total_decisions * 100) if total_decisions > 0 else 0
        
        metrics = [
            {
                'label': 'Total Decisions',
                'value': str(total_decisions),
                'icon': '📋'
            },
            {
                'label': 'Approval Rate',
                'value': f"{approval_rate:.1f}%",
                'icon': '✅',
                'color': 'success' if approval_rate > 70 else 'warning'
            },
            {
                'label': 'Approved',
                'value': str(approved),
                'icon': '✅',
                'color': 'success'
            },
            {
                'label': 'Rejected',
                'value': str(rejected),
                'icon': '❌',
                'color': 'error'
            }
        ]
        
        self.dashboard.render_modern_metrics_grid(metrics)
    
    def _render_history_timeline(self, history: List[Dict[str, Any]]):
        """Render decision history timeline chart"""
        if not history:
            return
        
        # Prepare timeline data
        df = pd.DataFrame(history)
        df['date'] = pd.to_datetime(df['created_at'])
        df['date_only'] = df['date'].dt.date
        
        # Group by date and status
        timeline_data = df.groupby(['date_only', 'status']).size().unstack(fill_value=0)
        
        def render_timeline_chart():
            fig = go.Figure()
            
            colors = {'approved': '#10b981', 'rejected': '#ef4444', 'pending': '#f59e0b'}
            
            for status in timeline_data.columns:
                fig.add_trace(go.Scatter(
                    x=timeline_data.index,
                    y=timeline_data[status],
                    mode='lines+markers',
                    name=status.title(),
                    line=dict(color=colors.get(status, '#3b82f6'), width=2),
                    marker=dict(size=6)
                ))
            
            fig.update_layout(
                title="Decision Timeline",
                xaxis_title="Date",
                yaxis_title="Number of Decisions",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        self.dashboard.render_modern_chart_container(
            "Decision Timeline",
            render_timeline_chart,
            "📈"
        )
    
    def _render_decision_analytics_tab(self):
        """Render decision analytics and insights"""
        st.markdown("### 📈 Decision Analytics & Insights")
        
        # Analytics overview
        all_decisions = st.session_state.decisions + st.session_state.decision_history
        
        if not all_decisions:
            st.info("No decision data available for analytics.")
            return
        
        # Key insights
        self._render_decision_insights(all_decisions)
        
        # Analytics charts
        col1, col2 = st.columns(2)
        
        with col1:
            self._render_priority_distribution_chart(all_decisions)
        
        with col2:
            self._render_cost_impact_analysis(all_decisions)
        
        # Approval patterns
        self._render_approval_patterns(all_decisions)
    
    def _render_decision_insights(self, decisions: List[Dict[str, Any]]):
        """Render key decision insights"""
        # Calculate insights
        total_cost_impact = sum(d.get('cost_impact', 0) for d in decisions)
        avg_approval_time = self._calculate_avg_approval_time(decisions)
        most_common_priority = self._get_most_common_priority(decisions)
        
        insights = [
            f"💰 Total cost impact of all decisions: ${total_cost_impact:,.2f}",
            f"⏱️ Average approval time: {avg_approval_time:.1f} hours",
            f"📊 Most common priority level: {most_common_priority.title()}",
            f"📈 Decision volume trend: {'Increasing' if len(decisions) > 10 else 'Stable'}"
        ]
        
        self.dashboard.render_status_card(
            "Key Insights",
            "healthy",
            insights,
            "💡"
        )
    
    def _render_priority_distribution_chart(self, decisions: List[Dict[str, Any]]):
        """Render priority distribution pie chart"""
        priority_counts = {}
        for decision in decisions:
            priority = decision.get('priority', 'medium')
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        def render_priority_chart():
            if priority_counts:
                fig = self.dashboard.create_modern_chart(
                    'pie',
                    {
                        'labels': list(priority_counts.keys()),
                        'values': list(priority_counts.values()),
                        'name': 'Priority Distribution'
                    }
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No priority data available")
        
        self.dashboard.render_modern_chart_container(
            "Priority Distribution",
            render_priority_chart,
            "📊"
        )
    
    def _render_cost_impact_analysis(self, decisions: List[Dict[str, Any]]):
        """Render cost impact analysis chart"""
        cost_ranges = {'$0-100': 0, '$100-1K': 0, '$1K-10K': 0, '$10K+': 0}
        
        for decision in decisions:
            cost = decision.get('cost_impact', 0)
            if cost <= 100:
                cost_ranges['$0-100'] += 1
            elif cost <= 1000:
                cost_ranges['$100-1K'] += 1
            elif cost <= 10000:
                cost_ranges['$1K-10K'] += 1
            else:
                cost_ranges['$10K+'] += 1
        
        def render_cost_chart():
            if any(cost_ranges.values()):
                fig = self.dashboard.create_modern_chart(
                    'bar',
                    {
                        'x': list(cost_ranges.keys()),
                        'y': list(cost_ranges.values()),
                        'name': 'Cost Impact Distribution'
                    }
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No cost impact data available")
        
        self.dashboard.render_modern_chart_container(
            "Cost Impact Distribution",
            render_cost_chart,
            "💰"
        )
    
    def _render_approval_patterns(self, decisions: List[Dict[str, Any]]):
        """Render approval patterns analysis"""
        approved_decisions = [d for d in decisions if d.get('status') == 'approved']
        
        if not approved_decisions:
            st.info("No approved decisions available for pattern analysis.")
            return
        
        # Approval time by priority
        approval_times = {}
        for decision in approved_decisions:
            priority = decision.get('priority', 'medium')
            approval_time = decision.get('approval_time', 0)
            if priority not in approval_times:
                approval_times[priority] = []
            approval_times[priority].append(approval_time)
        
        # Calculate averages
        avg_times = {p: sum(times)/len(times) for p, times in approval_times.items() if times}
        
        def render_approval_patterns_chart():
            if avg_times:
                fig = self.dashboard.create_modern_chart(
                    'bar',
                    {
                        'x': list(avg_times.keys()),
                        'y': list(avg_times.values()),
                        'name': 'Average Approval Time by Priority'
                    }
                )
                fig.update_layout(yaxis_title="Hours")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No approval time data available")
        
        self.dashboard.render_modern_chart_container(
            "Approval Time by Priority",
            render_approval_patterns_chart,
            "⏱️"
        )
    
    # Helper methods
    def _refresh_decision_data(self):
        """Refresh decision data from real-time service"""
        try:
            # Get active decisions from real-time service
            active_decisions = self.real_time_service.get_active_decisions()
            decision_history = self.real_time_service.get_decision_history()
            
            # Convert to session state format
            st.session_state.decisions = [self._convert_decision_to_dict(d) for d in active_decisions]
            st.session_state.decision_history = [self._convert_decision_to_dict(d) for d in decision_history]
            
            # If no data, create demo data
            if not st.session_state.decisions and not st.session_state.decision_history:
                demo_decisions = self.real_time_service.create_demo_decisions()
                st.session_state.decisions = [self._convert_decision_to_dict(d) for d in demo_decisions]
            
            st.session_state.last_update_time = datetime.now()
            
        except Exception as e:
            st.error(f"Error refreshing decision data: {e}")
    
    def _convert_decision_to_dict(self, decision: DecisionProposal) -> Dict[str, Any]:
        """Convert DecisionProposal to dictionary for session state"""
        return {
            'id': decision.proposal_id,
            'title': decision.title,
            'description': decision.description,
            'priority': decision.risk_level.value,
            'cost_impact': decision.estimated_cost_impact,
            'risk_level': decision.risk_level.value,
            'status': decision.status.value,
            'created_at': decision.created_at,
            'deadline': decision.approval_deadline,
            'affected_resources': decision.metadata.get('affected_resources', []),
            'recommendations': decision.recommendations,
            'required_approvers': decision.required_approvers,
            'approval_responses': decision.approval_responses,
            'approval_time': self._calculate_approval_time(decision),
            'created_today': decision.created_at.date() == datetime.now().date(),
            'impact_analysis': {
                'monthly_impact': decision.estimated_cost_impact,
                'annual_impact': decision.estimated_cost_impact * 12,
                'operational_impact': decision.metadata.get('operational_impact', [])
            }
        }
    
    def _calculate_approval_time(self, decision: DecisionProposal) -> float:
        """Calculate approval time in hours"""
        if not decision.approval_responses:
            return 0.0
        
        approved_responses = [r for r in decision.approval_responses if r['decision'] == 'approved']
        if not approved_responses:
            return 0.0
        
        # Get the first approval time
        first_approval = min(
            datetime.fromisoformat(r['timestamp']) for r in approved_responses
        )
        
        return (first_approval - decision.created_at).total_seconds() / 3600
    
    def _check_connection_status(self) -> bool:
        """Check connection status to backend services"""
        # In production, this would check actual service connectivity
        return True
    
    def _create_demo_decision(self):
        """Create a demo decision for testing"""
        demo_decision = {
            'id': f"DEC-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'title': 'Optimize EC2 Instance Types',
            'description': 'AI recommends switching from t3.large to t3.medium instances to reduce costs',
            'priority': 'medium',
            'cost_impact': 245.50,
            'risk_level': 'low',
            'status': 'pending',
            'created_at': datetime.now(),
            'deadline': datetime.now() + timedelta(days=3),
            'affected_resources': ['i-1234567890abcdef0', 'i-0987654321fedcba0'],
            'recommendations': [
                'Switch to t3.medium instances during low-traffic hours',
                'Monitor performance for 48 hours after change',
                'Set up CloudWatch alarms for performance metrics'
            ],
            'impact_analysis': {
                'monthly_impact': 245.50,
                'annual_impact': 2946.00,
                'operational_impact': ['Minimal performance impact expected', 'No downtime required']
            },
            'created_today': True
        }
        
        st.session_state.decisions.append(demo_decision)
    
    def _create_demo_decisions(self):
        """Create multiple demo decisions for testing"""
        demo_decisions = [
            {
                'id': 'DEC-001',
                'title': 'Terminate Unused EBS Volumes',
                'description': 'Remove 5 unattached EBS volumes to reduce storage costs',
                'priority': 'low',
                'cost_impact': 125.00,
                'risk_level': 'low',
                'status': 'pending',
                'created_at': datetime.now() - timedelta(hours=2),
                'deadline': datetime.now() + timedelta(days=7),
                'affected_resources': ['vol-1', 'vol-2', 'vol-3', 'vol-4', 'vol-5'],
                'created_today': True
            },
            {
                'id': 'DEC-002',
                'title': 'Scale Down RDS Instance',
                'description': 'Downgrade RDS instance from db.t3.large to db.t3.medium',
                'priority': 'high',
                'cost_impact': 450.00,
                'risk_level': 'medium',
                'status': 'pending',
                'created_at': datetime.now() - timedelta(hours=1),
                'deadline': datetime.now() + timedelta(days=2),
                'affected_resources': ['db-prod-mysql'],
                'created_today': True
            }
        ]
        
        st.session_state.decisions.extend(demo_decisions)
    
    def _process_approval(self, decision_id: str, status: str, comments: str):
        """Process approval decision"""
        try:
            # Get current user (in production, this would come from authentication)
            current_user = st.session_state.get('current_user', 'finops_lead')
            
            # Process approval through real-time service
            success = asyncio.run(
                self.real_time_service.process_approval(
                    decision_id, current_user, status, comments
                )
            )
            
            if success:
                # Refresh local data
                self._refresh_decision_data()
                
                # Show success message
                if status == 'approved':
                    st.success(f"✅ Decision {decision_id} approved successfully!")
                else:
                    st.warning(f"❌ Decision {decision_id} rejected.")
            else:
                st.error(f"Failed to process approval for decision {decision_id}")
                
        except Exception as e:
            st.error(f"Error processing approval: {e}")
    
    def _process_detailed_approval(self, decision_id: str, status: str, comments: str, conditions: List[str]):
        """Process detailed approval with conditions"""
        try:
            # Add conditions to comments if provided
            full_comments = comments
            if conditions:
                condition_text = "\n\nConditions:\n" + "\n".join(f"- {c}" for c in conditions)
                full_comments = (comments or "") + condition_text
            
            # Process through real-time service
            self._process_approval(decision_id, status, full_comments)
            
            # Store additional approval details
            approval_key = f"approval_{decision_id}"
            st.session_state.approval_responses[approval_key] = {
                'decision_id': decision_id,
                'status': status,
                'comments': comments,
                'conditions': conditions,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            st.error(f"Error processing detailed approval: {e}")
    
    def _send_approval_email(self, decision: Dict[str, Any]):
        """Send approval email (simulated)"""
        # In production, this would integrate with email service
        pass
    
    def _get_filtered_history(self, date_range: str, status_filter: str, priority_filter: str = "All") -> List[Dict[str, Any]]:
        """Get filtered decision history"""
        history = st.session_state.decision_history.copy()
        
        # Apply date filter
        if date_range != "All time":
            days_map = {"Last 7 days": 7, "Last 30 days": 30, "Last 90 days": 90}
            days = days_map.get(date_range, 30)
            cutoff_date = datetime.now() - timedelta(days=days)
            history = [h for h in history if h.get('created_at', datetime.now()) >= cutoff_date]
        
        # Apply status filter
        if status_filter != "All":
            history = [h for h in history if h.get('status', '').lower() == status_filter.lower()]
        
        # Apply priority filter
        if priority_filter != "All":
            history = [h for h in history if h.get('priority', '').lower() == priority_filter.lower()]
        
        return history
    
    def _format_history_dataframe(self, history: List[Dict[str, Any]]) -> pd.DataFrame:
        """Format history data as DataFrame"""
        if not history:
            return pd.DataFrame()
        
        data = []
        for h in history:
            data.append({
                'ID': h.get('id', ''),
                'Title': h.get('title', ''),
                'Priority': h.get('priority', '').title(),
                'Status': h.get('status', '').title(),
                'Cost Impact': h.get('cost_impact', 0),
                'Created': h.get('created_at', datetime.now()).strftime('%Y-%m-%d %H:%M'),
                'Approved': h.get('approved_at', datetime.now()).strftime('%Y-%m-%d %H:%M') if h.get('approved_at') else 'N/A'
            })
        
        return pd.DataFrame(data)
    
    def _export_decision_history(self):
        """Export decision history as CSV"""
        history = st.session_state.decision_history
        if not history:
            st.warning("No history data to export")
            return
        
        df = self._format_history_dataframe(history)
        csv = df.to_csv(index=False)
        
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"decision_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    def _calculate_avg_approval_time(self, decisions: List[Dict[str, Any]]) -> float:
        """Calculate average approval time"""
        approved_decisions = [d for d in decisions if d.get('approval_time')]
        if not approved_decisions:
            return 0.0
        
        total_time = sum(d.get('approval_time', 0) for d in approved_decisions)
        return total_time / len(approved_decisions)
    
    def _get_most_common_priority(self, decisions: List[Dict[str, Any]]) -> str:
        """Get most common priority level"""
        priorities = [d.get('priority', 'medium') for d in decisions]
        if not priorities:
            return 'medium'
        
        priority_counts = {}
        for priority in priorities:
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        return max(priority_counts, key=priority_counts.get)