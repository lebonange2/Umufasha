"""
Example usage of the Multi-Agent Book Generation System.

This script demonstrates how to use the system programmatically.
"""

import asyncio
from app.book_writer.multi_agent_system import MultiAgentBookGenerator


async def example_mars_story():
    """Example: Generate outline for the Mars story."""
    print("=" * 60)
    print("Example: Mars Story Outline Generation")
    print("=" * 60)
    print()
    
    generator = MultiAgentBookGenerator(
        title="Exile to Mars",
        premise="A man from Earth goes to live on Mars where there is an advanced civilization.",
        num_chapters=3,  # Short example
        tone="narrative",
        style="third person"
    )
    
    # Generate outline only
    result = await generator.generate_book(generate_prose=False)
    
    # Export to markdown
    output_file = "exile_to_mars_example.md"
    generator.export_to_markdown(output_file, include_prose=False)
    
    print(f"\n✓ Example complete!")
    print(f"  Output saved to: {output_file}")
    print(f"  Chapters generated: {result['total_chapters']}")
    
    # Print first chapter structure
    if result['outline']:
        chapter = result['outline'][0]
        print(f"\nFirst Chapter Preview:")
        print(f"  Title: {chapter['title']}")
        print(f"  Sections: {len(chapter.get('sections', []))}")
        for section in chapter.get('sections', []):
            print(f"    - {section['title']}")
            for subsection in section.get('subsections', []):
                print(f"      - {subsection['title']}")
                print(f"        Main points: {len(subsection.get('main_points', []))}")


async def example_with_prose():
    """Example: Generate outline with full prose."""
    print("\n" + "=" * 60)
    print("Example: Full Prose Generation")
    print("=" * 60)
    print()
    
    generator = MultiAgentBookGenerator(
        title="The Time Traveler's Journal",
        premise="A historian discovers a journal that allows them to witness historical events firsthand, but changing anything has dire consequences.",
        num_chapters=2,  # Short example
        tone="mysterious",
        style="first person"
    )
    
    # Generate with prose
    result = await generator.generate_book(generate_prose=True)
    
    # Export with prose
    output_file = "time_traveler_full.md"
    generator.export_to_markdown(output_file, include_prose=True)
    
    print(f"\n✓ Example complete!")
    print(f"  Output saved to: {output_file}")
    print(f"  Chapters generated: {result['total_chapters']}")


async def example_custom_settings():
    """Example: Custom settings and structure."""
    print("\n" + "=" * 60)
    print("Example: Custom Settings")
    print("=" * 60)
    print()
    
    generator = MultiAgentBookGenerator(
        title="The Last Library",
        premise="In a world where all books are digital, a librarian discovers the last physical library hidden beneath the city.",
        num_chapters=5,
        tone="nostalgic",
        style="third person limited"
    )
    
    result = await generator.generate_book(generate_prose=False)
    
    output_file = "last_library_custom.md"
    generator.export_to_markdown(output_file, include_prose=False)
    
    print(f"\n✓ Example complete!")
    print(f"  Output saved to: {output_file}")
    print(f"  Story Arc:")
    for phase, description in result['story_arc'].items():
        print(f"    {phase.capitalize()}: {description[:100]}...")


async def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("Multi-Agent Book Generation System - Examples")
    print("=" * 60)
    print("\nNote: These examples will make LLM API calls.")
    print("Make sure your LLM service is running.\n")
    
    # Run examples
    await example_mars_story()
    # Uncomment to run other examples:
    # await example_with_prose()
    # await example_custom_settings()
    
    print("\n" + "=" * 60)
    print("All examples complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

