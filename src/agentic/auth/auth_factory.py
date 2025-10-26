"""
Authentication system factory for dependency injection
"""

from typing import Optional
import logging

from .auth_service import AuthenticationService
from .role_manager import RoleManager
from .session_manager import SessionManager
from .middleware import AuthenticationMiddleware

logger = logging.getLogger(__name__)


class AuthenticationFactory:
    """Factory for creating authentication system components"""
    
    _instance: Optional['AuthenticationFactory'] = None
    _session_manager: Optional[SessionManager] = None
    _auth_service: Optional[AuthenticationService] = None
    _role_manager: Optional[RoleManager] = None
    _middleware: Optional[AuthenticationMiddleware] = None
    
    def __new__(cls) -> 'AuthenticationFactory':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_session_manager(self) -> SessionManager:
        """Get or create session manager"""
        if self._session_manager is None:
            self._session_manager = SessionManager()
            logger.info("Created SessionManager instance")
        return self._session_manager
    
    def get_role_manager(self) -> RoleManager:
        """Get or create role manager"""
        if self._role_manager is None:
            self._role_manager = RoleManager()
            logger.info("Created RoleManager instance")
        return self._role_manager
    
    def get_auth_service(self) -> AuthenticationService:
        """Get or create authentication service"""
        if self._auth_service is None:
            session_manager = self.get_session_manager()
            self._auth_service = AuthenticationService(session_manager)
            logger.info("Created AuthenticationService instance")
        return self._auth_service
    
    def get_middleware(self) -> AuthenticationMiddleware:
        """Get or create authentication middleware"""
        if self._middleware is None:
            auth_service = self.get_auth_service()
            role_manager = self.get_role_manager()
            self._middleware = AuthenticationMiddleware(auth_service, role_manager)
            logger.info("Created AuthenticationMiddleware instance")
        return self._middleware
    
    async def initialize(self) -> bool:
        """Initialize authentication system"""
        try:
            # Initialize all components
            session_manager = self.get_session_manager()
            role_manager = self.get_role_manager()
            auth_service = self.get_auth_service()
            middleware = self.get_middleware()
            
            # Clean up expired sessions
            await session_manager.cleanup_expired_sessions()
            
            logger.info("Authentication system initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize authentication system: {e}")
            return False
    
    async def health_check(self) -> dict:
        """Perform health check on authentication system"""
        try:
            session_manager = self.get_session_manager()
            auth_service = self.get_auth_service()
            
            # Check session manager
            session_count = await session_manager.get_session_count()
            
            # Check auth service
            user_count = len(auth_service.list_users())
            
            return {
                'status': 'healthy',
                'session_count': session_count,
                'user_count': user_count,
                'components': {
                    'session_manager': 'healthy',
                    'auth_service': 'healthy',
                    'role_manager': 'healthy',
                    'middleware': 'healthy'
                }
            }
            
        except Exception as e:
            logger.error(f"Authentication system health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'components': {
                    'session_manager': 'unknown',
                    'auth_service': 'unknown',
                    'role_manager': 'unknown',
                    'middleware': 'unknown'
                }
            }
    
    def reset(self) -> None:
        """Reset factory (for testing)"""
        self._session_manager = None
        self._auth_service = None
        self._role_manager = None
        self._middleware = None
        logger.info("Authentication factory reset")


# Global factory instance
auth_factory = AuthenticationFactory()