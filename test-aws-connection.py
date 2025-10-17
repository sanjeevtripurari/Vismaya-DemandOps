#!/usr/bin/env python3
"""
Test AWS Connection for Vismaya DemandOps
Quick test to verify AWS credentials and connectivity
"""

import boto3
import json
from config import Config

def test_basic_connection():
    """Test basic AWS connection"""
    print("🔗 Testing basic AWS connection...")
    
    try:
        if Config.use_sso():
            print(f"   Using AWS Profile: {Config.AWS_PROFILE}")
            session = boto3.Session(
                profile_name=Config.AWS_PROFILE,
                region_name=Config.AWS_REGION
            )
        else:
            print("   Using explicit credentials")
            session = boto3.Session(
                aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
                aws_session_token=Config.AWS_SESSION_TOKEN,
                region_name=Config.AWS_REGION
            )
        
        sts = session.client('sts')
        identity = sts.get_caller_identity()
        
        print("✅ AWS connection successful!")
        print(f"   Account: {identity.get('Account', 'Unknown')}")
        print(f"   User: {identity.get('Arn', 'Unknown')}")
        print(f"   Region: {Config.AWS_REGION}")
        
        return session
        
    except Exception as e:
        print(f"❌ AWS connection failed: {e}")
        return None

def test_cost_explorer(session):
    """Test Cost Explorer access"""
    print("\n💰 Testing Cost Explorer access...")
    
    try:
        ce = session.client('ce')
        
        # Try to get current month costs
        from datetime import datetime
        now = datetime.now()
        start_date = now.replace(day=1).strftime('%Y-%m-%d')
        end_date = now.strftime('%Y-%m-%d')
        
        response = ce.get_cost_and_usage(
            TimePeriod={
                'Start': start_date,
                'End': end_date
            },
            Granularity='MONTHLY',
            Metrics=['BlendedCost']
        )
        
        if response['ResultsByTime']:
            amount = response['ResultsByTime'][0]['Total']['BlendedCost']['Amount']
            print(f"✅ Cost Explorer access successful!")
            print(f"   Current month cost: ${float(amount):.2f}")
        else:
            print("✅ Cost Explorer access successful (no cost data)")
        
        return True
        
    except Exception as e:
        print(f"❌ Cost Explorer access failed: {e}")
        return False

def test_ec2_access(session):
    """Test EC2 access"""
    print("\n🖥️  Testing EC2 access...")
    
    try:
        ec2 = session.client('ec2')
        response = ec2.describe_instances()
        
        instance_count = 0
        for reservation in response['Reservations']:
            instance_count += len(reservation['Instances'])
        
        print(f"✅ EC2 access successful!")
        print(f"   Found {instance_count} instances")
        
        return True
        
    except Exception as e:
        print(f"❌ EC2 access failed: {e}")
        return False

def test_bedrock_access(session):
    """Test Bedrock access"""
    print("\n🤖 Testing Bedrock access...")
    
    try:
        bedrock = session.client('bedrock-runtime')
        
        # Try to list available models (this is a read-only operation)
        bedrock_models = session.client('bedrock')
        response = bedrock_models.list_foundation_models()
        
        model_count = len(response.get('modelSummaries', []))
        print(f"✅ Bedrock access successful!")
        print(f"   Found {model_count} available models")
        
        # Check if our specific model is available
        claude_available = any(
            model['modelId'] == Config.BEDROCK_MODEL_ID 
            for model in response.get('modelSummaries', [])
        )
        
        if claude_available:
            print(f"   ✅ Claude model ({Config.BEDROCK_MODEL_ID}) is available")
        else:
            print(f"   ⚠️  Claude model ({Config.BEDROCK_MODEL_ID}) not found")
        
        return True
        
    except Exception as e:
        print(f"❌ Bedrock access failed: {e}")
        print("   Note: Bedrock may not be available in all regions or accounts")
        return False

def main():
    """Main test function"""
    print("=" * 60)
    print("🧪 Vismaya DemandOps - AWS Connection Test")
    print("Team MaximAI - AI-Powered FinOps Platform")
    print("=" * 60)
    
    # Test basic connection
    session = test_basic_connection()
    if not session:
        print("\n❌ Basic AWS connection failed. Please check your credentials.")
        return
    
    # Test individual services
    services_tested = 0
    services_working = 0
    
    if test_cost_explorer(session):
        services_working += 1
    services_tested += 1
    
    if test_ec2_access(session):
        services_working += 1
    services_tested += 1
    
    if test_bedrock_access(session):
        services_working += 1
    services_tested += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    print(f"Services tested: {services_tested}")
    print(f"Services working: {services_working}")
    
    if services_working == services_tested:
        print("🎉 All AWS services are accessible!")
        print("\n🚀 You can now run the application:")
        print("   python app.py")
    elif services_working > 0:
        print("⚠️  Some AWS services are accessible.")
        print("   The application will work with limited functionality.")
        print("\n🚀 You can still run the application:")
        print("   python app.py")
    else:
        print("❌ No AWS services are accessible.")
        print("   Please check your credentials and permissions.")
    
    print("=" * 60)

if __name__ == "__main__":
    main()