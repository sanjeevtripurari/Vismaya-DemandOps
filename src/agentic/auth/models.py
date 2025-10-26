"""
Authentication and role-based access control models
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
import uuid


class PermissionType(Enum):
    """System permission types"""
    # Cost management permissions
    COST_ANALYSIS = "cost_analysis"
    BUDGET_MANAGEMENT = "budget_management"
    COST_DECISIONS = "cost_decisions"
    
    # Resource management permissions
    RESOURCE_MONITORING = "resource_monitoring"
    RESOURCE_MANAGEMENT = "resource_management"
    TECHNICAL_DECISIONS = "technical_decisions"
    
    # System permissions
    SYSTEM_CONFIGURATION = "system_configuration"
    SYSTEM_HEALTH = "system_health"
    USER_MANAGEMENT = "user_management"
    
    # Reporting permissions
    REPORTING = "reporting"
    ALERT_MANAGEMENT = "alert_management"
    
    # Special permissions
    ALL_PERMISSIONS = "*"


class DashboardSection(Enum):
    """Dashboard sections that can be accessed"""
    EXECUTIVE_SUMMARY = "executive_summary"
    COST_ANALYSIS = "cost_analysis"
    BUDGET_TRACKING = "budget_tracking"
    FORECASTING = "forecasting"
    TECHNICAL_METRICS = "technical_metrics"
    RESOURCE_UTILIZATION = "resource_utilization"
    RESOURCE_MONITORING = "resource_monitoring"
    ALERTS = "alerts"
    SYSTEM_METRICS = "system_metrics"
    SYSTEM_HEALTH = "system_health"
    ALL_DECISIONS = "all_decisions"


@dataclass
class UserRole:
    """User role with permissions and access controls"""
    role_id: str
    role_name: str
    permissions: List[str]
    approval_authority: Dict[str, Any]  # decision types and limits
    dashboard_access: List[str]
    notification_preferences: Dict[str, Any]
    description: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def has_permission(self, permission: str) -> bool:
        """Check if role has specific permission"""
        return "*" in self.permissions or permission in self.permissions
    
    def can_approve_decision(self, decision_type: str, amount: Optional[float] = None) -> bool:
        """Check if role can approve a specific decision type and amount"""
        if decision_type not in self.approval_authority:
            return False
        
        authority = self.approval_authority[decision_type]
        
        # If authority is just True, can approve any amount
        if authority is True:
            return True
        
        # If authority has max_amount, check against it
        if isinstance(authority, dict) and 'max_amount' in authority:
            if amount is None:
                return True
            return amount <= authority['max_amount']
        
        return False
    
    def has_dashboard_access(self, section: str) -> bool:
        """Check if role has access to dashboard section"""
        return section in self.dashboard_access


@dataclass
class User:
    """System user with roles and authentication info"""
    user_id: str
    email: str
    name: str
    roles: List[UserRole]
    department: str
    manager_id: Optional[str] = None
    active: bool = True
    last_login: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    password_hash: Optional[str] = None  # For future password authentication
    
    def __post_init__(self):
        if not self.user_id:
            self.user_id = str(uuid.uuid4())
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission through any role"""
        return any(role.has_permission(permission) for role in self.roles if role)
    
    def can_approve_decision(self, decision_type: str, amount: Optional[float] = None) -> bool:
        """Check if user can approve a specific decision type and amount"""
        return any(
            role.can_approve_decision(decision_type, amount) 
            for role in self.roles if role
        )
    
    def has_dashboard_access(self, section: str) -> bool:
        """Check if user has access to dashboard section"""
        return any(role.has_dashboard_access(section) for role in self.roles if role)
    
    def get_max_approval_amount(self, decision_type: str) -> float:
        """Get maximum amount user can approve for decision type"""
        max_amount = 0.0
        
        for role in self.roles:
            if role and decision_type in role.approval_authority:
                authority = role.approval_authority[decision_type]
                if authority is True:
                    return float('inf')
                elif isinstance(authority, dict) and 'max_amount' in authority:
                    max_amount = max(max_amount, authority['max_amount'])
        
        return max_amount
    
    def get_accessible_dashboard_sections(self) -> List[str]:
        """Get all dashboard sections user can access"""
        sections = set()
        for role in self.roles:
            if role:
                sections.update(role.dashboard_access)
        return list(sections)
    
    def get_all_permissions(self) -> List[str]:
        """Get all permissions user has through roles"""
        permissions = set()
        for role in self.roles:
            if role:
                permissions.update(role.permissions)
        return list(permissions)


@dataclass
class UserSession:
    """User session for authentication tracking"""
    session_id: str
    user_id: str
    created_at: datetime
    expires_at: datetime
    last_activity: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    active: bool = True
    
    def __post_init__(self):
        if not self.session_id:
            self.session_id = str(uuid.uuid4())
    
    @classmethod
    def create_session(cls, user_id: str, duration_hours: int = 24, 
                      ip_address: Optional[str] = None, 
                      user_agent: Optional[str] = None) -> 'UserSession':
        """Create a new user session"""
        now = datetime.now()
        return cls(
            session_id=str(uuid.uuid4()),
            user_id=user_id,
            created_at=now,
            expires_at=now + timedelta(hours=duration_hours),
            last_activity=now,
            ip_address=ip_address,
            user_agent=user_agent,
            active=True
        )
    
    @property
    def is_expired(self) -> bool:
        """Check if session is expired"""
        return datetime.now() > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """Check if session is valid (active and not expired)"""
        return self.active and not self.is_expired
    
    def extend_session(self, hours: int = 24) -> None:
        """Extend session expiration"""
        self.expires_at = datetime.now() + timedelta(hours=hours)
        self.last_activity = datetime.now()
    
    def update_activity(self) -> None:
        """Update last activity timestamp"""
        self.last_activity = datetime.now()


