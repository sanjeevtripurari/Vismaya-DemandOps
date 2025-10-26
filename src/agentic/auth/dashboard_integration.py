"""
Integration script to demonstrate role-based dashboard functionality
"""

import asyncio
import logging
from typing import Optional

from .authenticated_dashboard import authenticated_dashboard
from .auth_factory import auth_factory

logger = logging.getLogger(__name__)


class DashboardIntegration:
    """Integration helper for connecting authentication with existing dashboard"""
    
    def __init__(self, original_dashboard=None):
        self.authenticated_dashboard = authenticated_dashboard
        self.original_dashboard = original_dashboard
        
        # Connect original dashboard to authenticated dashboard
        if original_dashboard:
            self.authenticated_dashboard.original_dashboard = original_dashboard
    
    async def initialize(self) -> bool:
        """Initialize the integrated dashboard system"""
        try:
            # Initialize authentication system
            auth_success = await auth_factory.initialize()
            if not auth_success:
                logger.error("Failed to initialize authentication system")
                return False
            
            # Initialize authenticated dashboard
            dashboard_success = await self.authenticated_dashboard.initialize()
            if not dashboard_success:
                logger.error("Failed to initialize authenticated dashboard")
                return False
            
            logger.info("Dashboard integration initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize dashboard integration: {e}")
            return False
    
    def run(self) -> None:
        """Run the integrated dashboard"""
        try:
            self.authenticated_dashboard.run()
        except Exception as e:
            logger.error(f"Error running integrated dashboard: {e}")
            import streamlit as st
            st.error(f"Dashboard error: {e}")
    
    async def health_check(self) -> dict:
        """Perform health check on integrated system"""
        try:
            auth_health = await auth_factory.health_check()
            
            return {
                'status': 'healthy' if auth_health['status'] == 'healthy' else 'unhealthy',
                'authentication': auth_health,
                'dashboard': {
                    'status': 'healthy',
                    'original_dashboard_connected': self.original_dashboard is not None
                }
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'authentication': {'status': 'unknown'},
                'dashboard': {'status': 'unknown'}
            }


def create_integrated_dashboard(original_dashboard=None) -> DashboardIntegration:
    """Factory function to create integrated dashboard"""
    return DashboardIntegration(original_dashboard)


# Example usage function
async def demo_authentication_system():
    """Demonstrate the authentication system functionality"""
    print("🔐 Vismaya DemandOps Authentication System Demo")
    print("=" * 50)
    
    try:
        # Initialize authentication system
        print("Initializing authentication system...")
        success = await auth_factory.initialize()
        
        if not success:
            print("❌ Failed to initialize authentication system")
            return
        
        print("✅ Authentication system initialized")
        
        # Get services
        auth_service = auth_factory.get_auth_service()
        role_manager = auth_factory.get_role_manager()
        session_manager = auth_factory.get_session_manager()
        
        # List available users
        print("\n👥 Available Users:")
        users = auth_service.list_users()
        for user in users:
            roles = ", ".join([role.role_name for role in user.roles])
            print(f"  • {user.email} - {roles}")
        
        # Demonstrate authentication
        print("\n🔑 Testing Authentication:")
        test_email = "ceo@company.com"
        
        auth_result = await auth_service.authenticate_user(test_email)
        if auth_result.success:
            print(f"✅ Successfully authenticated {test_email}")
            print(f"   Session ID: {auth_result.session.session_id}")
            print(f"   User: {auth_result.user.name}")
            
            # Test permissions
            print("\n🔍 Testing Permissions:")
            user = auth_result.user
            
            # Test various permissions
            permissions_to_test = [
                "cost_analysis",
                "budget_management", 
                "technical_decisions",
                "system_configuration"
            ]
            
            for permission in permissions_to_test:
                check = role_manager.validate_permission(user, permission)
                status = "✅" if check.allowed else "❌"
                print(f"   {status} {permission}: {check.reason}")
            
            # Test dashboard access
            print("\n📊 Testing Dashboard Access:")
            dashboard_sections = [
                "executive_summary",
                "cost_analysis",
                "technical_metrics",
                "resource_monitoring"
            ]
            
            for section in dashboard_sections:
                check = role_manager.validate_dashboard_access(user, section)
                status = "✅" if check.allowed else "❌"
                print(f"   {status} {section}")
            
            # Test approval authority
            print("\n💰 Testing Approval Authority:")
            test_amounts = [1000, 5000, 15000]
            
            for amount in test_amounts:
                check = role_manager.validate_approval_authority(user, "cost_decisions", amount)
                status = "✅" if check.allowed else "❌"
                print(f"   {status} Cost decision ${amount:,}: {check.reason}")
            
            # Cleanup session
            await auth_service.logout_user(auth_result.session.session_id)
            print(f"\n🚪 Logged out {test_email}")
            
        else:
            print(f"❌ Authentication failed: {auth_result.error_message}")
        
        # System health check
        print("\n🏥 System Health Check:")
        health = await auth_factory.health_check()
        print(f"   Status: {health['status']}")
        print(f"   Active Sessions: {health.get('session_count', 0)}")
        print(f"   Total Users: {health.get('user_count', 0)}")
        
        print("\n✅ Authentication system demo completed successfully!")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        logger.error(f"Demo error: {e}")


if __name__ == "__main__":
    # Run the demo
    asyncio.run(demo_authentication_system())