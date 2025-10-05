"""Prompt templates for brainstorming assistant."""
from typing import List, Dict, Any


SYSTEM_PROMPT = """You are an expert brainstorming assistant. Your role is to:
1. Help expand and refine ideas through creative thinking
2. Identify themes, patterns, and connections between ideas
3. Propose concrete next steps and action items
4. Organize thoughts into clear, actionable structures

Guidelines:
- Be concise and actionable in your responses
- Use bullet points for clarity
- Always suggest tags for categorization
- Provide both conservative and bold variations when expanding ideas
- Focus on practical next steps
- Avoid vague or generic suggestions

Output format:
- Use clear section headers
- Tag ideas with relevant keywords in [brackets]
- Mark action items with verbs (e.g., "Research...", "Draft...", "Contact...")
- Provide 1-3 concrete next steps after each response"""


def build_brainstorm_prompt(user_input: str, context: str = "") -> str:
    """Build a brainstorming prompt.
    
    Args:
        user_input: User's latest input
        context: Recent context from session
        
    Returns:
        Formatted prompt
    """
    parts = []
    
    if context:
        parts.append("## Current Context")
        parts.append(context)
        parts.append("")
    
    parts.append("## User Input")
    parts.append(user_input)
    parts.append("")
    parts.append("## Your Task")
    parts.append("Respond with:")
    parts.append("1. **Idea Expansion**: Provide 2 variations (conservative and bold)")
    parts.append("2. **Tags**: Suggest 2-3 relevant tags [tag1, tag2, tag3]")
    parts.append("3. **Next Steps**: List 1-3 concrete action items")
    parts.append("4. **Connections**: Note any links to previous ideas (if context provided)")
    
    return "\n".join(parts)


def build_clustering_prompt(ideas: List[str]) -> str:
    """Build a prompt for clustering ideas.
    
    Args:
        ideas: List of idea texts
        
    Returns:
        Formatted prompt
    """
    parts = [
        "## Ideas to Cluster",
        ""
    ]
    
    for i, idea in enumerate(ideas, 1):
        parts.append(f"{i}. {idea}")
    
    parts.extend([
        "",
        "## Your Task",
        "Analyze these ideas and:",
        "1. Identify 2-4 thematic clusters",
        "2. Name each cluster clearly",
        "3. Assign ideas to clusters (by number)",
        "4. Suggest tags for each cluster",
        "",
        "Format:",
        "**Cluster Name** [tag1, tag2]",
        "- Ideas: 1, 3, 5",
        "- Description: Brief explanation"
    ])
    
    return "\n".join(parts)


def build_summary_prompt(ideas: List[str], scope: str = "session") -> str:
    """Build a prompt for summarizing ideas.
    
    Args:
        ideas: List of idea texts
        scope: Scope of summary
        
    Returns:
        Formatted prompt
    """
    parts = [
        f"## Ideas to Summarize ({scope})",
        ""
    ]
    
    for i, idea in enumerate(ideas, 1):
        parts.append(f"{i}. {idea}")
    
    parts.extend([
        "",
        "## Your Task",
        "Create a concise summary (2-3 paragraphs) that:",
        "1. Captures the main themes and insights",
        "2. Highlights key ideas and their relationships",
        "3. Notes any emerging patterns or opportunities",
        "4. Suggests overall direction or focus areas"
    ])
    
    return "\n".join(parts)


def build_action_items_prompt(idea: str, context: str = "") -> str:
    """Build a prompt for generating action items.
    
    Args:
        idea: Idea text
        context: Optional context
        
    Returns:
        Formatted prompt
    """
    parts = [
        "## Idea",
        idea,
        ""
    ]
    
    if context:
        parts.append("## Context")
        parts.append(context)
        parts.append("")
    
    parts.extend([
        "## Your Task",
        "Generate 3-5 concrete action items to move this idea forward.",
        "",
        "Requirements:",
        "- Start each with an action verb",
        "- Be specific and measurable",
        "- Order by priority (most important first)",
        "- Include estimated effort (low/medium/high)",
        "",
        "Format:",
        "- [ ] Action item [priority: high] [effort: medium]"
    ])
    
    return "\n".join(parts)


def build_variation_prompt(idea: str, variation_type: str = "both") -> str:
    """Build a prompt for generating idea variations.
    
    Args:
        idea: Original idea
        variation_type: "conservative", "bold", or "both"
        
    Returns:
        Formatted prompt
    """
    parts = [
        "## Original Idea",
        idea,
        "",
        "## Your Task"
    ]
    
    if variation_type in ("conservative", "both"):
        parts.append("**Conservative Variation**: A safer, more practical version")
    
    if variation_type in ("bold", "both"):
        parts.append("**Bold Variation**: An ambitious, innovative version")
    
    parts.extend([
        "",
        "For each variation:",
        "- Explain the key difference",
        "- Note pros and cons",
        "- Suggest relevant tags"
    ])
    
    return "\n".join(parts)


def build_search_prompt(query: str, candidates: List[Dict[str, Any]]) -> str:
    """Build a prompt for semantic search refinement.
    
    Args:
        query: Search query
        candidates: List of candidate ideas with metadata
        
    Returns:
        Formatted prompt
    """
    parts = [
        "## Search Query",
        query,
        "",
        "## Candidate Ideas",
        ""
    ]
    
    for i, candidate in enumerate(candidates, 1):
        idea_text = candidate.get('text', '')
        tags = candidate.get('tags', [])
        tags_str = f" [{', '.join(tags)}]" if tags else ""
        parts.append(f"{i}. {idea_text}{tags_str}")
    
    parts.extend([
        "",
        "## Your Task",
        "Rank these ideas by relevance to the query (1 = most relevant).",
        "Provide brief explanation for top 3 matches.",
        "",
        "Format:",
        "1. Idea #X - Reason",
        "2. Idea #Y - Reason",
        "3. Idea #Z - Reason"
    ])
    
    return "\n".join(parts)


def parse_llm_response(response: str) -> Dict[str, Any]:
    """Parse structured information from LLM response.
    
    Args:
        response: Raw LLM response
        
    Returns:
        Parsed data dictionary
    """
    result: Dict[str, Any] = {
        'raw': response,
        'ideas': [],
        'tags': [],
        'actions': [],
        'clusters': []
    }
    
    lines = response.split('\n')
    current_section = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Detect sections
        lower = line.lower()
        if 'idea' in lower and ('expansion' in lower or 'variation' in lower):
            current_section = 'ideas'
        elif 'tag' in lower:
            current_section = 'tags'
        elif 'action' in lower or 'next step' in lower:
            current_section = 'actions'
        elif 'cluster' in lower:
            current_section = 'clusters'
        
        # Extract tags [tag1, tag2]
        import re
        tag_matches = re.findall(r'\[([^\]]+)\]', line)
        for match in tag_matches:
            tags = [t.strip() for t in match.split(',')]
            result['tags'].extend(tags)
        
        # Extract action items (lines starting with -, *, or checkbox)
        if current_section == 'actions' and (line.startswith('-') or line.startswith('*') or '[ ]' in line):
            # Clean up the action text
            action = line.lstrip('-*[] ').strip()
            if action:
                result['actions'].append(action)
        
        # Extract ideas (bullet points in ideas section)
        if current_section == 'ideas' and (line.startswith('-') or line.startswith('*')):
            idea = line.lstrip('-*[] ').strip()
            if idea and not idea.startswith('**'):  # Skip headers
                result['ideas'].append(idea)
    
    # Deduplicate tags
    result['tags'] = list(set(result['tags']))
    
    return result
