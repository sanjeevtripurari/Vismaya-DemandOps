"""
Authentication service for user login and session management
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

from .models import User, UserSession, AuthenticationResult, EXECUTIVE_ROLES
from .session_manager import SessionManager

logger = logging.getLogger(__name__)


class AuthenticationService:
    """Service for handling user authentication and session management"""
    
    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager
        self._users: Dict[str, User] = {}  # In-memory user store (replace with DB later)
        self._initialize_default_users()
    
    def _initialize_default_users(self) -> None:
        """Initialize default users for each role"""
        default_users = [
            {
                'email': 'ceo@company.com',
                'name': 'Chief Executive Officer',
                'department': 'Executive',
                'roles': ['ceo']
            },
            {
                'email': 'cto@company.com', 
                'name': 'Chief Technology Officer',
                'department': 'Technology',
                'roles': ['cto']
            },
            {
                'email': 'finops@company.com',
                'name': 'FinOps Lead',
                'department': 'Finance',
                'roles': ['finops_lead']
            },
            {
                'email': 'devops@company.com',
                'name': 'DevOps Engineer', 
                'department': 'Engineering',
                'roles': ['devops_engineer']
            }
        ]
        
        for user_data in default_users:
            user_roles = [EXECUTIVE_ROLES[role_id] for role_id in user_data['roles']]
            user = User(
                user_id=self._generate_user_id(),
                email=user_data['email'],
                name=user_data['name'],
                roles=user_roles,
                department=user_data['department'],
                active=True
            )
            self._users[user.email] = user
            logger.info(f"Initialized default user: {user.email} with roles: {user_data['roles']}")
    
    def _generate_user_id(self) -> str:
        """Generate unique user ID"""
        return secrets.token_urlsafe(16)
    
    def _hash_password(self, password: str, salt: Optional[str] = None) -> tuple[str, str]:
        """Hash password with salt"""
        if salt is None:
            salt = secrets.token_hex(32)
        
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # iterations
        )
        return password_hash.hex(), salt
    
    def _verify_password(self, password: str, password_hash: str, salt: str) -> bool:
        """Verify password against hash"""
        computed_hash, _ = self._hash_password(password, salt)
        return secrets.compare_digest(computed_hash, password_hash)
    
    async def authenticate_user(self, email: str, password: Optional[str] = None,
                              ip_address: Optional[str] = None,
                              user_agent: Optional[str] = None) -> AuthenticationResult:
        """
        Authenticate user by email and password
        For now, we'll use email-only authentication for simplicity
        """
        try:
            # Find user by email
            user = self._users.get(email.lower())
            if not user:
                logger.warning(f"Authentication failed: User not found for email {email}")
                return AuthenticationResult.failure_result("Invalid email or password")
            
            if not user.active:
                logger.warning(f"Authentication failed: User {email} is inactive")
                return AuthenticationResult.failure_result("Account is inactive")
            
            # For now, skip password verification (implement later)
            # In production, you would verify password here
            
            # Create session
            session = UserSession.create_session(
                user_id=user.user_id,
                duration_hours=24,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Store session
            await self.session_manager.create_session(session)
            
            # Update last login
            user.last_login = datetime.now()
            
            logger.info(f"User {email} authenticated successfully")
            return AuthenticationResult.success_result(user, session)
            
        except Exception as e:
            logger.error(f"Authentication error for {email}: {e}")
            return AuthenticationResult.failure_result("Authentication failed")
    
    async def authenticate_by_session(self, session_id: str) -> AuthenticationResult:
        """Authenticate user by session ID"""
        try:
            session = await self.session_manager.get_session(session_id)
            if not session or not session.is_valid:
                return AuthenticationResult.failure_result("Invalid or expired session")
            
            # Find user
            user = self.get_user_by_id(session.user_id)
            if not user or not user.active:
                return AuthenticationResult.failure_result("User not found or inactive")
            
            # Update session activity
            session.update_activity()
            await self.session_manager.update_session(session)
            
            return AuthenticationResult.success_result(user, session)
            
        except Exception as e:
            logger.error(f"Session authentication error: {e}")
            return AuthenticationResult.failure_result("Session authentication failed")
    
    async def logout_user(self, session_id: str) -> bool:
        """Logout user by invalidating session"""
        try:
            return await self.session_manager.invalidate_session(session_id)
        except Exception as e:
            logger.error(f"Logout error: {e}")
            return False
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self._users.get(email.lower())
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        for user in self._users.values():
            if user.user_id == user_id:
                return user
        return None
    
    def create_user(self, email: str, name: str, role_ids: list[str], 
                   department: str, manager_id: Optional[str] = None) -> User:
        """Create new user with specified roles"""
        if email.lower() in self._users:
            raise ValueError(f"User with email {email} already exists")
        
        # Get roles
        user_roles = []
        for role_id in role_ids:
            if role_id in EXECUTIVE_ROLES:
                user_roles.append(EXECUTIVE_ROLES[role_id])
            else:
                raise ValueError(f"Invalid role ID: {role_id}")
        
        user = User(
            user_id=self._generate_user_id(),
            email=email.lower(),
            name=name,
            roles=user_roles,
            department=department,
            manager_id=manager_id,
            active=True
        )
        
        self._users[email.lower()] = user
        logger.info(f"Created new user: {email} with roles: {role_ids}")
        return user
    
    def update_user_roles(self, user_id: str, role_ids: list[str]) -> bool:
        """Update user roles"""
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        try:
            user_roles = []
            for role_id in role_ids:
                if role_id in EXECUTIVE_ROLES:
                    user_roles.append(EXECUTIVE_ROLES[role_id])
                else:
                    raise ValueError(f"Invalid role ID: {role_id}")
            
            user.roles = user_roles
            logger.info(f"Updated roles for user {user.email}: {role_ids}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating user roles: {e}")
            return False
    
    def deactivate_user(self, user_id: str) -> bool:
        """Deactivate user account"""
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        user.active = False
        logger.info(f"Deactivated user: {user.email}")
        return True
    
    def activate_user(self, user_id: str) -> bool:
        """Activate user account"""
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        user.active = True
        logger.info(f"Activated user: {user.email}")
        return True
    
    def list_users(self) -> list[User]:
        """List all users"""
        return list(self._users.values())
    
    def get_users_by_role(self, role_id: str) -> list[User]:
        """Get all users with specific role"""
        users = []
        for user in self._users.values():
            if any(role.role_id == role_id for role in user.roles):
                users.append(user)
        return users