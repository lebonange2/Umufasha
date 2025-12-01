"""Data models for product debate system."""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
import json


class AgentRole(str, Enum):
    """Agent roles in the debate."""
    OPPORTUNITY_SEEKER = "opportunity_seeker"  # Agent A
    SKEPTICAL_BUILDER = "skeptical_builder"    # Agent B


class ProposalStatus(str, Enum):
    """Status of a product proposal."""
    PROPOSED = "proposed"
    ATTACKED = "attacked"
    REFINED = "refined"
    CONVERGED = "converged"
    REJECTED = "rejected"


@dataclass
class FeatureVector:
    """Feature vector representation of a product."""
    functional_attributes: List[str] = field(default_factory=list)
    target_user: str = ""
    price_band: str = ""  # e.g., "$50-100", "$100-200"
    channel: str = ""  # DTC, Amazon, B2B, etc.
    materials: List[str] = field(default_factory=list)
    regulations: List[str] = field(default_factory=list)
    pain_points: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "functional_attributes": self.functional_attributes,
            "target_user": self.target_user,
            "price_band": self.price_band,
            "channel": self.channel,
            "materials": self.materials,
            "regulations": self.regulations,
            "pain_points": self.pain_points
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FeatureVector":
        """Create from dictionary."""
        return cls(
            functional_attributes=data.get("functional_attributes", []),
            target_user=data.get("target_user", ""),
            price_band=data.get("price_band", ""),
            channel=data.get("channel", ""),
            materials=data.get("materials", []),
            regulations=data.get("regulations", []),
            pain_points=data.get("pain_points", [])
        )


@dataclass
class DeviationProposal:
    """A product deviation proposal from Agent A."""
    id: str
    name: str
    description: str
    feature_vector: FeatureVector
    user_value: float  # 0-10
    novelty_sigma: float  # Target 0.5-1.0
    complexity: float  # 0-10, lower is better
    status: ProposalStatus = ProposalStatus.PROPOSED
    feasibility_concerns: List[str] = field(default_factory=list)
    refinements: List[str] = field(default_factory=list)
    composite_score: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "feature_vector": self.feature_vector.to_dict(),
            "user_value": self.user_value,
            "novelty_sigma": self.novelty_sigma,
            "complexity": self.complexity,
            "status": self.status.value,
            "feasibility_concerns": self.feasibility_concerns,
            "refinements": self.refinements,
            "composite_score": self.composite_score
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DeviationProposal":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            feature_vector=FeatureVector.from_dict(data["feature_vector"]),
            user_value=data["user_value"],
            novelty_sigma=data["novelty_sigma"],
            complexity=data["complexity"],
            status=ProposalStatus(data.get("status", "proposed")),
            feasibility_concerns=data.get("feasibility_concerns", []),
            refinements=data.get("refinements", []),
            composite_score=data.get("composite_score")
        )


@dataclass
class FeasibilityAnalysis:
    """Feasibility analysis from Agent B."""
    proposal_id: str
    blockers: List[str] = field(default_factory=list)
    bom_estimate: Optional[float] = None  # Unit cost at MOQ 500/1000
    manufacturability: str = ""
    compliance_path: str = ""
    channel_fit: str = ""
    suggested_fixes: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "proposal_id": self.proposal_id,
            "blockers": self.blockers,
            "bom_estimate": self.bom_estimate,
            "manufacturability": self.manufacturability,
            "compliance_path": self.compliance_path,
            "channel_fit": self.channel_fit,
            "suggested_fixes": self.suggested_fixes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FeasibilityAnalysis":
        """Create from dictionary."""
        return cls(
            proposal_id=data["proposal_id"],
            blockers=data.get("blockers", []),
            bom_estimate=data.get("bom_estimate"),
            manufacturability=data.get("manufacturability", ""),
            compliance_path=data.get("compliance_path", ""),
            channel_fit=data.get("channel_fit", ""),
            suggested_fixes=data.get("suggested_fixes", [])
        )


