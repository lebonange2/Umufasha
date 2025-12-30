# Research Team Feature - Autonomous Product Discovery

## Overview

The Research Team is an autonomous multi-agent system that discovers and validates product opportunities when the Owner doesn't have a specific product idea. This feature transforms Core Devices Company from a product development system into a complete innovation pipeline.

## Key Enhancement

**Before:** Product idea and primary need were REQUIRED fields. Users had to know exactly what they wanted to build.

**After:** Product idea and primary need are now OPTIONAL. Users can enable **Research Mode** to let AI agents discover the best opportunities.

## Research Team Composition

### 1. **Market_Research_Agent**
**Responsibilities:**
- Analyze current market trends in electronics/devices
- Identify emerging needs and market gaps
- Discover underserved primary human needs
- Identify 3-5 specific product opportunities

**Checklist (2 items):**
1. Research market trends and emerging needs
2. Identify specific product opportunities with market potential

### 2. **Technology_Research_Agent**
**Responsibilities:**
- Research enabling technologies for each opportunity
- Assess technology readiness levels (mature/emerging/experimental)
- Evaluate technical feasibility (high/medium/low)
- Determine component availability

**Checklist (1 item):**
1. Analyze enabling technologies and feasibility for all opportunities

### 3. **User_Research_Agent**
**Responsibilities:**
- Analyze user pain points for each opportunity
- Research current user behaviors and solutions
- Identify friction in existing solutions
- Define user preferences and needs

**Checklist (1 item):**
1. Research user needs, behaviors, and friction points

### 4. **Research_Lead_Agent**
**Responsibilities:**
- Synthesize all research findings
- Evaluate opportunities against criteria:
  - Market strength
  - Technical feasibility
  - Friction reduction potential
  - Primary need alignment
- Make ONE final product recommendation
- Generate comprehensive PDF report

**Checklist (1 item):**
1. Synthesize research and recommend best opportunity

## Phase 0: Research & Discovery

This new phase (Phase 0) executes before Phase 1 when research mode is enabled.

### Research Process Flow

```
1. Owner creates project in Research Mode
   ↓
2. Market_Research_Agent analyzes markets
   ↓
3. Technology_Research_Agent evaluates tech feasibility
   ↓
4. User_Research_Agent studies user needs
   ↓
5. Research_Lead_Agent synthesizes & recommends
   ↓
6. Comprehensive PDF Report generated
   ↓
7. CEO_Agent presents to Owner for approval
   ↓
8. Owner Decision:
   - Approve → Use recommendation, proceed to Phase 1
   - Request Changes → Specify new research focus
   - Provide Own Idea → Override with manual idea
```

### Research Outputs

**1. Market Analysis**
- 5-7 current market trends
- Emerging needs analysis
- Market gaps identification
- Opportunity areas

**2. Technology Analysis**
- For each opportunity:
  - Enabling technologies required
  - Technology readiness level
  - Technical feasibility score
  - Component availability

**3. User Analysis**
- For each opportunity:
  - Primary pain points
  - Current behaviors
  - Friction in existing solutions
  - User preferences

**4. Final Recommendation**
- Selected product concept (detailed)
- Primary human need addressed
- Justification (3-5 bullet points)
- Expected impact
- Next steps for development

**5. Downloadable PDF Report**
- Executive summary
- Complete market analysis
- Technology assessment tables
- User research findings
- Recommendation with justification
- Alternative opportunities for future

## PDF Report Structure

The system generates a professional PDF report using ReportLab with:

### Report Sections

1. **Title Page**
   - Report title
   - Company name (Core Devices Company)
   - Research date
   - Research scope

2. **Executive Summary**
   - Recommended product
   - Primary need
   - Expected impact

3. **Table of Contents**
   - 6 main sections with page numbers

4. **Section 1: Market Analysis**
   - Market trends (numbered list)
   - Emerging needs
   - Market gaps
   - Visual tables

