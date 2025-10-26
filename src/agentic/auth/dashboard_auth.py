"""
Dashboard authentication and role-based view management
"""

import streamlit as st
from typing import Optional, Dict, Any, List
import logging

from .models import User, DashboardSection, PermissionType
from .auth_factory import auth_factory
from .middleware import create_auth_context, extract_session_from_cookies

logger = logging.getLogger(__name__)


class DashboardAuthManager:
    """Manages authentication and role-based access for dashboard views"""
    
    def __init__(self):
        self.auth_factory = auth_factory
        self.middleware = None
        self.current_user: Optional[User] = None
        self._initialize_session_state()
    
    def _initialize_session_state(self):
        """Initialize session state for authentication"""
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        if 'current_user' not in st.session_state:
            st.session_state.current_user = None
        if 'session_id' not in st.session_state:
            st.session_state.session_id = None
        if 'auth_context' not in st.session_state:
            st.session_state.auth_context = None
    
    async def initialize(self) -> bool:
        """Initialize authentication system"""
        try:
            success = await self.auth_factory.initialize()
            if success:
                self.middleware = self.auth_factory.get_middleware()
                logger.info("Dashboard authentication manager initialized")
            return success
        except Exception as e:
            logger.error(f"Failed to initialize dashboard auth manager: {e}")
            return False
    
    def render_login_form(self) -> None:
        """Render login form for user authentication"""
        st.markdown("## 🔐 Login to Vismaya DemandOps")
        st.markdown("*AI-Powered FinOps Platform*")
        
        with st.form("login_form"):
            st.markdown("### Select Your Role")
            
            # Role selection with descriptions
            role_options = {
                "ceo@company.com": "👑 CEO - Chief Executive Officer (Full Access)",
                "cto@company.com": "🔧 CTO - Chief Technology Officer (Technical Decisions)",
                "finops@company.com": "💰 FinOps Lead - Financial Operations (Cost Management)",
                "devops@company.com": "⚙️ DevOps Engineer - Operations (Monitoring & Alerts)"
            }
            
            selected_email = st.selectbox(
                "Choose your role:",
                options=list(role_options.keys()),
                format_func=lambda x: role_options[x],
                help="Select your organizational role to access appropriate dashboard views"
            )
            
            # Show role permissions preview
            if selected_email:
                auth_service = self.auth_factory.get_auth_service()
                user = auth_service.get_user_by_email(selected_email)
                if user:
                    with st.expander("🔍 View Role Permissions", expanded=False):
                        role_manager = self.auth_factory.get_role_manager()
                        permissions_summary = role_manager.get_user_permissions_summary(user)
                        
                        st.markdown("**Dashboard Access:**")
                        for section in permissions_summary['dashboard_access']:
                            st.markdown(f"• {section.replace('_', ' ').title()}")
                        
                        st.markdown("**Approval Authority:**")
                        for decision_type, authority in permissions_summary['approval_authority'].items():
                            if authority['can_approve']:
                                max_amount = authority['max_amount']
                                if max_amount == 'unlimited':
                                    st.markdown(f"• {decision_type.replace('_', ' ').title()}: Unlimited")
                                else:
                                    st.markdown(f"• {decision_type.replace('_', ' ').title()}: Up to ${max_amount:,.2f}")
                            else:
                                st.markdown(f"• {decision_type.replace('_', ' ').title()}: View Only")
            
            col1, col2 = st.columns(2)
            with col1:
                login_clicked = st.form_submit_button("🚀 Login", type="primary", use_container_width=True)
            with col2:
                demo_clicked = st.form_submit_button("👀 Demo Mode", use_container_width=True)
            
            if login_clicked and selected_email:
                success = self._authenticate_user(selected_email)
                if success:
                    st.success(f"✅ Logged in successfully as {role_options[selected_email]}")
                    st.rerun()
                else:
                    st.error("❌ Login failed. Please try again.")
            
            elif demo_clicked:
                # Set demo mode without authentication
                st.session_state.demo_mode = True
                st.session_state.authenticated = False
                st.info("👀 Demo mode activated - Limited functionality available")
                st.rerun()
    
    def _authenticate_user(self, email: str) -> bool:
        """Authenticate user and create session"""
        try:
            import asyncio
            
            auth_service = self.auth_factory.get_auth_service()
            
            # Authenticate user (simplified for demo - no password required)
            auth_result = asyncio.run(auth_service.authenticate_user(
                email=email,
                ip_address=self._get_client_ip(),
                user_agent=self._get_user_agent()
            ))
            
            if auth_result.success:
                # Store authentication info in session state
                st.session_state.authenticated = True
                st.session_state.current_user = auth_result.user
                st.session_state.session_id = auth_result.session.session_id
                st.session_state.auth_context = create_auth_context(auth_result.user)
                
                # Store in class instance
                self.current_user = auth_result.user
                
                logger.info(f"User {email} authenticated successfully")
                return True
            else:
                logger.warning(f"Authentication failed for {email}: {auth_result.error_message}")
                return False
                
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False
    
    def _get_client_ip(self) -> Optional[str]:
        """Get client IP address (simplified for Streamlit)"""
        try:
            # In a real deployment, you'd get this from headers
            return "127.0.0.1"  # Localhost for demo
        except:
            return None
    
    def _get_user_agent(self) -> Optional[str]:
        """Get user agent (simplified for Streamlit)"""
        try:
            return "Streamlit Dashboard"
        except:
            return None
    
    def check_authentication(self) -> bool:
        """Check if user is authenticated"""
        if not st.session_state.get('authenticated', False):
            return False
        
        if not st.session_state.get('current_user'):
            return False
        
        # Validate session if exists
        if st.session_state.get('session_id'):
            try:
                import asyncio
                auth_service = self.auth_factory.get_auth_service()
                auth_result = asyncio.run(auth_service.authenticate_by_session(
                    st.session_state.session_id
                ))
                
                if not auth_result.success:
                    # Session expired or invalid
                    self.logout()
                    return False
                
                # Update current user
                st.session_state.current_user = auth_result.user
                self.current_user = auth_result.user
                
            except Exception as e:
                logger.error(f"Session validation error: {e}")
                self.logout()
                return False
        
        return True
    
    def logout(self) -> None:
        """Logout current user"""
        try:
            if st.session_state.get('session_id'):
                import asyncio
                auth_service = self.auth_factory.get_auth_service()
                asyncio.run(auth_service.logout_user(st.session_state.session_id))
            
            # Clear session state
            st.session_state.authenticated = False
            st.session_state.current_user = None
            st.session_state.session_id = None
            st.session_state.auth_context = None
            st.session_state.demo_mode = False
            
            # Clear class instance
            self.current_user = None
            
            logger.info("User logged out successfully")
            
        except Exception as e:
            logger.error(f"Logout error: {e}")
    
    def get_current_user(self) -> Optional[User]:
        """Get current authenticated user"""
        return st.session_state.get('current_user')
    
    def has_permission(self, permission: str) -> bool:
        """Check if current user has specific permission"""
        user = self.get_current_user()
        if not user:
            return False
        
        try:
            role_manager = self.auth_factory.get_role_manager()
            permission_check = role_manager.validate_permission(user, permission)
            return permission_check.allowed
        except Exception as e:
            logger.error(f"Permission check error: {e}")
            return False
    
    def has_dashboard_access(self, section: str) -> bool:
        """Check if current user has access to dashboard section"""
        user = self.get_current_user()
        if not user:
            return False
        
        try:
            role_manager = self.auth_factory.get_role_manager()
            access_check = role_manager.validate_dashboard_access(user, section)
            return access_check.allowed
        except Exception as e:
            logger.error(f"Dashboard access check error: {e}")
            return False
    
    def can_approve_decision(self, decision_type: str, amount: Optional[float] = None) -> bool:
        """Check if current user can approve decision"""
        user = self.get_current_user()
        if not user:
            return False
        
        try:
            role_manager = self.auth_factory.get_role_manager()
            approval_check = role_manager.validate_approval_authority(user, decision_type, amount)
            return approval_check.allowed
        except Exception as e:
            logger.error(f"Approval authority check error: {e}")
            return False
    
    def get_accessible_tabs(self) -> List[str]:
        """Get list of dashboard tabs user can access"""
        user = self.get_current_user()
        if not user:
            return []
        
        accessible_tabs = []
        
        # Map dashboard sections to tab names
        section_tab_mapping = {
            DashboardSection.COST_ANALYSIS.value: "Current Usage",
            DashboardSection.BUDGET_TRACKING.value: "Detailed Usage", 
            DashboardSection.FORECASTING.value: "Forecast",
            DashboardSection.TECHNICAL_METRICS.value: "Detailed Billing",
            DashboardSection.RESOURCE_MONITORING.value: "Historical Data",
            DashboardSection.SYSTEM_HEALTH.value: "Settings",
            DashboardSection.EXECUTIVE_SUMMARY.value: "Executive Summary",
            DashboardSection.ALL_DECISIONS.value: "Decisions"
        }
        
        for section, tab_name in section_tab_mapping.items():
            if self.has_dashboard_access(section):
                accessible_tabs.append(tab_name)
        
        # Ensure basic tabs are always available
        basic_tabs = ["Current Usage", "Settings"]
        for tab in basic_tabs:
            if tab not in accessible_tabs:
                accessible_tabs.append(tab)
        
        return accessible_tabs
    
    def render_user_info(self) -> None:
        """Render current user information in sidebar"""
        user = self.get_current_user()
        if not user:
            return
        
        with st.sidebar:
            st.markdown("---")
            st.markdown("### 👤 Current User")
            st.markdown(f"**Name:** {user.name}")
            st.markdown(f"**Email:** {user.email}")
            st.markdown(f"**Department:** {user.department}")
            
            # Show roles
            st.markdown("**Roles:**")
            for role in user.roles:
                st.markdown(f"• {role.role_name}")
            
            # Logout button
            if st.button("🚪 Logout", use_container_width=True):
                self.logout()
                st.rerun()
            
            # Show session info
            with st.expander("🔍 Session Info"):
                if st.session_state.get('session_id'):
                    session_manager = self.auth_factory.get_session_manager()
                    session_info = session_manager.get_session_info(st.session_state.session_id)
                    if session_info:
                        st.json(session_info)
    
    def render_permission_denied(self, section: str) -> None:
        """Render permission denied message"""
        st.error(f"🚫 Access Denied")
        st.markdown(f"You don't have permission to access the **{section}** section.")
        
        user = self.get_current_user()
        if user:
            st.info(f"Your current role(s): {', '.join([role.role_name for role in user.roles])}")
            st.markdown("Contact your administrator to request additional permissions.")
        else:
            st.markdown("Please log in to access this section.")
    
    def filter_dashboard_content(self, content_type: str, content: Dict[str, Any]) -> Dict[str, Any]:
        """Filter dashboard content based on user permissions"""
        user = self.get_current_user()
        if not user:
            return {}
        
        filtered_content = content.copy()
        
        # Filter based on content type and user permissions
        if content_type == "metrics":
            # All users can see basic metrics
            pass
        
        elif content_type == "cost_details":
            # Only users with cost analysis permission can see detailed costs
            if not self.has_permission(PermissionType.COST_ANALYSIS.value):
                filtered_content = {
                    "message": "Detailed cost information requires cost analysis permissions"
                }
        
        elif content_type == "resource_details":
            # Only users with resource monitoring permission can see resource details
            if not self.has_permission(PermissionType.RESOURCE_MONITORING.value):
                filtered_content = {
                    "message": "Resource details require resource monitoring permissions"
                }
        
        elif content_type == "system_config":
            # Only users with system configuration permission can see system settings
            if not self.has_permission(PermissionType.SYSTEM_CONFIGURATION.value):
                filtered_content = {
                    "message": "System configuration requires administrative permissions"
                }
        
        return filtered_content
    
    def get_role_specific_welcome_message(self) -> str:
        """Get welcome message tailored to user's role"""
        user = self.get_current_user()
        if not user:
            return "Welcome to Vismaya DemandOps!"
        
        primary_role = user.roles[0] if user.roles else None
        if not primary_role:
            return f"Welcome {user.name}!"
        
        role_messages = {
            'ceo': f"Welcome {user.name}! 👑 As CEO, you have full access to all cost decisions and strategic insights.",
            'cto': f"Welcome {user.name}! 🔧 As CTO, you can manage technical decisions and monitor system health.",
            'finops_lead': f"Welcome {user.name}! 💰 As FinOps Lead, you can analyze costs and manage budgets up to $5,000.",
            'devops_engineer': f"Welcome {user.name}! ⚙️ As DevOps Engineer, you can monitor resources and manage alerts."
        }
        
        return role_messages.get(primary_role.role_id, f"Welcome {user.name}!")


# Global dashboard auth manager instance
dashboard_auth = DashboardAuthManager()