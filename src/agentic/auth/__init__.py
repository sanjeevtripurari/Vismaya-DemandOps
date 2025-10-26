"""
Authentication and authorization module for the agentic AI system
"""

from .models import (
    User, UserRole, UserSession, AuthenticationResult, PermissionCheck,
    PermissionType, DashboardSection, EXECUTIVE_ROLES
)
from .auth_service import AuthenticationService
from .role_manager import RoleManager
from .session_manager import SessionManager
from .middleware import AuthenticationMiddleware, AuthenticationError, AuthorizationError
from .auth_factory import AuthenticationFactory, auth_factory
from .dashboard_auth import DashboardAuthManager, dashboard_auth
from .role_dashboard import RoleBasedDashboard, role_dashboard
from .authenticated_dashboard import AuthenticatedDashboard, authenticated_dashboard

__all__ = [
    # Models
    'User',
    'UserRole', 
    'UserSession',
    'AuthenticationResult',
    'PermissionCheck',
    'PermissionType',
    'DashboardSection',
    'EXECUTIVE_ROLES',
    
    # Services
    'AuthenticationService',
    'RoleManager',
    'SessionManager',
    'AuthenticationMiddleware',
    
    # Factory
    'AuthenticationFactory',
    'auth_factory',
    
    # Dashboard Components
    'DashboardAuthManager',
    'dashboard_auth',
    'RoleBasedDashboard',
    'role_dashboard',
    'AuthenticatedDashboard',
    'authenticated_dashboard',
    
    # Exceptions
    'AuthenticationError',
    'AuthorizationError'
]