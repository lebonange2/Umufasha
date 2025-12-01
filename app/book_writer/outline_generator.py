"""Generate book outlines using LLM agents."""
import re
from typing import Dict, List
from app.book_writer.agents import BookAgents
from app.book_writer.config import get_config
from app.llm.client import LLMClient


class OutlineGenerator:
    """Generates book outlines from initial prompts."""
    
    def __init__(self, agents: BookAgents, agent_config: Dict):
        self.agents = agents
        self.agent_config = agent_config

    async def _generate_section_content(self, chapter_info: Dict, section_num: int) -> Dict:
        """Generate section content using LLM when missing - creates fully descriptive content."""
        try:
            system_prompt = """You are a story structure expert. Generate specific, detailed section titles, subsection descriptions, and main points for paragraphs. 
            
CRITICAL: Every main point must be a FULL SENTENCE (10+ words) describing what happens in that paragraph. 
Example: "Introduce Daniel, a tired Earth engineer living in a collapsing megacity, who secretly dreams of the stars."
NOT: "Main point for paragraph 1" or "Character introduction"."""
            
            user_prompt = f"""Chapter {chapter_info['chapter_number']}: {chapter_info['title']}

Chapter Details:
{chapter_info.get('prompt', '')}

Generate Section {section_num} with FULLY DESCRIPTIVE content:
- A specific, descriptive section title (e.g., "Leaving Earth" NOT "Section {section_num}")
- 2 subsections with descriptive titles (e.g., "The Offer from Mars" NOT "Subsection X.Y")
- Each subsection must have 3 main points
- Each main point must be a FULL SENTENCE (10+ words) describing what happens in that paragraph
- Base all content on the chapter details above

Return in this format:
Section Title: [specific descriptive title]
Subsection 1: [specific descriptive title]
Main Points:
* Main point for paragraph 1: [full sentence describing what happens]
* Main point for paragraph 2: [full sentence describing what happens]
* Main point for paragraph 3: [full sentence describing what happens]
Subsection 2: [specific descriptive title]
Main Points:
* Main point for paragraph 1: [full sentence describing what happens]
* Main point for paragraph 2: [full sentence describing what happens]
* Main point for paragraph 3: [full sentence describing what happens]"""
            
            response = await self.agents.llm_client.complete(system=system_prompt, user=user_prompt)
            
            # Parse the response
            section_title = None
            subsections = []
            current_subsection = None
            
            for line in response.split('\n'):
                line = line.strip()
                if not line:
                    continue
                
                # Extract section title
                if line.startswith('Section Title:'):
                    section_title = line.replace('Section Title:', '').strip()
                elif line.startswith('Subsection'):
                    if current_subsection:
                        subsections.append(current_subsection)
                    title = line.split(':', 1)[1].strip() if ':' in line else line.replace('Subsection', '').strip()
                    if not title or title.startswith('Subsection'):
                        title = f"Subsection {section_num}.{len(subsections) + 1}"
                    current_subsection = {"title": title, "main_points": []}
                elif line.startswith('*') or line.startswith('-'):
                    if current_subsection:
                        mp = line.lstrip('*-').strip()
                        # Handle format: "Main point for paragraph 1: [sentence]" or just "[sentence]"
                        if ':' in mp and 'main point' in mp.lower():
                            mp = mp.split(':', 1)[1].strip()
                        if mp and len(mp) > 10:  # Must be a full sentence
                            current_subsection["main_points"].append({"text": mp})
            
            if current_subsection:
                subsections.append(current_subsection)
            
            if not section_title or section_title.startswith('Section '):
                # Try to generate a better title
                section_title = f"Section {section_num}"
            
            # Ensure we have subsections with main points
            if not subsections or len(subsections) < 2:
                # Regenerate if incomplete
                subsections = []
                for k in range(2):
                    # Generate subsection content
                    sub_prompt = f"""Generate a subsection for Section {section_num} of Chapter {chapter_info['chapter_number']}: {chapter_info['title']}
                    
Chapter context: {chapter_info.get('prompt', '')[:500]}

Return:
Subsection Title: [specific descriptive title]
Main Points:
* Main point for paragraph 1: [full sentence]
* Main point for paragraph 2: [full sentence]
* Main point for paragraph 3: [full sentence]"""
                    
                    sub_response = await self.agents.llm_client.complete(
                        system="Generate specific subsection content with full sentence main points.",
                        user=sub_prompt
                    )
                    
                    # Parse subsection
                    sub_title = None
                    sub_main_points = []
                    for sub_line in sub_response.split('\n'):
                        sub_line = sub_line.strip()
                        if sub_line.startswith('Subsection Title:'):
                            sub_title = sub_line.split(':', 1)[1].strip()
                        elif (sub_line.startswith('*') or sub_line.startswith('-')) and 'main point' in sub_line.lower():
                            mp = sub_line.lstrip('*-').strip()
                            if ':' in mp:
                                mp = mp.split(':', 1)[1].strip()
                            if mp and len(mp) > 10:
                                sub_main_points.append({"text": mp})
                    
                    if not sub_title:
                        sub_title = f"Subsection {section_num}.{k+1}"
                    if not sub_main_points:
                        sub_main_points = [{"text": f"Main point {k+1}.{m+1}"} for m in range(3)]
                    
                    subsections.append({"title": sub_title, "main_points": sub_main_points})
            
            return {
                "title": section_title,
                "subsections": subsections
            }
        except Exception as e:
            print(f"Error generating section content: {e}")
            # Return default structure with placeholders (will be regenerated)
            return {
                "title": f"Section {section_num}",
                "subsections": [
                    {"title": f"Subsection {section_num}.{k+1}", "main_points": [{"text": f"Main point {k+1}.{m+1}"} for m in range(3)]}
                    for k in range(2)
                ]
            }

    async def generate_outline(self, initial_prompt: str, num_chapters: int = 25) -> List[Dict]:
        """Generate a book outline based on initial prompt."""
        print("\nGenerating outline...")

        try:
            # Step 1: Story Planner
            print("Step 1: Creating story arc...")
            story_arc = await self.agents.story_planner(initial_prompt)
            
            # Step 2: World Builder
            print("Step 2: Building world...")
            world_elements = await self.agents.world_builder(story_arc)
            
            # Step 3: Outline Creator
            print("Step 3: Creating detailed outline...")
            outline_text = await self.agents.outline_creator(initial_prompt, story_arc, world_elements, num_chapters)
            
            # Extract and process the outline
            return await self._process_outline_results(outline_text, num_chapters)
            
        except Exception as e:
            print(f"Error generating outline: {str(e)}")
            # Try to salvage any outline content we can find
            return await self._emergency_outline_processing(outline_text if 'outline_text' in locals() else "", num_chapters)

    async def _process_outline_results(self, outline_content: str, num_chapters: int) -> List[Dict]:
        """Extract and process the outline with strict format requirements."""
        if not outline_content:
            print("No structured outline found, attempting emergency processing...")
            return await self._emergency_outline_processing(outline_content, num_chapters)

        chapters = []
        
        # Extract content between OUTLINE: and END OF OUTLINE
        start_idx = outline_content.find("OUTLINE:")
        end_idx = outline_content.find("END OF OUTLINE")
        
        if start_idx != -1:
            if end_idx != -1:
                outline_content = outline_content[start_idx:end_idx]
            else:
                outline_content = outline_content[start_idx:]
        
        # Split by chapter markers
        chapter_sections = re.split(r'Chapter \d+:', outline_content)
        
        for i, section in enumerate(chapter_sections[1:], 1):  # Skip first empty section
            try:
                # Extract required components
                title_match = re.search(r'\*?\*?Title:\*?\*?\s*(.+?)(?=\n|$)', section, re.IGNORECASE)
                events_match = re.search(r'\*?\*?Key Events:\*?\*?\s*(.*?)(?=\*?\*?Character Developments:|Sections:|$)', section, re.DOTALL | re.IGNORECASE)
                character_match = re.search(r'\*?\*?Character Developments:\*?\*?\s*(.*?)(?=\*?\*?Setting:|Sections:|$)', section, re.DOTALL | re.IGNORECASE)
                setting_match = re.search(r'\*?\*?Setting:\*?\*?\s*(.*?)(?=\*?\*?Tone:|Sections:|$)', section, re.DOTALL | re.IGNORECASE)
                tone_match = re.search(r'\*?\*?Tone:\*?\*?\s*(.*?)(?=\*?\*?Sections:|Chapter \d+:|$)', section, re.DOTALL | re.IGNORECASE)
                sections_match = re.search(r'\*?\*?Sections:\*?\*?\s*(.*?)(?=\*?\*?Chapter \d+:|END OF OUTLINE|$)', section, re.DOTALL | re.IGNORECASE)

                # If no explicit title match, try to get it from the chapter header
                if not title_match:
                    title_match = re.search(r'\*?\*?Chapter \d+:\s*(.+?)(?=\n|$)', section)

                # Verify all required components exist (sections are now mandatory)
                if not all([title_match, events_match, character_match, setting_match, tone_match]):
                    print(f"Missing required components in Chapter {i}")
                    missing = []
                    if not title_match: missing.append("Title")
                    if not events_match: missing.append("Key Events")
                    if not character_match: missing.append("Character Developments")
                    if not setting_match: missing.append("Setting")
                    if not tone_match: missing.append("Tone")
                    print(f"  Missing: {', '.join(missing)}")
                    continue
                
                # Sections are now mandatory - warn if missing
                sections_list = []
                if not sections_match:
                    print(f"WARNING: Chapter {i} is missing Sections. This is required for book generation.")
                    # Create placeholder sections to ensure structure exists
                    sections_list = [
                        {
                            "title": f"Section {j+1}",
                            "subsections": [
                                {
                                    "title": f"Subsection {j+1}.{k+1}",
                                    "main_points": [
                                        {"text": f"Main point {j+1}.{k+1}.{m+1}"} for m in range(3)
                                    ]
                                } for k in range(2)
                            ]
                        } for j in range(3)
                    ]
                else:
                    # Extract sections and subsections with main points
                    sections_text = sections_match.group(1).strip()
                    print(f"DEBUG: Extracting sections from text (length: {len(sections_text)})")
                    
                    # Split by "Section X:" markers - be more flexible with format
                    section_parts = re.split(r'Section\s+\d+\s*:', sections_text, flags=re.IGNORECASE)
                    if len(section_parts) == 1:
                        # Try alternative format
                        section_parts = re.split(r'Section\s+\d+', sections_text, flags=re.IGNORECASE)
                    
                    print(f"DEBUG: Found {len(section_parts) - 1} sections")
                    
                    for section_idx, part in enumerate(section_parts[1:], 1):  # Skip first empty part
                        part = part.strip()
                        if not part:
                            continue
                            
                        lines = part.split('\n')
                        # Extract section title - first non-empty line
                        section_title = None
                        title_line_idx = 0
                        for idx, line in enumerate(lines):
                            line_stripped = line.strip()
                            if line_stripped and not line_stripped.startswith('-') and not line_stripped.startswith('*'):
                                section_title = line_stripped
                                title_line_idx = idx
                                break
                        
                        if not section_title:
                            section_title = f"Section {section_idx}"
                            print(f"WARNING: Could not extract title for Section {section_idx}, using default")
                        
                        subsections = []
                        current_subsection = None
                        
                        # Process remaining lines after title
                        for line in lines[title_line_idx + 1:]:
                            line_stripped = line.strip()
                            
                            # Skip empty lines
                            if not line_stripped:
                                continue
                            
                            # Match subsections like "- Subsection X.Y: description" or "- Subsection X.Y:description"
                            sub_match = re.match(r'-\s*Subsection\s+\d+\.\d+\s*:\s*(.+)', line_stripped, re.IGNORECASE)
                            if sub_match:
                                # Save previous subsection if exists
                                if current_subsection:
                                    subsections.append(current_subsection)
                                
                                # Start new subsection
                                subsection_title = sub_match.group(1).strip()
                                if not subsection_title:
                                    subsection_title = f"Subsection {section_idx}.{len(subsections) + 1}"
                                
                                current_subsection = {
                                    "title": subsection_title,
                                    "main_points": []
                                }
                            # Match "Main Points:" header (optional, can skip)
                            elif line_stripped.lower().startswith('main points'):
                                continue
                            # Match main points like "* [Main point]" or "- [Main point]" or "* Main point for paragraph X: [sentence]"
                            elif current_subsection and (line_stripped.startswith('*') or (line_stripped.startswith('-') and 'Subsection' not in line_stripped.lower())):
                                main_point_match = re.match(r'[*-]\s*(.+)', line_stripped)
                                if main_point_match:
                                    main_point = main_point_match.group(1).strip()
                                    
                                    # Handle format: "Main point for paragraph 1: [full sentence]"
                                    if 'main point for paragraph' in main_point.lower() and ':' in main_point:
                                        # Extract the sentence after the colon
                                        main_point = main_point.split(':', 1)[1].strip()
                                    
                                    # Filter out placeholder text but keep full sentences
                                    if main_point and len(main_point) > 10:  # Must be a full sentence
                                        # Remove brackets if present
                                        main_point = main_point.strip('[]')
                                        if not main_point.startswith('[') and 'placeholder' not in main_point.lower():
                                            # Only skip if it's literally "Main point for paragraph X" without description
                                            if not (main_point.lower().startswith('main point') and len(main_point) < 30):
                                                # Store as object with text property
                                                current_subsection["main_points"].append({"text": main_point})
                                            else:
                                                print(f"DEBUG: Skipping placeholder main point: {main_point}")
                                    elif main_point:
                                        print(f"DEBUG: Skipping short/placeholder main point: {main_point}")
                            
                            # If we hit another section marker, stop processing this section
                            if re.match(r'Section\s+\d+', line_stripped, re.IGNORECASE):
                                break
                        
                        # Don't forget the last subsection
                        if current_subsection:
                            subsections.append(current_subsection)
                        
                        # Ensure section has subsections
                        if not subsections:
                            print(f"WARNING: Section {section_idx} has no subsections, creating defaults")
                            subsections = [
                                {
                                    "title": f"Subsection {section_idx}.{k+1}",
                                    "main_points": [
                                        {"text": f"Main point {k+1}.{m+1}"} for m in range(3)
                                    ]
                                } for k in range(2)
                            ]
                        
                        sections_list.append({
                            "title": section_title,
                            "subsections": subsections
                        })
                        print(f"DEBUG: Added Section {section_idx}: '{section_title}' with {len(subsections)} subsections")
                
                # Format chapter content
                chapter_prompt_parts = [
                    f"- Key Events: {events_match.group(1).strip()}",
                    f"- Character Developments: {character_match.group(1).strip()}",
                    f"- Setting: {setting_match.group(1).strip()}",
                    f"- Tone: {tone_match.group(1).strip()}"
                ]
                
                if sections_list:
                    sections_text_parts = []
                    for sec_idx, sec in enumerate(sections_list, 1):
                        section_text = f"  Section {sec_idx}: {sec['title']}"
                        if sec.get('subsections'):
                            for sub_idx, sub in enumerate(sec['subsections'], 1):
                                section_text += f"\n    - Subsection {sec_idx}.{sub_idx}: {sub.get('title', '')}"
                                if sub.get('main_points'):
                                    section_text += "\n      Main Points:"
                                    for mp_idx, mp in enumerate(sub['main_points'], 1):
                                        # Handle both string and object formats
                                        mp_text = mp.get('text', mp) if isinstance(mp, dict) else mp
                                        section_text += f"\n        * {mp_text}"
                        sections_text_parts.append(section_text)
                    
                    chapter_prompt_parts.append(f"- Sections:\n" + "\n".join(sections_text_parts))
                
                # Ensure sections_list is not empty - generate using LLM if needed
                if not sections_list:
                    print(f"Generating sections for Chapter {i} using LLM as fallback")
                    sections_list = []
                    # We'll generate sections after we have chapter_info, so mark it for later
                    # For now, create temporary structure
                    sections_list = [
                        {
                            "title": f"Section {j+1}",
                            "subsections": [
                                {
                                    "title": f"Subsection {j+1}.{k+1}",
                                    "main_points": [
                                        {"text": f"Main point {j+1}.{k+1}.{m+1}"} for m in range(3)
                                    ]
                                } for k in range(2)
                            ]
                        } for j in range(3)
                    ]
                
                # If sections_list is empty or has placeholder text, generate real content
                needs_regeneration = False
                if not sections_list:
                    needs_regeneration = True
                else:
                    # Check if sections have placeholder text
                    for sec in sections_list:
                        sec_title = sec.get("title", "")
                        if sec_title.startswith("Section ") and len(sec_title) < 15:
                            needs_regeneration = True
                            break
                        for sub in sec.get("subsections", []):
                            sub_title = sub.get("title", "")
                            if sub_title.startswith("Subsection ") or len(sub_title) < 5:
                                needs_regeneration = True
                                break
                            # Check main points - they must be full sentences (10+ words)
                            for mp in sub.get("main_points", []):
                                mp_text = mp.get("text", "") if isinstance(mp, dict) else str(mp)
                                # Check if it's a placeholder or too short
                                if (mp_text.lower().startswith("main point") and len(mp_text) < 30) or len(mp_text) < 10:
                                    needs_regeneration = True
                                    break
                            if needs_regeneration:
                                break
                        if needs_regeneration:
                            break
                
                chapter_info = {
                    "chapter_number": i,
                    "title": title_match.group(1).strip(),
                    "prompt": "\n".join(chapter_prompt_parts),
                    "sections": sections_list
                }
                
                # If we need to regenerate sections, do it now
                if needs_regeneration:
                    print(f"Regenerating sections for Chapter {i} with actual content")
                    chapter_info["sections"] = []
                    for j in range(3):
                        section = await self._generate_section_content(chapter_info, j + 1)
                        chapter_info["sections"].append(section)
                
                # Verify events (at least 3)
                events = re.findall(r'-\s*(.+?)(?=\n|$)', events_match.group(1))
                if len(events) < 3:
                    print(f"Chapter {i} has fewer than 3 events")
                    continue

                chapters.append(chapter_info)

            except Exception as e:
                print(f"Error processing Chapter {i}: {str(e)}")
                continue

        # Post-process: Ensure all chapters have fully descriptive content
        # Check for placeholder text and regenerate if needed
        for chapter in chapters:
            # Check if sections exist
            if not chapter.get("sections") or len(chapter.get("sections", [])) == 0:
                print(f"Generating sections for Chapter {chapter['chapter_number']} using LLM")
                chapter["sections"] = []
                for j in range(3):
                    section = await self._generate_section_content(chapter, j + 1)
                    chapter["sections"].append(section)
            else:
                # Check for placeholder text in existing sections and regenerate if needed
                needs_regeneration = False
                for section in chapter.get("sections", []):
                    # Check section title
                    if not section.get("title") or section["title"].strip() in ["Section 1", "Section 2", "Section 3"] or (section["title"].startswith("Section ") and len(section["title"]) < 15):
                        needs_regeneration = True
                        break
                    
                    # Check subsections
                    for subsection in section.get("subsections", []):
                        # Check subsection title
                        if not subsection.get("title") or subsection["title"].startswith("Subsection "):
                            needs_regeneration = True
                            break
                        
                        # Check main points for placeholder text
                        for mp in subsection.get("main_points", []):
                            mp_text = mp.get("text", "") if isinstance(mp, dict) else str(mp)
                            if "main point for paragraph" in mp_text.lower() or ("main point" in mp_text.lower() and len(mp_text) < 30 and "paragraph" in mp_text.lower()):
                                needs_regeneration = True
                                break
                    
                    if needs_regeneration:
                        break
                
                # Regenerate sections if they have placeholder text
                if needs_regeneration:
                    print(f"Regenerating sections for Chapter {chapter['chapter_number']} - placeholder text detected")
                    chapter["sections"] = []
                    for j in range(3):
                        section = await self._generate_section_content(chapter, j + 1)
                        chapter["sections"].append(section)
                
                # Final pass: Ensure all main points are full sentences (10+ words)
                for section in chapter.get("sections", []):
                    for subsection in section.get("subsections", []):
                        for mp_idx, mp in enumerate(subsection.get("main_points", [])):
                            mp_text = mp.get("text", "") if isinstance(mp, dict) else str(mp)
                            # If main point is too short or is a placeholder, regenerate it
                            if len(mp_text) < 10 or (mp_text.lower().startswith("main point") and len(mp_text) < 30):
                                print(f"Regenerating main point {mp_idx + 1} for Chapter {chapter['chapter_number']}, {section['title']} - {subsection['title']}")
                                # Generate a single main point
                                mp_prompt = f"""Chapter {chapter['chapter_number']}: {chapter['title']}
Section: {section['title']}
Subsection: {subsection['title']}
Chapter Context: {chapter.get('prompt', '')[:500]}

Generate a FULL SENTENCE (10+ words minimum) describing what happens in paragraph {mp_idx + 1} of this subsection.
Make it specific to the story and descriptive.
Return ONLY the sentence, no labels, prefixes, or "Main point for paragraph X:"."""
                                
                                try:
                                    mp_response = await self.agents.llm_client.complete(
                                        system="Generate a full descriptive sentence for a paragraph main point. Return only the sentence.",
                                        user=mp_prompt
                                    )
                                    new_mp = mp_response.strip()
                                    # Clean up response
                                    new_mp = new_mp.lstrip('*-').strip()
                                    if ':' in new_mp and 'main point' in new_mp.lower():
                                        new_mp = new_mp.split(':', 1)[1].strip()
                                    # Remove quotes if present
                                    new_mp = new_mp.strip('"\'')
                                    if len(new_mp) > 10:
                                        if isinstance(mp, dict):
                                            mp["text"] = new_mp
                                        else:
                                            subsection["main_points"][mp_idx] = {"text": new_mp}
                                    else:
                                        print(f"Warning: Generated main point too short: {new_mp}")
                                except Exception as e:
                                    print(f"Error regenerating main point: {e}")
                # Update prompt to include sections
                if "- Sections:" not in chapter["prompt"]:
                    sections_text = "\n".join([
                        f"  Section {j+1}: {sec['title']}" + 
                        "\n    " + "\n    ".join([
                            f"- Subsection {j+1}.{k+1}: {sub['title']}\n      Main Points:\n        " +
                            "\n        ".join([f"* {mp.get('text', mp) if isinstance(mp, dict) else mp}" for mp in sub['main_points']])
                            for k, sub in enumerate(sec['subsections'])
                        ])
                        for j, sec in enumerate(chapter["sections"])
                    ])
                    chapter["prompt"] += f"\n- Sections:\n{sections_text}"

        # If we don't have enough valid chapters, create placeholders
        if len(chapters) < num_chapters:
            print(f"Only processed {len(chapters)} valid chapters, creating placeholders for remaining...")
            chapters = await self._verify_chapter_sequence(chapters, num_chapters)

        return chapters

    async def _verify_chapter_sequence(self, chapters: List[Dict], num_chapters: int) -> List[Dict]:
        """Verify and fix chapter numbering."""
        # Sort chapters by their current number
        chapters.sort(key=lambda x: x['chapter_number'])
        
        # Renumber chapters sequentially starting from 1
        for i, chapter in enumerate(chapters, 1):
            chapter['chapter_number'] = i
        
        # Add placeholder chapters if needed (with sections)
        while len(chapters) < num_chapters:
            next_num = len(chapters) + 1
            sections = [
                {
                    "title": f"Section {j+1}",
                    "subsections": [
                        {
                            "title": f"Subsection {j+1}.{k+1}",
                            "main_points": [
                                {"text": f"Main point for paragraph {m+1}"} for m in range(3)
                            ]
                        } for k in range(2)
                    ]
                } for j in range(3)
            ]
            sections_text = "\n".join([
                f"  Section {j+1}: {sec['title']}" + 
                "\n    " + "\n    ".join([
                    f"- Subsection {j+1}.{k+1}: {sub['title']}\n      Main Points:\n        " +
                    "\n        ".join([f"* {mp.get('text', mp) if isinstance(mp, dict) else mp}" for mp in sub['main_points']])
                    for k, sub in enumerate(sec['subsections'])
                ])
                for j, sec in enumerate(sections)
            ])
            chapters.append({
                'chapter_number': next_num,
                'title': f'Chapter {next_num}',
                'prompt': '- Key events: [To be determined]\n- Character developments: [To be determined]\n- Setting: [To be determined]\n- Tone: [To be determined]\n- Sections:\n' + sections_text,
                'sections': sections
            })
        
        # Trim excess chapters if needed
        chapters = chapters[:num_chapters]
        
        return chapters

    async def _emergency_outline_processing(self, outline_content: str, num_chapters: int) -> List[Dict]:
        """Emergency processing when normal outline extraction fails."""
        print("Attempting emergency outline processing...")
        
        chapters = []
        current_chapter = None
        
        # Look through content for any chapter markers
        lines = outline_content.split('\n')
        
        for line in lines:
            # Look for chapter markers
            chapter_match = re.search(r'Chapter (\d+)', line)
            if chapter_match and "Key events:" in outline_content:
                if current_chapter:
                    chapters.append(current_chapter)
                
                current_chapter = {
                    'chapter_number': int(chapter_match.group(1)),
                    'title': line.split(':')[-1].strip() if ':' in line else f"Chapter {chapter_match.group(1)}",
                    'prompt': []
                }
            
            # Collect bullet points
            if current_chapter and line.strip().startswith('-'):
                current_chapter['prompt'].append(line.strip())
        
        # Add the last chapter if it exists
        if current_chapter and current_chapter.get('prompt'):
            current_chapter['prompt'] = '\n'.join(current_chapter['prompt'])
            chapters.append(current_chapter)
        
        if not chapters:
            print("Emergency processing failed to find any chapters")
            # Create a basic outline structure with sections
            chapters = []
            for i in range(1, num_chapters + 1):
                sections = [
                    {
                        "title": f"Section {j+1}",
                        "subsections": [
                            {
                                "title": f"Subsection {j+1}.{k+1}",
                                "main_points": [
                                    {"text": f"Main point for paragraph {m+1}"} for m in range(3)
                                ]
                            } for k in range(2)
                        ]
                    } for j in range(3)
                ]
                sections_text = "\n".join([
                    f"  Section {j+1}: {sec['title']}" + 
                    "\n    " + "\n    ".join([
                        f"- Subsection {j+1}.{k+1}: {sub['title']}\n      Main Points:\n        " +
                        "\n        ".join([f"* {mp.get('text', mp) if isinstance(mp, dict) else mp}" for mp in sub['main_points']])
                        for k, sub in enumerate(sec['subsections'])
                    ])
                    for j, sec in enumerate(sections)
                ])
                chapters.append({
                    'chapter_number': i,
                    'title': f'Chapter {i}',
                    'prompt': '- Key events: [To be determined]\n- Character developments: [To be determined]\n- Setting: [To be determined]\n- Tone: [To be determined]\n- Sections:\n' + sections_text,
                    'sections': sections
                })
        
        # Ensure proper sequence and number of chapters
        return await self._verify_chapter_sequence(chapters, num_chapters)

