#!/usr/bin/env python3
"""
Local AWS Credentials Setup for Vismaya DemandOps
Sets up AWS credentials for local testing
"""

import os
import sys
import subprocess
from pathlib import Path

def create_aws_directory():
    """Create .aws directory if it doesn't exist"""
    aws_dir = Path.home() / '.aws'
    aws_dir.mkdir(exist_ok=True)
    print(f"✅ AWS directory created/verified: {aws_dir}")
    return aws_dir

def setup_credentials_file(aws_dir):
    """Setup AWS credentials file"""
    credentials_file = aws_dir / 'credentials'
    
    print("\n🔐 Setting up AWS credentials...")
    print("Please provide your AWS credentials from the hackathon environment:")
    
    access_key = input("AWS Access Key ID: ").strip()
    secret_key = input("AWS Secret Access Key: ").strip()
    session_token = input("AWS Session Token (optional): ").strip()
    
    credentials_content = f"""[default]
aws_access_key_id = {access_key}
aws_secret_access_key = {secret_key}"""
    
    if session_token:
        credentials_content += f"\naws_session_token = {session_token}"
    
    credentials_content += f"""

[hackathon]
aws_access_key_id = {access_key}
aws_secret_access_key = {secret_key}"""
    
    if session_token:
        credentials_content += f"\naws_session_token = {session_token}"
    
    with open(credentials_file, 'w') as f:
        f.write(credentials_content)
    
    # Set appropriate permissions (Unix/Linux/Mac)
    if os.name != 'nt':
        os.chmod(credentials_file, 0o600)
    
    print(f"✅ Credentials saved to: {credentials_file}")
    return access_key, secret_key, session_token

def setup_config_file(aws_dir):
    """Setup AWS config file"""
    config_file = aws_dir / 'config'
    
    config_content = """[default]
region = us-east-2
output = json

[profile hackathon]
region = us-east-2
output = json
sso_start_url = https://superopsglobalhackathon.awsapps.com/start/#
sso_region = us-east-2"""
    
    with open(config_file, 'w') as f:
        f.write(config_content)
    
    print(f"✅ Config saved to: {config_file}")

def update_env_file(access_key, secret_key, session_token):
    """Update .env file with credentials"""
    env_file = Path('.env')
    
    if not env_file.exists():
        print("⚠️  .env file not found, creating from template...")
        subprocess.run(['cp', '.env.example', '.env'], check=True)
    
    # Read current .env content
    with open(env_file, 'r') as f:
        content = f.read()
    
    # Update credentials
    lines = content.split('\n')
    updated_lines = []
    
    for line in lines:
        if line.startswith('AWS_ACCESS_KEY_ID='):
            updated_lines.append(f'AWS_ACCESS_KEY_ID={access_key}')
        elif line.startswith('AWS_SECRET_ACCESS_KEY='):
            updated_lines.append(f'AWS_SECRET_ACCESS_KEY={secret_key}')
        elif line.startswith('AWS_SESSION_TOKEN='):
            updated_lines.append(f'AWS_SESSION_TOKEN={session_token}')
        else:
            updated_lines.append(line)
    
    # Write updated content
    with open(env_file, 'w') as f:
        f.write('\n'.join(updated_lines))
    
    print(f"✅ Updated .env file with credentials")

def test_credentials():
    """Test AWS credentials"""
    print("\n🧪 Testing AWS credentials...")
    
    try:
        result = subprocess.run(['aws', 'sts', 'get-caller-identity'], 
                              capture_output=True, text=True, check=True)
        
        import json
        identity = json.loads(result.stdout)
        print(f"✅ AWS credentials working!")
        print(f"   Account: {identity.get('Account', 'Unknown')}")
        print(f"   User: {identity.get('Arn', 'Unknown')}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ AWS credentials test failed: {e}")
        print("Please check your credentials and try again")
        return False
    except FileNotFoundError:
        print("⚠️  AWS CLI not found. Please install AWS CLI v2")
        print("   https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html")
        return False

def main():
    """Main setup function"""
    print("=" * 60)
    print("🔐 Vismaya DemandOps - Local AWS Credentials Setup")
    print("=" * 60)
    
    # Create AWS directory
    aws_dir = create_aws_directory()
    
    # Setup credentials
    access_key, secret_key, session_token = setup_credentials_file(aws_dir)
    
    # Setup config
    setup_config_file(aws_dir)
    
    # Update .env file
    update_env_file(access_key, secret_key, session_token)
    
    # Test credentials
    if test_credentials():
        print("\n" + "=" * 60)
        print("🎉 AWS credentials setup completed successfully!")
        print("=" * 60)
        print("\n🚀 Next steps:")
        print("1. Run the application: python app.py")
        print("2. Or test first: python local-test.py")
        print("3. Dashboard will be at: http://localhost:8501")
    else:
        print("\n" + "=" * 60)
        print("⚠️  Setup completed but credentials test failed")
        print("Please verify your credentials and try again")
        print("=" * 60)

if __name__ == "__main__":
    main()