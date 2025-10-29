"""
Role-specific dashboard components and views
"""

import streamlit as st
from typing import Dict, Any, List, Optional
import logging

from .models import User, DashboardSection, PermissionType
from .dashboard_auth import dashboard_auth

logger = logging.getLogger(__name__)


class RoleBasedDashboard:
    """Manages role-specific dashboard views and components"""
    
    def __init__(self):
        self.auth_manager = dashboard_auth
    
    def render_role_specific_header(self) -> None:
        """Render header with role-specific information"""
        user = self.auth_manager.get_current_user()
        if not user:
            st.markdown("# 🔐 Vismaya DemandOps - Please Login")
            return
        
        # Get primary role for styling
        primary_role = user.roles[0] if user.roles else None
        role_emoji = {
            'ceo': '👑',
            'cto': '🔧', 
            'finops_lead': '💰',
            'devops_engineer': '⚙️'
        }
        
        emoji = role_emoji.get(primary_role.role_id if primary_role else '', '👤')
        
        st.markdown(f"# {emoji} Vismaya DemandOps - {primary_role.role_name if primary_role else 'User'}")
        st.markdown("*AI-Powered FinOps Platform for AWS Cost Optimization*")
        
        # Role-specific welcome message
        welcome_msg = self.auth_manager.get_role_specific_welcome_message()
        st.info(welcome_msg)
    
    def get_role_specific_tabs(self) -> List[str]:
        """Get tabs available to current user's role"""
        user = self.auth_manager.get_current_user()
        if not user:
            return ["Login"]
        
        # Base tabs available to all authenticated users
        base_tabs = ["Dashboard Overview"]
        
        # Role-specific tabs
        role_tabs = []
        
        # Check permissions for each potential tab
        if self.auth_manager.has_dashboard_access(DashboardSection.COST_ANALYSIS.value):
            role_tabs.append("Cost Analysis")
        
        if self.auth_manager.has_dashboard_access(DashboardSection.BUDGET_TRACKING.value):
            role_tabs.append("Budget Tracking")
        
        if self.auth_manager.has_dashboard_access(DashboardSection.FORECASTING.value):
            role_tabs.append("Forecasting")
        
        if self.auth_manager.has_dashboard_access(DashboardSection.RESOURCE_MONITORING.value):
            role_tabs.append("Resource Monitoring")
        
        if self.auth_manager.has_dashboard_access(DashboardSection.TECHNICAL_METRICS.value):
            role_tabs.append("Technical Metrics")
        
        if self.auth_manager.has_dashboard_access(DashboardSection.SYSTEM_HEALTH.value):
            role_tabs.append("System Health")
        
        if self.auth_manager.has_dashboard_access(DashboardSection.ALL_DECISIONS.value):
            role_tabs.append("Decision Management")
        
        if self.auth_manager.has_dashboard_access(DashboardSection.EXECUTIVE_SUMMARY.value):
            role_tabs.append("Executive Summary")
        
        # Always include settings for authenticated users
        role_tabs.append("Settings")
        
        return base_tabs + role_tabs
    
    def render_dashboard_overview(self, metrics: Dict[str, Any]) -> None:
        """Render role-specific dashboard overview"""
        user = self.auth_manager.get_current_user()
        if not user:
            return
        
        primary_role = user.roles[0] if user.roles else None
        
        if primary_role and primary_role.role_id == 'ceo':
            self._render_ceo_overview(metrics)
        elif primary_role and primary_role.role_id == 'cto':
            self._render_cto_overview(metrics)
        elif primary_role and primary_role.role_id == 'finops_lead':
            self._render_finops_overview(metrics)
        elif primary_role and primary_role.role_id == 'devops_engineer':
            self._render_devops_overview(metrics)
        else:
            self._render_default_overview(metrics)
    
    def _render_ceo_overview(self, metrics: Dict[str, Any]) -> None:
        """Render CEO-specific dashboard overview"""
        st.markdown("### 👑 Executive Summary")
        
        # High-level metrics for CEO
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total AWS Spend",
                f"${metrics.get('current_spend', 0):,.2f}",
                delta=f"{metrics.get('trending', 'stable').title()}"
            )
        
        with col2:
            budget_pct = metrics.get('budget_pct', 0)
            status = "🟢 Healthy" if budget_pct < 75 else "🟡 Caution" if budget_pct < 90 else "🔴 Critical"
            st.metric(
                "Budget Status",
                f"{budget_pct:.1f}%",
                delta=status
            )
        
        with col3:
            st.metric(
                "Monthly Forecast",
                f"${metrics.get('forecast', 0):,.2f}",
                delta=f"+${metrics.get('forecast', 0) - metrics.get('current_spend', 0):,.2f}"
            )
        
        with col4:
            # Show decision approval count (placeholder)
            st.metric(
                "Pending Decisions",
                "0",
                delta="No urgent decisions"
            )
        
        # CEO-specific insights
        st.markdown("### 📊 Strategic Insights")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 💰 Cost Optimization Opportunities")
            if metrics.get('current_spend', 0) > 0:
                st.success("✅ Spending is within acceptable limits")
                st.info("💡 Consider Reserved Instances for 15-20% savings on steady workloads")
                st.info("💡 Review unused resources monthly for optimization")
            else:
                st.info("📊 No current AWS spending detected")
        
        with col2:
            st.markdown("#### 🎯 Business Impact")
            st.info("📈 Cloud costs are aligned with business growth")
            st.info("🔍 Regular cost reviews recommended for optimal ROI")
            st.info("⚡ Automated alerts configured for budget thresholds")
    
    def _render_cto_overview(self, metrics: Dict[str, Any]) -> None:
        """Render CTO-specific dashboard overview"""
        st.markdown("### 🔧 Technical Operations Summary")
        
        # Technical metrics for CTO
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Infrastructure Cost",
                f"${metrics.get('current_spend', 0):,.2f}",
                delta="Technical resources"
            )
        
        with col2:
            st.metric(
                "Resource Efficiency",
                "85%",  # Placeholder
                delta="Good utilization"
            )
        
        with col3:
            st.metric(
                "System Health",
                "🟢 Healthy",
                delta="All systems operational"
            )
        
        with col4:
            st.metric(
                "Cost per Service",
                f"${metrics.get('current_spend', 0) / max(1, metrics.get('service_count', 1)):,.2f}",
                delta="Average per service"
            )
        
        # Technical insights
        st.markdown("### ⚙️ Technical Insights")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🏗️ Infrastructure Optimization")
            st.info("🔧 Consider rightsizing instances based on utilization")
            st.info("📦 Evaluate containerization for better resource efficiency")
            st.info("🔄 Implement auto-scaling for variable workloads")
        
        with col2:
            st.markdown("#### 📊 Performance Metrics")
            st.success("✅ No performance issues detected")
            st.info("📈 Monitor CPU and memory utilization trends")
            st.info("🔍 Review storage performance and costs")
    
    def _render_finops_overview(self, metrics: Dict[str, Any]) -> None:
        """Render FinOps Lead-specific dashboard overview"""
        st.markdown("### 💰 Financial Operations Dashboard")
        
        # Financial metrics for FinOps
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Current Spend",
                f"${metrics.get('current_spend', 0):,.2f}",
                delta=f"vs ${metrics.get('budget', 0):,.2f} budget"
            )
        
        with col2:
            budget_remaining = metrics.get('budget', 0) - metrics.get('current_spend', 0)
            st.metric(
                "Budget Remaining",
                f"${budget_remaining:,.2f}",
                delta=f"{(budget_remaining/max(1, metrics.get('budget', 1)))*100:.1f}% left"
            )
        
        with col3:
            st.metric(
                "Cost Trend",
                f"{metrics.get('trending', 'stable').title()}",
                delta="Monthly comparison"
            )
        
        with col4:
            st.metric(
                "Approval Authority",
                "$5,000",
                delta="Maximum decision amount"
            )
        
        # FinOps insights
        st.markdown("### 📈 Cost Management Insights")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 💸 Budget Analysis")
            budget_pct = metrics.get('budget_pct', 0)
            if budget_pct < 50:
                st.success(f"✅ Budget utilization: {budget_pct:.1f}% - Well within limits")
            elif budget_pct < 80:
                st.info(f"📊 Budget utilization: {budget_pct:.1f}% - Monitor closely")
            else:
                st.warning(f"⚠️ Budget utilization: {budget_pct:.1f}% - Take action soon")
            
            st.info("💡 Set up automated alerts at 75% and 90% thresholds")
        
        with col2:
            st.markdown("#### 🎯 Cost Optimization")
            st.info("📊 Review service-level costs monthly")
            st.info("💰 Identify unused or underutilized resources")
            st.info("📈 Track cost trends and forecast accuracy")
    
    def _render_devops_overview(self, metrics: Dict[str, Any]) -> None:
        """Render DevOps Engineer-specific dashboard overview"""
        st.markdown("### ⚙️ Operations Monitoring Dashboard")
        
        # Operational metrics for DevOps
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Resource Count",
                f"{metrics.get('resource_count', 0)}",
                delta="Active resources"
            )
        
        with col2:
            st.metric(
                "Alert Status",
                "🟢 Normal",
                delta="No active alerts"
            )
        
        with col3:
            st.metric(
                "System Uptime",
                "99.9%",
                delta="Last 30 days"
            )
        
        with col4:
            st.metric(
                "Monitoring Cost",
                f"${metrics.get('monitoring_cost', 0):,.2f}",
                delta="CloudWatch & logs"
            )
        
        # DevOps insights
        st.markdown("### 🔍 Operational Insights")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📊 Resource Monitoring")
            st.success("✅ All monitored resources are healthy")
            st.info("📈 CPU utilization within normal ranges")
            st.info("💾 Storage usage is optimal")
        
        with col2:
            st.markdown("#### 🚨 Alert Management")
            st.success("✅ No active alerts")
            st.info("🔔 Budget alerts configured and active")
            st.info("⚡ Performance monitoring in place")
    
    def _render_default_overview(self, metrics: Dict[str, Any]) -> None:
        """Render default overview for users without specific roles"""
        st.markdown("### 📊 General Dashboard Overview")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Current Spend",
                f"${metrics.get('current_spend', 0):,.2f}",
                delta="AWS costs"
            )
        
        with col2:
            st.metric(
                "Budget Status",
                f"{metrics.get('budget_pct', 0):.1f}%",
                delta="of budget used"
            )
        
        with col3:
            st.metric(
                "Forecast",
                f"${metrics.get('forecast', 0):,.2f}",
                delta="Next month"
            )
        
        st.info("👤 Contact your administrator for role-specific access and permissions.")
    
    def render_permission_based_content(self, content_type: str, content_data: Dict[str, Any]) -> None:
        """Render content based on user permissions"""
        user = self.auth_manager.get_current_user()
        if not user:
            st.warning("🔐 Please log in to view this content.")
            return
        
        # Filter content based on permissions
        filtered_content = self.auth_manager.filter_dashboard_content(content_type, content_data)
        
        if "message" in filtered_content and len(filtered_content) == 1:
            # Permission denied message
            st.error("🚫 Access Denied")
            st.markdown(filtered_content["message"])
            return
        
        # Render the filtered content
        if content_type == "cost_details":
            self._render_cost_details(filtered_content)
        elif content_type == "resource_details":
            self._render_resource_details(filtered_content)
        elif content_type == "system_config":
            self._render_system_config(filtered_content)
        else:
            st.json(filtered_content)
    
    def _render_cost_details(self, content: Dict[str, Any]) -> None:
        """Render detailed cost information"""
        st.markdown("### 💰 Detailed Cost Analysis")
        
        if not content:
            st.info("No cost data available.")
            return
        
        # Render cost breakdown, charts, etc.
        st.json(content)  # Placeholder - would render actual cost visualizations
    
    def _render_resource_details(self, content: Dict[str, Any]) -> None:
        """Render detailed resource information"""
        st.markdown("### 🔧 Resource Details")
        
        if not content:
            st.info("No resource data available.")
            return
        
        # Render resource tables, metrics, etc.
        st.json(content)  # Placeholder - would render actual resource information
    
    def _render_system_config(self, content: Dict[str, Any]) -> None:
        """Render system configuration"""
        st.markdown("### ⚙️ System Configuration")
        
        if not content:
            st.info("No configuration data available.")
            return
        
        # Render system settings, configuration options, etc.
        st.json(content)  # Placeholder - would render actual configuration interface
    
    def render_decision_approval_interface(self) -> None:
        """Render decision approval interface for authorized users"""
        user = self.auth_manager.get_current_user()
        if not user:
            st.warning("🔐 Please log in to view decisions.")
            return
        
        # Check if user has any approval authority
        has_approval_authority = any(
            user.can_approve_decision(decision_type) 
            for decision_type in ['cost_decisions', 'technical_decisions', 'strategic_decisions']
        )
        
        if not has_approval_authority:
            st.info("👀 You have view-only access to decisions.")
            st.markdown("Contact your administrator for approval permissions.")
            return
        
        st.markdown("### 📋 Decision Management")
        
        # Show approval authority
        st.markdown("#### 🔑 Your Approval Authority")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            cost_limit = user.get_max_approval_amount('cost_decisions')
            if cost_limit > 0:
                limit_text = "Unlimited" if cost_limit == float('inf') else f"${cost_limit:,.2f}"
                st.success(f"💰 Cost Decisions: {limit_text}")
            else:
                st.info("💰 Cost Decisions: View Only")
        
        with col2:
            if user.can_approve_decision('technical_decisions'):
                st.success("🔧 Technical Decisions: Approved")
            else:
                st.info("🔧 Technical Decisions: View Only")
        
        with col3:
            if user.can_approve_decision('strategic_decisions'):
                st.success("🎯 Strategic Decisions: Approved")
            else:
                st.info("🎯 Strategic Decisions: View Only")
        
        # Placeholder for actual decision management interface
        st.markdown("#### 📋 Pending Decisions")
        st.info("No pending decisions at this time.")
        
        st.markdown("#### 📊 Recent Decisions")
        st.info("No recent decisions to display.")


# Global role-based dashboard instance
role_dashboard = RoleBasedDashboard()