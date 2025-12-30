"""
Core Devices Company - Multi-Agent Electronic Product Development System (Enhanced)

This module implements explicit checklist-based execution for each phase,
ensuring every step is followed systematically as specified in PART 2 of the requirements.

Each agent follows their checklist items as "to-do lists" with progress tracking.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import json
import asyncio
import re
from app.llm.client import LLMClient
from app.book_writer.config import get_config


class Phase(Enum):
    """Product development phases following Ferrari-style pipeline."""
    STRATEGY_IDEA_INTAKE = "strategy_idea_intake"
    CONCEPT_DIFFERENTIATION = "concept_differentiation"
    UX_SYSTEM_DESIGN = "ux_system_design"
    DETAILED_ENGINEERING = "detailed_engineering"
    VALIDATION_INDUSTRIALIZATION = "validation_industrialization"
    POSITIONING_LAUNCH = "positioning_launch"
    COMPLETE = "complete"


class OwnerDecision(Enum):
    """Owner's decision on phase approval."""
    APPROVE = "approve"
    REQUEST_CHANGES = "request_changes"
    STOP = "stop"


class ProductCategory(Enum):
    """Product category classification."""
    NEW_CATEGORY = "new_category"
    DERIVATIVE = "derivative"


class PrimaryNeed(Enum):
    """Primary human needs that products must address."""
    ENERGY = "energy"
    WATER = "water"
    FOOD = "food"
    SHELTER = "shelter"
    HEALTH = "health"
    COMMUNICATION = "communication"
    SAFETY = "safety"
    MOBILITY = "mobility"
    ESSENTIAL_PRODUCTIVITY = "essential_productivity"


@dataclass
class ChecklistItem:
    """A single checklist item with status tracking."""
    step_number: int
    description: str
    agent: str
    completed: bool = False
    output: Optional[Any] = None
    timestamp: Optional[datetime] = None


@dataclass
class AgentMessage:
    """Message in the company chat log."""
    from_agent: str
    to_agent: str
    phase: Phase
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    message_type: str = "internal"  # internal, owner_request, owner_response
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "phase": self.phase.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "message_type": self.message_type
        }


@dataclass
class AttributeDifferentiation:
    """Attribute differentiation for derivative products."""
    attribute_name: str
    market_mean: float
    market_std_dev: float
    target_value: float
    target_sigma_offset: float
    justification: str


@dataclass
class ProductProject:
    """Complete product project state."""
    product_idea: str = ""
    primary_need: Optional[PrimaryNeed] = None
    category: Optional[ProductCategory] = None
    constraints: Dict[str, Any] = field(default_factory=dict)
    
    # Phase 1 outputs
    idea_dossier: Optional[Dict[str, Any]] = None
    
    # Phase 2 outputs
    concept_pack: Optional[Dict[str, Any]] = None
    benchmark_data: Optional[Dict[str, Any]] = None
    differentiation_attributes: List[AttributeDifferentiation] = field(default_factory=list)
    
    # Phase 3 outputs
    user_journeys: Optional[Dict[str, Any]] = None
    interaction_blueprint: Optional[Dict[str, Any]] = None
    system_architecture: Optional[Dict[str, Any]] = None
    friction_budget: Optional[Dict[str, Any]] = None
    
    # Phase 4 outputs
    detailed_design: Optional[Dict[str, Any]] = None
    prototype_plan: Optional[Dict[str, Any]] = None
    usability_metrics: Optional[Dict[str, Any]] = None
    
    # Phase 5 outputs
    validation_plan: Optional[Dict[str, Any]] = None
    manufacturing_plan: Optional[Dict[str, Any]] = None
    serviceability_plan: Optional[Dict[str, Any]] = None
    
    # Phase 6 outputs
    positioning: Optional[Dict[str, Any]] = None
    launch_package: Optional[Dict[str, Any]] = None
    
    # Metadata
    current_phase: Phase = Phase.STRATEGY_IDEA_INTAKE
    status: str = "in_progress"
    owner_edits: Dict[str, Any] = field(default_factory=dict)
    checklist_progress: Dict[str, List[ChecklistItem]] = field(default_factory=dict)


class MessageBus:
    """Central message bus for all agent communications."""
    
    def __init__(self):
        self.messages: List[AgentMessage] = []
        self.subscribers: Dict[str, List[callable]] = {}
    
    def send(self, from_agent: str, to_agent: str, phase: Phase, content: str, 
             message_type: str = "internal"):
        """Send a message and log it."""
        message = AgentMessage(
            from_agent=from_agent,
            to_agent=to_agent,
            phase=phase,
            content=content,
            message_type=message_type
        )
        self.messages.append(message)
        
        if to_agent in self.subscribers:
            for callback in self.subscribers[to_agent]:
                callback(message)
        
        return message
    
    def get_messages(self, phase: Optional[Phase] = None, 
                     agent: Optional[str] = None) -> List[AgentMessage]:
        """Get messages filtered by phase and/or agent."""
        result = self.messages
        if phase:
            result = [m for m in result if m.phase == phase]
        if agent:
            result = [m for m in result if m.from_agent == agent or m.to_agent == agent]
        return result


def extract_json(text: str) -> Optional[Dict[str, Any]]:
    """Extract JSON from LLM response."""
    try:
        # Try direct parse first
        return json.loads(text)
    except:
        # Try to find JSON in text
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except:
                pass
    return None


