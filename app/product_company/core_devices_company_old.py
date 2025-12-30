"""
Core Devices Company - Multi-Agent Electronic Product Development System

This module implements a complete organizational structure where every role is an AI agent,
mirroring a Ferrari-style production pipeline for electrical/electronic products.

The Owner (human user) has absolute override and can see all agent communications.

Each agent follows explicit checklists for each phase as defined in the specification.
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
    target_sigma_offset: float  # How many σ from mean (should be within 1-2)
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
        
        # Notify subscribers
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


class CEOAgent:
    """Chief Executive Officer - orchestrates all phases and presents to Owner."""
    
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
        """Announce phase start."""
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
    
    async def summarize_phase(self, phase: Phase, artifacts: Dict[str, Any]) -> str:
        """Create phase summary for Owner approval."""
        prompt = f"""You are the CEO of Core Devices Company. Summarize the following phase artifacts for Owner approval.

Phase: {phase.value}
Artifacts: {json.dumps(artifacts, indent=2)}

Create a clear, concise summary highlighting:
1. What was accomplished
2. Key decisions made
3. What the Owner needs to review

Format as markdown. Be concise and business-focused."""
        
        response = await self.llm.generate(prompt)
        summary = f"[CEO_Agent] Phase Summary\n\n{response}"
        
        self.bus.send(self.role, "OWNER", phase, summary, "owner_request")
        return summary
    
    async def request_owner_decision(self, phase: Phase) -> str:
        """Ask Owner for decision."""
        message = f"""[CEO_Agent] Owner Decision Required

Please review the phase summary above and decide:
- **Approve**: Proceed to next phase
- **Request Changes**: Specify what needs to be revised
- **Stop**: Stop the project

Your decision?"""
        
        self.bus.send(self.role, "OWNER", phase, message, "owner_request")
        return message


class CPOAgent:
    """Chief Product Officer - owns product portfolio and idea intake."""
    
    def __init__(self, llm_client: LLMClient, message_bus: MessageBus):
        self.role = "CPO_Agent"
        self.llm = llm_client
        self.bus = message_bus
    
    async def phase1_idea_intake(self, project: ProductProject) -> Dict[str, Any]:
        """Phase 1: Strategy & Idea Intake."""
        self.bus.send(self.role, "CEO_Agent", Phase.STRATEGY_IDEA_INTAKE,
                     f"[CPO_Agent] Analyzing product idea: {project.product_idea}")
        
        # Classify product and validate against primary needs
        prompt = f"""You are the Chief Product Officer of Core Devices Company.

Product Idea: {project.product_idea}
Primary Need Stated: {project.primary_need.value if project.primary_need else 'Not specified'}

Tasks:
1. Restate the idea clearly
2. Validate it addresses a primary human need (energy, water, food, shelter, health, communication, safety, mobility, essential productivity)
3. Determine if this is a NEW CATEGORY or DERIVATIVE product
4. Describe current user context (how people solve this need today)
5. Create a friction-reduction hypothesis

Output as JSON with keys: idea_restatement, primary_need, category (new_category or derivative), current_context, friction_hypothesis, working_title"""
        
        response = await self.llm.generate(prompt)
        
        try:
            # Try to parse JSON from response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                dossier = json.loads(json_match.group())
            else:
                # Fallback: create structured dossier from text
                dossier = {
                    "idea_restatement": project.product_idea,
                    "primary_need": project.primary_need.value if project.primary_need else "unknown",
                    "category": "new_category",
                    "current_context": "To be determined",
                    "friction_hypothesis": "Reduces user effort through simplified interaction",
                    "working_title": "Innovative Device"
                }
        except:
            dossier = {
                "idea_restatement": project.product_idea,
                "primary_need": project.primary_need.value if project.primary_need else "unknown",
                "category": "new_category",
                "current_context": "To be determined",
                "friction_hypothesis": response,
                "working_title": "Innovative Device"
            }
        
        self.bus.send(self.role, "CEO_Agent", Phase.STRATEGY_IDEA_INTAKE,
                     f"[CPO_Agent] Created Product Idea Dossier: {dossier.get('working_title', 'Product')}")
        
        return dossier
    
    async def phase2_concept_development(self, project: ProductProject) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
        """Phase 2: Concept & Differentiation (with CMO)."""
        category = project.idea_dossier.get("category", "new_category")
        
        if category == "derivative":
            # Benchmark existing products and define differentiation
            prompt = f"""You are the CPO analyzing a derivative product.

