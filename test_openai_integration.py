#!/usr/bin/env python3
"""Test script to verify OpenAI integration works correctly."""
import os
import sys
import asyncio

# Add project to path
sys.path.insert(0, os.path.dirname(__file__))

from app.llm.client import LLMClient
from app.book_writer.config import get_config

async def test_openai_integration():
    """Test OpenAI API integration."""
    print("=" * 60)
    print("Testing OpenAI Integration")
    print("=" * 60)
    print()
    
    # Check API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("❌ ERROR: OPENAI_API_KEY environment variable not set")
        print("   Set it with: export OPENAI_API_KEY=sk-your-key-here")
        return False
    
    print(f"✅ OPENAI_API_KEY found: {api_key[:10]}...")
    print()
    
    # Get config
    try:
        config = get_config()
        print(f"✅ Config loaded successfully")
        print(f"   Provider: {config.get('provider')}")
        print(f"   Model: {config.get('model')}")
        print(f"   Base URL: {config.get('base_url')}")
        print()
    except Exception as e:
        print(f"❌ ERROR loading config: {e}")
        return False
    
    # Test LLM client
    try:
        print("Testing LLM Client...")
        llm_client = LLMClient(
            api_key=config.get('api_key'),
            base_url=config.get('base_url'),
            model=config.get('model'),
            provider=config.get('provider')
        )
        print("✅ LLM Client created successfully")
        print()
    except Exception as e:
        print(f"❌ ERROR creating LLM client: {e}")
        return False
    
    # Test API call
    try:
        print("Testing OpenAI API call...")
        print("   Sending test prompt...")
        response = await llm_client.complete(
            system="You are a helpful assistant.",
            user="Say 'OpenAI integration is working!' if you can respond."
        )
        
        if response:
            print(f"✅ API call successful!")
            print(f"   Response: {response[:100]}...")
            print()
            return True
        else:
            print("❌ ERROR: Empty response from API")
            return False
            
    except Exception as e:
        print(f"❌ ERROR calling OpenAI API: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_exam_generator_config():
    """Test exam generator configuration."""
    print("=" * 60)
    print("Testing Exam Generator Configuration")
    print("=" * 60)
    print()
    
    try:
        from app.book_writer.exam_generator import ExamGeneratorCompany
        
        print("Creating ExamGeneratorCompany instance...")
        company = ExamGeneratorCompany()
        print("✅ ExamGeneratorCompany created successfully")
        print(f"   Provider: {company.llm_client.provider}")
        print(f"   Model: {company.llm_client.model}")
        print(f"   Number of clients: {len(company.llm_clients)}")
        print()
        return True
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests."""
    print()
    print("🧪 Testing Application Integration")
    print()
    
    # Test OpenAI integration
    openai_ok = await test_openai_integration()
    print()
    
    # Test exam generator
    exam_gen_ok = await test_exam_generator_config()
    print()
    
    # Summary
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"OpenAI Integration: {'✅ PASS' if openai_ok else '❌ FAIL'}")
    print(f"Exam Generator Config: {'✅ PASS' if exam_gen_ok else '❌ FAIL'}")
    print()
    
    if openai_ok and exam_gen_ok:
        print("🎉 All tests passed! Application is ready to use.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
