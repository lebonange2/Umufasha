"""Debate protocol orchestrator."""
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
import structlog

from app.product_debate.models import (
    DebateSession, DebateRound, DeviationProposal,
    FeasibilityAnalysis, ConceptOnePager, ProposalStatus
)
from app.product_debate.agents import OpportunitySeeker, SkepticalBuilder
from app.product_debate.scoring import NoveltyScorer, check_go_threshold
from app.llm.client import LLMClient
from app.core.config import settings

logger = structlog.get_logger(__name__)


class DebateOrchestrator:
    """Orchestrates the debate between two agents."""
    
    def __init__(
        self,
        session_id: str,
        seed: int,
        temperature: float,
        max_rounds: int,
        core_market: str,
        category: str,
        known_products: List[Dict[str, Any]],
        agent_a_model: str = "gpt-4o",
        agent_b_model: str = "claude-3-haiku-20240307"
    ):
        """Initialize debate orchestrator.
        
        Args:
            session_id: Unique session ID
            seed: Random seed
            temperature: Sampling temperature
            max_rounds: Maximum debate rounds
            core_market: Core market name
            category: Product category
            known_products: List of known products
            agent_a_model: OpenAI model name for Agent A
            agent_b_model: Anthropic model name for Agent B
        """
        self.session_id = session_id
        self.seed = seed
        self.temperature = temperature
        self.max_rounds = max_rounds
        self.core_market = core_market
        self.category = category
        self.known_products = known_products
        
        # Initialize LLM clients - auto-detect provider from model name
        from app.product_debate.utils import detect_provider_from_model, get_api_key_for_provider
        
        agent_a_provider = detect_provider_from_model(agent_a_model)
        agent_a_api_key = get_api_key_for_provider(agent_a_provider)
        agent_b_provider = detect_provider_from_model(agent_b_model)
        agent_b_api_key = get_api_key_for_provider(agent_b_provider)
        
        if not agent_a_api_key:
            logger.warning(f"API key for {agent_a_provider} is not set - Agent A will fail")
        if not agent_b_api_key:
            logger.warning(f"API key for {agent_b_provider} is not set - Agent B will fail")
        
        self.agent_a_client = LLMClient(
            api_key=agent_a_api_key,
            model=agent_a_model,
            provider=agent_a_provider
        )
        self.agent_b_client = LLMClient(
            api_key=agent_b_api_key,
            model=agent_b_model,
            provider=agent_b_provider
        )
        
        # Initialize agents
        self.agent_a = OpportunitySeeker(self.agent_a_client, seed, temperature)
        self.agent_b = SkepticalBuilder(self.agent_b_client, seed, temperature)
        
        # Initialize scorer
        self.scorer = NoveltyScorer(known_products)
        
        # Cancellation flag
        self.cancelled = False
        
        # Session state
        self.session = DebateSession(
            session_id=session_id,
            seed=seed,
            temperature=temperature,
            max_rounds=max_rounds,
            core_market=core_market,
            category=category,
            known_products=known_products
        )
    
    async def run_debate(self) -> DebateSession:
        """Run the complete debate protocol.
        
        Returns:
            Completed debate session
        """
        logger.info("Starting debate session", session_id=self.session_id)
        
        try:
            for round_num in range(1, self.max_rounds + 1):
                # Check if cancelled
                if self.cancelled:
                    logger.info("Debate cancelled", session_id=self.session_id)
                    break
                
                logger.info("Starting debate round", round=round_num, max_rounds=self.max_rounds)
                
                # Save session before starting round (so UI knows round is starting)
                from app.product_debate.storage import SessionStorage
                storage = SessionStorage()
                storage.save_session(self.session)
                
                # Step 1: Agent A generates deviations
                try:
                    proposals, agent_a_prompt, agent_a_response = await self.agent_a.generate_deviations(
                        self.core_market,
                        self.category,
                        self.known_products,
                        self.session.rounds
                    )
                    logger.info("Agent A completed", 
                               round=round_num,
                               proposals_count=len(proposals),
                               response_length=len(agent_a_response) if agent_a_response else 0)
                except Exception as e:
                    logger.error("Agent A failed", error=str(e), round=round_num)
                    # Create error response so debate can continue
                    agent_a_prompt = "Error occurred"
                    agent_a_response = f"Error generating proposals: {str(e)}"
                    proposals = []
                
                # Create a partial round with Agent A's response (for live display)
                partial_round = DebateRound(
                    round_number=round_num,
                    timestamp=datetime.now(),
                    agent_a_proposals=proposals if proposals else [],
                    agent_b_analyses=[],
                    converged_proposals=[],
                    agent_a_prompt=agent_a_prompt,
                    agent_a_response=agent_a_response,
                    agent_b_prompt="",
                    agent_b_response=""
                )
                
                # Add or update the round in session
                # Find existing round or append new one
                existing_round_idx = None
                for idx, r in enumerate(self.session.rounds):
                    if r.round_number == round_num:
                        existing_round_idx = idx
                        break
                
                if existing_round_idx is not None:
                    # Update existing round
                    self.session.rounds[existing_round_idx] = partial_round
                else:
                    # Add new round
                    self.session.rounds.append(partial_round)
                
                # Save session after Agent A responds (for live updates)
                storage.save_session(self.session)
                
                if not proposals:
                    logger.warning("No proposals generated", round=round_num, response_preview=agent_a_response[:200])
                    # Don't break - continue to next round or create a default proposal
                    # Create a default proposal so the debate can continue
                    from app.product_debate.models import FeatureVector
                    default_proposal = DeviationProposal(
                        id=str(uuid.uuid4()),
                        name="Default Proposal",
                        description=agent_a_response[:500] if agent_a_response else "No proposals generated",
                        feature_vector=FeatureVector(
                            functional_attributes=[],
                            target_user="consumer",
                            price_band="$100-500",
                            channel="DTC",
                            materials=[],
                            regulations=[],
                            pain_points=[]
                        ),
                        user_value=5.0,
                        novelty_sigma=0.5,
                        complexity=5.0,
                        status=ProposalStatus.PROPOSED
                    )
                    proposals = [default_proposal]
                    logger.info("Created default proposal to continue debate", round=round_num)
                
                # Update novelty sigma for each proposal
                for proposal in proposals:
                    proposal.novelty_sigma = self.scorer.calculate_novelty_sigma(
                        proposal.feature_vector
                    )
                    proposal.composite_score = self.scorer.calculate_composite_score(proposal)
                
                # Step 2: Agent B analyzes feasibility
                try:
                    analyses, agent_b_prompt, agent_b_response = await self.agent_b.analyze_feasibility(
                        proposals,
                        self.core_market,
                        self.category,
                        self.session.rounds  # Pass previous rounds for context
                    )
                    logger.info("Agent B completed analysis", 
                               round=round_num,
                               analyses_count=len(analyses),
                               response_length=len(agent_b_response) if agent_b_response else 0)
                except Exception as e:
                    logger.error("Agent B analysis failed", error=str(e), round=round_num)
                    # Create a default analysis so debate can continue
                    analyses = []
                    agent_b_prompt = "Error occurred"
                    agent_b_response = f"Error analyzing proposals: {str(e)}"
                    
                    # Create at least one analysis per proposal
                    for proposal in proposals:
                        from app.product_debate.models import FeasibilityAnalysis
                        analysis = FeasibilityAnalysis(
                            proposal_id=proposal.id,
                            blockers=["Analysis error occurred"],
                            bom_estimate=None,
                            manufacturability=agent_b_response,
                            compliance_path="",
                            channel_fit="",
                            suggested_fixes=[]
                        )
                        analyses.append(analysis)
                
                # Update the round with Agent B's response
                complete_round = DebateRound(
                    round_number=round_num,
                    timestamp=partial_round.timestamp,
                    agent_a_proposals=proposals,
                    agent_b_analyses=analyses,
                    converged_proposals=[],
                    agent_a_prompt=agent_a_prompt,
                    agent_a_response=agent_a_response,
                    agent_b_prompt=agent_b_prompt,
                    agent_b_response=agent_b_response
                )
                
                # Update the round in session immediately after Agent B responds
                existing_round_idx = None
                for idx, r in enumerate(self.session.rounds):
                    if r.round_number == round_num:
                        existing_round_idx = idx
                        break
                
                if existing_round_idx is not None:
                    self.session.rounds[existing_round_idx] = complete_round
                else:
                    self.session.rounds.append(complete_round)
                
                # Save session after Agent B responds (for live updates)
                storage.save_session(self.session)
                
                # Step 3: Apply feasibility concerns to proposals
                for analysis in analyses:
                    for proposal in proposals:
                        if proposal.id == analysis.proposal_id:
                            proposal.feasibility_concerns = analysis.blockers
                            proposal.refinements = analysis.suggested_fixes
                            proposal.status = ProposalStatus.ATTACKED
                
                # Step 4: Convergence - compute composite scores and keep top 3
                proposals.sort(key=lambda p: p.composite_score or 0, reverse=True)
                converged = proposals[:3]
                
                for proposal in converged:
                    proposal.status = ProposalStatus.CONVERGED
                
                # Update the round with convergence results
                complete_round.converged_proposals = converged
                complete_round.agent_b_analyses = analyses
                
                # Update the round in session
                existing_round_idx = None
                for idx, r in enumerate(self.session.rounds):
                    if r.round_number == round_num:
                        existing_round_idx = idx
                        break
                
                if existing_round_idx is not None:
                    self.session.rounds[existing_round_idx] = complete_round
                else:
                    self.session.rounds.append(complete_round)
                
                # Save session after round complete
                storage.save_session(self.session)
                
                # Step 5: Check if we should deepen a concept
                if converged and converged[0].composite_score and converged[0].composite_score >= 7.0:
                    logger.info("Deepening top concept", 
                               proposal=converged[0].name,
                               score=converged[0].composite_score)
                    
                    concept = await self._deepen_concept(converged[0])
                    
                    if concept:
                        self.session.final_concept = concept
                        
                        # Check Go Threshold
                        if check_go_threshold(converged[0], concept):
                            logger.info("Go Threshold met!", 
                                       composite_score=converged[0].composite_score,
                                       margin=concept.gross_margin)
                            self.session.go_threshold_met = True
                            break
                
                # If we have a good concept but didn't meet threshold, continue
                if converged and converged[0].composite_score and converged[0].composite_score >= 6.5:
                    # Continue to next round to refine
                    continue
                elif round_num >= self.max_rounds:
                    # Max rounds reached, use best available
                    if converged:
                        concept = await self._deepen_concept(converged[0])
                        if concept:
                            self.session.final_concept = concept
                    break
            
            # Generate taxonomy if we have a final concept
            if self.session.final_concept:
                self.session.taxonomy = await self._generate_taxonomy()
            
            logger.info("Debate session completed", 
                       session_id=self.session_id,
                       rounds=len(self.session.rounds),
                       go_threshold_met=self.session.go_threshold_met)
            
            return self.session
        except Exception as e:
            logger.error("Debate session failed", error=str(e), session_id=self.session_id, exc_info=True)
            # Save session even if debate failed
            from app.product_debate.storage import SessionStorage
            storage = SessionStorage()
            storage.save_session(self.session)
            raise
    
    async def _deepen_concept(self, proposal: DeviationProposal) -> Optional[ConceptOnePager]:
        """Deepen a concept into a full one-pager.
        
        Args:
            proposal: Top proposal to deepen
            
        Returns:
            ConceptOnePager or None
        """
        logger.info("Deepening concept", proposal_id=proposal.id)
        
        # Use Agent A to generate one-pager
        system_prompt = """You are creating a detailed product concept one-pager. Provide all the following information in JSON format."""
        
        user_prompt = f"""Create a detailed one-pager for this product concept:

Name: {proposal.name}
Description: {proposal.description}
Feature Vector: {proposal.feature_vector.to_dict()}

Provide a JSON object with this exact structure:
{{
  "name": "Product Name",
  "user_story": "As a [user], I want [goal] so that [benefit]",
  "top_features": ["feature1", "feature2", "feature3"],
  "bom": {{"component1": 10.50, "component2": 5.25, ...}},
  "unit_cost": 25.75,
  "target_msrp": 49.99,
  "gross_margin": 48.5,
  "supply_notes": "Notes on suppliers and supply chain...",
  "compliance_path": "Required certifications and steps...",
  "pilot_channel": "DTC/Amazon/B2B/etc",
  "first_run_moqs": {{"component1": 500, "component2": 1000}},
  "risks": [
    {{"risk": "Risk description", "mitigation": "Mitigation strategy"}},
    ...
  ]
}}

Ensure:
- BOM costs are realistic for MOQ 500/1000
- Gross margin is calculated as: ((MSRP - unit_cost) / MSRP) * 100
- Risks include top 3 risks with practical mitigations
- All information is realistic and buildable within 6-18 months"""
        
        try:
            response = await self.agent_a_client.complete(system_prompt, user_prompt)
            
            # Parse JSON response
            import json
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                data = json.loads(json_str)
                
                concept = ConceptOnePager.from_dict(data)
                return concept
        except Exception as e:
            logger.error("Failed to deepen concept", error=str(e))
        
        return None
    
    async def _generate_taxonomy(self) -> Dict[str, List[str]]:
        """Generate taxonomy structure from final concept.
        
        Returns:
            Taxonomy dictionary
        """
        if not self.session.final_concept:
            return {}
        
        # Use Agent A to generate taxonomy
        system_prompt = """You are generating a product taxonomy. Output only the taxonomy structure in JSON format, no prose."""
        
        user_prompt = f"""Generate a taxonomy for this product:

Name: {self.session.final_concept.name}
Category: {self.session.category}
Market: {self.session.core_market}
Features: {self.session.final_concept.top_features}

Output ONLY a JSON object with this structure (populate as many levels as justified):
{{
  "Core Market": ["{self.session.core_market}"],
  "Category": ["category1", "category2", ...],
  "Subcategory": ["subcat1", "subcat2", ...],
  "Niche": ["niche1", "niche2", ...],
  "Sub-Niche": ["sub-niche1", ...],
  "Sub-Sub-Niche": ["sub-sub-niche1", ...]
}}

No explanations, no prose, just the JSON structure."""
        
        try:
            response = await self.agent_a_client.complete(system_prompt, user_prompt)
            
            import json
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                taxonomy = json.loads(json_str)
                return taxonomy
        except Exception as e:
            logger.error("Failed to generate taxonomy", error=str(e))
        
        return {}