# Predefined roles as specified in the design document
EXECUTIVE_ROLES = {
    'ceo': UserRole(
        role_id='ceo',
        role_name='Chief Executive Officer',
        permissions=['*'],  # All permissions
        approval_authority={
            'cost_decisions': {'max_amount': float('inf')}, 
            'strategic_decisions': True,
            'technical_decisions': True
        },
        dashboard_access=[
            DashboardSection.EXECUTIVE_SUMMARY.value,
            DashboardSection.ALL_DECISIONS.value,
            DashboardSection.SYSTEM_HEALTH.value,
            DashboardSection.COST_ANALYSIS.value,
            DashboardSection.BUDGET_TRACKING.value,
            DashboardSection.FORECASTING.value,
            DashboardSection.TECHNICAL_METRICS.value,
            DashboardSection.RESOURCE_UTILIZATION.value
        ],
        notification_preferences={'email': True, 'sms': True, 'dashboard': True},
        description='Chief Executive Officer with full system access and unlimited approval authority'
    ),
    'cto': UserRole(
        role_id='cto',
        role_name='Chief Technology Officer',
        permissions=[
            PermissionType.TECHNICAL_DECISIONS.value,
            PermissionType.RESOURCE_MANAGEMENT.value,
            PermissionType.SYSTEM_CONFIGURATION.value,
            PermissionType.SYSTEM_HEALTH.value,
            PermissionType.RESOURCE_MONITORING.value
        ],
        approval_authority={
            'technical_decisions': True, 
            'cost_decisions': {'max_amount': 10000}
        },
        dashboard_access=[
            DashboardSection.TECHNICAL_METRICS.value,
            DashboardSection.RESOURCE_UTILIZATION.value,
            DashboardSection.SYSTEM_HEALTH.value,
            DashboardSection.SYSTEM_METRICS.value,
            DashboardSection.RESOURCE_MONITORING.value
        ],
        notification_preferences={'email': True, 'dashboard': True},
        description='Chief Technology Officer with technical decision authority and cost approval up to $10,000'
    ),
    'finops_lead': UserRole(
        role_id='finops_lead',
        role_name='FinOps Lead',
        permissions=[
            PermissionType.COST_ANALYSIS.value,
            PermissionType.BUDGET_MANAGEMENT.value,
            PermissionType.REPORTING.value,
            PermissionType.COST_DECISIONS.value
        ],
        approval_authority={'cost_decisions': {'max_amount': 5000}},
        dashboard_access=[
            DashboardSection.COST_ANALYSIS.value,
            DashboardSection.BUDGET_TRACKING.value,
            DashboardSection.FORECASTING.value,
            DashboardSection.EXECUTIVE_SUMMARY.value
        ],
        notification_preferences={'email': True, 'dashboard': True},
        description='FinOps Lead with cost management authority and approval up to $5,000'
    ),
    'devops_engineer': UserRole(
        role_id='devops_engineer',
        role_name='DevOps Engineer',
        permissions=[
            PermissionType.RESOURCE_MONITORING.value,
            PermissionType.ALERT_MANAGEMENT.value,
            PermissionType.REPORTING.value
        ],
        approval_authority={},  # View only
        dashboard_access=[
            DashboardSection.RESOURCE_MONITORING.value,
            DashboardSection.ALERTS.value,
            DashboardSection.SYSTEM_METRICS.value,
            DashboardSection.TECHNICAL_METRICS.value
        ],
        notification_preferences={'dashboard': True},
        description='DevOps Engineer with monitoring and alerting access (view-only)'
    )
}


@dataclass
class AuthenticationResult:
    """Result of authentication attempt"""
    success: bool
    user: Optional[User] = None
    session: Optional[UserSession] = None
    error_message: Optional[str] = None
    
    @classmethod
    def success_result(cls, user: User, session: UserSession) -> 'AuthenticationResult':
        """Create successful authentication result"""
        return cls(success=True, user=user, session=session)
    
    @classmethod
    def failure_result(cls, error_message: str) -> 'AuthenticationResult':
        """Create failed authentication result"""
        return cls(success=False, error_message=error_message)


@dataclass
class PermissionCheck:
    """Result of permission check"""
    allowed: bool
    user_id: str
    permission: str
    reason: Optional[str] = None
    
    @classmethod
    def allow(cls, user_id: str, permission: str, reason: Optional[str] = None) -> 'PermissionCheck':
        """Create allowed permission check"""
        return cls(allowed=True, user_id=user_id, permission=permission, reason=reason)
    
    @classmethod
    def deny(cls, user_id: str, permission: str, reason: str) -> 'PermissionCheck':
        """Create denied permission check"""
        return cls(allowed=False, user_id=user_id, permission=permission, reason=reason)