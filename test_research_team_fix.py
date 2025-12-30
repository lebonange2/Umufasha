#!/usr/bin/env python3
"""
Test script to verify Research Team agents can call LLM correctly.
"""

import asyncio
import sys
from app.llm.client import LLMClient
from app.product_company.research_team import MarketResearchAgent, TechnologyResearchAgent, UserResearchAgent, ResearchLeadAgent
from app.product_company.core_devices_company import MessageBus


async def test_research_agents():
    """Test that all research agents can call LLM without errors."""
    
    print("🧪 Testing Research Team Agents...")
    print("=" * 60)
    
    # Create LLM client and message bus
    llm_client = LLMClient(
        base_url="http://localhost:11434/v1",
        model="qwen3:30b",
        provider="local"
    )
    
    message_bus = MessageBus()
    
    try:
        # Test 1: Market Research Agent
        print("\n1️⃣  Testing MarketResearchAgent...")
        market_agent = MarketResearchAgent(llm_client, message_bus)
        
        # Call the method that was failing before
        market_data = await market_agent.research_market_trends("health devices", {})
        print(f"   ✅ market_trends: {len(market_data.get('market_trends', []))} items")
        print(f"   ✅ emerging_needs: {len(market_data.get('emerging_needs', []))} items")
        print(f"   ✅ market_gaps: {len(market_data.get('market_gaps', []))} items")
        
        # Test 2: Identify opportunities
        print("\n2️⃣  Testing opportunity identification...")
        opportunities = await market_agent.identify_product_opportunities(market_data)
        print(f"   ✅ Identified {len(opportunities)} product opportunities")
        
        if opportunities:
            print(f"   📋 First opportunity: {opportunities[0].get('product_concept', 'N/A')[:80]}...")
        
        # Test 3: Technology Research Agent
        print("\n3️⃣  Testing TechnologyResearchAgent...")
        tech_agent = TechnologyResearchAgent(llm_client, message_bus)
        tech_data = await tech_agent.research_enabling_technologies(opportunities)
        print(f"   ✅ Technology analysis for {len(tech_data.get('technology_analysis', []))} opportunities")
        
        # Test 4: User Research Agent
        print("\n4️⃣  Testing UserResearchAgent...")
        user_agent = UserResearchAgent(llm_client, message_bus)
        user_data = await user_agent.research_user_needs(opportunities)
        print(f"   ✅ User analysis for {len(user_data.get('user_analysis', []))} opportunities")
        
        # Test 5: Research Lead Agent
        print("\n5️⃣  Testing ResearchLeadAgent...")
        lead_agent = ResearchLeadAgent(llm_client, message_bus)
        recommendation = await lead_agent.synthesize_research(market_data, tech_data, user_data)
        
        if recommendation.get('recommended_product'):
            rec_product = recommendation['recommended_product']
            print(f"   ✅ Recommendation generated")
            print(f"   📦 Product: {rec_product.get('product_concept', 'N/A')[:80]}...")
            print(f"   🎯 Primary Need: {rec_product.get('primary_need', 'N/A')}")
            print(f"   💡 Justification: {len(rec_product.get('justification', []))} points")
        else:
            print("   ⚠️  No recommendation generated")
        
        # Test 6: Message Bus
        print("\n6️⃣  Testing MessageBus transparency...")
        all_messages = message_bus.get_messages()
        print(f"   ✅ Total messages captured: {len(all_messages)}")
        
        if all_messages:
            print(f"   📨 Sample messages:")
            for i, msg in enumerate(all_messages[:3], 1):
                print(f"      {i}. {msg.from_agent} → {msg.to_agent}: {msg.content[:60]}...")
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED! Research Team is working correctly!")
        print("=" * 60)
        
        # Close client
        await llm_client.close()
        
        return True
        
    except AttributeError as e:
        print(f"\n❌ AttributeError (method doesn't exist): {e}")
        print("\nThis is the bug that was causing the infinite hang!")
        await llm_client.close()
        return False
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        await llm_client.close()
        return False


if __name__ == "__main__":
    print("\n🔬 Research Team Fix Verification Test")
    print("Testing that agents use LLMClient.complete() instead of .generate()")
    print()
    
    success = asyncio.run(test_research_agents())
    
    if success:
        print("\n✅ Fix verified! Research phase should work now.")
        sys.exit(0)
    else:
        print("\n❌ Fix failed! There are still issues.")
        sys.exit(1)