5. **Section 2: Technology Analysis**
   - Per-opportunity breakdowns
   - Technology readiness tables
   - Feasibility assessments
   - Component availability

6. **Section 3: User Research**
   - Pain points per opportunity
   - Current user behaviors
   - Friction analysis
   - User preference insights

7. **Section 4: Product Opportunities Evaluated**
   - Complete list of all opportunities considered
   - Brief descriptions

8. **Section 5: Final Recommendation**
   - Detailed product concept
   - Primary need justification
   - Selection reasoning
   - Impact assessment

9. **Section 6: Next Steps**
   - Recommended actions
   - Development roadmap
   - Alternative opportunities

### PDF Styling

- **Professional Layout**: Letter size, 1-inch margins
- **Typography**: Clean Helvetica fonts with hierarchy
- **Color Scheme**: Professional grays and accent colors
- **Tables**: Formatted with gridlines and backgrounds
- **Lists**: Bullet points and numbered lists
- **Sections**: Clear headings and spacing

## UI Changes

### Create Project Modal

**New Toggle:**
```
🔬 Research Mode - Let our Research Team discover product opportunities for you

[Toggle Switch]
```

**When Research Mode is OFF (Default):**
- Product Idea field (required)
- Primary Need dropdown (required)
- Constraints (optional)
- AI Model selector

**When Research Mode is ON:**
- Product Idea field → HIDDEN
- Primary Need dropdown → HIDDEN
- Research Focus field (optional) → SHOWN
  - Placeholder: "e.g., 'health devices', 'energy solutions', 'smart home'..."
  - Allows narrowing research scope
- Constraints (optional)
- AI Model selector

### Phase Display

**Phase 0 Card:** (Only visible for research mode projects)
```
┌─────────────────────────────────────────┐
│ 🔍 Research & Discovery          [Active]│
│                                           │
│ Research Team discovers product           │
│ opportunities                             │
│                                           │
│ [Start Research]                          │
│ [Download Report]  (after completion)     │
│ [Approve] (after report review)           │
└─────────────────────────────────────────┘
```

### Research Phase Actions

1. **Start Research Button**
   - Triggers background research execution
   - Shows: "Research Team activated! They are analyzing markets, technologies, and user needs..."

2. **Download Report Button**
   - Appears after research completes
   - Downloads PDF: `research_report_{project_id}.pdf`

3. **Approve Button**
   - Uses research recommendation
   - Moves to Phase 1 with discovered product idea

4. **Reject Options**
   - Request different research focus
   - Provide own idea instead

## API Endpoints

### 1. Create Project (Enhanced)
```
POST /api/core-devices/projects
```

**Request Body:**
```json
{
  "product_idea": "",  // Optional - empty for research mode
  "primary_need": "",  // Optional - empty for research mode  
  "research_mode": true,  // NEW: Enable research mode
  "research_scope": "health devices",  // NEW: Optional focus
  "constraints": { "description": "..." },
  "model": "qwen3:30b"
}
```

### 2. Execute Research Phase
```
POST /api/core-devices/projects/{project_id}/execute-research
```

**Response:**
```json
{
  "message": "Research phase started",
  "project_id": "..."
}
```

### 3. Download Research Report
```
GET /api/core-devices/projects/{project_id}/research-report
```

**Response:**
- Content-Type: `application/pdf`
- Content-Disposition: `attachment; filename=research_report_{id}.pdf`
- Binary PDF data

### 4. Approve Research Recommendation
```
POST /api/core-devices/projects/{project_id}/approve-research
```

**Request Body:**
```json
{
  "approve": true,  // true to use recommendation
  "provide_own_idea": false,  // true to override
  "product_idea": null,  // if providing own idea
  "primary_need": null  // if providing own idea
}
```

**Response:**
```json
{
  "message": "Research recommendation approved. Proceeding to Phase 1.",
  "project_id": "...",
  "current_phase": "strategy_idea_intake"
}
```

## Database Schema Changes

### CoreDevicesProject Table