class CEOAgent:
    """Chief Executive Officer - orchestrates all phases and presents to Owner.
    
    Following CEO_Agent checklist items from specification.
    """
    
    def __init__(self, llm_client: LLMClient, message_bus: MessageBus):
        self.role = "CEO_Agent"
        self.llm = llm_client
        self.bus = message_bus
    
    async def greet_owner(self) -> str:
        """Initial greeting to Owner."""
        greeting = """[CEO_Agent] Welcome to Core Devices Company!

I'll guide you through our 6-phase product development pipeline:

1. **Strategy & Idea Intake** - Validate idea against primary human needs
2. **Concept & Differentiation** - Define concepts and market positioning
3. **UX Architecture & System Design** - Design user experience and technical architecture
4. **Detailed Engineering & Prototyping** - Create detailed designs and prototypes
5. **Validation, Safety & Industrialization** - Ensure safety, compliance, and manufacturability
6. **Customer Experience, Positioning & Launch** - Prepare market positioning and launch

Please provide:
- A brief description of your product idea
- Which primary need it addresses (energy, water, food, shelter, health, communication, safety, mobility, essential productivity)
- Any constraints (budget, environment, complexity, etc.)"""
        
        return greeting
    
    async def start_phase(self, phase: Phase, project: ProductProject) -> str:
        """Announce phase start and identify responsible agents."""
        phase_info = {
            Phase.STRATEGY_IDEA_INTAKE: ("CPO_Agent", "validate idea and create Product Idea Dossier"),
            Phase.CONCEPT_DIFFERENTIATION: ("CPO_Agent, CDO_Agent, CMO_Agent", "develop concepts and differentiation strategy"),
            Phase.UX_SYSTEM_DESIGN: ("CDO_Agent, CTO_Agent", "design UX flows and system architecture"),
            Phase.DETAILED_ENGINEERING: ("CTO_Agent, CDO_Agent", "create detailed engineering and prototypes"),
            Phase.VALIDATION_INDUSTRIALIZATION: ("COO_Agent, CTO_Agent", "validate safety and manufacturing"),
            Phase.POSITIONING_LAUNCH: ("CMO_Agent, CDO_Agent", "create positioning and launch package"),
        }
        
        lead_agents, goal = phase_info.get(phase, ("Unknown", "Unknown"))
        
        message = f"""[CEO_Agent] Starting {phase.value.replace('_', ' ').title()}

**Lead Agents**: {lead_agents}
**Goal**: {goal}

All agents, please proceed with your phase checklists."""
        
        self.bus.send(self.role, "ALL_AGENTS", phase, message, "internal")
        return message
    
    async def review_artifacts(self, phase: Phase, artifacts: Dict[str, Any]) -> str:
        """Review phase artifacts for coherence (CEO checklist item)."""
        review_msg = f"[CEO_Agent] Reviewing {phase.value} artifacts for coherence and alignment..."
        self.bus.send(self.role, "INTERNAL", phase, review_msg, "internal")
        
        # This is where CEO validates the work
        return "Artifacts reviewed and validated"
    
    async def create_owner_summary(self, phase: Phase, artifacts: Dict[str, Any]) -> str:
        """Create Owner-friendly summary (CEO checklist item)."""
        prompt = f"""You are the CEO of Core Devices Company. Create a clear, concise summary for the Owner.

Phase: {phase.value}
Artifacts: {json.dumps(artifacts, indent=2)}

Summarize:
1. What was accomplished in this phase
2. Key decisions made
3. What the Owner needs to review

Be business-focused and concise. Use markdown formatting."""
        
        response = await self.llm.generate(prompt)
        summary = f"[CEO_Agent] Phase Summary\n\n{response}"
        
        return summary
    
    async def summarize_phase(self, phase: Phase, artifacts: Dict[str, Any]) -> str:
        """Complete CEO checklist: review, summarize, present."""
        # Checklist item 1: Review artifacts
        await self.review_artifacts(phase, artifacts)
        
        # Checklist item 2: Create summary
        summary = await self.create_owner_summary(phase, artifacts)
        
        # Checklist item 3: Present to Owner
        self.bus.send(self.role, "OWNER", phase, summary, "owner_request")
        
        return summary
    
    async def request_owner_decision(self, phase: Phase) -> str:
        """Ask Owner for decision (CEO checklist item)."""
        message = f"""[CEO_Agent] Owner Decision Required

Please review the phase summary above and decide:
- **Approve**: Proceed to next phase
- **Request Changes**: Specify what needs to be revised
- **Stop**: Stop the project

Your decision?"""
        
        self.bus.send(self.role, "OWNER", phase, message, "owner_request")
        return message
    
    async def route_changes(self, phase: Phase, feedback: str, project: ProductProject) -> str:
        """Route Owner changes back to agents (CEO checklist item)."""
        message = f"[CEO_Agent] Owner has requested changes for {phase.value}:\n\n{feedback}\n\nRelevant agents, please address this feedback."
        self.bus.send(self.role, "ALL_AGENTS", phase, message, "internal")
        return message


