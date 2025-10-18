import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # AWS Configuration
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-2')
    AWS_PROFILE = os.getenv('AWS_PROFILE', 'default')
    
    # AWS SSO Configuration
    SSO_START_URL = os.getenv('SSO_START_URL', 'https://superopsglobalhackathon.awsapps.com/start/#')
    SSO_REGION = os.getenv('SSO_REGION', 'us-east-2')
    SSO_ACCOUNT_ID = os.getenv('SSO_ACCOUNT_ID')
    SSO_ROLE_NAME = os.getenv('SSO_ROLE_NAME')
    AWS_USER_EMAIL = os.getenv('AWS_USER_EMAIL')
    
    # For AWS deployment or explicit credentials
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_SESSION_TOKEN = os.getenv('AWS_SESSION_TOKEN')
    
    # Bedrock Configuration
    BEDROCK_MODEL_ID = os.getenv('BEDROCK_MODEL_ID', 'us.anthropic.claude-3-haiku-20240307-v1:0')
    
    # Application Configuration
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    PORT = int(os.getenv('PORT', 8501))
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
    
    # Budget Configuration
    DEFAULT_BUDGET = int(os.getenv('DEFAULT_BUDGET', 80))  # Warning threshold
    BUDGET_WARNING_LIMIT = int(os.getenv('BUDGET_WARNING_LIMIT', 80))  # Warning at $80
    BUDGET_MAXIMUM_LIMIT = int(os.getenv('BUDGET_MAXIMUM_LIMIT', 100))  # Hard limit at $100
    
    @classmethod
    def is_production(cls):
        return cls.ENVIRONMENT.lower() == 'production'
    
    @classmethod
    def use_sso(cls):
        """Check if we should use SSO authentication"""
        # Use explicit credentials if they are provided
        if cls.AWS_ACCESS_KEY_ID and cls.AWS_SECRET_ACCESS_KEY:
            return False
        # Otherwise use SSO/profile
        return True
    
    @classmethod
    def has_credentials(cls):
        """Check if explicit credentials are available"""
        return bool(cls.AWS_ACCESS_KEY_ID and cls.AWS_SECRET_ACCESS_KEY)