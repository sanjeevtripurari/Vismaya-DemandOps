"""
AWS Session Factory
Creates and manages AWS sessions with proper authentication
Following Factory Pattern and Single Responsibility Principle
"""

import boto3
import logging
from typing import Optional, Dict

from ..core.interfaces import IAuthenticationService

logger = logging.getLogger(__name__)


class AWSSessionFactory:
    """Factory for creating AWS sessions"""
    
    def __init__(self, config):
        self._config = config
        self._session = None
    
    def create_session(self) -> boto3.Session:
        """Create AWS session with appropriate authentication for different environments"""
        try:
            # Priority order for AWS credentials:
            # 1. Explicit credentials (for local development)
            # 2. IAM roles (for AWS deployment)
            # 3. SSO/Profile (for local development)
            # 4. Environment variables (for Docker)
            
            session = None
            auth_method = "unknown"
            
            # Try explicit credentials first (local development)
            if (hasattr(self._config, 'AWS_ACCESS_KEY_ID') and 
                self._config.AWS_ACCESS_KEY_ID and 
                len(self._config.AWS_ACCESS_KEY_ID.strip()) > 10):
                
                logger.info("Using explicit AWS credentials")
                session = boto3.Session(
                    aws_access_key_id=self._config.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=self._config.AWS_SECRET_ACCESS_KEY,
                    aws_session_token=self._config.AWS_SESSION_TOKEN,
                    region_name=self._config.AWS_REGION
                )
                auth_method = "explicit_credentials"
                
            # Try IAM role (AWS deployment - EC2, ECS, Lambda)
            elif self._is_running_on_aws():
                logger.info("Detected AWS environment, using IAM role")
                session = boto3.Session(region_name=self._config.AWS_REGION)
                auth_method = "iam_role"
                
            # Try SSO/Profile (local development)
            elif self._config.use_sso():
                logger.info("Using AWS SSO/Profile authentication")
                session = boto3.Session(
                    profile_name=self._config.AWS_PROFILE,
                    region_name=self._config.AWS_REGION
                )
                auth_method = "sso_profile"
                
            # Try default session (environment variables, instance metadata)
            else:
                logger.info("Using default AWS session (env vars or instance metadata)")
                session = boto3.Session(region_name=self._config.AWS_REGION)
                auth_method = "default"
            
            # Test the session
            sts = session.client('sts')
            identity = sts.get_caller_identity()
            
            # Get user identifier - prefer email if available
            user_identifier = getattr(self._config, 'AWS_USER_EMAIL', None)
            if not user_identifier:
                user_identifier = identity.get('Arn', 'Unknown').split('/')[-1]
            
            logger.info(f"✅ AWS session created successfully")
            logger.info(f"   Auth Method: {auth_method}")
            logger.info(f"   Account: {identity.get('Account', 'Unknown')}")
            logger.info(f"   Region: {self._config.AWS_REGION}")
            logger.info(f"   User: {user_identifier}")
            
            self._session = session
            return session
            
        except Exception as e:
            logger.error(f"❌ Failed to create AWS session: {e}")
            logger.error("   Check your AWS credentials and permissions")
            raise Exception(f"AWS authentication failed: {str(e)}")
    
    def _is_running_on_aws(self) -> bool:
        """Detect if running on AWS (EC2, ECS, Lambda, etc.)"""
        try:
            import os
            import requests
            
            # Check for AWS environment variables
            aws_env_vars = [
                'AWS_EXECUTION_ENV',  # Lambda
                'ECS_CONTAINER_METADATA_URI',  # ECS
                'AWS_CONTAINER_CREDENTIALS_RELATIVE_URI'  # ECS
            ]
            
            for env_var in aws_env_vars:
                if os.environ.get(env_var):
                    logger.info(f"Detected AWS environment: {env_var}")
                    return True
            
            # Try to access EC2 instance metadata (with timeout)
            try:
                response = requests.get(
                    'http://169.254.169.254/latest/meta-data/instance-id',
                    timeout=2
                )
                if response.status_code == 200:
                    logger.info("Detected EC2 instance metadata")
                    return True
            except:
                pass
            
            return False
            
        except Exception:
            return False
    
    def get_session(self) -> boto3.Session:
        """Get existing session or create new one"""
        if self._session is None:
            return self.create_session()
        return self._session


class AWSAuthenticationService(IAuthenticationService):
    """AWS authentication service implementation"""
    
    def __init__(self, session_factory: AWSSessionFactory):
        self._session_factory = session_factory
        self._authenticated = False
        self._caller_identity = None
    
    async def authenticate(self) -> bool:
        """Authenticate with AWS"""
        try:
            session = self._session_factory.get_session()
            sts = session.client('sts')
            self._caller_identity = sts.get_caller_identity()
            self._authenticated = True
            logger.info("AWS authentication successful")
            return True
        except Exception as e:
            logger.error(f"AWS authentication failed: {e}")
            self._authenticated = False
            return False
    
    async def get_caller_identity(self) -> Dict:
        """Get current AWS caller identity"""
        if not self._authenticated:
            await self.authenticate()
        
        return self._caller_identity or {}
    
    def is_authenticated(self) -> bool:
        """Check if currently authenticated"""
        return self._authenticated