Product: {project.idea_dossier.get('working_title')}
Idea: {project.idea_dossier.get('idea_restatement')}

Tasks:
1. Identify 3-7 existing products in this category
2. List key attributes (setup time, steps to complete task, battery life, size, noise, durability, etc.)
3. Estimate mean and std deviation for each attribute
4. Choose 2-3 attributes to differentiate on
5. Specify target within 1-2 standard deviations of mean

Output as JSON with keys: existing_products, attributes, chosen_differentiations"""
            
            benchmark_response = await self.llm.generate(prompt)
            
            try:
                import re
                json_match = re.search(r'\{.*\}', benchmark_response, re.DOTALL)
                if json_match:
                    benchmark = json.loads(json_match.group())
                else:
                    benchmark = {
                        "existing_products": ["Product A", "Product B", "Product C"],
                        "attributes": {},
                        "chosen_differentiations": []
                    }
            except:
                benchmark = {
                    "existing_products": [],
                    "attributes": {},
                    "chosen_differentiations": []
                }
        else:
            benchmark = None
        
        # Develop 2-3 concepts
        concept_prompt = f"""You are the CPO developing product concepts.

Product: {project.idea_dossier.get('working_title')}
Category: {category}
{'Benchmarks: ' + json.dumps(benchmark) if benchmark else ''}

Create 2-3 product concepts. For each:
1. Concept name
2. Core approach
3. Friction reduction strategy

Output as JSON with key "concepts" containing list of concept objects."""
        
        concept_response = await self.llm.generate(concept_prompt)
        
        try:
            import re
            json_match = re.search(r'\{.*\}', concept_response, re.DOTALL)
            if json_match:
                concept_pack = json.loads(json_match.group())
            else:
                concept_pack = {
                    "concepts": [
                        {
                            "name": "Concept A",
                            "approach": "Simplify existing workflow",
                            "friction_reduction": "Reduce steps by 50%"
                        }
                    ]
                }
        except:
            concept_pack = {"concepts": []}
        
        self.bus.send(self.role, "CEO_Agent", Phase.CONCEPT_DIFFERENTIATION,
                     f"[CPO_Agent] Developed {len(concept_pack.get('concepts', []))} concepts")
        
        return concept_pack, benchmark


class CDOAgent:
    """Chief Design & UX Officer - owns user experience end-to-end."""
    
    def __init__(self, llm_client: LLMClient, message_bus: MessageBus):
        self.role = "CDO_Agent"
        self.llm = llm_client
        self.bus = message_bus
    
    async def phase2_usage_concepts(self, project: ProductProject) -> Dict[str, Any]:
        """Phase 2: Develop usage concepts."""
        prompt = f"""You are the Chief Design Officer creating usage concepts.

Product: {project.idea_dossier.get('working_title')}
Primary Need: {project.idea_dossier.get('primary_need')}

Create 2-3 usage scenarios showing:
1. Typical use case (day-in-the-life)
2. How it reduces friction vs current solutions
3. Physical form and interaction style

Output as JSON with key "usage_concepts"."""
        
        response = await self.llm.generate(prompt)
        
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                usage_concepts = json.loads(json_match.group())
            else:
                usage_concepts = {
                    "usage_concepts": [
                        {
                            "scenario": "User needs solution for primary need",
                            "friction_reduction": "Simplifies interaction",
                            "form": "Compact, intuitive device"
                        }
                    ]
                }
        except:
            usage_concepts = {"usage_concepts": []}
        
        self.bus.send(self.role, "CPO_Agent", Phase.CONCEPT_DIFFERENTIATION,
                     "[CDO_Agent] Created usage concepts")
        
        return usage_concepts
    
    async def phase3_ux_design(self, project: ProductProject) -> Dict[str, Any]:
        """Phase 3: UX Architecture & System Design."""
        prompt = f"""You are the CDO designing the complete UX architecture.