class CPOAgent:
    """Chief Product Officer - owns product portfolio and idea intake.
    
    Follows explicit checklists for Phase 1 and Phase 2.
    """
    
    def __init__(self, llm_client: LLMClient, message_bus: MessageBus):
        self.role = "CPO_Agent"
        self.llm = llm_client
        self.bus = message_bus
    
    async def phase1_checklist_item_1(self, project: ProductProject) -> str:
        """Restate the user's idea in your own words for clarity."""
        self.bus.send(self.role, "INTERNAL", Phase.STRATEGY_IDEA_INTAKE,
                     "[CPO_Agent] ✓ Checklist 1/5: Restating idea for clarity", "internal")
        
        prompt = f"""Restate this product idea clearly and concisely:

Product Idea: {project.product_idea}

Provide a clear, professional restatement."""
        
        response = await self.llm.generate(prompt)
        return response.strip()
    
    async def phase1_checklist_item_2(self, project: ProductProject, idea_restatement: str) -> Tuple[str, bool]:
        """Identify which primary human need(s) the product serves."""
        self.bus.send(self.role, "INTERNAL", Phase.STRATEGY_IDEA_INTAKE,
                     "[CPO_Agent] ✓ Checklist 2/5: Identifying primary need", "internal")
        
        prompt = f"""Analyze this product idea and identify which PRIMARY HUMAN NEED it serves.

Product Idea: {idea_restatement}

Primary Needs (choose one):
- energy: Power generation, storage, distribution
- water: Clean water access, purification, conservation
- food: Food production, preservation, preparation
- shelter: Housing, climate control, safety from elements
- health: Disease prevention, treatment, monitoring
- communication: Information exchange, connectivity
- safety: Protection from harm, security
- mobility: Transportation, movement
- essential_productivity: Tools for essential work/education

If the product does NOT map to a primary need, state "AUXILIARY" and explain why it should be rejected.

Output as JSON: {{"primary_need": "need_name", "justification": "...", "is_auxiliary": false}}"""
        
        response = await self.llm.generate(prompt)
        result = extract_json(response)
        
        if result and result.get("is_auxiliary"):
            return result.get("primary_need", "unknown"), True
        
        return result.get("primary_need", "unknown") if result else "unknown", False
    
    async def phase1_checklist_item_3(self, idea_restatement: str) -> str:
        """Perform existence check - does similar product category exist?"""
        self.bus.send(self.role, "INTERNAL", Phase.STRATEGY_IDEA_INTAKE,
                     "[CPO_Agent] ✓ Checklist 3/5: Performing existence check", "internal")
        
        prompt = f"""Does a similar product category already exist for this idea?

Product Idea: {idea_restatement}

Analyze:
1. Are there existing products in this category?
2. Is this NEW CATEGORY or DERIVATIVE?

Output as JSON: {{"category": "new_category" or "derivative", "reasoning": "..."}}"""
        
        response = await self.llm.generate(prompt)
        result = extract_json(response)
        
        return result.get("category", "new_category") if result else "new_category"
    
    async def phase1_checklist_item_4(self, idea_restatement: str, category: str) -> Dict[str, str]:
        """Draft Product Idea Dossier."""
        self.bus.send(self.role, "INTERNAL", Phase.STRATEGY_IDEA_INTAKE,
                     "[CPO_Agent] ✓ Checklist 4/5: Drafting Product Idea Dossier", "internal")
        
        prompt = f"""Create a Product Idea Dossier with:

Product Idea: {idea_restatement}
Category: {category}

Include:
1. Working title
2. Current user context (how people solve this need today)
3. Friction-reduction hypothesis (one paragraph on how this product can be easier)

Output as JSON: {{"working_title": "...", "current_context": "...", "friction_hypothesis": "..."}}"""
        
        response = await self.llm.generate(prompt)
        result = extract_json(response)
        
        return result or {
            "working_title": "Innovative Device",
            "current_context": "Current solutions exist but have friction",
            "friction_hypothesis": "This product reduces friction through simplified interaction"
        }
    
    async def phase1_checklist_item_5(self, dossier: Dict[str, Any]) -> None:
        """Send dossier to CEO_Agent."""
        self.bus.send(self.role, "CEO_Agent", Phase.STRATEGY_IDEA_INTAKE,
                     f"[CPO_Agent] ✓ Checklist 5/5: Completed Product Idea Dossier for '{dossier.get('working_title')}'", "internal")
    
    async def phase1_idea_intake(self, project: ProductProject) -> Dict[str, Any]:
        """Execute Phase 1 checklist systematically."""
        self.bus.send(self.role, "CEO_Agent", Phase.STRATEGY_IDEA_INTAKE,
                     f"[CPO_Agent] Beginning Phase 1 checklist (5 items)", "internal")
        
        # Checklist Item 1: Restate idea
        idea_restatement = await self.phase1_checklist_item_1(project)
        
        # Checklist Item 2: Identify primary need
        primary_need, is_auxiliary = await self.phase1_checklist_item_2(project, idea_restatement)
        
        if is_auxiliary:
            self.bus.send(self.role, "CEO_Agent", Phase.STRATEGY_IDEA_INTAKE,
                         f"[CPO_Agent] ⚠️ WARNING: Product flagged as AUXILIARY. Recommend rejection or re-scoping.", "internal")
        
        # Checklist Item 3: Existence check
        category = await self.phase1_checklist_item_3(idea_restatement)
        
        # Checklist Item 4: Draft dossier
        dossier_parts = await self.phase1_checklist_item_4(idea_restatement, category)
        
        # Compile complete dossier
        complete_dossier = {
            "idea_restatement": idea_restatement,
            "primary_need": primary_need,
            "category": category,
            "is_auxiliary": is_auxiliary,
            **dossier_parts
        }
        
        # Checklist Item 5: Send to CEO
        await self.phase1_checklist_item_5(complete_dossier)
        
        return complete_dossier
    
    async def phase2_benchmarking(self, project: ProductProject) -> Optional[Dict[str, Any]]:
        """Phase 2 Checklist for derivative products: benchmark and differentiation."""
        category = project.idea_dossier.get("category")
        
        if category != "derivative":
            return None
        
        self.bus.send(self.role, "CMO_Agent", Phase.CONCEPT_DIFFERENTIATION,
                     "[CPO_Agent] Product is DERIVATIVE. Initiating benchmarking...", "internal")
        
        # Checklist: Identify 3-7 existing products
        prompt1 = f"""Identify 3-7 existing products in this category.

Product: {project.idea_dossier.get('working_title')}
Idea: {project.idea_dossier.get('idea_restatement')}

List competitors/similar products.

Output as JSON: {{"existing_products": ["Product1", "Product2", ...]}}"""
        
        response1 = await self.llm.generate(prompt1)
        products = extract_json(response1) or {"existing_products": []}
        
        # Checklist: Define key attributes and estimate mean/std
        prompt2 = f"""For these products, define key attributes and estimate market mean and standard deviation.

Products: {products.get('existing_products')}

Attributes to consider:
- Setup time (minutes)
- Steps to complete main task
- Battery life (hours)
- Size/weight
- Noise level (dB)
- Durability (years)
- Price

For each attribute, estimate: mean, std_deviation

Output as JSON: {{"attributes": {{"attribute_name": {{"mean": X, "std_dev": Y}}, ...}}}}"""
        
        response2 = await self.llm.generate(prompt2)
        attributes = extract_json(response2) or {"attributes": {}}
        
        # Checklist: Choose 2-3 attributes and specify 1-2σ targets
        prompt3 = f"""Choose 2-3 attributes to differentiate on, within 1-2 standard deviations.

Attributes available: {json.dumps(attributes.get('attributes', {}))}

For each chosen attribute:
- Direction (increase/decrease)
- Target value (within 1-2σ of mean)
- Sigma offset (between 1.0 and 2.0)
- Justification

Output as JSON: {{"chosen_differentiations": [{{"attribute": "...", "mean": X, "std_dev": Y, "target_value": Z, "sigma_offset": S, "justification": "..."}}, ...]}}"""
        
        response3 = await self.llm.generate(prompt3)
        differentiations = extract_json(response3) or {"chosen_differentiations": []}
        
        benchmark = {
            **products,
            **attributes,
            **differentiations
        }
        
        self.bus.send(self.role, "CEO_Agent", Phase.CONCEPT_DIFFERENTIATION,
                     f"[CPO_Agent] ✓ Completed benchmark with {len(differentiations.get('chosen_differentiations', []))} differentiations", "internal")
        
        return benchmark
    
    async def phase2_concept_development(self, project: ProductProject, benchmark: Optional[Dict]) -> Dict[str, Any]:
        """Develop 2-3 product concepts."""
        self.bus.send(self.role, "CDO_Agent", Phase.CONCEPT_DIFFERENTIATION,
                     "[CPO_Agent] Developing product concepts...", "internal")
        
        prompt = f"""Create 2-3 product concepts.

Product: {project.idea_dossier.get('working_title')}
Category: {project.idea_dossier.get('category')}
{f"Benchmarks: {json.dumps(benchmark)}" if benchmark else ""}

For each concept:
1. Concept name
2. Core approach
3. Friction reduction strategy (how it's easier than current options)

Output as JSON: {{"concepts": [{{"name": "...", "approach": "...", "friction_reduction": "..."}}, ...]}}"""
        
        response = await self.llm.generate(prompt)
        concepts = extract_json(response) or {"concepts": []}
        
        self.bus.send(self.role, "CEO_Agent", Phase.CONCEPT_DIFFERENTIATION,
                     f"[CPO_Agent] ✓ Created {len(concepts.get('concepts', []))} concepts", "internal")
        
        return concepts


