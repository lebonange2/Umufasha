"""AI agents for product debate."""
import json
import uuid
from typing import List, Dict, Any, Optional
from app.product_debate.models import (
    AgentRole, DeviationProposal, FeasibilityAnalysis,
    FeatureVector, ProposalStatus
)
from app.llm.client import LLMClient
import structlog

logger = structlog.get_logger(__name__)


class OpportunitySeeker:
    """Agent A: Enumerates deviations and articulates value."""
    
    def __init__(self, llm_client: LLMClient, seed: int, temperature: float):
        """Initialize Opportunity Seeker agent.
        
        Args:
            llm_client: OpenAI LLM client
            seed: Random seed for determinism
            temperature: Sampling temperature
        """
        self.llm_client = llm_client
        self.seed = seed
        self.temperature = temperature
        self.role = AgentRole.OPPORTUNITY_SEEKER
    
    async def generate_deviations(
        self,
        core_market: str,
        category: str,
        known_products: List[Dict[str, Any]],
        previous_rounds: List[Any] = None
    ) -> tuple[List[DeviationProposal], str, str]:
        """Generate 5-10 deviation proposals.
        
        Args:
            core_market: Core market name
            category: Product category
            known_products: List of known products
            previous_rounds: Previous debate rounds for context
            
        Returns:
            Tuple of (proposals list, system_prompt, response_text)
        """
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(
            core_market, category, known_products, previous_rounds
        )
        
        logger.info("Opportunity Seeker generating deviations", 
                   market=core_market, category=category)
        
        try:
            response = await self.llm_client.complete(system_prompt, user_prompt)
            if not response:
                logger.warning("Empty response from LLM")
                response = "No response received from model"
            
            proposals = self._parse_proposals(response)
            logger.info("Opportunity Seeker generated proposals", count=len(proposals), response_length=len(response))
            
            # Ensure we have at least one proposal
            if not proposals:
                logger.warning("No proposals parsed from response, creating default", response_preview=response[:200])
                # Create a default proposal from the response
                from app.product_debate.models import FeatureVector
                default_proposal = DeviationProposal(
                    id=str(uuid.uuid4()),
                    name="Parsed Opportunity",
                    description=response[:500] if len(response) > 500 else response,
                    feature_vector=FeatureVector(
                        functional_attributes=[],
                        target_user="consumer",
                        price_band="$100-500",
                        channel="DTC",
                        materials=[],
                        regulations=[],
                        pain_points=[]
                    ),
                    user_value=7.0,
                    novelty_sigma=0.75,
                    complexity=5.0,
                    status=ProposalStatus.PROPOSED
                )
                proposals = [default_proposal]
            
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            return proposals, full_prompt, response or ""
        except Exception as e:
            logger.error("Opportunity Seeker failed", error=str(e), exc_info=True)
            # Return error response but don't fail completely
            error_response = f"Error: {str(e)}"
            return [], system_prompt, error_response
    
    def _build_system_prompt(self) -> str:
        """Build system prompt for Opportunity Seeker."""
        return """You are Agent A: Opportunity Seeker. Your role is to enumerate small but meaningful deviations from known products that could unlock new demand or margin opportunities.

Your task:
1. Generate 5-10 product deviation proposals
2. Each proposal should be within ~1 standard deviation of novelty (adjacent innovation, not moonshots)
3. Focus on small but meaningful changes in: features, form factor, materials, channels, or business model
4. For each proposal, provide:
   - Name and description
   - Feature vector (functional attributes, target user, price band, channel, materials, regulations, pain points)
   - User Value score (0-10): How much value does this provide to users?
   - Novelty σ estimate (target 0.5-1.0): How novel is this relative to known products?
   - Complexity score (0-10, lower is better): How complex is this to build?
   - Why this deviation could unlock demand or margin

CRITICAL: You will receive context from previous rounds. DO NOT repeat proposals that were already made. Generate NEW and DIFFERENT ideas. Build on previous feedback, but explore new angles, features, or approaches. If similar ideas were rejected, learn from that and propose alternatives.

IMPORTANT: Write your response in natural, conversational language. Do NOT output JSON. Instead, describe each product opportunity in detail, explaining the name, description, features, target user, pricing, channel, materials, regulations, pain points it addresses, user value score, novelty estimate, complexity, and rationale. Be creative and thorough."""
    
    def _build_user_prompt(
        self,
        core_market: str,
        category: str,
        known_products: List[Dict[str, Any]],
        previous_rounds: List[Any] = None
    ) -> str:
        """Build user prompt."""
        prompt = f"""Core Market: {core_market}
Category: {category}

Known Products in this category:
{json.dumps(known_products, indent=2)}

"""
        
        # Add comprehensive previous rounds context
        if previous_rounds and len(previous_rounds) > 0:
            prompt += "\n" + "="*80 + "\n"
            prompt += "PREVIOUS ROUNDS CONTEXT (IMPORTANT: Do NOT repeat these ideas):\n"
            prompt += "="*80 + "\n\n"
            
            # Include last 3 rounds for context
            for round_data in previous_rounds[-3:]:
                if hasattr(round_data, 'round_number'):
                    prompt += f"\n--- Round {round_data.round_number} ---\n\n"
                    
                    # Agent A's previous proposals
                    if hasattr(round_data, 'agent_a_proposals') and round_data.agent_a_proposals:
                        prompt += "Previous proposals I made:\n"
                        for prop in round_data.agent_a_proposals:
                            desc = prop.description[:200] if prop.description else 'No description'
                            prompt += f"  • {prop.name}: {desc}\n"
                        prompt += "\n"
                    
                    # Agent B's previous analyses
                    if hasattr(round_data, 'agent_b_analyses') and round_data.agent_b_analyses:
                        prompt += "Agent B's previous feedback:\n"
                        for analysis in round_data.agent_b_analyses:
                            if hasattr(analysis, 'blockers') and analysis.blockers:
                                prompt += f"  • Blockers identified: {', '.join(analysis.blockers[:3])}\n"
                            if hasattr(analysis, 'suggested_fixes') and analysis.suggested_fixes:
                                prompt += f"  • Suggested fixes: {', '.join(analysis.suggested_fixes[:3])}\n"
                        prompt += "\n"
                    
                    # Converged proposals
                    if hasattr(round_data, 'converged_proposals') and round_data.converged_proposals:
                        prompt += "Proposals that converged:\n"
                        for prop in round_data.converged_proposals:
                            score = prop.composite_score if prop.composite_score is not None else 0.0
                            prompt += f"  • {prop.name} (Score: {score:.2f}/10)\n"
                        prompt += "\n"
                    
                    # Agent B's full response for context
                    if hasattr(round_data, 'agent_b_response') and round_data.agent_b_response:
                        prompt += f"Agent B's full analysis:\n{round_data.agent_b_response[:500]}...\n\n"
            
            prompt += "\n" + "="*80 + "\n"
            prompt += "INSTRUCTIONS:\n"
            prompt += "- Generate NEW proposals that are DIFFERENT from the ones above\n"
            prompt += "- Build on previous feedback and avoid repeating rejected ideas\n"
            prompt += "- Consider the feasibility concerns raised in previous rounds\n"
            prompt += "- Explore different angles, features, or approaches\n"
            prompt += "="*80 + "\n\n"
        
        prompt += "\nGenerate 5-10 NEW deviation proposals that are within 1-sigma novelty. Focus on realistic, buildable opportunities that could be launched in 6-18 months. Make sure these are DIFFERENT from any proposals made in previous rounds."
        
        return prompt
    
    def _parse_proposals(self, response: str) -> List[DeviationProposal]:
        """Parse LLM response into DeviationProposal objects.
        
        Handles both JSON and natural language responses.
        """
        proposals = []
        
        # First, try to extract JSON from response
        try:
            # Look for JSON array in the response
            start_idx = response.find('[')
            end_idx = response.rfind(']') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                data = json.loads(json_str)
                
                for item in data:
                    proposal = DeviationProposal(
                        id=str(uuid.uuid4()),
                        name=item.get("name", "Unnamed"),
                        description=item.get("description", ""),
                        feature_vector=FeatureVector.from_dict(item.get("feature_vector", {})),
                        user_value=float(item.get("user_value", 5.0)),
                        novelty_sigma=float(item.get("novelty_sigma", 0.5)),
                        complexity=float(item.get("complexity", 5.0)),
                        status=ProposalStatus.PROPOSED
                    )
                    proposals.append(proposal)
                
                if proposals:
                    logger.info("Parsed proposals from JSON", count=len(proposals))
                    return proposals
        except Exception as e:
            logger.debug("No valid JSON found, parsing natural language", error=str(e))
        
        # If no JSON or parsing failed, extract proposals from natural language
        # Look for numbered lists or product names
        lines = response.split('\n')
        current_proposal = None
        proposal_count = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for numbered items (1., 2., etc.) or product names
            if (line[0].isdigit() and ('.' in line[:3] or ')' in line[:3])) or \
               ('**' in line and len(line) < 100):  # Likely a product name
                # Save previous proposal if exists
                if current_proposal:
                    proposals.append(current_proposal)
                    proposal_count += 1
                
                # Extract name (remove numbering, markdown, etc.)
                name = line
                for prefix in ['1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.', '10.',
                              '1)', '2)', '3)', '4)', '5)', '6)', '7)', '8)', '9)', '10)',
                              '**', '*', '-']:
                    if name.startswith(prefix):
                        name = name[len(prefix):].strip()
                
                # Create new proposal
                current_proposal = DeviationProposal(
                    id=str(uuid.uuid4()),
                    name=name[:100] if len(name) < 100 else name[:97] + "...",
                    description="",
                    feature_vector=FeatureVector(
                        functional_attributes=[],
                        target_user="consumer",
                        price_band="$100-500",
                        channel="DTC",
                        materials=[],
                        regulations=[],
                        pain_points=[]
                    ),
                    user_value=7.0,  # Default reasonable value
                    novelty_sigma=0.75,  # Default within target range
                    complexity=5.0,  # Default moderate complexity
                    status=ProposalStatus.PROPOSED
                )
            elif current_proposal:
                # Add to description
                if current_proposal.description:
                    current_proposal.description += " " + line
                else:
                    current_proposal.description = line
                
                # Try to extract scores if mentioned
                if "user value" in line.lower() or "value:" in line.lower():
                    try:
                        import re
                        match = re.search(r'(\d+\.?\d*)', line)
                        if match:
                            current_proposal.user_value = float(match.group(1))
                    except:
                        pass
                if "novelty" in line.lower() or "σ" in line or "sigma" in line.lower():
                    try:
                        import re
                        match = re.search(r'(\d+\.?\d*)', line)
                        if match:
                            current_proposal.novelty_sigma = float(match.group(1))
                    except:
                        pass
                if "complexity" in line.lower():
                    try:
                        import re
                        match = re.search(r'(\d+\.?\d*)', line)
                        if match:
                            current_proposal.complexity = float(match.group(1))
                    except:
                        pass
        
        # Add last proposal
        if current_proposal:
            proposals.append(current_proposal)
            proposal_count += 1
        
        # If we still have no proposals, create at least one from the response
        if not proposals:
            logger.warning("Could not parse proposals, creating default from response")
            # Extract first sentence or first 100 chars as name
            first_line = response.split('\n')[0].strip()[:100]
            if not first_line:
                first_line = response[:100]
            
            proposal = DeviationProposal(
                id=str(uuid.uuid4()),
                name=first_line if len(first_line) < 100 else first_line[:97] + "...",
                description=response[:500],
                feature_vector=FeatureVector(
                    functional_attributes=[],
                    target_user="consumer",
                    price_band="$100-500",
                    channel="DTC",
                    materials=[],
                    regulations=[],
                    pain_points=[]
                ),
                user_value=7.0,
                novelty_sigma=0.75,
                complexity=5.0,
                status=ProposalStatus.PROPOSED
            )
            proposals.append(proposal)
        
        logger.info("Parsed proposals from natural language", count=len(proposals))
        return proposals


