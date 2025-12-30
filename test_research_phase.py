"""Test script for Research & Discovery phase with mock LLM."""
import asyncio
import sys
import os

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.llm.mock_client import MockLLMClient
from app.product_company.core_devices_company import CoreDevicesCompany
from app.product_company.models import Phase


async def test_research_phase():
    """Test the Research & Discovery phase with mock LLM."""
    print("=" * 80)
    print("TESTING RESEARCH & DISCOVERY PHASE")
    print("=" * 80)
    print()
    
    # Create mock LLM client
    print("✓ Creating mock LLM client...")
    mock_llm = MockLLMClient()
    
    # Create company instance with mock LLM
    print("✓ Creating CoreDevicesCompany...")
    company = CoreDevicesCompany(llm_client=mock_llm, model="mock")
    
    # Initialize project with research mode
    print("✓ Initializing project in research mode...")
    await company.initialize_project(
        idea="",
        primary_need="",
        constraints={},
        research_mode=True
    )
    
    # Execute research phase
    print()
    print("-" * 80)
    print("EXECUTING RESEARCH PHASE")
    print("-" * 80)
    print()
    
    try:
        result = await company.execute_phase_0(
            research_scope="Explore opportunities in consumer electronics for everyday needs"
        )
        
        print()
        print("=" * 80)
        print("RESEARCH PHASE COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        print()
        
        # Print results
        print("📊 RESULTS:")
        print("-" * 80)
        
        if "text_report" in result:
            print("\n📄 TEXT REPORT:")
            print(result["text_report"][:500] + "..." if len(result["text_report"]) > 500 else result["text_report"])
        
        if "artifacts" in result:
            print("\n📦 ARTIFACTS:")
            artifacts = result["artifacts"]
            print(f"  - Research Findings: {type(artifacts.get('research_findings'))}")
            print(f"  - Recommendation: {type(artifacts.get('recommendation'))}")
            print(f"  - Opportunities: {len(artifacts.get('opportunities', []))} found")
        
        if "summary" in result:
            print("\n💼 CEO SUMMARY:")
            print(result["summary"][:300] + "..." if len(result["summary"]) > 300 else result["summary"])
        
        # Check chat log
        if "chat_log" in result:
            print(f"\n💬 CHAT LOG: {len(result['chat_log'])} messages")
            print("  Sample messages:")
            for msg in result["chat_log"][:3]:
                sender = msg.get("sender", "Unknown")
                content = msg.get("content", "")[:60]
                print(f"    - {sender}: {content}...")
        
        print()
        print("✅ ALL TESTS PASSED!")
        print()
        
        return True
        
    except Exception as e:
        print()
        print("=" * 80)
        print("❌ TEST FAILED!")
        print("=" * 80)
        print(f"Error: {type(e).__name__}: {str(e)}")
        print()
        
        import traceback
        print("TRACEBACK:")
        print("-" * 80)
        traceback.print_exc()
        print()
        
        return False


if __name__ == "__main__":
    print()
    print("🧪 Starting Research Phase Test with Mock LLM")
    print()
    
    success = asyncio.run(test_research_phase())
    
    if success:
        print("🎉 Test completed successfully!")
        sys.exit(0)
    else:
        print("💥 Test failed. Please check errors above.")
        sys.exit(1)
