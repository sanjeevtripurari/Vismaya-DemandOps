"""
Unit tests for the authentication and role-based access control system
"""

import pytest
import asyncio
from datetime import datetime, timedelta

from src.agentic.auth import (
    User, UserRole, UserSession, AuthenticationResult, PermissionCheck,
    PermissionType, DashboardSection, EXECUTIVE_ROLES,
    AuthenticationService, RoleManager, SessionManager,
    auth_factory
)


class TestUserModels:
    """Test user and role models"""
    
    def test_user_role_creation(self):
        """Test creating a user role"""
        role = UserRole(
            role_id="test_role",
            role_name="Test Role",
            permissions=["test_permission"],
            approval_authority={"test_decisions": {"max_amount": 1000}},
            dashboard_access=["test_section"],
            notification_preferences={"email": True}
        )
        
        assert role.role_id == "test_role"
        assert role.role_name == "Test Role"
        assert role.has_permission("test_permission")
        assert not role.has_permission("other_permission")
        assert role.can_approve_decision("test_decisions", 500)
        assert not role.can_approve_decision("test_decisions", 1500)
        assert role.has_dashboard_access("test_section")
    
    def test_user_creation(self):
        """Test creating a user with roles"""
        role = EXECUTIVE_ROLES['ceo']
        user = User(
            user_id="test_user",
            email="test@example.com",
            name="Test User",
            roles=[role],
            department="Test"
        )
        
        assert user.user_id == "test_user"
        assert user.email == "test@example.com"
        assert user.has_permission("*")  # CEO has all permissions
        assert user.can_approve_decision("cost_decisions", 10000)
        assert user.has_dashboard_access("executive_summary")
    
    def test_user_session_creation(self):
        """Test creating a user session"""
        session = UserSession.create_session("test_user", duration_hours=24)
        
        assert session.user_id == "test_user"
        assert session.active
        assert not session.is_expired
        assert session.is_valid
        
        # Test expiration
        session.expires_at = datetime.now() - timedelta(hours=1)
        assert session.is_expired
        assert not session.is_valid


class TestAuthenticationService:
    """Test authentication service"""
    
    @pytest.fixture
    async def auth_service(self):
        """Create authentication service for testing"""
        session_manager = SessionManager()
        return AuthenticationService(session_manager)
    
    @pytest.mark.asyncio
    async def test_user_authentication(self, auth_service):
        """Test user authentication"""
        # Test successful authentication
        result = await auth_service.authenticate_user("ceo@company.com")
        
        assert result.success
        assert result.user is not None
        assert result.session is not None
        assert result.user.email == "ceo@company.com"
        
        # Test invalid user
        result = await auth_service.authenticate_user("invalid@example.com")
        assert not result.success
        assert result.error_message is not None
    
    @pytest.mark.asyncio
    async def test_session_authentication(self, auth_service):
        """Test session-based authentication"""
        # First authenticate to get a session
        auth_result = await auth_service.authenticate_user("cto@company.com")
        assert auth_result.success
        
        session_id = auth_result.session.session_id
        
        # Test session authentication
        session_result = await auth_service.authenticate_by_session(session_id)
        assert session_result.success
        assert session_result.user.email == "cto@company.com"
        
        # Test invalid session
        invalid_result = await auth_service.authenticate_by_session("invalid_session")
        assert not invalid_result.success