Product: {project.idea_dossier.get('working_title')}
Concept: {json.dumps(project.concept_pack)}

Design:
1. Key user journeys (unboxing, first use, daily use, maintenance, error recovery)
2. Interaction blueprint (inputs, outputs, states, transitions)
3. Friction budget (max steps for setup, max steps for main task, max UI options)

For each journey, list steps and identify friction points to eliminate.

Output as JSON with keys: user_journeys, interaction_blueprint, friction_budget"""
        
        response = await self.llm.generate(prompt)
        
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                ux_design = json.loads(json_match.group())
            else:
                ux_design = {
                    "user_journeys": {},
                    "interaction_blueprint": {},
                    "friction_budget": {
                        "max_setup_steps": 3,
                        "max_task_steps": 2,
                        "max_ui_options": 5
                    }
                }
        except:
            ux_design = {
                "user_journeys": {},
                "interaction_blueprint": {},
                "friction_budget": {}
            }
        
        self.bus.send(self.role, "CTO_Agent", Phase.UX_SYSTEM_DESIGN,
                     "[CDO_Agent] Completed UX architecture design")
        
        return ux_design
    
    async def phase4_industrial_design(self, project: ProductProject) -> Dict[str, Any]:
        """Phase 4: Industrial design and prototyping."""
        prompt = f"""You are the CDO creating industrial design specifications.

Product: {project.idea_dossier.get('working_title')}
UX Design: {json.dumps(project.interaction_blueprint)}

Specify:
1. Physical design (shape, size, weight targets)
2. Affordances (how to hold, grip, orient)
3. Prototype mockup approach
4. Usability test metrics

Output as JSON with keys: industrial_design, prototype_approach, test_metrics"""
        
        response = await self.llm.generate(prompt)
        
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                design = json.loads(json_match.group())
            else:
                design = {
                    "industrial_design": {},
                    "prototype_approach": {},
                    "test_metrics": {}
                }
        except:
            design = {"industrial_design": {}, "prototype_approach": {}, "test_metrics": {}}
        
        return design
    
    async def phase6_onboarding(self, project: ProductProject) -> Dict[str, Any]:
        """Phase 6: Onboarding and documentation."""
        prompt = f"""You are the CDO creating onboarding materials.

Product: {project.idea_dossier.get('working_title')}

Create:
1. One-page quick-start guide (clear steps, pictograms)
2. Device labeling strategy
3. Support paths (how users find help)

Output as JSON with keys: quick_start, labeling, support_paths"""
        
        response = await self.llm.generate(prompt)
        
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                onboarding = json.loads(json_match.group())
            else:
                onboarding = {"quick_start": {}, "labeling": {}, "support_paths": {}}
        except:
            onboarding = {"quick_start": {}, "labeling": {}, "support_paths": {}}
        
        return onboarding


class CTOAgent:
    """Chief Technology Officer - owns technical feasibility, safety, and reliability."""
    
    def __init__(self, llm_client: LLMClient, message_bus: MessageBus):
        self.role = "CTO_Agent"
        self.llm = llm_client
        self.bus = message_bus
    
    async def phase3_system_architecture(self, project: ProductProject) -> Dict[str, Any]:
        """Phase 3: System architecture design."""
        prompt = f"""You are the CTO designing the system architecture.

Product: {project.idea_dossier.get('working_title')}
UX Requirements: {json.dumps(project.user_journeys)}

Design:
1. Power subsystem
2. Sensors/actuators needed
3. Processing & memory requirements
4. Connectivity (if needed)
5. Block diagram description
6. Constraints affecting UX (warm-up time, safety delays)

