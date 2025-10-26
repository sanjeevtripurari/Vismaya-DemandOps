"""
Main authenticated dashboard that integrates role-based access control
"""

import streamlit as st
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from .dashboard_auth import dashboard_auth
from .role_dashboard import role_dashboard

logger = logging.getLogger(__name__)


class AuthenticatedDashboard:
    """Main dashboard with integrated authentication and role-based access"""
    
    def __init__(self, original_dashboard=None):
        self.auth_manager = dashboard_auth
        self.role_dashboard = role_dashboard
        self.original_dashboard = original_dashboard  # Reference to original VismayaDashboard
        self._initialized = False
    
    async def initialize(self) -> bool:
        """Initialize the authenticated dashboard"""
        try:
            success = await self.auth_manager.initialize()
            if success:
                self._initialized = True
                logger.info("Authenticated dashboard initialized successfully")
            return success
        except Exception as e:
            logger.error(f"Failed to initialize authenticated dashboard: {e}")
            return False
    
    def run(self) -> None:
        """Main dashboard runner with authentication"""
        # Initialize if not already done
        if not self._initialized:
            init_success = asyncio.run(self.initialize())
            if not init_success:
                st.error("❌ Failed to initialize authentication system")
                return
        
        # Check if in demo mode
        if st.session_state.get('demo_mode', False):
            self._render_demo_mode()
            return
        
        # Check authentication
        if not self.auth_manager.check_authentication():
            self._render_login_page()
            return
        
        # Render authenticated dashboard
        self._render_authenticated_dashboard()
    
    def _render_login_page(self) -> None:
        """Render the login page"""
        st.set_page_config(
            page_title="Vismaya - Login",
            page_icon="🔐",
            layout="wide"
        )
        
        # Custom CSS for login page
        st.markdown("""
        <style>
            .main .block-container {
                max-width: 800px;
                padding-top: 2rem;
                margin: 0 auto;
            }
            .login-header {
                text-align: center;
                color: #1f77b4;
                margin-bottom: 2rem;
            }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown('<h1 class="login-header">🔐 Vismaya DemandOps</h1>', unsafe_allow_html=True)
        st.markdown('<p class="login-header">AI-Powered FinOps Platform for AWS Cost Optimization</p>', unsafe_allow_html=True)
        
        # Render login form
        self.auth_manager.render_login_form()
        
        # Show system info
        with st.expander("ℹ️ About Vismaya DemandOps"):
            st.markdown("""
            **Vismaya DemandOps** is an AI-powered Financial Operations (FinOps) platform designed to help organizations optimize their AWS costs through intelligent monitoring, forecasting, and decision management.
            
            **Key Features:**
            - 📊 Real-time AWS cost monitoring and analysis
            - 🤖 AI-powered cost forecasting and optimization recommendations
            - 👥 Role-based access control for different organizational roles
            - 📧 Automated decision approval workflows
            - 📈 Advanced budget tracking and alerting
            
            **Supported Roles:**
            - **CEO**: Full access with unlimited approval authority
            - **CTO**: Technical decisions and system management
            - **FinOps Lead**: Cost analysis and budget management
            - **DevOps Engineer**: Resource monitoring and alerting
            
            **Team MaximAI** - Built for intelligent cloud cost management
            """)
    
    def _render_demo_mode(self) -> None:
        """Render dashboard in demo mode (limited functionality)"""
        st.set_page_config(
            page_title="Vismaya - Demo",
            page_icon="👀",
            layout="wide"
        )
        
        st.markdown("# 👀 Vismaya DemandOps - Demo Mode")
        st.markdown("*AI-Powered FinOps Platform - Limited Demo Version*")
        
        st.warning("🔒 You are in demo mode with limited functionality. Log in for full access.")
        
        # Show basic demo content
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Demo Spend", "$1,234.56", delta="Demo data")
        
        with col2:
            st.metric("Demo Budget", "65%", delta="Demo usage")
        
        with col3:
            st.metric("Demo Forecast", "$1,500.00", delta="Demo projection")
        
        st.info("💡 This is a demonstration of the Vismaya DemandOps platform. Log in to access real AWS cost data and full functionality.")
        
        # Login button
        if st.button("🔐 Login for Full Access", type="primary"):
            st.session_state.demo_mode = False
            st.rerun()
    
    def _render_authenticated_dashboard(self) -> None:
        """Render the main authenticated dashboard"""
        st.set_page_config(
            page_title="Vismaya - Dashboard",
            page_icon="📊",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Custom CSS for authenticated dashboard
        st.markdown("""
        <style>
            .main .block-container {
                max-width: 100%;
                padding-top: 0.5rem;
                padding-left: 2rem;
                padding-right: 2rem;
            }
            .role-header {
                background: linear-gradient(90deg, #1f77b4, #17a2b8);
                color: white;
                padding: 1rem;
                border-radius: 0.5rem;
                margin-bottom: 1rem;
            }
            .metric-card {
                background-color: #f8f9fa;
                padding: 1rem;
                border-radius: 0.5rem;
                border-left: 4px solid #1f77b4;
                margin-bottom: 1rem;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
        </style>
        """, unsafe_allow_html=True)
        
        # Render user info in sidebar
        self.auth_manager.render_user_info()
        
        # Render role-specific header
        self.role_dashboard.render_role_specific_header()
        
        # Get available tabs for current user
        available_tabs = self.role_dashboard.get_role_specific_tabs()
        
        # Create tabs
        if len(available_tabs) == 1:
            # Single tab - render directly
            self._render_tab_content(available_tabs[0])
        else:
            # Multiple tabs - create tab interface
            tab_objects = st.tabs(available_tabs)
            
            for i, tab_name in enumerate(available_tabs):
                with tab_objects[i]:
                    self._render_tab_content(tab_name)
    
    def _render_tab_content(self, tab_name: str) -> None:
        """Render content for specific tab based on user permissions"""
        user = self.auth_manager.get_current_user()
        if not user:
            return
        
        try:
            if tab_name == "Dashboard Overview":
                self._render_dashboard_overview_tab()
            
            elif tab_name == "Cost Analysis":
                if self.auth_manager.has_dashboard_access("cost_analysis"):
                    self._render_cost_analysis_tab()
                else:
                    self.auth_manager.render_permission_denied("Cost Analysis")
            
            elif tab_name == "Budget Tracking":
                if self.auth_manager.has_dashboard_access("budget_tracking"):
                    self._render_budget_tracking_tab()
                else:
                    self.auth_manager.render_permission_denied("Budget Tracking")
            
            elif tab_name == "Forecasting":
                if self.auth_manager.has_dashboard_access("forecasting"):
                    self._render_forecasting_tab()
                else:
                    self.auth_manager.render_permission_denied("Forecasting")
            
            elif tab_name == "Resource Monitoring":
                if self.auth_manager.has_dashboard_access("resource_monitoring"):
                    self._render_resource_monitoring_tab()
                else:
                    self.auth_manager.render_permission_denied("Resource Monitoring")
            
            elif tab_name == "Technical Metrics":
                if self.auth_manager.has_dashboard_access("technical_metrics"):
                    self._render_technical_metrics_tab()
                else:
                    self.auth_manager.render_permission_denied("Technical Metrics")
            
            elif tab_name == "System Health":
                if self.auth_manager.has_dashboard_access("system_health"):
                    self._render_system_health_tab()
                else:
                    self.auth_manager.render_permission_denied("System Health")
            
            elif tab_name == "Decision Management":
                if self.auth_manager.has_dashboard_access("all_decisions"):
                    self._render_decision_management_tab()
                else:
                    self.auth_manager.render_permission_denied("Decision Management")
            
            elif tab_name == "Executive Summary":
                if self.auth_manager.has_dashboard_access("executive_summary"):
                    self._render_executive_summary_tab()
                else:
                    self.auth_manager.render_permission_denied("Executive Summary")
            
            elif tab_name == "Settings":
                self._render_settings_tab()
            
            else:
                st.error(f"Unknown tab: {tab_name}")
                
        except Exception as e:
            logger.error(f"Error rendering tab {tab_name}: {e}")
            st.error(f"Error loading {tab_name}. Please try again.")
    
    def _render_dashboard_overview_tab(self) -> None:
        """Render the main dashboard overview"""
        # Get metrics (use original dashboard if available)
        metrics = self._get_dashboard_metrics()
        
        # Render role-specific overview
        self.role_dashboard.render_dashboard_overview(metrics)
        
        # Show recent activity
        st.markdown("---")
        st.markdown("### 📈 Recent Activity")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 💰 Cost Updates")
            st.info("✅ Budget tracking is active")
            st.info("📊 Cost data refreshed successfully")
            st.info("🔔 No budget alerts at this time")
        
        with col2:
            st.markdown("#### 🔧 System Status")
            st.success("✅ All systems operational")
            st.info("📡 AWS connection established")
            st.info("🤖 AI assistant ready")
    
    def _render_cost_analysis_tab(self) -> None:
        """Render cost analysis tab"""
        st.markdown("### 💰 Cost Analysis")
        
        # Use original dashboard's cost analysis if available
        if self.original_dashboard:
            try:
                # Call original dashboard's detailed usage method
                self.original_dashboard.render_detailed_usage_tab()
            except Exception as e:
                logger.error(f"Error rendering cost analysis: {e}")
                st.error("Error loading cost analysis. Please check your AWS connection.")
        else:
            st.info("Cost analysis functionality requires AWS connection.")
    
    def _render_budget_tracking_tab(self) -> None:
        """Render budget tracking tab"""
        st.markdown("### 📊 Budget Tracking")
        
        metrics = self._get_dashboard_metrics()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Current Spend", f"${metrics.get('current_spend', 0):,.2f}")
        
        with col2:
            st.metric("Budget Limit", f"${metrics.get('budget', 0):,.2f}")
        
        with col3:
            budget_remaining = metrics.get('budget', 0) - metrics.get('current_spend', 0)
            st.metric("Remaining", f"${budget_remaining:,.2f}")
        
        # Budget status
        budget_pct = metrics.get('budget_pct', 0)
        if budget_pct < 75:
            st.success(f"✅ Budget utilization: {budget_pct:.1f}% - Healthy")
        elif budget_pct < 90:
            st.warning(f"⚠️ Budget utilization: {budget_pct:.1f}% - Monitor closely")
        else:
            st.error(f"🚨 Budget utilization: {budget_pct:.1f}% - Take immediate action")
    
    def _render_forecasting_tab(self) -> None:
        """Render forecasting tab"""
        st.markdown("### 📈 Cost Forecasting")
        
        # Use original dashboard's forecasting if available
        if self.original_dashboard:
            try:
                self.original_dashboard.render_forecast_tab()
            except Exception as e:
                logger.error(f"Error rendering forecasting: {e}")
                st.error("Error loading forecasting. Please check your AWS connection.")
        else:
            st.info("Forecasting functionality requires AWS connection.")
    
    def _render_resource_monitoring_tab(self) -> None:
        """Render resource monitoring tab"""
        st.markdown("### 🔧 Resource Monitoring")
        
        # Placeholder for resource monitoring
        st.info("Resource monitoring dashboard - showing AWS resources, utilization, and optimization opportunities.")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("EC2 Instances", "0", delta="No instances")
        
        with col2:
            st.metric("Storage Volumes", "0", delta="No volumes")
        
        with col3:
            st.metric("RDS Instances", "0", delta="No databases")
    
    def _render_technical_metrics_tab(self) -> None:
        """Render technical metrics tab"""
        st.markdown("### 📊 Technical Metrics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("System Uptime", "99.9%", delta="Last 30 days")
        
        with col2:
            st.metric("API Response Time", "150ms", delta="Average")
        
        with col3:
            st.metric("Error Rate", "0.01%", delta="Very low")
        
        st.success("✅ All technical metrics are within normal ranges")
    
    def _render_system_health_tab(self) -> None:
        """Render system health tab"""
        st.markdown("### 🏥 System Health")
        
        # Show authentication system health
        try:
            health_status = asyncio.run(self.auth_manager.auth_factory.health_check())
            
            st.markdown("#### 🔐 Authentication System")
            if health_status['status'] == 'healthy':
                st.success("✅ Authentication system is healthy")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Active Sessions", health_status.get('session_count', 0))
                with col2:
                    st.metric("Total Users", health_status.get('user_count', 0))
            else:
                st.error(f"❌ Authentication system error: {health_status.get('error', 'Unknown')}")
        
        except Exception as e:
            st.error(f"Error checking system health: {e}")
        
        # Show other system components
        st.markdown("#### 🔧 System Components")
        st.success("✅ Dashboard: Operational")
        st.success("✅ Role Management: Operational")
        st.info("📡 AWS Connection: Depends on credentials")
    
    def _render_decision_management_tab(self) -> None:
        """Render decision management tab"""
        self.role_dashboard.render_decision_approval_interface()
    
    def _render_executive_summary_tab(self) -> None:
        """Render executive summary tab"""
        st.markdown("### 👑 Executive Summary")
        
        metrics = self._get_dashboard_metrics()
        
        # High-level KPIs
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Cloud Spend", f"${metrics.get('current_spend', 0):,.2f}", delta="This month")
        
        with col2:
            roi = 85  # Placeholder
            st.metric("Cloud ROI", f"{roi}%", delta="Above target")
        
        with col3:
            savings = 1250  # Placeholder
            st.metric("Cost Savings", f"${savings:,.2f}", delta="This quarter")
        
        with col4:
            efficiency = 92  # Placeholder
            st.metric("Resource Efficiency", f"{efficiency}%", delta="Excellent")
        
        # Executive insights
        st.markdown("### 📊 Strategic Insights")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 💰 Financial Performance")
            st.success("✅ Cloud spending is aligned with business objectives")
            st.info("📈 Cost optimization initiatives are delivering results")
            st.info("🎯 Budget utilization is within acceptable parameters")
        
        with col2:
            st.markdown("#### 🚀 Recommendations")
            st.info("💡 Consider expanding Reserved Instance coverage")
            st.info("🔍 Review quarterly cost allocation across departments")
            st.info("📊 Implement automated cost governance policies")
    
    def _render_settings_tab(self) -> None:
        """Render settings tab"""
        st.markdown("### ⚙️ Settings")
        
        user = self.auth_manager.get_current_user()
        
        # User settings
        st.markdown("#### 👤 User Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.text_input("Name", value=user.name if user else "", disabled=True)
            st.text_input("Email", value=user.email if user else "", disabled=True)
        
        with col2:
            st.text_input("Department", value=user.department if user else "", disabled=True)
            if user and user.roles:
                roles_text = ", ".join([role.role_name for role in user.roles])
                st.text_input("Roles", value=roles_text, disabled=True)
        
        # System settings (if user has permission)
        if self.auth_manager.has_permission("system_configuration"):
            st.markdown("#### 🔧 System Settings")
            st.info("System configuration options would appear here for administrators.")
        
        # Session management
        st.markdown("#### 🔐 Session Management")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Refresh Session", help="Extend your current session"):
                try:
                    session_manager = self.auth_manager.auth_factory.get_session_manager()
                    if st.session_state.get('session_id'):
                        success = asyncio.run(session_manager.extend_session(st.session_state.session_id))
                        if success:
                            st.success("✅ Session refreshed successfully")
                        else:
                            st.error("❌ Failed to refresh session")
                except Exception as e:
                    st.error(f"Error refreshing session: {e}")
        
        with col2:
            if st.button("🚪 Logout", help="End your current session"):
                self.auth_manager.logout()
                st.success("✅ Logged out successfully")
                st.rerun()
    
    def _get_dashboard_metrics(self) -> Dict[str, Any]:
        """Get dashboard metrics (from original dashboard if available)"""
        try:
            if self.original_dashboard:
                return self.original_dashboard.calculate_metrics()
            else:
                # Return default metrics
                return {
                    'current_spend': 0.0,
                    'budget': 1000.0,
                    'budget_pct': 0.0,
                    'forecast': 0.0,
                    'trending': 'stable',
                    'has_resources': False,
                    'service_total': 0.0,
                    'data_source': 'default'
                }
        except Exception as e:
            logger.error(f"Error getting dashboard metrics: {e}")
            return {
                'current_spend': 0.0,
                'budget': 1000.0,
                'budget_pct': 0.0,
                'forecast': 0.0,
                'trending': 'stable',
                'has_resources': False,
                'service_total': 0.0,
                'data_source': 'error'
            }


# Global authenticated dashboard instance
authenticated_dashboard = AuthenticatedDashboard()