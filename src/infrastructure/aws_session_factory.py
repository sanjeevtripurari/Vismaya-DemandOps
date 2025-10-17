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
        """Create AWS session with appropriate authentication"""
        try:
            if self._config.use_sso():
                logger.info("Creating AWS session with SSO/Profile authentication")
                session = boto3.Session(
                    profile_name=self._config.AWS_PROFILE,
                    region_name=self._config.AWS_REGION
                )
            else:
                logger.info("Creating AWS session with explicit credentials")
                session = boto3.Session(
                    aws_access_key_id=self._config.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=self._config.AWS_SECRET_ACCESS_KEY,
                    aws_session_token=self._config.AWS_SESSION_TOKEN,
                    region_name=self._config.AWS_REGION
                )
            
            # Test the session
            sts = session.client('sts')
            identity = sts.get_caller_identity()
            logger.info(f"AWS session created successfully - Account: {identity.get('Account', 'Unknown')}")
            
            self._session = session
            return session
            
        except Exception as e:
            logger.warning(f"Error creating AWS session: {e}. Using default session.")
            self._session = boto3.Session(region_name=self._config.AWS_REGION)
            return self._session
    
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