@dataclass
class ConceptOnePager:
    """Final concept one-pager."""
    name: str
    user_story: str
    top_features: List[str]
    bom: Dict[str, float]  # Component -> cost
    unit_cost: float
    target_msrp: float
    gross_margin: float
    supply_notes: str
    compliance_path: str
    pilot_channel: str
    first_run_moqs: Dict[str, int]  # Component -> MOQ
    risks: List[Dict[str, str]]  # [{"risk": "...", "mitigation": "..."}]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "user_story": self.user_story,
            "top_features": self.top_features,
            "bom": self.bom,
            "unit_cost": self.unit_cost,
            "target_msrp": self.target_msrp,
            "gross_margin": self.gross_margin,
            "supply_notes": self.supply_notes,
            "compliance_path": self.compliance_path,
            "pilot_channel": self.pilot_channel,
            "first_run_moqs": self.first_run_moqs,
            "risks": self.risks
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConceptOnePager":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            user_story=data["user_story"],
            top_features=data["top_features"],
            bom=data["bom"],
            unit_cost=data["unit_cost"],
            target_msrp=data["target_msrp"],
            gross_margin=data["gross_margin"],
            supply_notes=data["supply_notes"],
            compliance_path=data["compliance_path"],
            pilot_channel=data["pilot_channel"],
            first_run_moqs=data["first_run_moqs"],
            risks=data["risks"]
        )


@dataclass
class DebateRound:
    """A single round of debate."""
    round_number: int
    timestamp: datetime
    agent_a_proposals: List[DeviationProposal]
    agent_b_analyses: List[FeasibilityAnalysis]
    converged_proposals: List[DeviationProposal]
    agent_a_prompt: str = ""
    agent_a_response: str = ""
    agent_b_prompt: str = ""
    agent_b_response: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "round_number": self.round_number,
            "timestamp": self.timestamp.isoformat(),
            "agent_a_proposals": [p.to_dict() for p in self.agent_a_proposals],
            "agent_b_analyses": [a.to_dict() for a in self.agent_b_analyses],
            "converged_proposals": [p.to_dict() for p in self.converged_proposals],
            "agent_a_prompt": self.agent_a_prompt,
            "agent_a_response": self.agent_a_response,
            "agent_b_prompt": self.agent_b_prompt,
            "agent_b_response": self.agent_b_response
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DebateRound":
        """Create from dictionary."""
        return cls(
            round_number=data["round_number"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            agent_a_proposals=[DeviationProposal.from_dict(p) for p in data["agent_a_proposals"]],
            agent_b_analyses=[FeasibilityAnalysis.from_dict(a) for a in data["agent_b_analyses"]],
            converged_proposals=[DeviationProposal.from_dict(p) for p in data["converged_proposals"]],
            agent_a_prompt=data.get("agent_a_prompt", ""),
            agent_a_response=data.get("agent_a_response", ""),
            agent_b_prompt=data.get("agent_b_prompt", ""),
            agent_b_response=data.get("agent_b_response", "")
        )


@dataclass
class DebateSession:
    """A complete debate session."""
    session_id: str
    seed: int
    temperature: float
    max_rounds: int
    core_market: str
    category: str
    known_products: List[Dict[str, Any]]  # List of known products with feature vectors
    rounds: List[DebateRound] = field(default_factory=list)
    final_concept: Optional[ConceptOnePager] = None
    taxonomy: Optional[Dict[str, List[str]]] = None
    go_threshold_met: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "session_id": self.session_id,
            "seed": self.seed,
            "temperature": self.temperature,
            "max_rounds": self.max_rounds,
            "core_market": self.core_market,
            "category": self.category,
            "known_products": self.known_products,
            "rounds": [r.to_dict() for r in self.rounds],
            "final_concept": self.final_concept.to_dict() if self.final_concept else None,
            "taxonomy": self.taxonomy,
            "go_threshold_met": self.go_threshold_met,
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DebateSession":
        """Create from dictionary."""
        return cls(
            session_id=data["session_id"],
            seed=data["seed"],
            temperature=data["temperature"],
            max_rounds=data["max_rounds"],
            core_market=data["core_market"],
            category=data["category"],
            known_products=data["known_products"],
            rounds=[DebateRound.from_dict(r) for r in data.get("rounds", [])],
            final_concept=ConceptOnePager.from_dict(data["final_concept"]) if data.get("final_concept") else None,
            taxonomy=data.get("taxonomy"),
            go_threshold_met=data.get("go_threshold_met", False),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat()))
        )