**New Columns:**
```sql
-- Product idea is now nullable
product_idea TEXT NULL;  -- Was: NOT NULL

-- Research mode fields
research_mode BOOLEAN DEFAULT FALSE;
research_scope TEXT NULL;

-- PDF report storage
pdf_report BYTEA NULL;  -- Stores binary PDF data
```

## Use Cases

### Use Case 1: Full Research Mode

**Scenario:** Entrepreneur wants to build a product but doesn't have a specific idea.

**Steps:**
1. Create project with Research Mode enabled
2. Optionally specify focus: "health devices"
3. Click "Start Research"
4. Wait for Research Team to complete analysis (2-5 minutes)
5. Download and review PDF report
6. Read CEO's summary in chat log
7. Click "Approve" to use the recommendation
8. Proceed to Phase 1 with discovered product

**Result:** Project automatically populated with AI-discovered product idea and primary need.

### Use Case 2: Focused Research

**Scenario:** Company knows they want to work in energy sector but needs specific idea.

**Steps:**
1. Enable Research Mode
2. Set research scope: "renewable energy devices for homes"
3. Execute research
4. Review recommendations focused on home energy solutions
5. Approve and proceed

### Use Case 3: Manual Override

**Scenario:** User reviews research but prefers their own idea.

**Steps:**
1. Review research report
2. Click "Provide Own Idea"
3. Enter custom product idea and primary need
4. System switches to manual mode
5. Proceed to Phase 1 with manual idea

### Use Case 4: Traditional Mode (No Change)

**Scenario:** User already knows exactly what they want to build.

**Steps:**
1. Leave Research Mode OFF
2. Enter product idea and primary need
3. Create project
4. Start directly at Phase 1

**Result:** Works exactly as before - no change to existing workflow.

## Benefits

### 1. **Lower Barrier to Entry**
- Users don't need a fully-formed idea
- AI discovers opportunities based on real market/user data

### 2. **Data-Driven Innovation**
- Research backed by market trends, technology assessments, and user needs
- Systematic evaluation of multiple opportunities

### 3. **Professional Documentation**
- Comprehensive PDF report suitable for stakeholders
- Auditable research process

### 4. **Flexibility**
- Can use research recommendation OR provide own idea
- Can request re-research with different focus

### 5. **Quality Validation**
- Every discovered product validated against:
  - Primary human needs
  - Technical feasibility
  - Market opportunity
  - User friction reduction

## Technical Implementation

### Files Created/Modified

**New Files:**
- `app/product_company/research_team.py` - Complete research team implementation
  - MarketResearchAgent class
  - TechnologyResearchAgent class
  - UserResearchAgent class
  - ResearchLeadAgent class
  - ResearchReportGenerator class (PDF generation)
  - ResearchTeam orchestrator

**Modified Files:**
- `app/product_company/core_devices_company.py`
  - Added Phase.RESEARCH_DISCOVERY enum
  - Added execute_phase_0() method
  - Added apply_research_recommendation() method
  - Made product_idea and primary_need optional in initialize_project()
  - Integrated ResearchTeam

- `app/routes/core_devices.py`
  - Made product_idea/primary_need optional in CoreDevicesProjectCreate
  - Added research_mode and research_scope fields
  - Added execute_research_phase() endpoint
  - Added download_research_report() endpoint
  - Added approve_research_recommendation() endpoint
  - Updated save/load functions for research fields

- `app/models.py`
  - Made product_idea nullable
  - Added research_mode column (Boolean)
  - Added research_scope column (Text)
  - Added pdf_report column (LargeBinary)

- `app/templates/core_devices_company.html`
  - Added research mode toggle in create modal
  - Added toggleResearchMode() JavaScript function
  - Added research_discovery to phaseInfo
  - Added executeResearchPhase() function
  - Added downloadResearchReport() function
  - Added approveResearch() function
  - Updated phase rendering to show research buttons

- `requirements.txt`
  - Added reportlab==4.0.7

## Example Research Output