Output as JSON with keys: power, sensors_actuators, processing, connectivity, constraints"""
        
        response = await self.llm.generate(prompt)
        
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                architecture = json.loads(json_match.group())
            else:
                architecture = {
                    "power": "Battery-powered",
                    "sensors_actuators": [],
                    "processing": "Microcontroller",
                    "connectivity": "None",
                    "constraints": []
                }
        except:
            architecture = {}
        
        self.bus.send(self.role, "CDO_Agent", Phase.UX_SYSTEM_DESIGN,
                     "[CTO_Agent] Completed system architecture")
        
        return architecture
    
    async def phase4_detailed_engineering(self, project: ProductProject) -> Dict[str, Any]:
        """Phase 4: Detailed engineering design."""
        prompt = f"""You are the CTO creating detailed engineering specifications.

Product: {project.idea_dossier.get('working_title')}
System Architecture: {json.dumps(project.system_architecture)}

Create:
1. Schematic design (conceptual components and connections)
2. PCB layout considerations
3. Firmware/software responsibilities
4. Critical risks to validate in prototypes
5. Alpha prototype objectives

Output as JSON with keys: schematic, pcb_layout, firmware, risks, prototype_objectives"""
        
        response = await self.llm.generate(prompt)
        
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                engineering = json.loads(json_match.group())
            else:
                engineering = {
                    "schematic": {},
                    "pcb_layout": {},
                    "firmware": {},
                    "risks": [],
                    "prototype_objectives": []
                }
        except:
            engineering = {}
        
        return engineering
    
    async def phase5_validation(self, project: ProductProject) -> Dict[str, Any]:
        """Phase 5: Validation and safety."""
        prompt = f"""You are the CTO defining validation and safety requirements.

Product: {project.idea_dossier.get('working_title')}

Specify:
1. Electrical safety requirements
2. Environmental limits (heat, moisture, etc.)
3. Failure modes and safe behavior
4. Relevant standards (conceptual)

Output as JSON with keys: safety_requirements, environmental_limits, failure_modes, standards"""
        
        response = await self.llm.generate(prompt)
        
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                validation = json.loads(json_match.group())
            else:
                validation = {
                    "safety_requirements": [],
                    "environmental_limits": {},
                    "failure_modes": [],
                    "standards": []
                }
        except:
            validation = {}
        
        return validation


class COOAgent:
    """Chief Operations Officer - owns manufacturing, supply chain, quality."""
    
    def __init__(self, llm_client: LLMClient, message_bus: MessageBus):
        self.role = "COO_Agent"
        self.llm = llm_client
        self.bus = message_bus
    
    async def phase5_manufacturing(self, project: ProductProject) -> Dict[str, Any]:
        """Phase 5: Manufacturing and serviceability."""
        prompt = f"""You are the COO planning manufacturing and operations.

Product: {project.idea_dossier.get('working_title')}
Design: {json.dumps(project.detailed_design)}

Create:
1. DFM/DFA strategy (reduce part count, simple assembly)
2. Tolerance management
3. Serviceability plan (user-replaceable parts, firmware updates, diagnostics)
4. Pilot run monitoring plan

Output as JSON with keys: dfm_strategy, tolerances, serviceability, pilot_plan"""
        
        response = await self.llm.generate(prompt)
        
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                manufacturing = json.loads(json_match.group())
            else:
                manufacturing = {
                    "dfm_strategy": {},
                    "tolerances": {},
                    "serviceability": {},
                    "pilot_plan": {}
                }
        except:
            manufacturing = {}
        
        return manufacturing


class CMOAgent:
    """Chief Marketing Officer - owns market analysis, positioning, messaging."""
    
    def __init__(self, llm_client: LLMClient, message_bus: MessageBus):
        self.role = "CMO_Agent"
        self.llm = llm_client
        self.bus = message_bus
    
    async def phase2_market_analysis(self, project: ProductProject) -> Dict[str, Any]:
        """Phase 2: Market analysis for concept."""
        prompt = f"""You are the CMO analyzing the market.

Product: {project.idea_dossier.get('working_title')}
Category: {project.idea_dossier.get('category')}

Analyze:
1. Market context and current solutions
2. User pain points
3. Opportunity areas

