"""Mock LLM client for testing - returns predefined responses instantly."""
import json
from typing import Dict, Any, Optional, List


class MockLLMClient:
    """Mock LLM client that returns predefined responses for testing."""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, model: str = "mock", provider: str = "mock"):
        print("🧪 [MockLLMClient] Initialized - using mock responses for testing")
        self.provider = "mock"
        self.model = "mock"
        self.call_count = 0
    
    async def complete(self, system: str, user: str, tools: Optional[List[Dict[str, Any]]] = None) -> str:
        """Return mock response based on the prompt."""
        self.call_count += 1
        
        # Detect what kind of request this is based on system/user prompts
        prompt_lower = (system + " " + user).lower()
        
        print(f"🧪 [MockLLMClient] Call #{self.call_count}")
        print(f"   System (first 100): {system[:100]}...")
        print(f"   User (first 100): {user[:100]}...")
        
        # Check system prompt for agent type (more reliable)
        system_lower = system.lower()
        
        # Market Research Agent
        if "market research agent" in system_lower:
            # Check if it's brainstorming or synthesizing
            if "brainstorm" in user.lower() or "industries" in user.lower():
                print(f"🧪 [MockLLMClient] → Detected MARKET RESEARCH (Brainstorming)")
                return json.dumps({
                    "industries": [
                        "Consumer Electronics",
                        "Smart Home Technology",
                        "Health & Wellness Tech",
                        "Energy Management",
                        "Personal Productivity Tools"
                    ],
                    "product_ideas": [
                        {
                            "idea": "AI-Powered Universal Smart Charger",
                            "industry": "Consumer Electronics",
                            "addresses_need": "energy",
                            "description": "Intelligent charger that optimizes charging speed and battery longevity across all devices"
                        },
                        {
                            "idea": "Home Energy Optimizer",
                            "industry": "Smart Home Technology",
                            "addresses_need": "energy",
                            "description": "Real-time energy monitoring and AI-powered optimization for reduced electricity costs"
                        },
                        {
                            "idea": "Battery Health Monitor",
                            "industry": "Consumer Electronics",
                            "addresses_need": "essential_productivity",
                            "description": "Device that tracks battery health and provides actionable insights to extend battery life"
                        },
                        {
                            "idea": "Wireless Power Hub",
                            "industry": "Smart Home Technology",
                            "addresses_need": "energy",
                            "description": "Central wireless charging station for all household devices"
                        }
                    ],
                    "emerging_needs": [
                        "Better battery life and charging solutions",
                        "Device interoperability",
                        "Privacy-focused smart devices",
                        "Energy efficiency in homes"
                    ],
                    "opportunity_areas": [
                        "Smart charging technology",
                        "Battery longevity products",
                        "Multi-device power management",
                        "Home energy optimization"
                    ]
                })
            else:
                # Synthesizing opportunities
                print(f"🧪 [MockLLMClient] → Detected MARKET RESEARCH (Synthesizing)")
                return json.dumps({
                    "opportunities": [
                        {
                            "product_concept": "AI-Powered Universal Smart Charger",
                            "primary_need": "energy",
                            "market_size": "large",
                            "current_friction": "Multiple chargers needed, battery degradation from improper charging",
                            "differentiation": "AI optimization for speed and longevity, universal compatibility"
                        },
                        {
                            "product_concept": "Home Energy Optimizer",
                            "primary_need": "energy",
                            "market_size": "medium",
                            "current_friction": "High electricity bills, no visibility into energy usage patterns",
                            "differentiation": "Real-time monitoring with AI-powered recommendations"
                        }
                    ]
                })
        
        # Technology Research Agent
        elif "technology research agent" in system_lower:
            print(f"🧪 [MockLLMClient] → Detected TECHNOLOGY RESEARCH")
            return json.dumps({
                "technology_analysis": [
                    {
                        "product_concept": "Smart Universal Charger",
                        "feasibility": "High - existing USB-C PD technology can be enhanced with AI",
                        "readiness": "TRL 7-8 (System prototype demonstration)",
                        "enabling_technologies": ["USB Power Delivery 3.1", "AI/ML for optimization", "Temperature sensors"]
                    },
                    {
                        "product_concept": "Battery Health Monitor",
                        "feasibility": "Medium - requires integration with device battery management systems",
                        "readiness": "TRL 6-7 (Technology demonstration)",
                        "enabling_technologies": ["Battery analytics", "IoT connectivity", "Mobile app integration"]
                    }
                ]
            })
        
        # User Research Agent
        elif "user research agent" in system_lower:
            print(f"🧪 [MockLLMClient] → Detected USER RESEARCH")
            return json.dumps({
                "user_analysis": [
                    {
                        "product_concept": "Smart Universal Charger",
                        "pain_points": [
                            "Too many different chargers for different devices",
                            "Slow charging speeds",
                            "Battery degradation from fast charging"
                        ],
                        "user_preferences": [
                            "One charger for all devices",
                            "Fast but safe charging",
                            "Compact and portable design"
                        ]
                    }
                ]
            })
        
        # Product Opportunity Identification
        elif "product opportunities" in prompt_lower or "product concepts" in prompt_lower:
            return json.dumps({
                "product_opportunities": [
                    {
                        "product_concept": "AI-Powered Universal Smart Charger",
                        "primary_need": "energy",
                        "market_size": "Large - global charger market $25B+",
                        "differentiation": "AI optimization prevents battery degradation while maximizing charging speed"
                    },
                    {
                        "product_concept": "Battery Longevity Optimizer",
                        "primary_need": "health",
                        "market_size": "Medium - subset of tech-savvy users",
                        "differentiation": "Extends battery life by 30% through intelligent charging patterns"
                    }
                ]
            })
        
        # Final Recommendation (Research Lead Agent)
        elif "research lead agent" in system_lower:
            print(f"🧪 [MockLLMClient] ✅ Detected RESEARCH LEAD / RECOMMENDATION")
            response = json.dumps({
                "recommended_product": {
                    "product_concept": "AI-Powered Universal Smart Charger",
                    "primary_need": "energy",
                    "justification": [
                        "Addresses universal pain point of multiple chargers",
                        "Technology is mature and ready (TRL 7-8)",
                        "Large addressable market ($25B+)",
                        "Clear differentiation with AI optimization"
                    ],
                    "expected_impact": "Reduces charging time by 40% while extending battery life by 20%",
                    "next_steps": [
                        "Develop prototype with USB-PD 3.1 and AI algorithms",
                        "Conduct user testing with multiple device types",
                        "Secure regulatory certifications (UL, CE, FCC)"
                    ]
                },
                "alternative_opportunities": [
                    {
                        "concept": "Battery Longevity Optimizer",
                        "primary_need": "health",
                        "reason": "Smaller market but high value for tech enthusiasts"
                    }
                ]
            })
            print(f"🧪 [MockLLMClient] Returning: {response[:200]}...")
            return response
        
        # CEO Review
        elif "ceo" in prompt_lower or "review" in prompt_lower:
            return """## Research Phase Summary

The Research Team has completed a comprehensive market, technology, and user analysis.

**Key Findings:**
- Strong market opportunity in smart charging ($25B+ market)
- Technology is mature and ready for commercialization
- Clear user pain points around multiple chargers and battery degradation

**Recommendation:**
Proceed with AI-Powered Universal Smart Charger as the primary product concept.

**Next Steps:**
Move to Phase 1 (Strategy & Idea Intake) to refine the product concept and develop the idea dossier."""
        
        # Default fallback
        else:
            print(f"🧪 [MockLLMClient] ⚠️  NO MATCH - Using fallback")
            print(f"   Keywords in prompt: synthesize={('synthesize' in prompt_lower)}, recommend={('recommend' in prompt_lower)}")
            return json.dumps({
                "response": "Mock LLM response",
                "note": "This is a simulated response for testing"
            })
    
    async def close(self):
        """Mock close method."""
        pass


# Function to create mock client
def create_mock_llm_client():
    """Create a mock LLM client for testing."""
    return MockLLMClient()
