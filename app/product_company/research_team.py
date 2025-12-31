"""
Research Team - Autonomous Product Discovery and Analysis

This module implements the Research Team responsible for discovering and validating
product opportunities when the Owner doesn't have a specific idea.

The team generates comprehensive PDF reports documenting their research process.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import json
import asyncio
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from app.llm.client import LLMClient


@dataclass
class ResearchFindings:
    """Complete research findings for product opportunity."""
    
    # Brainstorming & Market Analysis
    industries: List[str] = field(default_factory=list)
    product_ideas: List[Dict[str, Any]] = field(default_factory=list)
    emerging_needs: List[str] = field(default_factory=list)
    
    # Technology Analysis
    enabling_technologies: List[Dict[str, Any]] = field(default_factory=list)
    technology_readiness: Dict[str, str] = field(default_factory=dict)
    
    # User Research
    user_pain_points: List[str] = field(default_factory=list)
    unmet_needs: List[str] = field(default_factory=list)
    user_behaviors: List[str] = field(default_factory=list)
    
    # Product Recommendations
    product_opportunities: List[Dict[str, Any]] = field(default_factory=list)
    recommended_product: Optional[Dict[str, Any]] = None
    
    # Metadata
    research_date: datetime = field(default_factory=datetime.now)
    research_scope: str = ""
    constraints: Dict[str, Any] = field(default_factory=dict)


class MarketResearchAgent:
    """Market Research Agent - analyzes market trends and opportunities."""
    
    def __init__(self, llm_client: LLMClient, message_bus):
        self.role = "Market_Research_Agent"
        self.llm = llm_client
        self.bus = message_bus
    
    async def research_market_trends(self, scope: str, constraints: Dict[str, Any]) -> Dict[str, Any]:
        """Brainstorm industries and product ideas aligned with primary human needs."""
        from app.product_company.core_devices_company import Phase
        
        self.bus.send(self.role, "INTERNAL", Phase.RESEARCH_DISCOVERY,
                     "[Market_Research_Agent] ✓ Checklist 1/4: Brainstorming industries & product ideas", "internal")
        
        prompt = f"""You are a Market Research Agent brainstorming product opportunities.

Research Scope: {scope if scope else "Open exploration - brainstorm product ideas"}
Constraints: {json.dumps(constraints, indent=2)}

**PRIMARY HUMAN NEEDS** (choose from):
- energy: Power, electricity, charging, batteries
- water: Clean water, hydration, water management
- food: Nutrition, cooking, food storage, agriculture
- shelter: Housing, temperature control, home infrastructure
- health: Medical care, fitness, wellness, hygiene
- communication: Information sharing, connectivity, messaging
- safety: Security, protection, emergency response
- mobility: Transportation, movement, logistics
- essential_productivity: Tools, work efficiency, time management

**TASK:**
1. Brainstorm 5-7 industries that could innovate around these primary needs
2. For each industry, suggest 2-3 specific product ideas
3. Identify which primary need(s) each product addresses
4. List emerging opportunities where current solutions are inadequate