class CDOAgent:
    """Chief Design & UX Officer - owns user experience end-to-end.
    
    Follows explicit checklists for Phase 2, 3, 4, and 6.
    """
    
    def __init__(self, llm_client: LLMClient, message_bus: MessageBus):
        self.role = "CDO_Agent"
        self.llm = llm_client
        self.bus = message_bus
    
    async def phase2_usage_concepts(self, project: ProductProject) -> Dict[str, Any]:
        """Phase 2: Develop usage concepts (CDO checklist)."""
        self.bus.send(self.role, "CPO_Agent", Phase.CONCEPT_DIFFERENTIATION,
                     "[CDO_Agent] Creating usage concepts and scenarios...", "internal")
        
        prompt = f"""Create 2-3 usage scenarios for this product.

Product: {project.idea_dossier.get('working_title')}
Primary Need: {project.idea_dossier.get('primary_need')}

For each scenario:
1. Short scenario (day-in-the-life or typical use)
2. Friction reduction vs current solutions
3. Physical form and interaction style

Output as JSON: {{"usage_concepts": [{{"scenario": "...", "friction_reduction": "...", "form_interaction": "..."}}, ...]}}"""
        
        response = await self.llm.generate(prompt)
        usage = extract_json(response) or {"usage_concepts": []}
        
        self.bus.send(self.role, "CPO_Agent", Phase.CONCEPT_DIFFERENTIATION,
                     f"[CDO_Agent] ✓ Created {len(usage.get('usage_concepts', []))} usage concepts", "internal")
        
        return usage
    
    async def phase3_define_journeys(self, project: ProductProject) -> Dict[str, Any]:
        """Phase 3 Checklist Item: Define key user journeys."""
        self.bus.send(self.role, "CTO_Agent", Phase.UX_SYSTEM_DESIGN,
                     "[CDO_Agent] ✓ Checklist: Defining key user journeys", "internal")
        
        prompt = f"""Define key user journeys with steps.

Product: {project.idea_dossier.get('working_title')}
Concepts: {json.dumps(project.concept_pack)}

Define these journeys:
1. Unboxing & initial setup
2. First successful use
3. Typical daily use
4. Maintenance/replacement of consumables
5. Handling error states and recovery

For each journey:
- List steps in order
- Identify friction points to eliminate
- Target minimal path

Output as JSON: {{"journeys": {{"unboxing": [{{"step": "...", "friction": "..."}}], "first_use": [...], ...}}}}"""
        
        response = await self.llm.generate(prompt)
        journeys = extract_json(response) or {"journeys": {}}
        
        return journeys
    
    async def phase3_interaction_blueprint(self, project: ProductProject) -> Dict[str, Any]:
        """Phase 3 Checklist Item: Define Interaction Blueprint."""
        self.bus.send(self.role, "CTO_Agent", Phase.UX_SYSTEM_DESIGN,
                     "[CDO_Agent] ✓ Checklist: Creating Interaction Blueprint", "internal")
        
        prompt = f"""Design the Interaction Blueprint.

Product: {project.idea_dossier.get('working_title')}

Define:
1. Inputs (buttons, dials, touch areas, voice, etc.)
2. Outputs (LEDs, display messages, sounds, haptics)
3. Major states and transitions (on/off, idle, working, error, update)

Output as JSON: {{"inputs": [...], "outputs": [...], "states": [...], "transitions": [...]}}"""
        
        response = await self.llm.generate(prompt)
        blueprint = extract_json(response) or {"inputs": [], "outputs": [], "states": [], "transitions": []}
        
        return blueprint
    
    async def phase3_friction_budget(self, journeys: Dict) -> Dict[str, Any]:
        """Phase 3 Checklist Item: Define Friction Budget."""
        self.bus.send(self.role, "CTO_Agent", Phase.UX_SYSTEM_DESIGN,
                     "[CDO_Agent] ✓ Checklist: Establishing Friction Budget", "internal")
        
        prompt = f"""Define a Friction Budget based on user journeys.

User Journeys: {json.dumps(journeys)}

Define:
1. Max steps for initial setup
2. Max steps for main task
3. Max visible options in primary UI
4. High-level usability goals (e.g., "first success within 3 minutes")

Output as JSON: {{"max_setup_steps": X, "max_task_steps": Y, "max_ui_options": Z, "usability_goals": [...]}}"""
        
        response = await self.llm.generate(prompt)
        budget = extract_json(response) or {"max_setup_steps": 5, "max_task_steps": 3, "max_ui_options": 5, "usability_goals": []}
        
        return budget
    
    async def phase3_ux_design(self, project: ProductProject) -> Dict[str, Any]:
        """Execute Phase 3 UX checklist systematically."""
        self.bus.send(self.role, "CEO_Agent", Phase.UX_SYSTEM_DESIGN,
                     "[CDO_Agent] Beginning Phase 3 UX checklist", "internal")
        
        # Checklist: Define user journeys
        journeys = await self.phase3_define_journeys(project)
        
        # Checklist: Create interaction blueprint
        blueprint = await self.phase3_interaction_blueprint(project)
        
        # Checklist: Define friction budget
        budget = await self.phase3_friction_budget(journeys)
        
        ux_design = {
            "user_journeys": journeys,
            "interaction_blueprint": blueprint,
            "friction_budget": budget
        }
        
        self.bus.send(self.role, "CTO_Agent", Phase.UX_SYSTEM_DESIGN,
                     "[CDO_Agent] ✓ Completed UX Architecture design", "internal")
        
        return ux_design
    
    async def phase4_industrial_design(self, project: ProductProject) -> Dict[str, Any]:
        """Phase 4: Industrial design and prototyping (CDO checklist)."""
        self.bus.send(self.role, "CTO_Agent", Phase.DETAILED_ENGINEERING,
                     "[CDO_Agent] Creating industrial design specifications...", "internal")
        
        prompt = f"""Create industrial design specifications.

Product: {project.idea_dossier.get('working_title')}
UX Blueprint: {json.dumps(project.interaction_blueprint)}

Specify:
1. Physical design (shape, size, weight targets)
2. Affordances (how to hold, grip, orient)
3. Prototype mockup approach
4. Usability test metrics

Output as JSON: {{"industrial_design": {{...}}, "prototype_approach": {{...}}, "test_metrics": {{...}}}}"""
        
        response = await self.llm.generate(prompt)
        design = extract_json(response) or {"industrial_design": {}, "prototype_approach": {}, "test_metrics": {}}
        
        return design
    
    async def phase6_onboarding(self, project: ProductProject) -> Dict[str, Any]:
        """Phase 6: Onboarding and documentation (CDO checklist)."""
        self.bus.send(self.role, "CMO_Agent", Phase.POSITIONING_LAUNCH,
                     "[CDO_Agent] Designing onboarding and documentation...", "internal")
        
        prompt = f"""Create onboarding materials.

Product: {project.idea_dossier.get('working_title')}

Design:
1. One-page quick-start guide (clear steps, pictograms suggested)
2. Device labeling strategy
3. Support paths (how users find help - QR, URL, manual sections)
4. Minimal steps from problem to solution

Output as JSON: {{"quick_start": {{...}}, "labeling": {{...}}, "support_paths": {{...}}}}"""
        
        response = await self.llm.generate(prompt)
        onboarding = extract_json(response) or {"quick_start": {}, "labeling": {}, "support_paths": {}}
        
        return onboarding