### Market Trends Identified
1. Increasing demand for home health monitoring devices
2. Rise in renewable energy adoption for residential use
3. Growing concern about indoor air quality post-pandemic
4. Shift toward contactless/automated home solutions
5. Demand for products that reduce daily routine friction

### Example Recommendation

**Product Concept:**
"Smart Air Quality Monitor with Automated Purification - A desktop device that continuously monitors indoor air quality (PM2.5, CO2, VOCs, humidity, temperature) and automatically activates built-in purification when thresholds are exceeded. One-touch setup, mobile app with health insights, solar-powered backup."

**Primary Need:** Health

**Justification:**
1. **Market Opportunity**: Post-pandemic surge in air quality awareness, $4.5B market growing 12% annually
2. **Technical Feasibility**: All sensors readily available, mature IoT technology, established manufacturing
3. **Friction Reduction**: Current solutions require manual monitoring and separate purifier control - this automates everything
4. **Primary Need Alignment**: Directly addresses health through prevention of respiratory issues and allergies

**Expected Impact:**
Users spend zero mental energy on air quality management while gaining continuous protection from poor air, with actionable health insights via app.

## Future Enhancements

Potential improvements to Research Team:

1. **Competitive Analysis**
   - Automated competitor research via web scraping
   - Patent search integration
   - Pricing analysis

2. **Market Size Estimation**
   - TAM/SAM/SOM calculations
   - Growth projections
   - Geographic opportunity mapping

3. **Cost Modeling**
   - BOM cost estimation
   - Manufacturing cost projections
   - Pricing recommendations

4. **Risk Assessment**
   - Regulatory/compliance risks
   - IP/patent risks
   - Supply chain risks

5. **Interactive Research**
   - Owner can ask questions during research
   - Iterative refinement of opportunities
   - Real-time research progress updates

## Migration Guide

### For Existing Projects

Existing projects are NOT affected. They will:
- Continue working with Phase 1 as starting phase
- Keep product_idea as required
- Maintain all existing functionality

### For New Development

To use Research Mode:
```python
# In your application code
project_data = {
    "research_mode": True,  # Enable research
    "research_scope": "optional focus area",  # Optional
    "constraints": {"budget": "< $50k"},  # Optional
    "model": "qwen3:30b"
}

# Product idea and primary need can be empty/omitted
response = await client.post("/api/core-devices/projects", json=project_data)
```

## Testing the Feature

### Manual Test Flow

1. **Navigate to Core Devices Company** (`/core-devices`)
2. **Click "New Product"**
3. **Enable Research Mode toggle** (🔬 Research Mode checkbox)
4. **Optionally set research focus** (e.g., "health")
5. **Click "Create Product"**
6. **Wait for project to load**
7. **Click "Start Research"** on Phase 0 card
8. **Wait 2-5 minutes** for research to complete
9. **Click "Download Report"** to get PDF
10. **Review PDF report** - verify all sections present
11. **Click "Approve"** to use recommendation
12. **Verify project updates** with discovered idea
13. **Proceed to Phase 1**

### Validation Points

✅ Research mode toggle works
✅ Product idea/need fields hide when research enabled
✅ Research focus field appears
✅ Project creates successfully without idea/need
✅ Phase 0 appears in phases list
✅ Research executes in background
✅ PDF downloads successfully
✅ PDF contains all required sections
✅ CEO summary appears in chat log
✅ Approve button updates project
✅ Phase 1 starts with discovered product

## Summary

The Research Team feature transforms Core Devices Company from a "product development system" into a complete "innovation discovery and development platform." Users can now:

- **Start with nothing** - Just constraints/focus areas
- **Let AI discover** - Research Team finds best opportunities
- **Get documentation** - Professional PDF reports
- **Maintain control** - Approve, modify, or override
- **Traditional mode still works** - Backward compatible

This enhancement significantly lowers the barrier to entry while maintaining the rigor and quality of the 6-phase Ferrari-style pipeline.

---

**Implementation Complete:** All components integrated, tested, and documented. Ready for production use.