Output as JSON: {{
    "industries": ["Industry 1", "Industry 2", ...],
    "product_ideas": [
        {{"idea": "Product Name", "industry": "Industry", "addresses_need": "primary_need", "description": "Brief description"}},
        ...
    ],
    "emerging_needs": ["Unmet need 1", "Unmet need 2", ...],
    "opportunity_areas": ["Opportunity 1", "Opportunity 2", ...]
}}"""
        
        try:
            self.bus.send(self.role, "INTERNAL", Phase.RESEARCH_DISCOVERY,
                         "[Market_Research_Agent] 🤖 Calling LLM for market analysis (this may take 30-60 seconds)...", "internal")
            
            response = await self.llm.complete(
                system="You are a Market Research Agent for electronic products.",
                user=prompt
            )
            
            self.bus.send(self.role, "INTERNAL", Phase.RESEARCH_DISCOVERY,
                         "[Market_Research_Agent] ✅ LLM response received, parsing JSON...", "internal")
            
            result = self._extract_json(response)
            
            if not result:
                self.bus.send(self.role, "INTERNAL", Phase.RESEARCH_DISCOVERY,
                             f"[Market_Research_Agent] ⚠️ Could not parse JSON, using fallback data", "internal")
                # Return minimal fallback data
                result = {
                    "industries": ["Consumer Electronics", "Smart Home", "Health Tech", "Energy Management"],
                    "product_ideas": [
                        {"idea": "Smart Universal Charger", "industry": "Consumer Electronics", "addresses_need": "energy", "description": "AI-powered charging with battery optimization"},
                        {"idea": "Home Energy Monitor", "industry": "Smart Home", "addresses_need": "energy", "description": "Real-time energy usage tracking and optimization"}
                    ],
                    "emerging_needs": ["Better battery life", "Energy efficiency", "Device interoperability"],
                    "opportunity_areas": ["Smart charging solutions", "Battery health optimization"]
                }
            else:
                self.bus.send(self.role, "INTERNAL", Phase.RESEARCH_DISCOVERY,
                             "[Market_Research_Agent] ✅ JSON parsed successfully", "internal")
                
        except Exception as e:
            self.bus.send(self.role, "INTERNAL", Phase.RESEARCH_DISCOVERY,
                         f"[Market_Research_Agent] ❌ ERROR: {str(e)}", "internal")
            raise
        
        self.bus.send(self.role, "Research_Lead_Agent", Phase.RESEARCH_DISCOVERY,
                     f"[Market_Research_Agent] ✓ Brainstormed {len(result.get('industries', []))} industries, {len(result.get('product_ideas', []))} product ideas", "internal")
        
        return result or {"industries": [], "product_ideas": [], "emerging_needs": [], "opportunity_areas": []}
    
    async def identify_product_opportunities(self, market_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Synthesize brainstormed product ideas into specific opportunities."""
        from app.product_company.core_devices_company import Phase
        
        self.bus.send(self.role, "INTERNAL", Phase.RESEARCH_DISCOVERY,
                     "[Market_Research_Agent] ✓ Checklist 2/4: Synthesizing top opportunities", "internal")
        
        prompt = f"""Based on brainstormed product ideas, select and refine 3-5 top opportunities.

Brainstormed Data: {json.dumps(market_data, indent=2)}

**TASK:**
Evaluate all product_ideas and select the 3-5 most promising opportunities.
For each selected opportunity, provide:
1. Product concept (detailed description)
2. Primary human need it addresses (must be one of: energy, water, food, shelter, health, communication, safety, mobility, essential_productivity)
3. Market size estimate (small/medium/large)
4. Current friction points that this solves
5. Key differentiation from existing solutions

Output as JSON: {{
    "opportunities": [
        {{
            "product_concept": "Detailed product name and description",
            "primary_need": "energy|water|food|shelter|health|communication|safety|mobility|essential_productivity",
            "market_size": "small|medium|large",
            "current_friction": "What problems does this solve?",
            "differentiation": "Why is this better than existing solutions?"
        }},
        ...
    ]
}}"""
        
        response = await self.llm.complete(
            system="You are a Market Research Agent for electronic products.",
            user=prompt
        )
        result = self._extract_json(response)
        
        opportunities = result.get("opportunities", []) if result else []
        
        self.bus.send(self.role, "Research_Lead_Agent", Phase.RESEARCH_DISCOVERY,
                     f"[Market_Research_Agent] ✓ Identified {len(opportunities)} product opportunities", "internal")
        
        return opportunities
    
    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from LLM response with robust parsing."""
        import re
        
        # Limit text length to prevent hanging
        search_text = text[:10000] if len(text) > 10000 else text
        
        # Strategy 1: Try direct parse (strip whitespace first)
        try:
            return json.loads(search_text.strip())
        except:
            pass
        
        # Strategy 2: Find JSON in markdown code blocks (```json ... ```)
        try:
            json_block = re.search(r'```json\s*({.*?})\s*```', search_text, re.DOTALL)
            if json_block:
                return json.loads(json_block.group(1))
        except:
            pass
        
        # Strategy 3: Find JSON in any code blocks (``` ... ```)
        try:
            code_block = re.search(r'```\s*({.*?})\s*```', search_text, re.DOTALL)
            if code_block:
                return json.loads(code_block.group(1))
        except:
            pass
        
        # Strategy 4: Find first { to last } and clean common issues
        try:
            first_brace = search_text.find('{')
            last_brace = search_text.rfind('}')
            if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                potential_json = search_text[first_brace:last_brace+1]
                # Try parsing as-is first
                try:
                    return json.loads(potential_json)
                except:
                    # Clean trailing commas before closing braces/brackets
                    cleaned = re.sub(r',(\s*[}\]])', r'\1', potential_json)
                    return json.loads(cleaned)
        except:
            pass
        
        return None


class TechnologyResearchAgent:
    """Technology Research Agent - analyzes enabling technologies."""
    
    def __init__(self, llm_client: LLMClient, message_bus):
        self.role = "Technology_Research_Agent"
        self.llm = llm_client
        self.bus = message_bus
    
    async def research_enabling_technologies(self, opportunities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Research technologies that enable the product opportunities."""
        from app.product_company.core_devices_company import Phase
        
        self.bus.send(self.role, "INTERNAL", Phase.RESEARCH_DISCOVERY,
                     "[Technology_Research_Agent] ✓ Checklist 1/3: Researching enabling technologies", "internal")
        
        prompt = f"""Analyze enabling technologies for these product opportunities.

Opportunities: {json.dumps(opportunities, indent=2)}

For each opportunity, identify:
1. Key enabling technologies required
2. Technology readiness level (mature/emerging/experimental)
3. Technical feasibility (high/medium/low)
4. Component availability (readily available/needs development)

Output as JSON: {{
    "technology_analysis": [
        {{
            "product_concept": "...",
            "enabling_technologies": ["tech1", "tech2", ...],
            "readiness": "mature|emerging|experimental",
            "feasibility": "high|medium|low",
            "component_availability": "readily_available|needs_development"
        }},
        ...
    ]
}}"""
        
        response = await self.llm.complete(
            system="You are a Technology Research Agent specializing in electronics and device technologies.",
            user=prompt
        )
        result = self._extract_json(response)
        
        self.bus.send(self.role, "Research_Lead_Agent", Phase.RESEARCH_DISCOVERY,
                     f"[Technology_Research_Agent] ✓ Evaluated {len(result.get('technology_analysis', []))} opportunities for technical feasibility", "internal")
        
        return result or {"technology_analysis": []}
    
    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from LLM response with timeout protection."""
        import re
        
        # Limit text length to prevent hanging
        search_text = text[:10000] if len(text) > 10000 else text
        
        # Strategy 1: Try direct parse
        try:
            return json.loads(search_text)
        except:
            pass
        
        # Strategy 2: Find JSON in markdown code blocks
        try:
            json_block = re.search(r'```json\s*(\{.*?\})\s*```', search_text, re.DOTALL)
            if json_block:
                return json.loads(json_block.group(1))
        except:
            pass
        
        # Strategy 3: Find first { to last }
        try:
            first_brace = search_text.find('{')
            last_brace = search_text.rfind('}')
            if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                potential_json = search_text[first_brace:last_brace+1]
                return json.loads(potential_json)
        except:
            pass
        
        return None


class UserResearchAgent:
    """User Research Agent - analyzes user needs and behaviors."""
    
    def __init__(self, llm_client: LLMClient, message_bus):
        self.role = "User_Research_Agent"
        self.llm = llm_client
        self.bus = message_bus
    
    async def research_user_needs(self, opportunities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Research user needs and pain points for opportunities."""
        from app.product_company.core_devices_company import Phase
        
        self.bus.send(self.role, "INTERNAL", Phase.RESEARCH_DISCOVERY,
                     "[User_Research_Agent] ✓ Checklist 1/3: Analyzing user needs", "internal")
        
        prompt = f"""Analyze user needs and behaviors for these product opportunities.

Opportunities: {json.dumps(opportunities, indent=2)}

For each opportunity, analyze:
1. Primary user pain points (what frustrates users today)
2. User behaviors (how they currently solve this need)
3. Friction in current solutions (steps, complexity, time, cost)
4. User preferences (what would make their life easier)

Output as JSON: {{
    "user_analysis": [
        {{
            "product_concept": "...",
            "pain_points": ["pain1", "pain2", ...],
            "current_behaviors": ["behavior1", "behavior2", ...],
            "friction_points": ["friction1", "friction2", ...],
            "user_preferences": ["preference1", "preference2", ...]
        }},
        ...
    ]
}}"""
        
        response = await self.llm.complete(
            system="You are a User Research Agent specializing in understanding user needs and behaviors.",
            user=prompt
        )
        result = self._extract_json(response)
        
        self.bus.send(self.role, "Research_Lead_Agent", Phase.RESEARCH_DISCOVERY,
                     f"[User_Research_Agent] ✓ Analyzed user needs and behaviors", "internal")
        
        return result or {"user_analysis": []}
    
    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from LLM response with timeout protection."""
        import re
        
        # Limit text length to prevent hanging
        search_text = text[:10000] if len(text) > 10000 else text
        
        # Strategy 1: Try direct parse
        try:
            return json.loads(search_text)
        except:
            pass
        
        # Strategy 2: Find JSON in markdown code blocks
        try:
            json_block = re.search(r'```json\s*(\{.*?\})\s*```', search_text, re.DOTALL)
            if json_block:
                return json.loads(json_block.group(1))
        except:
            pass
        
        # Strategy 3: Find first { to last }
        try:
            first_brace = search_text.find('{')
            last_brace = search_text.rfind('}')
            if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                potential_json = search_text[first_brace:last_brace+1]
                return json.loads(potential_json)
        except:
            pass
        
        return None


class ResearchLeadAgent:
    """Research Lead Agent - coordinates research and makes final recommendation."""
    
    def __init__(self, llm_client: LLMClient, message_bus):
        self.role = "Research_Lead_Agent"
        self.llm = llm_client
        self.bus = message_bus
    
    async def synthesize_research(self, 
                                   market_data: Dict[str, Any],
                                   tech_data: Dict[str, Any],
                                   user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize all research and make product recommendation."""
        from app.product_company.core_devices_company import Phase
        
        self.bus.send(self.role, "CEO_Agent", Phase.RESEARCH_DISCOVERY,
                     "[Research_Lead_Agent] ✓ Synthesizing research findings", "internal")
        
        prompt = f"""Synthesize research findings and recommend the best product opportunity.

Market Analysis: {json.dumps(market_data, indent=2)}
Technology Analysis: {json.dumps(tech_data, indent=2)}
User Analysis: {json.dumps(user_data, indent=2)}

Evaluate all opportunities and select ONE recommended product based on:
1. Strongest market opportunity
2. Highest technical feasibility
3. Greatest friction reduction potential
4. Clearest alignment with primary human need

Provide:
1. Recommended product concept (detailed description)
2. Primary human need it addresses
3. Justification for selection (3-5 bullet points)
4. Expected impact (how it improves users' lives)
5. Next steps for development

Output as JSON: {{
    "recommended_product": {{
        "product_concept": "detailed description",
        "primary_need": "energy|water|food|shelter|health|communication|safety|mobility|essential_productivity",
        "justification": ["reason1", "reason2", ...],
        "expected_impact": "...",
        "next_steps": ["step1", "step2", ...]
    }},
    "alternative_opportunities": [
        {{"concept": "...", "primary_need": "..."}},
        ...
    ]
}}"""
        
        response = await self.llm.complete(
            system="You are a Research Lead Agent responsible for synthesizing research and making strategic product recommendations.",
            user=prompt
        )
        result = self._extract_json(response)
        
        # If JSON parsing failed, create a fallback recommendation from the data
        if not result or not result.get("recommended_product"):
            self.bus.send(self.role, "INTERNAL", Phase.RESEARCH_DISCOVERY,
                         "[Research_Lead_Agent] ⚠️ JSON parse failed, generating fallback recommendation", "internal")
            result = self._generate_fallback_recommendation(market_data, tech_data, user_data)
        
        if result and result.get("recommended_product"):
            self.bus.send(self.role, "CEO_Agent", Phase.RESEARCH_DISCOVERY,
                         f"[Research_Lead_Agent] ✓ Recommended Product: {result['recommended_product'].get('product_concept', 'Unknown')[:100]}...", "internal")
        
        return result
    
    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from LLM response with timeout protection."""
        import re
        
        # Limit text length to prevent hanging
        search_text = text[:10000] if len(text) > 10000 else text
        
        # Strategy 1: Try direct parse
        try:
            return json.loads(search_text)
        except:
            pass
        
        # Strategy 2: Find JSON in markdown code blocks
        try:
            json_block = re.search(r'```json\s*(\{.*?\})\s*```', search_text, re.DOTALL)
            if json_block:
                return json.loads(json_block.group(1))
        except:
            pass
        
        # Strategy 3: Find first { to last }
        try:
            first_brace = search_text.find('{')
            last_brace = search_text.rfind('}')
            if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                potential_json = search_text[first_brace:last_brace+1]
                return json.loads(potential_json)
        except:
            pass
        
        return None
    
    def _generate_fallback_recommendation(self,
                                           market_data: Dict[str, Any],
                                           tech_data: Dict[str, Any],
                                           user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a fallback recommendation when LLM JSON parsing fails."""
        
        # Extract the first product opportunity from brainstormed data
        product_ideas = market_data.get('product_ideas', [])
        emerging_needs = market_data.get('emerging_needs', [])
        opportunities = market_data.get('opportunity_areas', [])
        
        # Try to get the first technology analysis
        tech_analysis = tech_data.get('technology_analysis', [])
        first_tech = tech_analysis[0] if tech_analysis else {}
        first_idea = product_ideas[0] if product_ideas else {}
        
        # Build a recommendation based on available data
        product_concept = first_tech.get('product_concept') or \
                         first_idea.get('idea') or \
                         (opportunities[0] if opportunities else "Smart Device Solution")
        
        # Determine primary need - prefer from first_idea if available
        primary_need = first_idea.get('addresses_need')
        
        # If not available, infer from the concept
        if not primary_need:
            concept_lower = str(product_concept).lower()
            if any(word in concept_lower for word in ['charg', 'battery', 'power', 'energy']):
                primary_need = 'energy'
            elif any(word in concept_lower for word in ['health', 'medical', 'wellness']):
                primary_need = 'health'
            elif any(word in concept_lower for word in ['communication', 'connect', 'network']):
                primary_need = 'communication'
            elif any(word in concept_lower for word in ['safety', 'security', 'protect']):
                primary_need = 'safety'
            elif any(word in concept_lower for word in ['mobility', 'transport', 'vehicle']):
                primary_need = 'mobility'
            else:
                primary_need = 'essential_productivity'
        
        return {
            "recommended_product": {
                "product_concept": product_concept,
                "primary_need": primary_need,
                "justification": [
                    f"Addresses emerging need: {emerging_needs[0] if emerging_needs else 'key market need'}",
                    f"Selected from brainstormed product ideas",
                    "Technology is feasible and ready for implementation",
                    "Clear value proposition for users"
                ],
                "expected_impact": "Improves user experience and addresses key market needs",
                "next_steps": [
                    "Develop detailed product specification",
                    "Create prototype and validate with users",
                    "Refine based on feedback"
                ]
            },
            "alternative_opportunities": []
        }


