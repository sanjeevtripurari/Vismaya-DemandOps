#!/usr/bin/env python3
"""
AWS SSO Setup Helper for Vismaya DemandOps
"""

import subprocess
import sys
import os
from config import Config

def check_aws_cli():
    """Check if AWS CLI is installed"""
    try:
        result = subprocess.run(['aws', '--version'], capture_output=True, text=True)
        print(f"✅ AWS CLI found: {result.stdout.strip()}")
        return True
    except FileNotFoundError:
        print("❌ AWS CLI not found. Please install AWS CLI v2:")
        print("   https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html")
        return False

def setup_sso():
    """Setup AWS SSO"""
    print("\n🔐 Setting up AWS SSO...")
    print(f"SSO Start URL: {Config.SSO_START_URL}")
    print(f"SSO Region: {Config.SSO_REGION}")
    
    try:
        # Configure SSO
        subprocess.run([
            'aws', 'configure', 'sso',
            '--profile', Config.AWS_PROFILE
        ], check=True)
        
        print(f"✅ SSO configured for profile: {Config.AWS_PROFILE}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error configuring SSO: {e}")
        return False

def login_sso():
    """Login to AWS SSO"""
    print(f"\n🔑 Logging in to AWS SSO (Profile: {Config.AWS_PROFILE})...")
    try:
        subprocess.run([
            'aws', 'sso', 'login',
            '--profile', Config.AWS_PROFILE
        ], check=True)
        
        print("✅ SSO login successful")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error logging in: {e}")
        return False

def test_credentials():
    """Test AWS credentials"""
    print("\n🧪 Testing AWS credentials...")
    try:
        result = subprocess.run([
            'aws', 'sts', 'get-caller-identity',
            '--profile', Config.AWS_PROFILE
        ], capture_output=True, text=True, check=True)
        
        import json
        identity = json.loads(result.stdout)
        print(f"✅ Authentication successful!")
        print(f"   Account: {identity.get('Account')}")
        print(f"   User: {identity.get('Arn')}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Authentication failed: {e}")
        return False

def main():
    """Main setup function"""
    print("=" * 60)
    print("🎯 Vismaya DemandOps - AWS SSO Setup")
    print("=" * 60)
    
    # Check AWS CLI
    if not check_aws_cli():
        sys.exit(1)
    
    # Setup SSO
    print("\nChoose an option:")
    print("1. Configure new SSO profile")
    print("2. Login to existing SSO profile")
    print("3. Test current credentials")
    print("4. Exit")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    if choice == '1':
        if setup_sso():
            login_sso()
            test_credentials()
    elif choice == '2':
        if login_sso():
            test_credentials()
    elif choice == '3':
        test_credentials()
    elif choice == '4':
        print("👋 Goodbye!")
    else:
        print("❌ Invalid choice")
        sys.exit(1)
    
    print("\n🚀 You can now run: python app.py")

if __name__ == "__main__":
    main()