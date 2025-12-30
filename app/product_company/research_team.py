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
    
    # Market Analysis
    market_trends: List[str] = field(default_factory=list)
    emerging_needs: List[str] = field(default_factory=list)
    market_gaps: List[str] = field(default_factory=list)
    
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
        """Research current market trends in electronics/devices."""
        from app.product_company.core_devices_company import Phase
        
        self.bus.send(self.role, "INTERNAL", Phase.RESEARCH_DISCOVERY,
                     "[Market_Research_Agent] ✓ Checklist 1/4: Analyzing market trends", "internal")
        
        prompt = f"""You are a Market Research Agent analyzing opportunities for electronic products.

Research Scope: {scope if scope else "Open exploration of electronic product opportunities"}
Constraints: {json.dumps(constraints, indent=2)}

Conduct market analysis:
1. Identify 5-7 current market trends in consumer electronics/devices
2. Analyze which primary human needs are underserved
3. Identify market gaps where current solutions have high friction
4. List emerging market opportunities

Focus on products that address primary human needs:
- energy, water, food, shelter, health, communication, safety, mobility, essential productivity

Output as JSON: {{
    "market_trends": ["trend1", "trend2", ...],
    "emerging_needs": ["need1", "need2", ...],
    "market_gaps": ["gap1", "gap2", ...],
    "opportunity_areas": ["area1", "area2", ...]
}}"""
        
        response = await self.llm.generate(prompt)
        result = self._extract_json(response)
        
        self.bus.send(self.role, "Research_Lead_Agent", Phase.RESEARCH_DISCOVERY,
                     f"[Market_Research_Agent] ✓ Identified {len(result.get('market_trends', []))} market trends", "internal")
        
        return result or {"market_trends": [], "emerging_needs": [], "market_gaps": [], "opportunity_areas": []}
    
    async def identify_product_opportunities(self, market_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify specific product opportunities from market analysis."""
        from app.product_company.core_devices_company import Phase
        
        self.bus.send(self.role, "INTERNAL", Phase.RESEARCH_DISCOVERY,
                     "[Market_Research_Agent] ✓ Checklist 2/4: Identifying product opportunities", "internal")
        
        prompt = f"""Based on market analysis, propose 3-5 specific product opportunities.

Market Data: {json.dumps(market_data, indent=2)}

For each opportunity:
1. Product concept (brief description)
2. Primary human need it addresses
3. Market size estimate (small/medium/large)
4. Friction points in current solutions
5. Differentiation potential

Output as JSON: {{
    "opportunities": [
        {{
            "product_concept": "...",
            "primary_need": "energy|water|food|shelter|health|communication|safety|mobility|essential_productivity",
            "market_size": "small|medium|large",
            "current_friction": "...",
            "differentiation": "..."
        }},
        ...
    ]
}}"""
        
        response = await self.llm.generate(prompt)
        result = self._extract_json(response)
        
        opportunities = result.get("opportunities", []) if result else []
        
        self.bus.send(self.role, "Research_Lead_Agent", Phase.RESEARCH_DISCOVERY,
                     f"[Market_Research_Agent] ✓ Identified {len(opportunities)} product opportunities", "internal")
        
        return opportunities
    
    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from LLM response."""
        try:
            return json.loads(text)
        except:
            import re
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
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
        
        response = await self.llm.generate(prompt)
        result = self._extract_json(response)
        
        self.bus.send(self.role, "Research_Lead_Agent", Phase.RESEARCH_DISCOVERY,
                     f"[Technology_Research_Agent] ✓ Analyzed technology feasibility", "internal")
        
        return result or {"technology_analysis": []}
    
    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from LLM response."""
        try:
            return json.loads(text)
        except:
            import re
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
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
        
        response = await self.llm.generate(prompt)
        result = self._extract_json(response)
        
        self.bus.send(self.role, "Research_Lead_Agent", Phase.RESEARCH_DISCOVERY,
                     f"[User_Research_Agent] ✓ Analyzed user needs and behaviors", "internal")
        
        return result or {"user_analysis": []}
    
    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from LLM response."""
        try:
            return json.loads(text)
        except:
            import re
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
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
        
        response = await self.llm.generate(prompt)
        result = self._extract_json(response)
        
        if result and result.get("recommended_product"):
            self.bus.send(self.role, "CEO_Agent", Phase.RESEARCH_DISCOVERY,
                         f"[Research_Lead_Agent] ✓ Recommended Product: {result['recommended_product'].get('product_concept', 'Unknown')[:100]}...", "internal")
        
        return result or {"recommended_product": None, "alternative_opportunities": []}
    
    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from LLM response."""
        try:
            return json.loads(text)
        except:
            import re
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except:
                    pass
        return None


class ResearchReportGenerator:
    """Generates comprehensive PDF reports from research findings."""
    
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
        
        # Step 5: Generate PDF report
        findings = ResearchFindings(
            market_trends=market_data.get('market_trends', []),
            emerging_needs=market_data.get('emerging_needs', []),
            market_gaps=market_data.get('market_gaps', []),
            product_opportunities=opportunities,
            recommended_product=recommendation.get('recommended_product'),
            research_scope=scope,
            constraints=constraints
        )
        
        pdf_report = ResearchReportGenerator.generate_pdf_report(
            findings, market_data, tech_data, user_data, recommendation
        )
        
        self.bus.send("Research_Team", "CEO_Agent", Phase.RESEARCH_DISCOVERY,
                     "[Research_Team] ✓ Research complete. PDF report generated.", "internal")
        
        return {
            "findings": findings,
            "market_data": market_data,
            "tech_data": tech_data,
            "user_data": user_data,
            "recommendation": recommendation,
            "pdf_report": pdf_report,  # bytes
            "opportunities": opportunities
        }