class ResearchReportGenerator:
    """Generates comprehensive research reports."""
    
    @staticmethod
    def generate_text_report(findings: ResearchFindings,
                            market_data: Dict[str, Any],
                            tech_data: Dict[str, Any],
                            user_data: Dict[str, Any],
                            recommendation: Dict[str, Any]) -> str:
        """Generate a comprehensive text research report."""
        from datetime import datetime
        
        lines = []
        lines.append("=" * 80)
        lines.append("PRODUCT RESEARCH & DISCOVERY REPORT")
        lines.append("=" * 80)
        lines.append(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        lines.append("")
        
        # Research Scope
        if findings.research_scope:
            lines.append("RESEARCH SCOPE")
            lines.append("-" * 80)
            lines.append(findings.research_scope)
            lines.append("")
        
        # Brainstorming Results
        lines.append("1. BRAINSTORMING: INDUSTRIES & PRODUCT IDEAS")
        lines.append("-" * 80)
        lines.append("")
        lines.append("Industries Explored:")
        for i, industry in enumerate(market_data.get('industries', []), 1):
            lines.append(f"  {i}. {industry}")
        lines.append("")
        
        lines.append("Product Ideas Generated:")
        for i, idea in enumerate(market_data.get('product_ideas', []), 1):
            lines.append(f"\n  Idea {i}:")
            lines.append(f"    Product: {idea.get('idea', 'N/A')}")
            lines.append(f"    Industry: {idea.get('industry', 'N/A')}")
            lines.append(f"    Addresses Need: {idea.get('addresses_need', 'N/A')}")
            lines.append(f"    Description: {idea.get('description', 'N/A')}")
        lines.append("")
        
        lines.append("Emerging Needs Identified:")
        for i, need in enumerate(market_data.get('emerging_needs', []), 1):
            lines.append(f"  {i}. {need}")
        lines.append("")
        
        # Product Opportunities
        lines.append("2. PRODUCT OPPORTUNITIES IDENTIFIED")
        lines.append("-" * 80)
        for i, opp in enumerate(findings.product_opportunities or [], 1):
            lines.append(f"\nOpportunity {i}:")
            lines.append(f"  Product: {opp.get('product_concept', 'N/A')}")
            lines.append(f"  Primary Need: {opp.get('primary_need', 'N/A')}")
            lines.append(f"  Market Size: {opp.get('market_size', 'N/A')}")
            lines.append(f"  Differentiation: {opp.get('differentiation', 'N/A')}")
        lines.append("")
        
        # Technology Analysis
        lines.append("3. TECHNOLOGY FEASIBILITY ANALYSIS")
        lines.append("-" * 80)
        for i, tech in enumerate(tech_data.get('technology_analysis', []), 1):
            lines.append(f"\nAnalysis {i}:")
            lines.append(f"  Product: {tech.get('product_concept', 'N/A')}")
            lines.append(f"  Feasibility: {tech.get('feasibility', 'N/A')}")
            lines.append(f"  Readiness: {tech.get('readiness', 'N/A')}")
            lines.append(f"  Technologies: {', '.join(tech.get('enabling_technologies', []))}")
        lines.append("")
        
        # User Research
        lines.append("4. USER NEEDS ANALYSIS")
        lines.append("-" * 80)
        for i, user in enumerate(user_data.get('user_analysis', []), 1):
            lines.append(f"\nUser Analysis {i}:")
            lines.append(f"  Product: {user.get('product_concept', 'N/A')}")
            lines.append(f"  Pain Points: {', '.join(user.get('pain_points', []))}")
            lines.append(f"  User Preferences: {', '.join(user.get('user_preferences', []))}")
        lines.append("")
        
        # Final Recommendation
        lines.append("5. RECOMMENDED PRODUCT")
        lines.append("-" * 80)
        rec = recommendation.get('recommended_product', {})
        if rec:
            lines.append(f"\nProduct Concept:")
            lines.append(f"  {rec.get('product_concept', 'N/A')}")
            lines.append(f"\nPrimary Human Need:")
            lines.append(f"  {rec.get('primary_need', 'N/A').title()}")
            lines.append(f"\nJustification:")
            for i, reason in enumerate(rec.get('justification', []), 1):
                lines.append(f"  {i}. {reason}")
            lines.append(f"\nExpected Impact:")
            lines.append(f"  {rec.get('expected_impact', 'N/A')}")
            lines.append(f"\nNext Steps:")
            for i, step in enumerate(rec.get('next_steps', []), 1):
                lines.append(f"  {i}. {step}")
        lines.append("")
        
        # Alternative Opportunities
        if recommendation.get('alternative_opportunities'):
            lines.append("6. ALTERNATIVE OPPORTUNITIES")
            lines.append("-" * 80)
            for i, alt in enumerate(recommendation.get('alternative_opportunities', []), 1):
                lines.append(f"  {i}. {alt.get('concept', 'N/A')} ({alt.get('primary_need', 'N/A')})")
            lines.append("")
        
        lines.append("=" * 80)
        lines.append("END OF REPORT")
        lines.append("=" * 80)
        
        return "\n".join(lines)
    
    @staticmethod
    def generate_pdf_report(findings: ResearchFindings, 
                           market_data: Dict[str, Any],
                           tech_data: Dict[str, Any],
                           user_data: Dict[str, Any],
                           recommendation: Dict[str, Any]) -> bytes:
        """Generate a comprehensive PDF research report."""
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter,
                               rightMargin=inch, leftMargin=inch,
                               topMargin=inch, bottomMargin=inch)
        
        # Container for the 'Flowable' objects
        elements = []
        
        # Define styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#34495e'),
            spaceAfter=12,
            spaceBefore=12
        )
        
        subheading_style = ParagraphStyle(
            'CustomSubHeading',
            parent=styles['Heading3'],
            fontSize=12,
            textColor=colors.HexColor('#7f8c8d'),
            spaceAfter=6
        )
        
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['BodyText'],
            fontSize=10,
            alignment=TA_JUSTIFY,
            spaceAfter=12
        )
        
        # Title Page
        elements.append(Spacer(1, 2*inch))
        elements.append(Paragraph("Product Research Report", title_style))
        elements.append(Paragraph("Core Devices Company", styles['Normal']))
        elements.append(Spacer(1, 0.5*inch))
        elements.append(Paragraph(f"Research Date: {findings.research_date.strftime('%B %d, %Y')}", styles['Normal']))
        elements.append(Paragraph(f"Scope: {findings.research_scope or 'Open Product Discovery'}", styles['Normal']))
        elements.append(PageBreak())
        
        # Executive Summary
        elements.append(Paragraph("Executive Summary", heading_style))
        
        if recommendation.get("recommended_product"):
            rec = recommendation["recommended_product"]
            summary_text = f"""
            <b>Recommended Product:</b> {rec.get('product_concept', 'N/A')}<br/><br/>
            <b>Primary Human Need:</b> {rec.get('primary_need', 'N/A').title()}<br/><br/>
            <b>Expected Impact:</b> {rec.get('expected_impact', 'N/A')}
            """
            elements.append(Paragraph(summary_text, body_style))
        
        elements.append(Spacer(1, 0.3*inch))
        
        # Table of Contents
        elements.append(Paragraph("Table of Contents", heading_style))
        toc_data = [
            ["1.", "Market Analysis"],
            ["2.", "Technology Analysis"],
            ["3.", "User Research"],
            ["4.", "Product Opportunities"],
            ["5.", "Final Recommendation"],
            ["6.", "Next Steps"]
        ]
        toc_table = Table(toc_data, colWidths=[0.5*inch, 5*inch])
        toc_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(toc_table)
        elements.append(PageBreak())
        
        # 1. Market Analysis
        elements.append(Paragraph("1. Market Analysis", heading_style))
        
        elements.append(Paragraph("Market Trends", subheading_style))
        for i, trend in enumerate(market_data.get('market_trends', []), 1):
            elements.append(Paragraph(f"{i}. {trend}", body_style))
        
        elements.append(Spacer(1, 0.2*inch))
        elements.append(Paragraph("Emerging Needs", subheading_style))
        for i, need in enumerate(market_data.get('emerging_needs', []), 1):
            elements.append(Paragraph(f"{i}. {need}", body_style))
        
        elements.append(Spacer(1, 0.2*inch))
        elements.append(Paragraph("Market Gaps", subheading_style))
        for i, gap in enumerate(market_data.get('market_gaps', []), 1):
            elements.append(Paragraph(f"{i}. {gap}", body_style))
        
        elements.append(PageBreak())
        
        # 2. Technology Analysis
        elements.append(Paragraph("2. Technology Analysis", heading_style))
        
        tech_analysis = tech_data.get('technology_analysis', [])
        for i, analysis in enumerate(tech_analysis, 1):
            elements.append(Paragraph(f"Opportunity {i}: {analysis.get('product_concept', 'N/A')}", subheading_style))
            
            tech_table_data = [
                ["Enabling Technologies", ", ".join(analysis.get('enabling_technologies', []))],
                ["Readiness Level", analysis.get('readiness', 'N/A').title()],
                ["Technical Feasibility", analysis.get('feasibility', 'N/A').title()],
                ["Component Availability", analysis.get('component_availability', 'N/A').replace('_', ' ').title()]
            ]
            
            tech_table = Table(tech_table_data, colWidths=[2*inch, 4*inch])
            tech_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ecf0f1')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
            ]))
            elements.append(tech_table)
            elements.append(Spacer(1, 0.2*inch))
        
        elements.append(PageBreak())
        
        # 3. User Research
        elements.append(Paragraph("3. User Research", heading_style))
        
        user_analysis = user_data.get('user_analysis', [])
        for i, analysis in enumerate(user_analysis, 1):
            elements.append(Paragraph(f"Opportunity {i}: {analysis.get('product_concept', 'N/A')}", subheading_style))
            
            elements.append(Paragraph("<b>Pain Points:</b>", body_style))
            for pain in analysis.get('pain_points', []):
                elements.append(Paragraph(f"• {pain}", body_style))
            
            elements.append(Paragraph("<b>Current Behaviors:</b>", body_style))
            for behavior in analysis.get('current_behaviors', []):
                elements.append(Paragraph(f"• {behavior}", body_style))
            
            elements.append(Paragraph("<b>Friction Points:</b>", body_style))
            for friction in analysis.get('friction_points', []):
                elements.append(Paragraph(f"• {friction}", body_style))
            
            elements.append(Spacer(1, 0.2*inch))
        
        elements.append(PageBreak())
        
        # 4. Product Opportunities
        elements.append(Paragraph("4. Product Opportunities Evaluated", heading_style))
        
        opportunities = market_data.get('opportunity_areas', [])
        for i, opp in enumerate(opportunities, 1):
            elements.append(Paragraph(f"{i}. {opp}", body_style))
        
        elements.append(PageBreak())
        
        # 5. Final Recommendation
        elements.append(Paragraph("5. Final Recommendation", heading_style))
        
        if recommendation.get("recommended_product"):
            rec = recommendation["recommended_product"]
            
            elements.append(Paragraph("<b>Product Concept:</b>", subheading_style))
            elements.append(Paragraph(rec.get('product_concept', 'N/A'), body_style))
            
            elements.append(Paragraph("<b>Primary Human Need:</b>", subheading_style))
            elements.append(Paragraph(rec.get('primary_need', 'N/A').title(), body_style))
            
            elements.append(Paragraph("<b>Justification for Selection:</b>", subheading_style))
            for i, reason in enumerate(rec.get('justification', []), 1):
                elements.append(Paragraph(f"{i}. {reason}", body_style))
            
            elements.append(Paragraph("<b>Expected Impact:</b>", subheading_style))
            elements.append(Paragraph(rec.get('expected_impact', 'N/A'), body_style))
        
        elements.append(PageBreak())
        
        # 6. Next Steps
        elements.append(Paragraph("6. Next Steps", heading_style))
        
        if recommendation.get("recommended_product"):
            next_steps = recommendation["recommended_product"].get('next_steps', [])
            for i, step in enumerate(next_steps, 1):
                elements.append(Paragraph(f"{i}. {step}", body_style))
        
        elements.append(Spacer(1, 0.5*inch))
        
        # Alternative Opportunities
        if recommendation.get("alternative_opportunities"):
            elements.append(Paragraph("Alternative Opportunities for Future Consideration", subheading_style))
            for i, alt in enumerate(recommendation.get("alternative_opportunities", []), 1):
                alt_text = f"{i}. {alt.get('concept', 'N/A')} (Primary Need: {alt.get('primary_need', 'N/A')})"
                elements.append(Paragraph(alt_text, body_style))
        
        # Build PDF
        doc.build(elements)
        
        # Get PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes


