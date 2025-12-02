# Quick Start Guide: Multi-Agent Book Generation System

## Overview

This guide shows you how to use the Manager-Writer multi-agent system to generate book outlines and optionally full prose.

## Prerequisites

- Python 3.8+
- Access to LLM (local Ollama or remote API)
- Required dependencies installed

## Basic Usage

### 1. Command Line Interface

Run the system interactively:

```bash
python -m app.book_writer.multi_agent_system
```

You'll be prompted for:
- **Book title**: e.g., "Exile to Mars"
- **Premise**: 1-3 sentences describing the story, e.g., "A man from Earth goes to live on Mars where there is an advanced civilization."
- **Number of chapters**: Default is 25
- **Tone**: Default is "narrative"
- **Style**: Default is "third person"
- **Generate prose?**: y/n (default: n)

### 2. Programmatic Usage

```python
import asyncio
from app.book_writer.multi_agent_system import MultiAgentBookGenerator

async def generate_book():
    # Create generator
    generator = MultiAgentBookGenerator(
        title="Exile to Mars",
        premise="A man from Earth goes to live on Mars where there is an advanced civilization.",
        num_chapters=25,
        tone="narrative",
        style="third person"
    )
    
    # Generate outline (without prose)
    result = await generator.generate_book(generate_prose=False)
    
    # Export to markdown
    generator.export_to_markdown("exile_to_mars_outline.md", include_prose=False)
    
    print(f"Generated {result['total_chapters']} chapters")
    return result

# Run
asyncio.run(generate_book())
```

### 3. With Full Prose

To generate full narrative prose for each subsection:

```python
# Generate with prose
result = await generator.generate_book(generate_prose=True)

# Export with prose
generator.export_to_markdown("exile_to_mars_full.md", include_prose=True)
```

## Example Output

For the premise: "A man from Earth goes to live on Mars where there is an advanced civilization."

The system generates:

```
Chapter 1 – Exile to the Red World
Section 1 – Leaving Earth
Subsection 1.1 – The Offer from Mars
  • Introduce Daniel, a tired Earth engineer living in a collapsing megacity, who secretly dreams of the stars.
  • He receives a mysterious encrypted message inviting him to join an advanced Martian civilization that has watched Earth for decades.
  • The message promises clean air, limitless energy, and a new life, but warns that he can never return to Earth.
Subsection 1.2 – Goodbyes on a Dying Planet
  • Daniel struggles with the choice, walking through polluted streets and remembering what Earth used to be like.
  • He tells his sister he's leaving; she's angry and hurt, but finally gives him an old family photo to take to Mars.
  • He boards a covert shuttle hidden in a cargo launch, watching Earth shrink as he wonders if he's a coward or a pioneer.
Section 2 – Arrival on Mars
Subsection 2.1 – The Hidden Martian City
  • The ship drops out of warp above Mars, but Daniel is shocked to see enormous glowing rings and glass domes floating in the thin atmosphere.
  • He lands inside an invisible energy shield and steps into a sprawling city of living metal, hovering trains, and crimson gardens.
  • Martians, human-like but taller with luminous eyes, greet him calmly, as if they've been expecting him his whole life.
Subsection 2.2 – Tests of a New Civilization
  • Daniel undergoes a "Resonance Trial," a mental and emotional test where the Martians read his memories instead of asking questions.
  • They explain their society: no money, shared knowledge, strict rules against disrupting young civilizations like Earth.
  • Daniel must decide whether to accept their rules and join them as an apprentice architect of worlds, or remain a permanent outsider on Mars.
```

## Understanding the Workflow

### Step 1: Book Planning
The Manager agent analyzes your premise and creates:
- Story arc (beginning, middle, end)
- Key characters
- Worldbuilding elements
- Chapter count recommendation

### Step 2: Outline Generation
For each chapter:
1. Manager creates detailed instructions
2. Writer generates chapter outline
3. Manager reviews and approves (or requests revisions)

### Step 3: Main Point Filling
For each subsection:
1. Manager instructs Writer to create full-sentence main points
2. Writer generates descriptive sentences (10+ words each)
3. Manager reviews for quality and story relevance

### Step 4: Prose Generation (Optional)
If enabled:
1. Writer expands each subsection into full narrative prose
2. Manager reviews for quality and consistency

## Customization

### Adjusting Chapter Structure

Modify the constraints in `ManagerAgent.instruct_writer_for_chapter_outline()`:

```python
constraints = {
    "sections_count": 3,  # Number of sections per chapter
    "subsections_per_section": 2,  # Subsections per section
    "main_points_per_subsection": 3,  # Main points per subsection
}
```

### Changing Review Criteria

Modify `ManagerAgent.review_writer_output()` to adjust:
- Quality thresholds
- Completeness requirements
- Consistency checks

### Adding Custom Agents

See `MULTI_AGENT_README.md` for instructions on adding new agents.

## Troubleshooting

### Issue: "JSON decode error"
**Solution**: The system has fallback text parsing. If this occurs frequently, check your LLM model's JSON generation capability.

### Issue: "Main points are too generic"
**Solution**: The system automatically detects and regenerates placeholder text. If issues persist, check the Writer agent's prompt in `generate_main_points()`.

### Issue: "Chapters not approved after 3 revisions"
**Solution**: This may indicate the LLM needs better instructions. Review the Manager's instruction prompts and adjust as needed.

## Integration with Existing System

The multi-agent system can work alongside the existing book writer:

```python
# Use existing system
from app.book_writer.outline_generator import OutlineGenerator

# Or use new multi-agent system
from app.book_writer.multi_agent_system import MultiAgentBookGenerator
```

Both systems use the same LLM client and can share configuration.

## Next Steps

1. Read `MULTI_AGENT_README.md` for detailed architecture
2. Review the code in `multi_agent_system.py`
3. Experiment with different premises and settings
4. Extend the system with custom agents

## Support

For issues or questions:
1. Check the logs for detailed error messages
2. Review the Manager's feedback in revision requests
3. Adjust prompts in the agent classes if needed

