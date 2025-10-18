"""
Production Error Handler for AWS Operations
Provides clear error messages for different deployment environments
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class AWSErrorHandler:
    """Handle AWS errors with production-ready messages"""
    
    @staticmethod
    def handle_aws_error(error: Exception, operation: str, user_email: str = None) -> str:
        """Convert AWS errors to user-friendly messages"""
        error_str = str(error).lower()
        
        # Extract user identifier for better error messages
        user_display = user_email if user_email else "your account"
        
        # Credential-related errors
        if any(keyword in error_str for keyword in ['expiredtoken', 'expired', 'invalid']):
            return f"AWS credentials have expired for {user_display}. Please refresh your SSO session and try again."
        
        # Permission-related errors
        if any(keyword in error_str for keyword in ['accessdenied', 'unauthorized', 'forbidden']):
            if 'ce:getcostandu' in error_str:
                return f"Access denied: {user_display} needs Cost Explorer permissions (ce:GetCostAndUsage). Contact your AWS administrator."
            elif 'bedrock:' in error_str:
                return f"Access denied: {user_display} needs Bedrock permissions. Contact your AWS administrator or check if Bedrock is enabled."
            else:
                return f"Access denied to AWS {operation} for {user_display}. Check your IAM permissions."
        
        # Network-related errors
        if any(keyword in error_str for keyword in ['timeout', 'connection', 'network']):
            return f"Network error connecting to AWS. Check your internet connection."
        
        # Service-specific errors
        if 'cost explorer' in error_str:
            return "AWS Cost Explorer is not available. Ensure Cost Explorer is enabled in your AWS account."
        
        if 'bedrock' in error_str:
            return "AWS Bedrock is not available in this region or account. Check service availability."
        
        # Rate limiting
        if any(keyword in error_str for keyword in ['throttling', 'rate', 'limit']):
            return "AWS API rate limit exceeded. Please wait a moment and try again."
        
        # Generic AWS error
        if 'aws' in error_str or 'boto' in error_str:
            return f"AWS service error: {str(error)[:100]}..."
        
        # Unknown error
        return f"Unexpected error in {operation}: {str(error)[:100]}..."
    
    @staticmethod
    def get_deployment_context() -> Dict[str, Any]:
        """Get information about the deployment environment"""
        import os
        
        context = {
            'environment': 'unknown',
            'has_iam_role': False,
            'has_credentials': False,
            'region': os.environ.get('AWS_REGION', 'not-set')
        }
        
        # Check if running on AWS
        if os.environ.get('AWS_EXECUTION_ENV'):
            context['environment'] = 'lambda'
        elif os.environ.get('ECS_CONTAINER_METADATA_URI'):
            context['environment'] = 'ecs'
        elif os.path.exists('/proc/sys/kernel/random/boot_id'):
            try:
                import requests
                response = requests.get('http://169.254.169.254/latest/meta-data/instance-id', timeout=2)
                if response.status_code == 200:
                    context['environment'] = 'ec2'
            except:
                pass
        else:
            context['environment'] = 'local'
        
        # Check for IAM role
        try:
            import boto3
            session = boto3.Session()
            sts = session.client('sts')
            identity = sts.get_caller_identity()
            if 'role' in identity.get('Arn', '').lower():
                context['has_iam_role'] = True
        except:
            pass
        
        # Check for explicit credentials
        if os.environ.get('AWS_ACCESS_KEY_ID'):
            context['has_credentials'] = True
        
        return context
    
    @staticmethod
    def log_deployment_info():
        """Log deployment environment information"""
        context = AWSErrorHandler.get_deployment_context()
        
        logger.info("🚀 Deployment Environment Information:")
        logger.info(f"   Environment: {context['environment']}")
        logger.info(f"   Region: {context['region']}")
        logger.info(f"   Has IAM Role: {context['has_iam_role']}")
        logger.info(f"   Has Credentials: {context['has_credentials']}")
        
        # Provide deployment-specific guidance
        if context['environment'] == 'local':
            logger.info("   💡 Local development detected - ensure AWS credentials are configured")
        elif context['environment'] in ['ec2', 'ecs', 'lambda']:
            logger.info("   ☁️ AWS deployment detected - using IAM roles for authentication")
        
        return context