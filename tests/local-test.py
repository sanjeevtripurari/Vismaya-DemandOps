#!/usr/bin/env python3
"""
Local Testing Script for Vismaya DemandOps
Tests the application locally before deployment
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import subprocess
import sys
import time
import requests
from config import Config

def test_dependencies():
    """Test if all dependencies are installed"""
    print("🧪 Testing dependencies...")
    try:
        import streamlit
        import boto3
        import plotly
        import pandas
        import numpy
        print("✅ All dependencies installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        return False

def test_aws_connection():
    """Test AWS connection"""
    print("🔗 Testing AWS connection...")
    try:
        from aws_client import AWSClient
        client = AWSClient()
        
        # Try to get caller identity
        sts = client.session.client('sts')
        identity = sts.get_caller_identity()
        print(f"✅ AWS connection successful - Account: {identity.get('Account', 'Unknown')}")
        return True
    except Exception as e:
        print(f"⚠️  AWS connection warning: {e}")
        print("📝 App will use mock data for demonstration")
        return False

def test_bedrock_access():
    """Test Bedrock access"""
    print("🤖 Testing Bedrock access...")
    try:
        from ai_assistant import AIAssistant
        assistant = AIAssistant()
        
        if assistant.bedrock is None:
            user_email = getattr(Config, 'AWS_USER_EMAIL', 'your account')
            print(f"❌ Bedrock not available for {user_email}")
            print("   💡 Contact AWS administrator to add bedrock:InvokeModel permission")
            return False
        
        # Try a simple test
        response = assistant.analyze_costs(1000, 5000, 1200, {'EC2': 500, 'RDS': 500})
        if response and not response.startswith("I'm having trouble"):
            print("✅ Bedrock access successful")
            return True
        else:
            user_email = getattr(Config, 'AWS_USER_EMAIL', 'your account')
            print(f"❌ Bedrock access denied for {user_email}")
            print("   💡 Contact AWS administrator to add bedrock:InvokeModel permission")
            return False
    except Exception as e:
        error_str = str(e)
        if 'AccessDenied' in error_str or 'not authorized' in error_str:
            user_email = getattr(Config, 'AWS_USER_EMAIL', 'your account')
            print(f"❌ Bedrock access denied for {user_email}")
            print("   💡 Contact AWS administrator to add bedrock:InvokeModel permission")
        else:
            print(f"❌ Bedrock connection failed: {error_str[:100]}...")
        return False

def start_app_background():
    """Start the app in background"""
    print("🚀 Starting Vismaya DemandOps...")
    try:
        process = subprocess.Popen([
            sys.executable, "-m", "streamlit", "run", "dashboard.py",
            "--server.port", str(Config.PORT),
            "--server.headless", "true",
            "--browser.gatherUsageStats", "false"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        return process
    except Exception as e:
        print(f"❌ Error starting app: {e}")
        return None

def test_app_health():
    """Test if the app is responding"""
    print("🏥 Testing application health...")
    max_retries = 30
    
    for i in range(max_retries):
        try:
            response = requests.get(f"http://localhost:{Config.PORT}/_stcore/health", timeout=5)
            if response.status_code == 200:
                print("✅ Application is healthy and responding")
                return True
        except requests.exceptions.RequestException:
            pass
        
        print(f"⏳ Waiting for app to start... ({i+1}/{max_retries})")
        time.sleep(2)
    
    print("❌ Application health check failed")
    return False

def main():
    """Main test function"""
    print("=" * 60)
    print("🧪 Vismaya DemandOps - Local Testing")
    print("=" * 60)
    
    # Test dependencies
    if not test_dependencies():
        print("\n📦 Installing dependencies...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    
    # Test AWS
    aws_ok = test_aws_connection()
    
    # Test Bedrock
    bedrock_ok = test_bedrock_access()
    
    # Start app
    process = start_app_background()
    if not process:
        sys.exit(1)
    
    try:
        # Test health
        if test_app_health():
            print(f"\n🎉 Success! Application is running at:")
            print(f"📊 http://localhost:{Config.PORT}")
            print("\n📋 Test Results:")
            print(f"   AWS Connection: {'✅ Working' if aws_ok else '❌ Issues detected'}")
            print(f"   Bedrock AI: {'✅ Working' if bedrock_ok else '❌ Permission needed'}")
            print(f"   Application: ✅ Working")
            print("\n🛑 Press Ctrl+C to stop the application")
            
            # Keep running
            process.wait()
        else:
            print("❌ Application failed to start properly")
            process.terminate()
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping application...")
        process.terminate()
        process.wait()
        print("👋 Application stopped")

if __name__ == "__main__":
    main()