class SkepticalBuilder:
    """Agent B: Attacks proposals on feasibility and prunes/refines."""
    
    def __init__(self, llm_client: LLMClient, seed: int, temperature: float):
        """Initialize Skeptical Builder agent.
        
        Args:
            llm_client: Anthropic LLM client
            seed: Random seed for determinism
            temperature: Sampling temperature
        """
        self.llm_client = llm_client
        self.seed = seed
        self.temperature = temperature
        self.role = AgentRole.SKEPTICAL_BUILDER
    
    async def analyze_feasibility(
        self,
        proposals: List[DeviationProposal],
        core_market: str,
        category: str,
        previous_rounds: List[Any] = None
    ) -> tuple[List[FeasibilityAnalysis], str, str]:
        """Analyze feasibility of proposals.
        
        Args:
            proposals: List of deviation proposals
            core_market: Core market name
            category: Product category
            previous_rounds: Previous debate rounds for context
            
        Returns:
            Tuple of (analyses list, system_prompt, response_text)
        """
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(proposals, core_market, category, previous_rounds)
        
        logger.info("Skeptical Builder analyzing feasibility", 
                   proposal_count=len(proposals))
        
        try:
            response = await self.llm_client.complete(system_prompt, user_prompt)
            if not response:
                logger.warning("Empty response from LLM")
                response = "No response received from model"
            
            analyses = self._parse_analyses(response, proposals)
            logger.info("Skeptical Builder completed analyses", count=len(analyses), response_length=len(response))
            
            # Ensure we have at least one analysis per proposal
            if not analyses and proposals:
                logger.warning("No analyses parsed, creating default analyses", response_preview=response[:200])
                # Create default analyses
                for proposal in proposals:
                    from app.product_debate.models import FeasibilityAnalysis
                    analysis = FeasibilityAnalysis(
                        proposal_id=proposal.id,
                        blockers=[],
                        bom_estimate=None,
                        manufacturability=response[:500] if len(response) > 500 else response,
                        compliance_path="",
                        channel_fit="",
                        suggested_fixes=[]
                    )
                    analyses.append(analysis)
            
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            return analyses, full_prompt, response or ""
        except Exception as e:
            logger.error("Skeptical Builder failed", error=str(e), exc_info=True)
            # Return error response but create default analyses
            error_response = f"Error: {str(e)}"
            analyses = []
            if proposals:
                for proposal in proposals:
                    from app.product_debate.models import FeasibilityAnalysis
                    analysis = FeasibilityAnalysis(
                        proposal_id=proposal.id,
                        blockers=["Analysis error"],
                        bom_estimate=None,
                        manufacturability=error_response,
                        compliance_path="",
                        channel_fit="",
                        suggested_fixes=[]
                    )
                    analyses.append(analysis)
            return analyses, system_prompt, error_response
    
    def _build_system_prompt(self) -> str:
        """Build system prompt for Skeptical Builder."""
        return """You are Agent B: Skeptical Builder. Your role is to critically evaluate product proposals for feasibility, unit economics, compliance, operational complexity, and channel fit.

Your task:
1. For each proposal, identify blockers and concerns
2. Evaluate:
   - BOM cost (unit cost at MOQ 500/1000)
   - Manufacturing feasibility (DFM, processes, tooling)
   - Compliance requirements (FCC/CE/UL/EPA/USDA/etc)
   - Channel fit (DTC/Amazon/B2B/etc)
   - Operational complexity
3. Suggest fixes that keep novelty within the 1-sigma band
4. Be realistic but constructive - help refine ideas, not just reject them

CRITICAL: You will receive context from previous rounds. DO NOT simply repeat your previous analyses. Provide NEW insights, different perspectives, or deeper analysis. If you've already covered certain concerns, reference them briefly but focus on NEW aspects or deeper exploration. Build on your previous feedback to create a more comprehensive understanding.

IMPORTANT: Write your response in natural, conversational language. Do NOT output JSON. Instead, write a detailed analysis for each proposal in plain text, discussing blockers, BOM estimates, manufacturability, compliance, channel fit, and suggested fixes. Be thorough and constructive."""
    
    def _build_user_prompt(
        self,
        proposals: List[DeviationProposal],
        core_market: str,
        category: str,
        previous_rounds: List[Any] = None
    ) -> str:
        """Build user prompt."""
        proposals_json = [p.to_dict() for p in proposals]
        
        prompt = f"""Core Market: {core_market}
Category: {category}

Current Proposals to analyze:
{json.dumps(proposals_json, indent=2)}

"""
        
        # Add previous rounds context for Agent B
        if previous_rounds and len(previous_rounds) > 0:
            prompt += "\n" + "="*80 + "\n"
            prompt += "PREVIOUS ROUNDS CONTEXT (to avoid repeating feedback):\n"
            prompt += "="*80 + "\n\n"
            
            # Include last 3 rounds
            for round_data in previous_rounds[-3:]:
                if hasattr(round_data, 'round_number'):
                    prompt += f"\n--- Round {round_data.round_number} ---\n\n"
                    
                    # Previous proposals analyzed
                    if hasattr(round_data, 'agent_a_proposals') and round_data.agent_a_proposals:
                        prompt += "Previous proposals I analyzed:\n"
                        for prop in round_data.agent_a_proposals:
                            prompt += f"  • {prop.name}\n"
                        prompt += "\n"
                    
                    # My previous analyses
                    if hasattr(round_data, 'agent_b_analyses') and round_data.agent_b_analyses:
                        prompt += "My previous analyses:\n"
                        for analysis in round_data.agent_b_analyses:
                            if hasattr(analysis, 'blockers') and analysis.blockers:
                                prompt += f"  • Blockers: {', '.join(analysis.blockers[:3])}\n"
                            if hasattr(analysis, 'suggested_fixes') and analysis.suggested_fixes:
                                prompt += f"  • Fixes suggested: {', '.join(analysis.suggested_fixes[:3])}\n"
                        prompt += "\n"
                    
                    # My full previous response
                    if hasattr(round_data, 'agent_b_response') and round_data.agent_b_response:
                        prompt += f"My previous full analysis:\n{round_data.agent_b_response[:400]}...\n\n"
            
            prompt += "\n" + "="*80 + "\n"
            prompt += "INSTRUCTIONS:\n"
            prompt += "- Provide NEW insights, don't just repeat previous feedback\n"
            prompt += "- If similar concerns exist, reference them but add new perspectives\n"
            prompt += "- Build on previous analyses to deepen understanding\n"
            prompt += "- Look for different angles or aspects not covered before\n"
            prompt += "="*80 + "\n\n"
        
        prompt += """For each proposal, provide a detailed feasibility analysis in natural language. Discuss:
- Key blockers and concerns
- Estimated BOM cost
- Manufacturing feasibility and challenges
- Compliance requirements and path
- Channel fit assessment
- Suggested fixes to improve feasibility

Write your response as a conversational analysis, not as JSON. Address each proposal by name and provide thoughtful, constructive feedback. Make sure your analysis is NEW and builds on previous rounds, not just repeating them."""
        
        return prompt
    
    def _parse_analyses(
        self,
        response: str,
        proposals: List[DeviationProposal]
    ) -> List[FeasibilityAnalysis]:
        """Parse LLM response into FeasibilityAnalysis objects.
        
        Tries to extract structured data from natural language response.
        Falls back to creating basic analyses if JSON parsing fails.
        """
        analyses = []
        
        # Create mapping of proposal names to IDs
        proposal_map = {p.name: p.id for p in proposals}
        
        # First, try to extract JSON if present
        try:
            start_idx = response.find('[')
            end_idx = response.rfind(']') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                data = json.loads(json_str)
                
                for item in data:
                    proposal_id = item.get("proposal_id")
                    # If proposal_id not found, try to match by name
                    if not proposal_id or proposal_id not in proposal_map.values():
                        proposal_name = item.get("proposal_name", "")
                        proposal_id = proposal_map.get(proposal_name, proposals[0].id if proposals else "")
                    
                    analysis = FeasibilityAnalysis(
                        proposal_id=proposal_id,
                        blockers=item.get("blockers", []),
                        bom_estimate=item.get("bom_estimate"),
                        manufacturability=item.get("manufacturability", ""),
                        compliance_path=item.get("compliance_path", ""),
                        channel_fit=item.get("channel_fit", ""),
                        suggested_fixes=item.get("suggested_fixes", [])
                    )
                    analyses.append(analysis)
                return analyses
        except Exception as e:
            logger.debug("No JSON found in response, parsing natural language", error=str(e))
        
        # If no JSON, create analyses from natural language response
        # Try to match proposals mentioned in the text
        for proposal in proposals:
            # Check if proposal name is mentioned in response
            if proposal.name.lower() in response.lower():
                # Extract relevant parts of response for this proposal
                # Create a basic analysis with the full response text
                analysis = FeasibilityAnalysis(
                    proposal_id=proposal.id,
                    blockers=[],  # Will be extracted if possible
                    bom_estimate=None,
                    manufacturability=response[:500] if len(response) > 500 else response,  # Use response as manufacturability
                    compliance_path="",
                    channel_fit="",
                    suggested_fixes=[]
                )
                analyses.append(analysis)
        
        # If no matches found, create one analysis per proposal with the full response
        if not analyses and proposals:
            for proposal in proposals:
                analysis = FeasibilityAnalysis(
                    proposal_id=proposal.id,
                    blockers=[],
                    bom_estimate=None,
                    manufacturability=response,
                    compliance_path="",
                    channel_fit="",
                    suggested_fixes=[]
                )
                analyses.append(analysis)
        
        return analyses

