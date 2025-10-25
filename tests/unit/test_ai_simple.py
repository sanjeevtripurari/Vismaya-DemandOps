#!/usr/bin/env python3
"""
Simple AI Assistant Test
"""

import asyncio
import sys
sys.path.append('.')

from src.application.dependency_injection import DependencyContainer
from config import Config

async def test_ai():
    print("🤖 Testing AI Assistant with Real Bedrock")
    print("=" * 50)
    
    try:
        # Initialize container
        container = DependencyContainer(Config)
        container.initialize()
        
        # Get chat use case
        chat_use_case = container.get_use_case('handle_chat')
        
        # Test questions
        questions = [
            "What is my current AWS spending?",
            "How many EC2 instances do I have?",
            "What are my top AWS services by cost?"
        ]
        
        for i, question in enumerate(questions, 1):
            print(f"\n{i}. Question: {question}")
            try:
                response = await chat_use_case.execute(question)
                print(f"   Answer: {response[:200]}...")
                print("   ✅ AI response received")
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        print("\n✅ AI Assistant test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ai())