Output as JSON with keys: market_context, pain_points, opportunities"""
        
        response = await self.llm.generate(prompt)
        
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
            else:
                analysis = {"market_context": {}, "pain_points": [], "opportunities": []}
        except:
            analysis = {}
        
        return analysis
    
    async def phase6_positioning(self, project: ProductProject) -> Dict[str, Any]:
        """Phase 6: Positioning and launch package."""
        prompt = f"""You are the CMO creating positioning and launch materials.

Product: {project.idea_dossier.get('working_title')}
Primary Need: {project.idea_dossier.get('primary_need')}
Differentiation: {json.dumps(project.concept_pack)}

Create:
1. Product name (if needed refinement)
2. One-sentence primary need description
3. One-sentence friction reduction benefit
4. 3-5 key benefits (user outcomes, no jargon)
5. Launch messaging

Output as JSON with keys: product_name, need_statement, benefit_statement, key_benefits, launch_messaging"""
        
        response = await self.llm.generate(prompt)
        
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                positioning = json.loads(json_match.group())
            else:
                positioning = {
                    "product_name": project.idea_dossier.get('working_title'),
                    "need_statement": "",
                    "benefit_statement": "",
                    "key_benefits": [],
                    "launch_messaging": {}
                }
        except:
            positioning = {}
        
        return positioning


class CoreDevicesCompany:
    """Main orchestrator for the Core Devices Company multi-agent system."""
    
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
        """Execute Phase 1: Strategy & Idea Intake."""
        if not self.project:
            raise ValueError("Project not initialized")
        
        await self.ceo.start_phase(Phase.STRATEGY_IDEA_INTAKE, self.project)
        
        # CPO leads this phase
        idea_dossier = await self.cpo.phase1_idea_intake(self.project)
        self.project.idea_dossier = idea_dossier
        self.project.current_phase = Phase.STRATEGY_IDEA_INTAKE
        
        # CEO summarizes
        summary = await self.ceo.summarize_phase(Phase.STRATEGY_IDEA_INTAKE, {
            "idea_dossier": idea_dossier
        })
        
        return {
            "phase": Phase.STRATEGY_IDEA_INTAKE.value,
            "artifacts": {"idea_dossier": idea_dossier},
            "summary": summary,
            "chat_log": [m.to_dict() for m in self.bus.get_messages(Phase.STRATEGY_IDEA_INTAKE)]
        }
    
    async def execute_phase_2(self) -> Dict[str, Any]:
        """Execute Phase 2: Concept & Differentiation."""
        if not self.project or not self.project.idea_dossier:
            raise ValueError("Phase 1 must be completed first")
        
        await self.ceo.start_phase(Phase.CONCEPT_DIFFERENTIATION, self.project)
        
        # CPO and CMO collaborate
        market_analysis = await self.cmo.phase2_market_analysis(self.project)
        concept_pack, benchmark = await self.cpo.phase2_concept_development(self.project)
        usage_concepts = await self.cdo.phase2_usage_concepts(self.project)
        
        # Combine into final concept pack
        final_concept_pack = {
            **concept_pack,
            "usage_concepts": usage_concepts.get("usage_concepts", []),
            "market_analysis": market_analysis
        }
        
        self.project.concept_pack = final_concept_pack
        self.project.benchmark_data = benchmark
        self.project.current_phase = Phase.CONCEPT_DIFFERENTIATION
        
        summary = await self.ceo.summarize_phase(Phase.CONCEPT_DIFFERENTIATION, {
            "concept_pack": final_concept_pack,
            "benchmark_data": benchmark
        })
        
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
        """Execute Phase 3: UX Architecture & System Design."""
        if not self.project or not self.project.concept_pack:
            raise ValueError("Phase 2 must be completed first")
        
        await self.ceo.start_phase(Phase.UX_SYSTEM_DESIGN, self.project)
        
        # CDO and CTO collaborate
        ux_design = await self.cdo.phase3_ux_design(self.project)
        self.project.user_journeys = ux_design.get("user_journeys", {})
        self.project.interaction_blueprint = ux_design.get("interaction_blueprint", {})
        self.project.friction_budget = ux_design.get("friction_budget", {})
        
        system_arch = await self.cto.phase3_system_architecture(self.project)
        self.project.system_architecture = system_arch
        self.project.current_phase = Phase.UX_SYSTEM_DESIGN
        
        summary = await self.ceo.summarize_phase(Phase.UX_SYSTEM_DESIGN, {
            "ux_design": ux_design,
            "system_architecture": system_arch
        })
        
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
        """Execute Phase 4: Detailed Engineering & Prototyping."""
        if not self.project or not self.project.system_architecture:
            raise ValueError("Phase 3 must be completed first")
        
        await self.ceo.start_phase(Phase.DETAILED_ENGINEERING, self.project)
        
        # CTO and CDO collaborate
        detailed_engineering = await self.cto.phase4_detailed_engineering(self.project)
        industrial_design = await self.cdo.phase4_industrial_design(self.project)
        
        combined_design = {
            "engineering": detailed_engineering,
            "industrial_design": industrial_design
        }
        
        self.project.detailed_design = combined_design
        self.project.prototype_plan = industrial_design.get("prototype_approach", {})
        self.project.usability_metrics = industrial_design.get("test_metrics", {})
        self.project.current_phase = Phase.DETAILED_ENGINEERING
        
        summary = await self.ceo.summarize_phase(Phase.DETAILED_ENGINEERING, {
            "detailed_design": combined_design
        })
        
        return {
            "phase": Phase.DETAILED_ENGINEERING.value,
            "artifacts": {"detailed_design": combined_design},
            "summary": summary,
            "chat_log": [m.to_dict() for m in self.bus.get_messages(Phase.DETAILED_ENGINEERING)]
        }
    
    async def execute_phase_5(self) -> Dict[str, Any]:
        """Execute Phase 5: Validation, Safety & Industrialization."""
        if not self.project or not self.project.detailed_design:
            raise ValueError("Phase 4 must be completed first")
        
        await self.ceo.start_phase(Phase.VALIDATION_INDUSTRIALIZATION, self.project)
        
        # COO and CTO collaborate
        validation = await self.cto.phase5_validation(self.project)
        manufacturing = await self.coo.phase5_manufacturing(self.project)
        
        combined_plan = {
            "validation": validation,
            "manufacturing": manufacturing
        }
        
        self.project.validation_plan = validation
        self.project.manufacturing_plan = manufacturing.get("dfm_strategy", {})
        self.project.serviceability_plan = manufacturing.get("serviceability", {})
        self.project.current_phase = Phase.VALIDATION_INDUSTRIALIZATION
        
        summary = await self.ceo.summarize_phase(Phase.VALIDATION_INDUSTRIALIZATION, {
            "validation_manufacturing": combined_plan
        })
        
        return {
            "phase": Phase.VALIDATION_INDUSTRIALIZATION.value,
            "artifacts": {"validation_manufacturing": combined_plan},
            "summary": summary,
            "chat_log": [m.to_dict() for m in self.bus.get_messages(Phase.VALIDATION_INDUSTRIALIZATION)]
        }
    
    async def execute_phase_6(self) -> Dict[str, Any]:
        """Execute Phase 6: Customer Experience, Positioning & Launch."""
        if not self.project or not self.project.manufacturing_plan:
            raise ValueError("Phase 5 must be completed first")
        
        await self.ceo.start_phase(Phase.POSITIONING_LAUNCH, self.project)
        
        # CMO and CDO collaborate
        positioning = await self.cmo.phase6_positioning(self.project)
        onboarding = await self.cdo.phase6_onboarding(self.project)
        
        launch_package = {
            "positioning": positioning,
            "onboarding": onboarding
        }
        
        self.project.positioning = positioning
        self.project.launch_package = launch_package
        self.project.current_phase = Phase.POSITIONING_LAUNCH
        
        summary = await self.ceo.summarize_phase(Phase.POSITIONING_LAUNCH, {
            "launch_package": launch_package
        })
        
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