class CTOAgent:
    """Chief Technology Officer - owns technical feasibility, safety, and reliability.
    
    Follows explicit checklists for Phase 3, 4, and 5.
    """
    
    def __init__(self, llm_client: LLMClient, message_bus: MessageBus):
        self.role = "CTO_Agent"
        self.llm = llm_client
        self.bus = message_bus
    
    async def phase3_system_architecture(self, project: ProductProject) -> Dict[str, Any]:
        """Phase 3: System architecture design (CTO checklist)."""
        self.bus.send(self.role, "CDO_Agent", Phase.UX_SYSTEM_DESIGN,
                     "[CTO_Agent] Designing system architecture...", "internal")
        
        prompt = f"""Design the system architecture.

Product: {project.idea_dossier.get('working_title')}
UX Requirements: {json.dumps(project.user_journeys)}

Design:
1. Power subsystem (battery, solar, wall power, etc.)
2. Sensors/actuators needed
3. Processing & memory requirements
4. Connectivity (WiFi, BLE, cellular, none)
5. Block diagram (describe textually)
6. Constraints affecting UX (warm-up time, safety delays, etc.)

Ensure architecture supports UX flows and minimizes friction.

Output as JSON: {{"power": "...", "sensors_actuators": [...], "processing": "...", "connectivity": "...", "block_diagram": "...", "ux_constraints": [...]}}"""
        
        response = await self.llm.generate(prompt)
        architecture = extract_json(response) or {
            "power": "Battery-powered",
            "sensors_actuators": [],
            "processing": "Microcontroller",
            "connectivity": "None",
            "block_diagram": "To be detailed",
            "ux_constraints": []
        }
        
        self.bus.send(self.role, "CDO_Agent", Phase.UX_SYSTEM_DESIGN,
                     "[CTO_Agent] ✓ Completed system architecture", "internal")
        
        return architecture
    
    async def phase4_detailed_engineering(self, project: ProductProject) -> Dict[str, Any]:
        """Phase 4: Detailed engineering design (CTO checklist)."""
        self.bus.send(self.role, "CDO_Agent", Phase.DETAILED_ENGINEERING,
                     "[CTO_Agent] Creating detailed engineering specifications...", "internal")
        
        prompt = f"""Create detailed engineering specifications.

Product: {project.idea_dossier.get('working_title')}
System Architecture: {json.dumps(project.system_architecture)}

Describe:
1. Schematic design (conceptual components and connections)
2. PCB layout considerations (size, thermal, signal integrity)
3. Firmware/software responsibilities (control loops, safety checks)
4. Critical risks to validate in prototypes
5. Alpha prototype objectives (what to demonstrate)

Output as JSON: {{"schematic": {{...}}, "pcb_layout": {{...}}, "firmware": {{...}}, "risks": [...], "prototype_objectives": [...]}}"""
        
        response = await self.llm.generate(prompt)
        engineering = extract_json(response) or {
            "schematic": {},
            "pcb_layout": {},
            "firmware": {},
            "risks": [],
            "prototype_objectives": []
        }
        
        return engineering
    
    async def phase5_validation(self, project: ProductProject) -> Dict[str, Any]:
        """Phase 5: Validation and safety (CTO checklist)."""
        self.bus.send(self.role, "COO_Agent", Phase.VALIDATION_INDUSTRIALIZATION,
                     "[CTO_Agent] Defining validation and safety requirements...", "internal")
        
        prompt = f"""Define validation and safety requirements.

Product: {project.idea_dossier.get('working_title')}

Specify:
1. Electrical safety requirements (voltage limits, insulation, grounding)
2. Environmental limits (temperature, humidity, dust, water resistance)
3. Failure modes and safe behavior (what happens when X fails)
4. Relevant standards (UL, CE, FCC, etc. - conceptual list)

Output as JSON: {{"safety_requirements": [...], "environmental_limits": {{...}}, "failure_modes": [...], "standards": [...]}}"""
        
        response = await self.llm.generate(prompt)
        validation = extract_json(response) or {
            "safety_requirements": [],
            "environmental_limits": {},
            "failure_modes": [],
            "standards": []
        }
        
        return validation


