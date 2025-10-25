#!/usr/bin/env python3
"""
GitHub Actions Setup Script for Vismaya DemandOps
Helps configure GitHub repository secrets for automated deployment
"""

import os
import sys
import json
import subprocess
from pathlib import Path

def print_header():
    """Print setup header"""
    print("=" * 60)
    print("🚀 GitHub Actions Setup for Vismaya DemandOps")
    print("Account: 559928724862")
    print("Repository: https://github.com/sanjeevtripurari/Vismaya-DemandOps")
    print("=" * 60)

def check_github_cli():
    """Check if GitHub CLI is installed"""
    try:
        result = subprocess.run(['gh', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ GitHub CLI is installed")
            return True
        else:
            print("❌ GitHub CLI not found")
            return False
    except FileNotFoundError:
        print("❌ GitHub CLI not found")
        return False

def check_github_auth():
    """Check if user is authenticated with GitHub"""
    try:
        result = subprocess.run(['gh', 'auth', 'status'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ GitHub CLI authenticated")
            return True
        else:
            print("❌ GitHub CLI not authenticated")
            return False
    except Exception:
        print("❌ GitHub CLI authentication check failed")
        return False

def get_current_aws_credentials():
    """Get current AWS credentials from environment or .env file"""
    credentials = {}
    
    # Try environment variables first
    credentials['AWS_ACCESS_KEY_ID'] = os.environ.get('AWS_ACCESS_KEY_ID')
    credentials['AWS_SECRET_ACCESS_KEY'] = os.environ.get('AWS_SECRET_ACCESS_KEY')
    credentials['AWS_SESSION_TOKEN'] = os.environ.get('AWS_SESSION_TOKEN')
    
    # If not in environment, try .env file
    env_file = Path('.env')
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"\'')
                    
                    if key in ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_SESSION_TOKEN']:
                        if not credentials.get(key):  # Don't override env vars
                            credentials[key] = value
    
    return credentials

def get_application_config():
    """Get application configuration"""
    config = {
        'BEDROCK_MODEL_ID': 'us.anthropic.claude-3-haiku-20240307-v1:0',
        'DEFAULT_BUDGET': '80',
        'BUDGET_WARNING_LIMIT': '80',
        'BUDGET_MAXIMUM_LIMIT': '100',
        'SSO_START_URL': 'https://superopsglobalhackathon.awsapps.com/start/#',
        'SSO_ACCOUNT_ID': '559928724862',
        'SSO_ROLE_NAME': 'AdministratorAccess',
        'AWS_USER_EMAIL': 'sanjeevtripurari@gmail.com'
    }
    
    # Try to get from .env file
    env_file = Path('.env')
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"\'')
                    
                    if key in config:
                        config[key] = value
    
    return config

def set_github_secret(secret_name, secret_value):
    """Set a GitHub repository secret"""
    try:
        result = subprocess.run([
            'gh', 'secret', 'set', secret_name, 
            '--body', secret_value,
            '--repo', 'sanjeevtripurari/Vismaya-DemandOps'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Set secret: {secret_name}")
            return True
        else:
            print(f"❌ Failed to set secret {secret_name}: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error setting secret {secret_name}: {e}")
        return False

def setup_github_secrets():
    """Setup all required GitHub secrets"""
    print("\n🔐 Setting up GitHub repository secrets...")
    
    # Get AWS credentials
    aws_creds = get_current_aws_credentials()
    app_config = get_application_config()
    
    # Required secrets
    secrets = {
        **aws_creds,
        **app_config
    }
    
    # Validate required AWS credentials
    required_aws_creds = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_SESSION_TOKEN']
    missing_creds = [cred for cred in required_aws_creds if not secrets.get(cred)]
    
    if missing_creds:
        print(f"❌ Missing AWS credentials: {', '.join(missing_creds)}")
        print("\n🔧 Please ensure you have AWS credentials configured:")
        print("1. Set environment variables, or")
        print("2. Update .env file with current credentials")
        return False
    
    # Set all secrets
    success_count = 0
    total_secrets = len(secrets)
    
    for secret_name, secret_value in secrets.items():
        if secret_value:
            if set_github_secret(secret_name, secret_value):
                success_count += 1
        else:
            print(f"⚠️  Skipping empty secret: {secret_name}")
    
    print(f"\n📊 Set {success_count}/{total_secrets} secrets successfully")
    
    if success_count == total_secrets:
        print("✅ All secrets configured successfully!")
        return True
    else:
        print("⚠️  Some secrets failed to configure")
        return False

def show_deployment_instructions():
    """Show deployment instructions"""
    print("\n" + "=" * 60)
    print("🚀 GitHub Actions Deployment Ready!")
    print("=" * 60)
    
    print("\n📋 Next Steps:")
    print("1. Push your code to the v2-dev branch:")
    print("   git add .")
    print("   git commit -m 'Setup GitHub Actions deployment'")
    print("   git push origin v2-dev")
    
    print("\n2. Or trigger manual deployment:")
    print("   Go to: https://github.com/sanjeevtripurari/Vismaya-DemandOps/actions")
    print("   Click 'Deploy Vismaya DemandOps to AWS'")
    print("   Click 'Run workflow'")
    print("   Select options and click 'Run workflow'")
    
    print("\n3. Monitor deployment:")
    print("   - GitHub Actions tab will show progress")
    print("   - Deployment creates EC2 infrastructure")
    print("   - Application will be available at the provided URL")
    
    print("\n🔄 Credential Refresh:")
    print("   AWS SSO credentials expire periodically")
    print("   Re-run this script to update secrets when needed")
    
    print("\n🌐 Expected Result:")
    print("   Your Vismaya DemandOps application running on AWS EC2")
    print("   Accessible via Application Load Balancer URL")
    print("   Automatic scaling and health monitoring")

def main():
    """Main setup function"""
    print_header()
    
    # Check prerequisites
    if not check_github_cli():
        print("\n❌ GitHub CLI is required for this setup")
        print("📥 Install from: https://cli.github.com/")
        sys.exit(1)
    
    if not check_github_auth():
        print("\n❌ Please authenticate with GitHub CLI:")
        print("   gh auth login")
        sys.exit(1)
    
    # Setup secrets
    if setup_github_secrets():
        show_deployment_instructions()
        print("\n🎉 GitHub Actions setup completed successfully!")
    else:
        print("\n❌ GitHub Actions setup failed")
        print("🔧 Please check your AWS credentials and try again")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)