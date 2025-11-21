"""
Role management and permission validation service
"""

from typing import Dict, List, Optional, Any
import logging

from .models import User, UserRole, PermissionCheck, PermissionType, DashboardSection, EXECUTIVE_ROLES

logger = logging.getLogger(__name__)


class RoleManager:
    """Manages user roles and permission validation"""
    
    def __init__(self):
        self._custom_roles: Dict[str, UserRole] = {}  # For future custom roles
    
    def get_role(self, role_id: str) -> Optional[UserRole]:
        """Get role by ID"""
        # Check predefined roles first
        if role_id in EXECUTIVE_ROLES:
            return EXECUTIVE_ROLES[role_id]
        
        # Check custom roles
        return self._custom_roles.get(role_id)
    
    def get_all_roles(self) -> Dict[str, UserRole]:
        """Get all available roles"""
        all_roles = EXECUTIVE_ROLES.copy()
        all_roles.update(self._custom_roles)
        return all_roles
    
    def validate_permission(self, user: User, permission: str, 
                          context: Optional[Dict[str, Any]] = None) -> PermissionCheck:
        """Validate if user has specific permission"""
        if not user or not user.active:
            return PermissionCheck.deny(
                user.user_id if user else "unknown",
                permission,
                "User is inactive or not found"
            )
        
        # Check if user has permission through any role
        if user.has_permission(permission):
            return PermissionCheck.allow(
                user.user_id,
                permission,
                f"Permission granted through user roles: {[r.role_name for r in user.roles]}"
            )
        
        return PermissionCheck.deny(
            user.user_id,
            permission,
            f"User does not have required permission. User roles: {[r.role_name for r in user.roles]}"
        )
    
    def validate_dashboard_access(self, user: User, section: str) -> PermissionCheck:
        """Validate if user can access dashboard section"""
        if not user or not user.active:
            return PermissionCheck.deny(
                user.user_id if user else "unknown",
                f"dashboard_access:{section}",
                "User is inactive or not found"
            )
        
        if user.has_dashboard_access(section):
            return PermissionCheck.allow(
                user.user_id,
                f"dashboard_access:{section}",
                f"Dashboard access granted through user roles"
            )
        
        return PermissionCheck.deny(
            user.user_id,
            f"dashboard_access:{section}",
            f"User does not have access to dashboard section '{section}'"
        )
    
    def validate_approval_authority(self, user: User, decision_type: str, 
                                  amount: Optional[float] = None) -> PermissionCheck:
        """Validate if user can approve specific decision type and amount"""
        if not user or not user.active:
            return PermissionCheck.deny(
                user.user_id if user else "unknown",
                f"approve:{decision_type}",
                "User is inactive or not found"
            )
        
        if user.can_approve_decision(decision_type, amount):
            max_amount = user.get_max_approval_amount(decision_type)
            reason = f"Approval authority granted. Max amount: {'unlimited' if max_amount == float('inf') else f'${max_amount:,.2f}'}"
            return PermissionCheck.allow(
                user.user_id,
                f"approve:{decision_type}",
                reason
            )
        
        max_amount = user.get_max_approval_amount(decision_type)
        if max_amount == 0:
            reason = f"User has no approval authority for '{decision_type}'"
        else:
            reason = f"Amount ${amount:,.2f} exceeds user's approval limit of ${max_amount:,.2f} for '{decision_type}'"
        
        return PermissionCheck.deny(
            user.user_id,
            f"approve:{decision_type}",
            reason
        )
    
    def get_user_permissions_summary(self, user: User) -> Dict[str, Any]:
        """Get comprehensive summary of user permissions"""
        if not user:
            return {}
        
        return {
            'user_id': user.user_id,
            'email': user.email,
            'name': user.name,
            'active': user.active,
            'roles': [
                {
                    'role_id': role.role_id,
                    'role_name': role.role_name,
                    'description': role.description
                }
                for role in user.roles
            ],
            'permissions': user.get_all_permissions(),
            'dashboard_access': user.get_accessible_dashboard_sections(),
            'approval_authority': self._get_approval_authority_summary(user),
            'last_login': user.last_login.isoformat() if user.last_login else None
        }
    
    def _get_approval_authority_summary(self, user: User) -> Dict[str, Any]:
        """Get summary of user's approval authority"""
        authority = {}
        
        # Common decision types to check
        decision_types = ['cost_decisions', 'technical_decisions', 'strategic_decisions']
        
        for decision_type in decision_types:
            max_amount = user.get_max_approval_amount(decision_type)
            if max_amount > 0:
                authority[decision_type] = {
                    'can_approve': True,
                    'max_amount': max_amount if max_amount != float('inf') else 'unlimited'
                }
            else:
                authority[decision_type] = {
                    'can_approve': False,
                    'max_amount': 0
                }
        
        return authority
    
    def create_custom_role(self, role_id: str, role_name: str, permissions: List[str],
                          approval_authority: Dict[str, Any], dashboard_access: List[str],
                          notification_preferences: Dict[str, Any],
                          description: Optional[str] = None) -> UserRole:
        """Create a custom role"""
        if role_id in EXECUTIVE_ROLES:
            raise ValueError(f"Cannot override predefined role: {role_id}")
        
        if role_id in self._custom_roles:
            raise ValueError(f"Custom role already exists: {role_id}")
        
        role = UserRole(
            role_id=role_id,
            role_name=role_name,
            permissions=permissions,
            approval_authority=approval_authority,
            dashboard_access=dashboard_access,
            notification_preferences=notification_preferences,
            description=description
        )
        
        self._custom_roles[role_id] = role
        logger.info(f"Created custom role: {role_id}")
        return role
    
    def update_custom_role(self, role_id: str, **updates) -> bool:
        """Update custom role"""
        if role_id in EXECUTIVE_ROLES:
            raise ValueError(f"Cannot modify predefined role: {role_id}")
        
        if role_id not in self._custom_roles:
            return False
        
        role = self._custom_roles[role_id]
        
        for key, value in updates.items():
            if hasattr(role, key):
                setattr(role, key, value)
        
        logger.info(f"Updated custom role: {role_id}")
        return True
    
    def delete_custom_role(self, role_id: str) -> bool:
        """Delete custom role"""
        if role_id in EXECUTIVE_ROLES:
            raise ValueError(f"Cannot delete predefined role: {role_id}")
        
        if role_id in self._custom_roles:
            del self._custom_roles[role_id]
            logger.info(f"Deleted custom role: {role_id}")
            return True
        
        return False
    
    def get_users_with_permission(self, users: List[User], permission: str) -> List[User]:
        """Get all users that have specific permission"""
        return [user for user in users if user.has_permission(permission)]
    
    def get_users_with_approval_authority(self, users: List[User], decision_type: str,
                                        amount: Optional[float] = None) -> List[User]:
        """Get all users that can approve specific decision type and amount"""
        return [user for user in users if user.can_approve_decision(decision_type, amount)]
    
    def get_role_hierarchy(self) -> Dict[str, int]:
        """Get role hierarchy for permission precedence"""
        # Define role hierarchy (higher number = more authority)
        hierarchy = {
            'ceo': 100,
            'cto': 80,
            'finops_lead': 60,
            'devops_engineer': 40
        }
        
        # Add custom roles with default hierarchy
        for role_id in self._custom_roles:
            if role_id not in hierarchy:
                hierarchy[role_id] = 50  # Default level
        
        return hierarchy