# Core Devices Company - Multi-Agent Electronic Product Development System

## Overview

Core Devices Company is a Ferrari-style multi-agent system for developing electrical and electronic products. It implements a complete organizational structure where every role is an AI agent, guiding products from initial idea to market launch through 6 rigorous phases.

## Key Features

### Multi-Agent System
- **CEO_Agent** - Orchestrates all phases and presents to Owner
- **CPO_Agent** - Chief Product Officer, owns product portfolio and idea intake
- **CDO_Agent** - Chief Design & UX Officer, owns user experience end-to-end
- **CTO_Agent** - Chief Technology Officer, owns technical feasibility and safety
- **COO_Agent** - Chief Operations Officer, owns manufacturing and supply chain
- **CMO_Agent** - Chief Marketing Officer, owns market analysis and positioning

### 6-Phase Pipeline

1. **Strategy & Idea Intake**
   - Validate idea against primary human needs (energy, water, food, shelter, health, communication, safety, mobility, essential productivity)
   - Classify as New Category or Derivative product
   - Create Product Idea Dossier

2. **Concept & Differentiation**
   - Develop 2-3 product concepts
   - For derivative products: benchmark competitors and apply 1-2σ differentiation rule
   - Create Concept Pack with usage scenarios

3. **UX Architecture & System Design**
   - Define user journeys (unboxing, first use, daily use, maintenance, error recovery)
   - Create interaction blueprint
   - Design system architecture (power, sensors, processing, connectivity)
   - Establish friction budget (minimize user effort)

4. **Detailed Engineering & Prototyping**
   - Detailed electrical/electronic design
   - Industrial design (form, affordances)
   - Prototype planning
   - Usability metrics

5. **Validation, Safety & Industrialization**
   - Safety validation (electrical, environmental)
   - Manufacturing planning (DFM/DFA)
   - Serviceability design
   - Pilot run planning

6. **Customer Experience, Positioning & Launch**
   - Market positioning and messaging
   - Onboarding materials
   - Support strategy
   - Launch package

## Core Principles

### Primary Human Needs
Every product must solve a primary human need. Auxiliary gadgets are rejected.

**Primary Needs:**
- Energy
- Water
- Food
- Shelter
- Health
- Communication
- Safety
- Mobility
- Essential Productivity

### Friction Reduction
Users follow the path of least resistance. Every decision must reduce:
- Number of steps
- Cognitive load
- Error recovery complexity

### 1-2σ Differentiation Rule
For derivative products, differentiate on 2-3 key attributes within 1-2 standard deviations of market mean:
- Different enough to stand out
- Close enough to feel familiar

### Owner Authority
The human user (Owner) has absolute authority to:
- Approve phases
- Request changes
- Stop projects at any time

## Files Created

### Backend
- **`app/product_company/core_devices_company.py`** - Main multi-agent system implementation
  - All agent classes (CEO, CPO, CDO, CTO, COO, CMO)
  - Phase execution logic
  - ProductProject dataclass
  - MessageBus for agent communication

- **`app/product_company/__init__.py`** - Package initialization

### Database
- **`app/models.py`** - Updated with `CoreDevicesProject` model
  - Stores project state, artifacts, chat logs
  - Tracks progress and errors
  - Supports project persistence and recovery

### API Routes
- **`app/routes/core_devices.py`** - Complete REST API
  - POST `/api/core-devices/projects` - Create new project
  - GET `/api/core-devices/projects` - List all projects
  - GET `/api/core-devices/projects/{id}` - Get project details
  - POST `/api/core-devices/projects/{id}/execute-phase` - Execute current phase
  - GET `/api/core-devices/projects/{id}/phase-status` - Check phase execution status
  - POST `/api/core-devices/projects/{id}/owner-decision` - Submit owner decision
  - GET `/api/core-devices/projects/{id}/chat-log` - Get agent communications
  - DELETE `/api/core-devices/projects/{id}` - Delete project

### Frontend
- **`app/templates/core_devices_company.html`** - Complete single-page application
  - Project creation modal
  - Phase progress visualization
  - Real-time agent chat display
  - Owner decision panel
  - Project list sidebar

