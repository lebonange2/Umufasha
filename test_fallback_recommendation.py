#!/usr/bin/env python3
"""Test fallback recommendation generation."""
import asyncio
import sys
import os

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.product_company.research_team import ResearchLeadAgent
from app.product_company.core_devices_company import MessageBus, Phase


async def test_fallback():
    """Test that fallback recommendation is generated when LLM fails."""
    print("=" * 80)
    print("TESTING FALLBACK RECOMMENDATION GENERATION")
    print("=" * 80)
    print()
    
    # Create a research lead agent with a mock LLM that returns invalid JSON
    class MockLLMThatFails:
        async def complete(self, system, user):
            # Return non-JSON response to trigger fallback
            return "This is not JSON, it's just plain text explaining the recommendation."
    
    bus = MessageBus()
    mock_llm = MockLLMThatFails()
    research_lead = ResearchLeadAgent(mock_llm, bus)
    
    # Prepare test data
    market_data = {
        'market_trends': ['Smart charging solutions', 'Energy efficiency'],
        'emerging_needs': ['Better battery life', 'Faster charging'],
        'market_gaps': ['Universal charging', 'Smart power management'],
        'opportunity_areas': ['Smart Universal Charger', 'Battery Optimizer']
    }
    
    tech_data = {
        'technology_analysis': [
            {
                'product_concept': 'AI-Powered Smart Charger',
                'feasibility': 'High',
                'readiness': 'TRL 7-8'
            }
        ]
    }
    
    user_data = {
        'user_analysis': []
    }
    
    print("Step 1: Calling synthesize_research with LLM that returns invalid JSON...")
    result = await research_lead.synthesize_research(market_data, tech_data, user_data)
    
    print()
    print("Step 2: Checking result...")
    
    if not result:
        print("❌ FAILED: No result returned")
        return False
    
    if not result.get('recommended_product'):
        print("❌ FAILED: No recommended_product in result")
        return False
    
    rec = result['recommended_product']
    print("✅ SUCCESS: Fallback recommendation generated!")
    print()
    print("Recommendation details:")
    print(f"  Product Concept: {rec.get('product_concept')}")
    print(f"  Primary Need: {rec.get('primary_need')}")
    print(f"  Justification: {len(rec.get('justification', []))} points")
    print(f"  Expected Impact: {rec.get('expected_impact')}")
    print(f"  Next Steps: {len(rec.get('next_steps', []))} steps")
    print()
    
    # Validate structure
    required_fields = ['product_concept', 'primary_need', 'justification', 'expected_impact', 'next_steps']
    missing = [f for f in required_fields if f not in rec]
    
    if missing:
        print(f"❌ FAILED: Missing required fields: {missing}")
        return False
    
    # Validate primary need is valid
    valid_needs = ['energy', 'water', 'food', 'shelter', 'health', 'communication', 'safety', 'mobility', 'essential_productivity']
    if rec['primary_need'] not in valid_needs:
        print(f"❌ FAILED: Invalid primary_need: {rec['primary_need']}")
        return False
    
    print("✅ All validation checks passed!")
    print()
    print("=" * 80)
    print("✅ FALLBACK RECOMMENDATION TEST PASSED!")
    print("=" * 80)
    
    return True


if __name__ == "__main__":
    print()
    print("🧪 Testing Fallback Recommendation Generation")
    print()
    
    success = asyncio.run(test_fallback())
    
    if success:
        print()
        print("🎉 Test completed successfully!")
        sys.exit(0)
    else:
        print()
        print("💥 Test failed!")
        sys.exit(1)