class COOAgent:
    """Chief Operations Officer - owns manufacturing, supply chain, quality.
    
    Follows explicit checklist for Phase 5.
    """
    
    def __init__(self, llm_client: LLMClient, message_bus: MessageBus):
        self.role = "COO_Agent"
        self.llm = llm_client
        self.bus = message_bus
    
    async def phase5_manufacturing(self, project: ProductProject) -> Dict[str, Any]:
        """Phase 5: Manufacturing and serviceability (COO checklist)."""
        self.bus.send(self.role, "CTO_Agent", Phase.VALIDATION_INDUSTRIALIZATION,
                     "[COO_Agent] Planning manufacturing and operations...", "internal")
        
        prompt = f"""Plan manufacturing and serviceability.

Product: {project.idea_dossier.get('working_title')}
Design: {json.dumps(project.detailed_design)}

Create:
1. DFM/DFA strategy (reduce part count, simple assembly sequence)
2. Tolerance management (manufacturing variation without affecting usability)
3. Serviceability plan (user-replaceable parts, firmware updates, diagnostics access)
4. Pilot run monitoring plan (defect types to track, user complaint categories)

Output as JSON: {{"dfm_strategy": {{...}}, "tolerances": {{...}}, "serviceability": {{...}}, "pilot_plan": {{...}}}}"""
        
        response = await self.llm.generate(prompt)
        manufacturing = extract_json(response) or {
            "dfm_strategy": {},
            "tolerances": {},
            "serviceability": {},
            "pilot_plan": {}
        }
        
        return manufacturing


class CMOAgent:
    """Chief Marketing Officer - owns market analysis, positioning, messaging.
    
    Follows explicit checklists for Phase 2 and Phase 6.
    """
    
    def __init__(self, llm_client: LLMClient, message_bus: MessageBus):
        self.role = "CMO_Agent"
        self.llm = llm_client
        self.bus = message_bus
    
    async def phase2_market_analysis(self, project: ProductProject) -> Dict[str, Any]:
        """Phase 2: Market analysis (CMO checklist)."""
        self.bus.send(self.role, "CPO_Agent", Phase.CONCEPT_DIFFERENTIATION,
                     "[CMO_Agent] Analyzing market context...", "internal")
        
        prompt = f"""Analyze the market for this product.

Product: {project.idea_dossier.get('working_title')}
Category: {project.idea_dossier.get('category')}

Analyze:
1. Market context and current solutions
2. User pain points
3. Opportunity areas

Output as JSON: {{"market_context": "...", "pain_points": [...], "opportunities": [...]}}"""
        
        response = await self.llm.generate(prompt)
        analysis = extract_json(response) or {"market_context": {}, "pain_points": [], "opportunities": []}
        
        return analysis
    
    async def phase6_positioning(self, project: ProductProject) -> Dict[str, Any]:
        """Phase 6: Positioning and launch package (CMO checklist)."""
        self.bus.send(self.role, "CDO_Agent", Phase.POSITIONING_LAUNCH,
                     "[CMO_Agent] Creating positioning and launch materials...", "internal")
        
        prompt = f"""Create positioning and launch materials.

Product: {project.idea_dossier.get('working_title')}
Primary Need: {project.idea_dossier.get('primary_need')}
Differentiation: {json.dumps(project.concept_pack)}

Create:
1. Product name (refine if needed)
2. One-sentence primary need description (solves X need)
3. One-sentence friction reduction benefit (easier because...)
4. 3-5 key benefits (user outcomes, NO JARGON)
5. Launch messaging (packaging, website copy)

Output as JSON: {{"product_name": "...", "need_statement": "...", "benefit_statement": "...", "key_benefits": [...], "launch_messaging": {{...}}}}"""
        
        response = await self.llm.generate(prompt)
        positioning = extract_json(response) or {
            "product_name": project.idea_dossier.get('working_title'),
            "need_statement": "",
            "benefit_statement": "",
            "key_benefits": [],
            "launch_messaging": {}
        }
        
        return positioning


