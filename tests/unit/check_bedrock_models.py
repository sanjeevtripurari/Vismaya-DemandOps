#!/usr/bin/env python3
"""
Check available Bedrock models
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import boto3
from config import Config

def main():
    try:
        # Create session with new credentials
        session = boto3.Session(
            aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
            aws_session_token=Config.AWS_SESSION_TOKEN,
            region_name=Config.AWS_REGION
        )

        bedrock = session.client('bedrock')
        response = bedrock.list_foundation_models()

        print("🤖 Available Bedrock Models:")
        print("=" * 50)
        
        # Find Claude/Anthropic models
        claude_models = []
        all_models = []
        
        for model in response['modelSummaries']:
            model_id = model['modelId']
            model_name = model['modelName']
            all_models.append(model_id)
            
            if 'anthropic' in model_id.lower() or 'claude' in model_id.lower():
                claude_models.append(model_id)
                print(f"✅ Claude: {model_id}")
                print(f"   Name: {model_name}")
                print()
        
        if not claude_models:
            print("❌ No Claude models found")
            print("\n📋 Available models (first 10):")
            for i, model_id in enumerate(all_models[:10]):
                print(f"   {i+1}. {model_id}")
        
        print(f"\n📊 Summary:")
        print(f"   Total models: {len(all_models)}")
        print(f"   Claude models: {len(claude_models)}")
        
        # Check current config
        print(f"\n⚙️ Current config: {Config.BEDROCK_MODEL_ID}")
        if Config.BEDROCK_MODEL_ID in all_models:
            print("✅ Current model is available")
        else:
            print("❌ Current model is NOT available")
            if claude_models:
                print(f"💡 Suggested model: {claude_models[0]}")
        
    except Exception as e:
        print(f"❌ Error checking models: {e}")

if __name__ == "__main__":
    main()