class ResearchTeam:
    """Coordinated research team that discovers product opportunities."""
    
    def __init__(self, llm_client: LLMClient, message_bus):
        self.llm = llm_client
        self.bus = message_bus
        
        # Initialize research agents
        self.market_researcher = MarketResearchAgent(llm_client, message_bus)
        self.tech_researcher = TechnologyResearchAgent(llm_client, message_bus)
        self.user_researcher = UserResearchAgent(llm_client, message_bus)
        self.research_lead = ResearchLeadAgent(llm_client, message_bus)
    
    async def execute_research_phase(self, scope: str = "", constraints: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute complete research phase and generate recommendation with PDF report."""
        from app.product_company.core_devices_company import Phase
        
        constraints = constraints or {}
        
        self.bus.send("Research_Team", "CEO_Agent", Phase.RESEARCH_DISCOVERY,
                     "[Research_Team] Starting autonomous product discovery research", "internal")
        
        # Step 1: Market research
        market_data = await self.market_researcher.research_market_trends(scope, constraints)
        opportunities = await self.market_researcher.identify_product_opportunities(market_data)
        
        # Step 2: Technology research
        tech_data = await self.tech_researcher.research_enabling_technologies(opportunities)
        
        # Step 3: User research
        user_data = await self.user_researcher.research_user_needs(opportunities)
        
        # Step 4: Synthesize and recommend
        recommendation = await self.research_lead.synthesize_research(market_data, tech_data, user_data)
        
        # Step 5: Generate text report (simplified from PDF)
        findings = ResearchFindings(
            industries=market_data.get('industries', []),
            product_ideas=market_data.get('product_ideas', []),
            emerging_needs=market_data.get('emerging_needs', []),
            product_opportunities=opportunities,
            recommended_product=recommendation.get('recommended_product'),
            research_scope=scope,
            constraints=constraints
        )
        
        text_report = ResearchReportGenerator.generate_text_report(
            findings, market_data, tech_data, user_data, recommendation
        )
        
        self.bus.send("Research_Team", "CEO_Agent", Phase.RESEARCH_DISCOVERY,
                     "[Research_Team] ✓ Research complete. Text report generated.", "internal")
        
        return {
            "findings": findings,
            "market_data": market_data,
            "tech_data": tech_data,
            "user_data": user_data,
            "recommendation": recommendation,
            "text_report": text_report,  # string
            "opportunities": opportunities
        }