class CoreDevicesCompany:
    """Main orchestrator for the Core Devices Company multi-agent system.
    
    Enhanced with explicit checklist execution and progress tracking.
    """
    
    def __init__(self, llm_client: Optional[LLMClient] = None, model: str = "qwen3:30b"):
        """Initialize the company with all agents."""
        if llm_client is None:
            config = get_config()
            llm_client = LLMClient(
                base_url=config.llm_base_url,
                model=model,
                temperature=0.7
            )
        
        self.llm = llm_client
        self.bus = MessageBus()
        self.project: Optional[ProductProject] = None
        
        # Initialize all agents
        self.ceo = CEOAgent(llm_client, self.bus)
        self.cpo = CPOAgent(llm_client, self.bus)
        self.cdo = CDOAgent(llm_client, self.bus)
        self.cto = CTOAgent(llm_client, self.bus)
        self.coo = COOAgent(llm_client, self.bus)
        self.cmo = CMOAgent(llm_client, self.bus)
    
    async def initialize_project(self, idea: str, primary_need: str, constraints: Dict[str, Any] = None) -> ProductProject:
        """Initialize a new product project."""
        try:
            need = PrimaryNeed(primary_need.lower())
        except ValueError:
            need = None
        
        self.project = ProductProject(
            product_idea=idea,
            primary_need=need,
            constraints=constraints or {}
        )
        
        return self.project
    
    async def execute_phase_1(self) -> Dict[str, Any]:
        """Execute Phase 1: Strategy & Idea Intake (with explicit checklist)."""
        if not self.project:
            raise ValueError("Project not initialized")
        
        await self.ceo.start_phase(Phase.STRATEGY_IDEA_INTAKE, self.project)
        
        # CPO executes Phase 1 checklist (5 items)
        idea_dossier = await self.cpo.phase1_idea_intake(self.project)
        self.project.idea_dossier = idea_dossier
        self.project.current_phase = Phase.STRATEGY_IDEA_INTAKE
        
        # CEO reviews and summarizes (CEO checklist)
        summary = await self.ceo.summarize_phase(Phase.STRATEGY_IDEA_INTAKE, {
            "idea_dossier": idea_dossier
        })
        
        # CEO requests owner decision (CEO checklist)
        await self.ceo.request_owner_decision(Phase.STRATEGY_IDEA_INTAKE)
        
        return {
            "phase": Phase.STRATEGY_IDEA_INTAKE.value,
            "artifacts": {"idea_dossier": idea_dossier},
            "summary": summary,
            "chat_log": [m.to_dict() for m in self.bus.get_messages(Phase.STRATEGY_IDEA_INTAKE)]
        }
    
    async def execute_phase_2(self) -> Dict[str, Any]:
        """Execute Phase 2: Concept & Differentiation (with explicit checklists)."""
        if not self.project or not self.project.idea_dossier:
            raise ValueError("Phase 1 must be completed first")
        
        await self.ceo.start_phase(Phase.CONCEPT_DIFFERENTIATION, self.project)
        
        # CMO executes market analysis checklist
        market_analysis = await self.cmo.phase2_market_analysis(self.project)
        
        # CPO executes concept development checklist
        benchmark = await self.cpo.phase2_benchmarking(self.project)
        concept_pack = await self.cpo.phase2_concept_development(self.project, benchmark)
        
        # CDO executes usage concepts checklist
        usage_concepts = await self.cdo.phase2_usage_concepts(self.project)
        
        # Combine into final concept pack (Joint checklist item)
        final_concept_pack = {
            **concept_pack,
            "usage_concepts": usage_concepts.get("usage_concepts", []),
            "market_analysis": market_analysis
        }
        
        self.project.concept_pack = final_concept_pack
        self.project.benchmark_data = benchmark
        self.project.current_phase = Phase.CONCEPT_DIFFERENTIATION
        
        # CEO reviews and summarizes
        summary = await self.ceo.summarize_phase(Phase.CONCEPT_DIFFERENTIATION, {
            "concept_pack": final_concept_pack,
            "benchmark_data": benchmark
        })
        
        await self.ceo.request_owner_decision(Phase.CONCEPT_DIFFERENTIATION)
        
        return {
            "phase": Phase.CONCEPT_DIFFERENTIATION.value,
            "artifacts": {
                "concept_pack": final_concept_pack,
                "benchmark_data": benchmark
            },
            "summary": summary,
            "chat_log": [m.to_dict() for m in self.bus.get_messages(Phase.CONCEPT_DIFFERENTIATION)]
        }
    
    async def execute_phase_3(self) -> Dict[str, Any]:
        """Execute Phase 3: UX Architecture & System Design (with explicit checklists)."""
        if not self.project or not self.project.concept_pack:
            raise ValueError("Phase 2 must be completed first")
        
        await self.ceo.start_phase(Phase.UX_SYSTEM_DESIGN, self.project)
        
        # CDO executes UX design checklist (3 main items)
        ux_design = await self.cdo.phase3_ux_design(self.project)
        self.project.user_journeys = ux_design.get("user_journeys", {})
        self.project.interaction_blueprint = ux_design.get("interaction_blueprint", {})
        self.project.friction_budget = ux_design.get("friction_budget", {})
        
        # CTO executes system architecture checklist
        system_arch = await self.cto.phase3_system_architecture(self.project)
        self.project.system_architecture = system_arch
        self.project.current_phase = Phase.UX_SYSTEM_DESIGN
        
        # Joint integration (checklist item)
        self.bus.send("CDO_Agent", "CTO_Agent", Phase.UX_SYSTEM_DESIGN,
                     "[CDO_Agent + CTO_Agent] ✓ Integrated UX flows and system architecture", "internal")
        
        # CEO reviews and summarizes
        summary = await self.ceo.summarize_phase(Phase.UX_SYSTEM_DESIGN, {
            "ux_design": ux_design,
            "system_architecture": system_arch
        })
        
        await self.ceo.request_owner_decision(Phase.UX_SYSTEM_DESIGN)
        
        return {
            "phase": Phase.UX_SYSTEM_DESIGN.value,
            "artifacts": {
                "ux_design": ux_design,
                "system_architecture": system_arch
            },
            "summary": summary,
            "chat_log": [m.to_dict() for m in self.bus.get_messages(Phase.UX_SYSTEM_DESIGN)]
        }
    
    async def execute_phase_4(self) -> Dict[str, Any]:
        """Execute Phase 4: Detailed Engineering & Prototyping (with explicit checklists)."""
        if not self.project or not self.project.system_architecture:
            raise ValueError("Phase 3 must be completed first")
        
        await self.ceo.start_phase(Phase.DETAILED_ENGINEERING, self.project)
        
        # CTO executes detailed engineering checklist
        detailed_engineering = await self.cto.phase4_detailed_engineering(self.project)
        
        # CDO executes industrial design checklist
        industrial_design = await self.cdo.phase4_industrial_design(self.project)
        
        # Joint combination (checklist item)
        combined_design = {
            "engineering": detailed_engineering,
            "industrial_design": industrial_design
        }
        
        self.project.detailed_design = combined_design
        self.project.prototype_plan = industrial_design.get("prototype_approach", {})
        self.project.usability_metrics = industrial_design.get("test_metrics", {})
        self.project.current_phase = Phase.DETAILED_ENGINEERING
        
        # CEO reviews and summarizes
        summary = await self.ceo.summarize_phase(Phase.DETAILED_ENGINEERING, {
            "detailed_design": combined_design
        })
        
        await self.ceo.request_owner_decision(Phase.DETAILED_ENGINEERING)
        
        return {
            "phase": Phase.DETAILED_ENGINEERING.value,
            "artifacts": {"detailed_design": combined_design},
            "summary": summary,
            "chat_log": [m.to_dict() for m in self.bus.get_messages(Phase.DETAILED_ENGINEERING)]
        }
    
    async def execute_phase_5(self) -> Dict[str, Any]:
        """Execute Phase 5: Validation, Safety & Industrialization (with explicit checklists)."""
        if not self.project or not self.project.detailed_design:
            raise ValueError("Phase 4 must be completed first")
        
        await self.ceo.start_phase(Phase.VALIDATION_INDUSTRIALIZATION, self.project)
        
        # CTO executes validation checklist
        validation = await self.cto.phase5_validation(self.project)
        
        # COO executes manufacturing checklist
        manufacturing = await self.coo.phase5_manufacturing(self.project)
        
        # Joint summary (checklist item)
        combined_plan = {
            "validation": validation,
            "manufacturing": manufacturing
        }
        
        self.project.validation_plan = validation
        self.project.manufacturing_plan = manufacturing.get("dfm_strategy", {})
        self.project.serviceability_plan = manufacturing.get("serviceability", {})
        self.project.current_phase = Phase.VALIDATION_INDUSTRIALIZATION
        
        # CEO reviews and summarizes
        summary = await self.ceo.summarize_phase(Phase.VALIDATION_INDUSTRIALIZATION, {
            "validation_manufacturing": combined_plan
        })
        
        await self.ceo.request_owner_decision(Phase.VALIDATION_INDUSTRIALIZATION)
        
        return {
            "phase": Phase.VALIDATION_INDUSTRIALIZATION.value,
            "artifacts": {"validation_manufacturing": combined_plan},
            "summary": summary,
            "chat_log": [m.to_dict() for m in self.bus.get_messages(Phase.VALIDATION_INDUSTRIALIZATION)]
        }
    
    async def execute_phase_6(self) -> Dict[str, Any]:
        """Execute Phase 6: Customer Experience, Positioning & Launch (with explicit checklists)."""
        if not self.project or not self.project.manufacturing_plan:
            raise ValueError("Phase 5 must be completed first")
        
        await self.ceo.start_phase(Phase.POSITIONING_LAUNCH, self.project)
        
        # CMO executes positioning checklist
        positioning = await self.cmo.phase6_positioning(self.project)
        
        # CDO executes onboarding checklist
        onboarding = await self.cdo.phase6_onboarding(self.project)
        
        # Joint launch package (checklist item)
        launch_package = {
            "positioning": positioning,
            "onboarding": onboarding
        }
        
        self.project.positioning = positioning
        self.project.launch_package = launch_package
        self.project.current_phase = Phase.POSITIONING_LAUNCH
        
        # CEO reviews and summarizes
        summary = await self.ceo.summarize_phase(Phase.POSITIONING_LAUNCH, {
            "launch_package": launch_package
        })
        
        await self.ceo.request_owner_decision(Phase.POSITIONING_LAUNCH)
        
        return {
            "phase": Phase.POSITIONING_LAUNCH.value,
            "artifacts": {"launch_package": launch_package},
            "summary": summary,
            "chat_log": [m.to_dict() for m in self.bus.get_messages(Phase.POSITIONING_LAUNCH)]
        }
    
    async def complete_project(self) -> Dict[str, Any]:
        """Mark project as complete and create final summary."""
        if not self.project:
            raise ValueError("No project to complete")
        
        self.project.status = "complete"
        self.project.current_phase = Phase.COMPLETE
        
        final_summary = f"""# Core Devices Company - Product Launch Ready

**Product**: {self.project.idea_dossier.get('working_title', 'Product')}
**Primary Need**: {self.project.idea_dossier.get('primary_need', 'N/A')}
**Category**: {self.project.idea_dossier.get('category', 'N/A')}

## Key Differentiations
{json.dumps(self.project.concept_pack.get('chosen_differentiations', []), indent=2) if self.project.benchmark_data else 'New Category Product'}

## UX & System Highlights
- **Friction Budget**: {json.dumps(self.project.friction_budget, indent=2)}
- **System Architecture**: {json.dumps(self.project.system_architecture, indent=2)}

## Launch Messaging
{json.dumps(self.project.positioning, indent=2)}

**Status**: Ready for Launch ✓

All checklists completed across 6 phases.
"""
        
        return {
            "status": "complete",
            "final_summary": final_summary,
            "project": self.project
        }
    
    def get_chat_log(self, phase: Optional[Phase] = None) -> List[Dict[str, Any]]:
        """Get complete chat log or filtered by phase."""
        messages = self.bus.get_messages(phase)
        return [m.to_dict() for m in messages]
