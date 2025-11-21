"""
Authentication middleware for request validation
"""

from typing import Optional, Callable, Any
from functools import wraps
import logging

from .models import User, PermissionCheck
from .auth_service import AuthenticationService
from .role_manager import RoleManager

logger = logging.getLogger(__name__)


class AuthenticationMiddleware:
    """Middleware for handling authentication and authorization"""
    
    def __init__(self, auth_service: AuthenticationService, role_manager: RoleManager):
        self.auth_service = auth_service
        self.role_manager = role_manager
    
    async def authenticate_request(self, session_id: Optional[str]) -> Optional[User]:
        """Authenticate request by session ID"""
        if not session_id:
            return None
        
        auth_result = await self.auth_service.authenticate_by_session(session_id)
        return auth_result.user if auth_result.success else None
    
    def require_authentication(self, func: Callable) -> Callable:
        """Decorator to require authentication"""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract session_id from kwargs or context
            session_id = kwargs.get('session_id') or kwargs.get('context', {}).get('session_id')
            
            user = await self.authenticate_request(session_id)
            if not user:
                raise AuthenticationError("Authentication required")
            
            # Add user to kwargs
            kwargs['current_user'] = user
            return await func(*args, **kwargs)
        
        return wrapper
    
    def require_permission(self, permission: str) -> Callable:
        """Decorator to require specific permission"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Get current user (should be set by require_authentication)
                user = kwargs.get('current_user')
                if not user:
                    raise AuthenticationError("Authentication required")
                
                # Check permission
                permission_check = self.role_manager.validate_permission(user, permission)
                if not permission_check.allowed:
                    raise AuthorizationError(f"Permission denied: {permission_check.reason}")
                
                return await func(*args, **kwargs)
            
            return wrapper
        return decorator
    
    def require_dashboard_access(self, section: str) -> Callable:
        """Decorator to require dashboard section access"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                user = kwargs.get('current_user')
                if not user:
                    raise AuthenticationError("Authentication required")
                
                access_check = self.role_manager.validate_dashboard_access(user, section)
                if not access_check.allowed:
                    raise AuthorizationError(f"Dashboard access denied: {access_check.reason}")
                
                return await func(*args, **kwargs)
            
            return wrapper
        return decorator
    
    def require_approval_authority(self, decision_type: str, amount_key: Optional[str] = None) -> Callable:
        """Decorator to require approval authority for decision type and amount"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                user = kwargs.get('current_user')
                if not user:
                    raise AuthenticationError("Authentication required")
                
                # Extract amount if specified
                amount = None
                if amount_key and amount_key in kwargs:
                    amount = kwargs[amount_key]
                
                approval_check = self.role_manager.validate_approval_authority(
                    user, decision_type, amount
                )
                if not approval_check.allowed:
                    raise AuthorizationError(f"Approval authority denied: {approval_check.reason}")
                
                return await func(*args, **kwargs)
            
            return wrapper
        return decorator


class AuthenticationError(Exception):
    """Raised when authentication fails"""
    pass


class AuthorizationError(Exception):
    """Raised when authorization fails"""
    pass


def create_auth_context(user: User) -> dict:
    """Create authentication context for user"""
    return {
        'user_id': user.user_id,
        'email': user.email,
        'name': user.name,
        'roles': [role.role_id for role in user.roles],
        'permissions': user.get_all_permissions(),
        'dashboard_access': user.get_accessible_dashboard_sections(),
        'active': user.active,
        'last_login': user.last_login.isoformat() if user.last_login else None
    }


def extract_session_from_headers(headers: dict) -> Optional[str]:
    """Extract session ID from request headers"""
    # Check Authorization header
    auth_header = headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        return auth_header[7:]  # Remove 'Bearer ' prefix
    
    # Check custom session header
    return headers.get('X-Session-ID')


def extract_session_from_cookies(cookies: dict) -> Optional[str]:
    """Extract session ID from cookies"""
    return cookies.get('session_id')