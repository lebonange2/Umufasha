#!/usr/bin/env python3
"""Comprehensive test of the full application with OpenAI integration."""
import os
import sys
import asyncio

# Add project to path
sys.path.insert(0, os.path.dirname(__file__))

from fastapi.testclient import TestClient
from app.main import app
from app.llm.client import LLMClient
from app.book_writer.exam_generator import ExamGeneratorCompany

def test_routes():
    """Test all critical routes."""
    print("=" * 60)
    print("Testing Application Routes")
    print("=" * 60)
    print()
    
    client = TestClient(app)
    routes_to_test = [
        ("/", "Root page"),
        ("/writer", "Writer page"),
        ("/writer/exam-generator", "Exam generator page"),
        ("/api/writer/models", "Models endpoint"),
        ("/health", "Health check"),
        ("/docs", "API documentation"),
    ]
    
    results = []
    for route, name in routes_to_test:
        try:
            response = client.get(route)
            status = response.status_code
            if status in [200, 307, 308]:  # 200 OK, 307/308 redirects are OK
                print(f"✅ {name}: {status}")
                results.append(True)
            else:
                print(f"❌ {name}: {status}")
                results.append(False)
        except Exception as e:
            print(f"❌ {name}: Error - {e}")
            results.append(False)
    
    print()
    return all(results)

async def test_openai_api():
    """Test OpenAI API directly."""
    print("=" * 60)
    print("Testing OpenAI API Integration")
    print("=" * 60)
    print()
    
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not set - skipping OpenAI test")
        return False
    
    try:
        print("Creating LLM client...")
        client = LLMClient(
            api_key=api_key,
            base_url="https://api.openai.com/v1",
            model="gpt-4o",
            provider="openai"
        )
        print("✅ LLM Client created")
        
        print("Making API call...")
        response = await client.complete(
            system="You are a helpful assistant.",
            user="Say 'OpenAI API is working correctly!' and nothing else."
        )
        
        if response and "working" in response.lower():
            print(f"✅ OpenAI API call successful!")
            print(f"   Response: {response[:100]}")
            return True
        else:
            print(f"⚠️  Unexpected response: {response}")
            return False
            
    except Exception as e:
        print(f"❌ OpenAI API test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_exam_generator_openai():
    """Test exam generator with OpenAI."""
    print("=" * 60)
    print("Testing Exam Generator with OpenAI")
    print("=" * 60)
    print()
    
    # Set OpenAI provider
    os.environ["LLM_PROVIDER"] = "openai"
    
    try:
        print("Creating ExamGeneratorCompany...")
        company = ExamGeneratorCompany()
        print(f"✅ ExamGeneratorCompany created")
        print(f"   Provider: {company.llm_client.provider}")
        print(f"   Model: {company.llm_client.model}")
        print(f"   Clients: {len(company.llm_clients)}")
        
        # Test a simple content analysis
        print("\nTesting content analysis...")
        test_content = """
        Topic 1: Introduction to Python
        Subtopic 1.1: Variables and Data Types
        Learning Objective 1.1.1.1: Understand basic Python data types
        Learning Objective 1.1.1.2: Use variables to store data
        """
        
        analysis = await company.content_analyst.analyze_content(test_content)
        if analysis and isinstance(analysis, dict) and "learning_objectives" in analysis:
            print(f"✅ Content analysis successful!")
            print(f"   Learning objectives: {len(analysis.get('learning_objectives', []))}")
            print(f"   Key topics: {len(analysis.get('key_topics', []))}")
            return True
        else:
            print(f"⚠️  Unexpected analysis result: {type(analysis)}")
            if isinstance(analysis, dict):
                print(f"   Keys: {list(analysis.keys())}")
            return False
            
    except Exception as e:
        print(f"❌ Exam generator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Restore original provider
        if "LLM_PROVIDER" in os.environ:
            del os.environ["LLM_PROVIDER"]

async def main():
    """Run all tests."""
    print()
    print("🧪 Comprehensive Application Test")
    print()
    
    # Test routes
    routes_ok = test_routes()
    print()
    
    # Test OpenAI API
    openai_ok = await test_openai_api()
    print()
    
    # Test exam generator
    exam_gen_ok = await test_exam_generator_openai()
    print()
    
    # Summary
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Routes: {'✅ PASS' if routes_ok else '❌ FAIL'}")
    print(f"OpenAI API: {'✅ PASS' if openai_ok else '❌ FAIL'}")
    print(f"Exam Generator: {'✅ PASS' if exam_gen_ok else '❌ FAIL'}")
    print()
    
    if routes_ok and openai_ok and exam_gen_ok:
        print("🎉 All tests passed! Application is fully functional.")
        print()
        print("You can now:")
        print("  1. Start the server: ./setup_and_run_local.sh")
        print("  2. Access: http://localhost:8000/writer")
        print("  3. Use the exam generator with OpenAI")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