class TestRoleManager:
    """Test role manager"""
    
    @pytest.fixture
    def role_manager(self):
        """Create role manager for testing"""
        return RoleManager()
    
    def test_permission_validation(self, role_manager):
        """Test permission validation"""
        # Create test user with CEO role
        ceo_role = EXECUTIVE_ROLES['ceo']
        user = User(
            user_id="test_ceo",
            email="ceo@test.com",
            name="Test CEO",
            roles=[ceo_role],
            department="Executive"
        )
        
        # Test permission validation
        check = role_manager.validate_permission(user, "cost_analysis")
        assert check.allowed
        
        # Test with DevOps user (limited permissions)
        devops_role = EXECUTIVE_ROLES['devops_engineer']
        devops_user = User(
            user_id="test_devops",
            email="devops@test.com",
            name="Test DevOps",
            roles=[devops_role],
            department="Engineering"
        )
        
        # DevOps should have resource monitoring permission
        check = role_manager.validate_permission(devops_user, "resource_monitoring")
        assert check.allowed
        
        # DevOps should not have cost decisions permission
        check = role_manager.validate_permission(devops_user, "cost_decisions")
        assert not check.allowed
    
    def test_dashboard_access_validation(self, role_manager):
        """Test dashboard access validation"""
        # Test FinOps user dashboard access
        finops_role = EXECUTIVE_ROLES['finops_lead']
        user = User(
            user_id="test_finops",
            email="finops@test.com",
            name="Test FinOps",
            roles=[finops_role],
            department="Finance"
        )
        
        # FinOps should have cost analysis access
        check = role_manager.validate_dashboard_access(user, "cost_analysis")
        assert check.allowed
        
        # FinOps should not have technical metrics access
        check = role_manager.validate_dashboard_access(user, "technical_metrics")
        assert not check.allowed
    
    def test_approval_authority_validation(self, role_manager):
        """Test approval authority validation"""
        # Test CTO approval authority
        cto_role = EXECUTIVE_ROLES['cto']
        user = User(
            user_id="test_cto",
            email="cto@test.com",
            name="Test CTO",
            roles=[cto_role],
            department="Technology"
        )
        
        # CTO can approve technical decisions
        check = role_manager.validate_approval_authority(user, "technical_decisions")
        assert check.allowed
        
        # CTO can approve cost decisions up to $10,000
        check = role_manager.validate_approval_authority(user, "cost_decisions", 5000)
        assert check.allowed
        
        check = role_manager.validate_approval_authority(user, "cost_decisions", 15000)
        assert not check.allowed


class TestSessionManager:
    """Test session manager"""
    
    @pytest.fixture
    def session_manager(self):
        """Create session manager for testing"""
        return SessionManager()
    
    @pytest.mark.asyncio
    async def test_session_creation(self, session_manager):
        """Test session creation and retrieval"""
        session = UserSession.create_session("test_user")
        
        # Create session
        success = await session_manager.create_session(session)
        assert success
        
        # Retrieve session
        retrieved = await session_manager.get_session(session.session_id)
        assert retrieved is not None
        assert retrieved.user_id == "test_user"
        assert retrieved.is_valid
    
    @pytest.mark.asyncio
    async def test_session_invalidation(self, session_manager):
        """Test session invalidation"""
        session = UserSession.create_session("test_user")
        await session_manager.create_session(session)
        
        # Invalidate session
        success = await session_manager.invalidate_session(session.session_id)
        assert success
        
        # Try to retrieve invalidated session
        retrieved = await session_manager.get_session(session.session_id)
        assert retrieved is None
    
    @pytest.mark.asyncio
    async def test_expired_session_cleanup(self, session_manager):
        """Test expired session cleanup"""
        session = UserSession.create_session("test_user")
        # Make session expired
        session.expires_at = datetime.now() - timedelta(hours=1)
        
        await session_manager.create_session(session)
        
        # Try to retrieve expired session (should be cleaned up)
        retrieved = await session_manager.get_session(session.session_id)
        assert retrieved is None


class TestAuthenticationFactory:
    """Test authentication factory"""
    
    @pytest.mark.asyncio
    async def test_factory_initialization(self):
        """Test factory initialization"""
        success = await auth_factory.initialize()
        assert success
        
        # Test component creation
        session_manager = auth_factory.get_session_manager()
        assert session_manager is not None
        
        role_manager = auth_factory.get_role_manager()
        assert role_manager is not None
        
        auth_service = auth_factory.get_auth_service()
        assert auth_service is not None
        
        middleware = auth_factory.get_middleware()
        assert middleware is not None
    
    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test system health check"""
        await auth_factory.initialize()
        
        health = await auth_factory.health_check()
        assert health['status'] == 'healthy'
        assert 'session_count' in health
        assert 'user_count' in health
        assert 'components' in health


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])