### Integration
- **`app/main.py`** - Updated with:
  - Import of `core_devices` routes
  - Route registration
  - Page endpoint `/core-devices`

- **`app/templates/homepage.html`** - Updated with:
  - Core Devices Company feature card
  - Quick link navigation
  - Updated feature count (6 → 7)

## Usage

### Creating a Project

1. Navigate to `/core-devices` or click "Core Devices Company" from the homepage
2. Click "New Product" button
3. Fill in:
   - Product idea description
   - Primary human need it addresses
   - Any constraints (budget, environment, etc.)
   - AI model preference
4. Click "Create Product"

### Working Through Phases

1. **Execute Phase**: Click "Execute" button on the active phase
2. **Monitor Progress**: Watch agent communications in real-time
3. **Review Artifacts**: Examine phase outputs and deliverables
4. **Make Decision**: When prompted, choose:
   - **Approve** - Move to next phase
   - **Request Changes** - Provide feedback and re-execute
   - **Stop** - Terminate the project

### Agent Communications

All agent messages are visible in the chat log, showing:
- Agent name (from → to)
- Message content
- Timestamp
- Message type (internal, owner_request, owner_response)

## Architecture

### Data Flow

```
User Input → CEO_Agent → Specialized Agents → Phase Execution → Artifacts → Owner Review
                ↓                                                              ↓
          MessageBus ←───────────────────────────────────────────────────────┘
                ↓
          Database (Persistence)
```

### Phase Execution

Each phase runs in the background:
1. User clicks "Execute"
2. Background task starts
3. Relevant agents collaborate
4. Artifacts are generated
5. CEO summarizes results
6. Owner decision required
7. Project advances or iterates

### State Management

- **In-Memory**: Active projects stored in dictionary for fast access
- **Database**: All projects persisted to PostgreSQL
- **Recovery**: Projects can be loaded from database on server restart

## Design Philosophy

### Ferrari-Style Excellence

Like Ferrari's approach to car manufacturing:
- **Uncompromising Quality**: Every phase must meet high standards
- **Systematic Process**: Clear gates between phases
- **Owner-Centric**: Final authority rests with the Owner
- **Visible Craftsmanship**: All agent work is transparent

### First Principles Thinking

- New category products are designed from scratch based on human needs
- Derivative products reference the market but innovate within constraints
- User friction is measured and minimized
- Technical complexity is hidden from users

## Example Product Ideas

### New Category
- "A device that purifies air and generates drinking water from humidity using solar power" (Energy + Water)
- "Smart bandage that monitors wound healing and alerts to infection" (Health + Safety)

### Derivative
- "Wireless earbuds with 3-day battery life and 2-minute fast charging" (Communication - differentiated on battery and charging)
- "Electric kettle that boils in 30 seconds with silent operation" (Food/Water - differentiated on speed and noise)

## Technical Requirements

### Dependencies
- FastAPI for REST API
- SQLAlchemy for database ORM
- PostgreSQL for persistence
- LLM client (Ollama/OpenAI) for agent intelligence
- Bootstrap 5 for UI

### LLM Configuration

The system uses the configured LLM client from `app/llm/client.py`. Default model is `qwen3:30b` but can be customized per project.

## Future Enhancements

Potential additions:
- Export final specifications as PDF
- Integration with CAD tools for industrial design
- BOM (Bill of Materials) generation
- Manufacturing partner suggestions
- Patent search integration
- Market size estimation
- Cost modeling tools

## Comparison with Book Publishing House

Both systems follow the same multi-agent architecture:
- **Book Publishing House**: Creates books through 6 literary phases
- **Core Devices Company**: Creates electronic products through 6 development phases

Key differences:
- Product focus vs. creative writing
- Technical validation vs. editorial revision
- Manufacturing concerns vs. publishing logistics
- Market differentiation rules (1-2σ) vs. genre conventions

## Summary

Core Devices Company provides a complete, production-ready system for developing electronic products with AI assistance. It enforces best practices, maintains quality gates, and keeps the human owner in control while leveraging AI agents for execution and collaboration.

The system is accessible via `/core-devices` and integrates seamlessly with the existing AI Assistant application.
