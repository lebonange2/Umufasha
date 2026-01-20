"""
Exam Generator - Multi-Agent Exam Creation System

This module implements an exam generation system using the Book Publishing House
multi-agent architecture to generate high-quality multiple choice questions from
input text files. The system includes rigorous validation with AI agents taking
the exam repeatedly to ensure correctness.
"""

from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import json
import asyncio
import re
from pathlib import Path
from app.llm.client import LLMClient
from app.book_writer.config import get_config


class ExamPhase(Enum):
    """Exam generation phases."""
    CONTENT_ANALYSIS = "content_analysis"
    PROBLEM_GENERATION = "problem_generation"
    VALIDATION = "validation"
    FINAL_REVIEW = "final_review"
    COMPLETE = "complete"


@dataclass
class ExamProblem:
    """Represents a single exam problem."""
    problem_number: int
    question: str
    choices: Dict[str, str]  # {"A": "choice text", "B": "choice text", ...}
    correct_answer: str  # "A", "B", "C", or "D"
    explanation: str
    topic: str
    difficulty: str  # "easy", "medium", "hard"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "problem_number": self.problem_number,
            "question": self.question,
            "choices": self.choices,
            "correct_answer": self.correct_answer,
            "explanation": self.explanation,
            "topic": self.topic,
            "difficulty": self.difficulty
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExamProblem":
        """Create from dictionary."""
        return cls(
            problem_number=data["problem_number"],
            question=data["question"],
            choices=data["choices"],
            correct_answer=data["correct_answer"],
            explanation=data["explanation"],
            topic=data.get("topic", ""),
            difficulty=data.get("difficulty", "medium")
        )


@dataclass
class ExamProject:
    """Complete exam project state."""
    project_id: str
    input_file_path: str
    input_content: str
    output_directory: str = "exam_outputs"
    
    # Phase outputs
    content_analysis: Optional[Dict[str, Any]] = None
    problems: List[ExamProblem] = field(default_factory=list)
    validation_results: List[Dict[str, Any]] = field(default_factory=list)
    final_review: Optional[Dict[str, Any]] = None
    
    # Metadata
    current_phase: ExamPhase = ExamPhase.CONTENT_ANALYSIS
    status: str = "in_progress"
    num_problems: int = 10
    validation_iterations: int = 3


class BaseAgent:
    """Base class for all exam generator agents."""
    
    def __init__(self, name: str, role: str, llm_client: LLMClient):
        self.name = name
        self.role = role
        self.llm_client = llm_client
    
    async def execute_task(self, task: str, context: Dict[str, Any]) -> Any:
        """Execute a task using LLM."""
        system_prompt = f"""You are {self.name}, {self.role} in an exam generation system.
Your role is to {self.role.lower()}."""
        
        user_prompt = f"""Task: {task}

Context:
{json.dumps(context, indent=2)}

Please provide your response in a clear, structured format."""
        
        response = await self.llm_client.complete(system=system_prompt, user=user_prompt)
        return response


class ContentAnalystAgent(BaseAgent):
    """Analyzes input content and identifies key topics for exam generation."""
    
    def __init__(self, llm_client: LLMClient):
        super().__init__("Content Analyst", "Content Analysis Specialist", llm_client)
    
    def _extract_learning_objectives(self, content: str) -> List[str]:
        """Extract learning objectives from the content text."""
        objectives = []
        # Pattern to match numbered learning objectives (e.g., 1.1.1.1, 1.1.1.2, etc.)
        # Must have at least 3 dots (4 numbers) to be a learning objective, not a section header
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            # Match patterns like "1.1.1.1 Objective text" or "1.1.1.1. Objective text"
            # Require at least 4 numbers separated by dots (e.g., 1.1.1.1)
            if re.match(r'^\d+\.\d+\.\d+\.\d+', line):
                # Extract the objective text (everything after the number)
                objective_text = re.sub(r'^\d+(\.\d+)+\.?\s*', '', line).strip()
                if objective_text:
                    objectives.append(objective_text)
        return objectives
    
    async def analyze_content(self, content: str) -> Dict[str, Any]:
        """Analyze the input content and identify key topics and learning objectives."""
        # Extract learning objectives first
        learning_objectives = self._extract_learning_objectives(content)
        
        system_prompt = """You are a Content Analyst specializing in educational content analysis.
Your task is to analyze text content and identify:
1. Key topics and concepts
2. Learning objectives (numbered items like 1.1.1.1, 1.1.1.2, etc.)
3. Important facts and details
4. Relationships between concepts
5. Difficulty levels of different topics
6. Suitable question types for each topic

Provide a structured analysis that will guide problem generation."""
        
        user_prompt = f"""Analyze the following content and provide a comprehensive analysis:

{content}

IMPORTANT: The content contains learning objectives (numbered items). You MUST identify ALL learning objectives and ensure problems are generated for EACH one.

Provide your analysis in JSON format with the following structure:
{{
    "learning_objectives": [
        {{"number": "1.1.1.1", "objective": "Evaluate square roots and nth roots"}},
        {{"number": "1.1.1.2", "objective": "Simplify radical expressions"}},
        ...
    ],
    "key_topics": ["topic1", "topic2", ...],
    "important_concepts": ["concept1", "concept2", ...],
    "factual_information": ["fact1", "fact2", ...],
    "concept_relationships": [{{"concept1": "relates to", "concept2": "..."}}],
    "difficulty_assessment": {{
        "easy_topics": ["topic1", ...],
        "medium_topics": ["topic2", ...],
        "hard_topics": ["topic3", ...]
    }},
    "recommended_question_count": {{
        "easy": <number>,
        "medium": <number>,
        "hard": <number>
    }}
}}"""
        
        response = await self.llm_client.complete(system=system_prompt, user=user_prompt)
        
        # Try to extract JSON from response
        analysis = None
        
        # Method 1: Try parsing the entire response
        try:
            analysis = json.loads(response.strip())
        except:
            pass
        
        # Method 2: Extract JSON with balanced braces
        if not analysis:
            start_idx = response.find('{')
            if start_idx != -1:
                brace_count = 0
                end_idx = start_idx
                for i in range(start_idx, len(response)):
                    if response[i] == '{':
                        brace_count += 1
                    elif response[i] == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end_idx = i + 1
                            break
                
                if brace_count == 0:
                    try:
                        json_str = response[start_idx:end_idx]
                        analysis = json.loads(json_str)
                    except:
                        pass
        
        # Method 3: Try extracting from markdown code blocks
        if not analysis:
            code_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if code_block_match:
                try:
                    analysis = json.loads(code_block_match.group(1))
                except:
                    pass
        
        # Fallback: create basic structure if JSON extraction failed
        if not analysis:
            import structlog
            logger = structlog.get_logger(__name__)
            logger.warning("Could not extract JSON from content analysis response, using fallback structure")
            analysis = {
                "learning_objectives": [{"number": str(i+1), "objective": obj} for i, obj in enumerate(learning_objectives)],
                "key_topics": [],
                "important_concepts": [],
                "factual_information": [],
                "concept_relationships": [],
                "difficulty_assessment": {
                    "easy_topics": [],
                    "medium_topics": [],
                    "hard_topics": []
                },
                "recommended_question_count": {
                    "easy": 3,
                    "medium": 4,
                    "hard": 3
                }
            }
        else:
            # Ensure learning_objectives are included even if LLM didn't extract them
            if "learning_objectives" not in analysis or not analysis.get("learning_objectives"):
                analysis["learning_objectives"] = [{"number": str(i+1), "objective": obj} for i, obj in enumerate(learning_objectives)]
        
        return analysis


class ProblemGeneratorAgent(BaseAgent):
    """Generates multiple choice problems from analyzed content."""
    
    def __init__(self, llm_client: LLMClient):
        super().__init__("Problem Generator", "Exam Problem Creator", llm_client)
    
    def _try_fix_json(self, response: str) -> Optional[str]:
        """Try to fix common JSON issues like unterminated strings by extracting complete problem objects."""
        try:
            import structlog
            logger = structlog.get_logger(__name__)
            
            # Strategy: Extract all complete problem objects we can find
            problems_found = []
            
            # Look for problem objects - they start with "problem_number"
            # Use a more flexible pattern to find problem objects
            pattern = r'\{\s*"problem_number"\s*:\s*\d+.*?"correct_answer"\s*:\s*"[ABCD]".*?\}'
            matches = list(re.finditer(pattern, response, re.DOTALL))
            
            for match in matches:
                problem_str = match.group(0)
                # Ensure it's properly closed
                if not problem_str.rstrip().endswith('}'):
                    # Try to close it
                    problem_str = problem_str.rstrip().rstrip(',') + '}'
                
                try:
                    problem_obj = json.loads(problem_str)
                    if isinstance(problem_obj, dict):
                        # Validate it has required fields
                        if "question" in problem_obj and "choices" in problem_obj and "correct_answer" in problem_obj:
                            problems_found.append(problem_obj)
                except:
                    # Try to extract fields manually if JSON parsing fails
                    try:
                        # Extract key fields using regex
                        question_match = re.search(r'"question"\s*:\s*"([^"]*)"', problem_str)
                        correct_match = re.search(r'"correct_answer"\s*:\s*"([ABCD])"', problem_str)
                        
                        if question_match and correct_match:
                            # Try to extract choices
                            choices_match = re.search(r'"choices"\s*:\s*\{([^}]*)\}', problem_str, re.DOTALL)
                            if choices_match:
                                problems_found.append({
                                    "problem_number": len(problems_found) + 1,
                                    "question": question_match.group(1),
                                    "choices": {"A": "", "B": "", "C": "", "D": ""},  # Placeholder
                                    "correct_answer": correct_match.group(1),
                                    "explanation": "",
                                    "topic": "",
                                    "difficulty": "medium"
                                })
                    except:
                        continue
            
            if len(problems_found) > 0:
                logger.info(f"Extracted {len(problems_found)} complete problems from truncated JSON")
                return json.dumps({"problems": problems_found}, indent=2)
        except Exception as e:
            import structlog
            logger = structlog.get_logger(__name__)
            logger.debug(f"Error in _try_fix_json: {e}")
        
        return None
    
    async def generate_problems_for_objective(self, content: str, analysis: Dict[str, Any], 
                                            objective: Dict[str, Any], num_problems: int) -> List[ExamProblem]:
        """Generate problems for a specific learning objective."""
        import structlog
        logger = structlog.get_logger(__name__)
        
        objective_text = objective.get("objective", str(objective))
        objective_number = objective.get("number", "")
        
        system_prompt = """You are a Problem Generator specializing in creating high-quality multiple choice exam questions.
Your task is to generate questions that:
1. Have exactly ONE correct answer
2. Have 4 answer choices (A, B, C, D)
3. Include plausible distractors (wrong answers that seem reasonable)
4. Test understanding, not just memorization
5. Are clear and unambiguous
6. Include appropriate difficulty levels

CRITICAL: Each question must have exactly ONE correct answer. All other choices must be clearly incorrect.

LATEX FORMATTING REQUIREMENTS:
- Use LaTeX syntax for ALL mathematical expressions, formulas, equations, and symbols
- Use \\( and \\) for inline math (e.g., \\(x^2 + 3x - 4\\))
- Use \\[ and \\] for display math (e.g., \\[\\frac{a}{b}\\])
- Common LaTeX symbols:
  * Fractions: \\frac{numerator}{denominator} (e.g., \\frac{3}{\\sqrt{7} - 1})
  * Square roots: \\sqrt{expression} (e.g., \\sqrt{25} or \\sqrt{x + 1})
  * Powers: ^{exponent} (e.g., x^2, a^{n+1})
  * Subscripts: _{subscript} (e.g., x_1, a_n)
  * Greek letters: \\alpha, \\beta, \\gamma, \\theta, \\pi, etc.
  * Operators: \\times, \\div, \\pm, \\mp, \\leq, \\geq, \\neq, \\approx
  * Sets: \\in, \\notin, \\subset, \\cup, \\cap
  * Other: \\infty, \\sum, \\prod, \\int, \\lim
- Always use LaTeX for mathematical notation - never use plain text for math

You MUST respond with valid JSON only. Do not include any text before or after the JSON."""
        
        # Use more content (up to 5000 chars) for better context
        content_preview = content[:5000] if len(content) > 5000 else content
        if len(content) > 5000:
            content_preview += "\n\n[Content truncated for brevity - use the key concepts shown above]"
        
        user_prompt = f"""Generate exactly {num_problems} multiple choice questions SPECIFICALLY for this learning objective:

LEARNING OBJECTIVE: {objective_number} - {objective_text}

Content:
{content_preview}

Analysis:
{json.dumps(analysis, indent=2)}

IMPORTANT: All {num_problems} questions MUST be directly related to the learning objective: "{objective_text}"

You MUST respond with ONLY valid JSON in this exact format (no markdown, no code blocks, just pure JSON):
{{
    "problems": [
        {{
            "problem_number": 1,
            "question": "Question text with LaTeX? For example: To rationalize the denominator of \\(\\frac{{3}}{{\\sqrt{{7}} - 1}}\\), what conjugate should be used?",
            "choices": {{
                "A": "First choice with LaTeX: \\(\\sqrt{{7}} + 1\\)",
                "B": "Second choice with LaTeX: \\(\\sqrt{{7}} - 1\\)",
                "C": "Third choice with LaTeX: \\(7 + \\sqrt{{1}}\\)",
                "D": "Fourth choice with LaTeX: \\(7 - \\sqrt{{1}}\\)"
            }},
            "correct_answer": "A",
            "explanation": "To rationalize the denominator \\(\\sqrt{{7}} - 1\\), we multiply both numerator and denominator by the conjugate \\(\\sqrt{{7}} + 1\\). The conjugate of a binomial \\(a - b\\) is \\(a + b\\). When we multiply \\((\\sqrt{{7}} - 1)(\\sqrt{{7}} + 1)\\), we get \\(7 - 1 = 6\\), which eliminates the radical from the denominator. Therefore, the conjugate \\(\\sqrt{{7}} + 1\\) (choice A) is correct. Choice B is the original denominator, not the conjugate. Choices C and D are incorrect as they don't follow the conjugate pattern.",
            "topic": "{objective_text}",
            "difficulty": "easy"
        }}
    ]
}}

IMPORTANT LATEX EXAMPLES:
- Fractions: \\(\\frac{{a}}{{b}}\\), \\(\\frac{{3x + 2}}{{x - 1}}\\)
- Square roots: \\(\\sqrt{{x}}\\), \\(\\sqrt{{x^2 + 1}}\\)
- Powers: \\(x^2\\), \\(a^{{n+1}}\\)
- Complex expressions: \\(\\frac{{3}}{{\\sqrt{{7}} - 1}}\\), \\(\\sqrt{{\\frac{{a}}{{b}}}}\\)
- Always escape curly braces in JSON strings by doubling them: {{ and }}

CRITICAL REQUIREMENTS:
- Generate exactly {num_problems} problems
- Each problem must be directly related to: {objective_text}
- Each problem must have exactly 4 choices (A, B, C, D)
- Each problem must have exactly ONE correct answer
- The correct_answer must be one of: A, B, C, or D
- Respond with ONLY the JSON object, no other text"""
        
        # Retry logic - try up to 3 times
        max_retries = 3
        problems = []
        
        for attempt in range(max_retries):
            try:
                response = await self.llm_client.complete(system=system_prompt, user=user_prompt)
                logger.info(f"Problem generation attempt {attempt + 1} for objective '{objective_text}'", response_length=len(response))
                
                # Check if response is empty
                if not response or len(response.strip()) == 0:
                    logger.warning(f"Empty response from LLM (attempt {attempt + 1})")
                    if attempt < max_retries - 1:
                        # Increase wait time with each retry
                        wait_time = 2 * (attempt + 1)
                        logger.info(f"Waiting {wait_time} seconds before retry...")
                        await asyncio.sleep(wait_time)
                    continue
                
                # Extract problems from response (same extraction logic as before)
                json_data = None
                
                # Method 1: Try parsing the entire response (cleanest)
                try:
                    json_data = json.loads(response.strip())
                    logger.info(f"Successfully parsed JSON using method 1 (full response)")
                except json.JSONDecodeError as e:
                    logger.debug(f"Method 1 failed: {e}")
                    # Try to fix common JSON issues and retry
                    if "Unterminated string" in str(e) or "Expecting" in str(e) or "Invalid" in str(e):
                        try:
                            # Try to fix unterminated strings by finding the JSON object boundaries
                            fixed_response = self._try_fix_json(response)
                            if fixed_response:
                                json_data = json.loads(fixed_response)
                                logger.info(f"Successfully parsed JSON using method 1 after fixing")
                        except Exception as fix_error:
                            logger.debug(f"Failed to fix JSON: {fix_error}")
                            pass
                except Exception as e:
                    logger.debug(f"Method 1 failed with non-JSON error: {e}")
                    pass
                
                # Method 2: Look for JSON object with balanced braces (handles nested structures)
                if not json_data:
                    # Find the first { and then find the matching closing }
                    start_idx = response.find('{')
                    if start_idx != -1:
                        brace_count = 0
                        end_idx = start_idx
                        for i in range(start_idx, len(response)):
                            if response[i] == '{':
                                brace_count += 1
                            elif response[i] == '}':
                                brace_count -= 1
                                if brace_count == 0:
                                    end_idx = i + 1
                                    break
                        
                        if brace_count == 0:
                            try:
                                json_str = response[start_idx:end_idx]
                                json_data = json.loads(json_str)
                                logger.info(f"Successfully parsed JSON using method 2 (balanced braces), length={len(json_str)}")
                            except Exception as e:
                                logger.debug(f"Method 2 failed: {e}, json_str preview: {json_str[:200] if len(json_str) > 200 else json_str}")
                                pass
                
                # Method 3: Look for JSON in code blocks (markdown)
                if not json_data:
                    # Try to extract from markdown code blocks
                    code_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
                    if code_block_match:
                        try:
                            json_data = json.loads(code_block_match.group(1))
                            logger.info(f"Successfully parsed JSON using method 3 (code block)")
                        except Exception as e:
                            logger.debug(f"Method 3 failed: {e}")
                            pass
                
                # Method 4: Look for JSON object with "problems" key (more permissive)
                if not json_data:
                    # Find JSON object containing "problems"
                    json_match = re.search(r'\{[^{]*"problems"\s*:\s*\[', response, re.DOTALL)
                    if json_match:
                        start_idx = json_match.start()
                        # Find matching closing brace
                        brace_count = 0
                        end_idx = start_idx
                        for i in range(start_idx, len(response)):
                            if response[i] == '{':
                                brace_count += 1
                            elif response[i] == '}':
                                brace_count -= 1
                                if brace_count == 0:
                                    end_idx = i + 1
                                    break
                        
                        if brace_count == 0:
                            try:
                                json_str = response[start_idx:end_idx]
                                json_data = json.loads(json_str)
                            except Exception as e:
                                logger.debug(f"Failed to parse JSON from method 4: {e}")
                                pass
                
                # Method 5: Try to extract just the problems array and wrap it
                if not json_data:
                    # Find the problems array directly - be more specific to avoid math expressions
                    array_match = re.search(r'"problems"\s*:\s*\[', response, re.DOTALL)
                    if array_match:
                        # Find the start of the array (must be right after "problems":)
                        array_start = response.find('[', array_match.end())
                        if array_start != -1 and array_start - array_match.end() < 10:  # Ensure it's close (not a math expr)
                            # Find matching closing bracket (handle nested structures)
                            bracket_count = 0
                            array_end = array_start
                            in_string = False
                            escape_next = False
                            brace_count = 0  # Track braces inside array
                            
                            for i in range(array_start, len(response)):
                                char = response[i]
                                
                                if escape_next:
                                    escape_next = False
                                    continue
                                
                                if char == '\\':
                                    escape_next = True
                                    continue
                                
                                if char == '"' and not escape_next:
                                    in_string = not in_string
                                    continue
                                
                                if not in_string:
                                    if char == '[':
                                        bracket_count += 1
                                    elif char == ']':
                                        bracket_count -= 1
                                        if bracket_count == 0:
                                            array_end = i + 1
                                            break
                                    elif char == '{':
                                        brace_count += 1
                                    elif char == '}':
                                        brace_count -= 1
                            
                            if bracket_count == 0:
                                try:
                                    array_str = response[array_start:array_end]
                                    # Validate it looks like JSON (starts with [ and contains {)
                                    if array_str.startswith('[') and '{' in array_str:
                                        problems_list = json.loads(array_str)
                                        
                                        # Validate that we got a list of dictionaries
                                        if isinstance(problems_list, list) and len(problems_list) > 0:
                                            # Check if first element is a dict (problem object)
                                            if isinstance(problems_list[0], dict):
                                                # Wrap in expected format
                                                json_data = {"problems": problems_list}
                                                logger.info(f"Successfully extracted {len(problems_list)} problems using method 5")
                                            else:
                                                logger.warning(f"Method 5 extracted array but first element is not a dict: {type(problems_list[0])}")
                                        else:
                                            logger.warning(f"Method 5 extracted invalid array: {problems_list}")
                                except Exception as e:
                                    logger.debug(f"Failed to parse problems array: {e}, array_str preview: {array_str[:200] if 'array_str' in locals() else 'N/A'}")
                                    pass
                
                # Method 6: Try to extract partial problems from truncated JSON
                if not json_data:
                    # Look for complete problem objects even if the JSON is truncated
                    problems_found = []
                    # Find all problem objects using regex
                    problem_pattern = r'\{\s*"problem_number"\s*:\s*\d+[^}]*"correct_answer"\s*:\s*"[ABCD]"[^}]*\}'
                    matches = re.finditer(problem_pattern, response, re.DOTALL)
                    
                    for match in matches:
                        try:
                            problem_str = match.group(0)
                            # Try to close the object if needed
                            if not problem_str.endswith('}'):
                                # Find the last complete field before truncation
                                # Look for the last "correct_answer" field
                                last_correct = problem_str.rfind('"correct_answer"')
                                if last_correct != -1:
                                    # Find the closing quote and value
                                    value_start = problem_str.find(':', last_correct) + 1
                                    value_end = problem_str.find(',', value_start)
                                    if value_end == -1:
                                        value_end = problem_str.find('}', value_start)
                                    if value_end != -1:
                                        # Close the object
                                        problem_str = problem_str[:value_end] + '}'
                            
                            problem_obj = json.loads(problem_str)
                            if isinstance(problem_obj, dict) and "question" in problem_obj and "choices" in problem_obj:
                                problems_found.append(problem_obj)
                        except:
                            continue
                    
                    if len(problems_found) > 0:
                        json_data = {"problems": problems_found}
                        logger.info(f"Successfully extracted {len(problems_found)} partial problems using method 6")
                
                if json_data:
                    problem_list = json_data.get("problems", [])
                    logger.info(f"Extracted {len(problem_list)} problems from JSON")
                    
                    # Validate that problem_list is actually a list of dictionaries
                    if not isinstance(problem_list, list):
                        logger.error(f"Expected list but got {type(problem_list)}: {problem_list}")
                        problem_list = []
                    else:
                        # Filter out non-dict items
                        valid_problems = [p for p in problem_list if isinstance(p, dict)]
                        if len(valid_problems) != len(problem_list):
                            logger.warning(f"Filtered out {len(problem_list) - len(valid_problems)} non-dict items from problem list")
                            problem_list = valid_problems
                    
                    for i, p in enumerate(problem_list, 1):
                        try:
                            # Ensure p is a dictionary
                            if not isinstance(p, dict):
                                logger.warning(f"Problem {i} is not a dictionary (type: {type(p)}), skipping")
                                continue
                            
                            # Validate required fields
                            if not p.get("question") or not p.get("choices"):
                                logger.warning(f"Problem {i} missing required fields, skipping")
                                continue
                            
                            problem = ExamProblem(
                                problem_number=len(problems) + 1,
                                question=p.get("question", "").strip(),
                                choices=p.get("choices", {}),
                                correct_answer=p.get("correct_answer", "A").strip().upper(),
                                explanation=p.get("explanation", "").strip(),
                                topic=p.get("topic", objective_text).strip(),
                                difficulty=p.get("difficulty", "medium").strip().lower()
                            )
                            
                            # Validate problem structure
                            if not problem.question:
                                logger.warning(f"Problem {i} has empty question, skipping")
                                continue
                            
                            if len(problem.choices) != 4:
                                logger.warning(f"Problem {i} has {len(problem.choices)} choices (expected 4), skipping")
                                continue
                            
                            if problem.correct_answer not in problem.choices:
                                logger.warning(f"Problem {i} has invalid correct_answer {problem.correct_answer}, skipping")
                                continue
                            
                            problems.append(problem)
                            logger.info(f"Added problem {problem.problem_number}: {problem.question[:50]}...")
                        except Exception as e:
                            logger.warning(f"Error creating problem {i}: {e}")
                            continue
                    
                    # If we got enough problems, break
                    if len(problems) >= num_problems:
                        problems = problems[:num_problems]  # Trim to exact number
                        logger.info(f"Successfully generated {len(problems)} problems for objective '{objective_text}', stopping retries")
                        break
                    elif len(problems) > 0:
                        # Got some problems but not enough - keep them and continue to next attempt
                        logger.warning(f"Only generated {len(problems)}/{num_problems} problems so far for objective '{objective_text}', continuing to accumulate...")
                        # Don't clear problems - accumulate across attempts
                else:
                    logger.warning(f"Could not extract JSON from response (attempt {attempt + 1})")
                    # Log more of the response for debugging
                    preview_length = min(1000, len(response))
                    logger.debug(f"Response preview (first {preview_length} chars): {response[:preview_length]}")
                    # Also try to find where JSON might start
                    json_start = response.find('{')
                    if json_start != -1:
                        logger.debug(f"Found '{{' at position {json_start}, showing context: {response[max(0, json_start-50):min(len(response), json_start+500)]}")
            
            except Exception as e:
                logger.error(f"Error generating problems (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)  # Wait before retry
        
        if not problems:
            logger.error(f"Failed to generate any problems for objective '{objective_text}' after {max_retries} attempts")
            # Don't raise exception here - let it accumulate and try other objectives
        
        logger.info(f"Successfully generated {len(problems)} problems for objective '{objective_text}'")
        return problems
    
    async def generate_problems(self, content: str, analysis: Dict[str, Any], num_problems: int) -> List[ExamProblem]:
        """Generate multiple choice problems based on content and analysis."""
        import structlog
        logger = structlog.get_logger(__name__)
        
        system_prompt = """You are a Problem Generator specializing in creating high-quality multiple choice exam questions.
Your task is to generate questions that:
1. Have exactly ONE correct answer
2. Have 4 answer choices (A, B, C, D)
3. Include plausible distractors (wrong answers that seem reasonable)
4. Test understanding, not just memorization
5. Are clear and unambiguous
6. Include appropriate difficulty levels

CRITICAL: Each question must have exactly ONE correct answer. All other choices must be clearly incorrect.

LATEX FORMATTING REQUIREMENTS:
- Use LaTeX syntax for ALL mathematical expressions, formulas, equations, and symbols
- Use \\( and \\) for inline math (e.g., \\(x^2 + 3x - 4\\))
- Use \\[ and \\] for display math (e.g., \\[\\frac{a}{b}\\])
- Common LaTeX symbols:
  * Fractions: \\frac{numerator}{denominator} (e.g., \\frac{3}{\\sqrt{7} - 1})
  * Square roots: \\sqrt{expression} (e.g., \\sqrt{25} or \\sqrt{x + 1})
  * Powers: ^{exponent} (e.g., x^2, a^{n+1})
  * Subscripts: _{subscript} (e.g., x_1, a_n)
  * Greek letters: \\alpha, \\beta, \\gamma, \\theta, \\pi, etc.
  * Operators: \\times, \\div, \\pm, \\mp, \\leq, \\geq, \\neq, \\approx
  * Sets: \\in, \\notin, \\subset, \\cup, \\cap
  * Other: \\infty, \\sum, \\prod, \\int, \\lim
- Always use LaTeX for mathematical notation - never use plain text for math

You MUST respond with valid JSON only. Do not include any text before or after the JSON."""
        
        # Use more content (up to 5000 chars) for better context
        content_preview = content[:5000] if len(content) > 5000 else content
        if len(content) > 5000:
            content_preview += "\n\n[Content truncated for brevity - use the key concepts shown above]"
        
        user_prompt = f"""Generate exactly {num_problems} multiple choice questions based on the following content and analysis.

Content:
{content_preview}

Analysis:
{json.dumps(analysis, indent=2)}

You MUST respond with ONLY valid JSON in this exact format (no markdown, no code blocks, just pure JSON):
{{
    "problems": [
        {{
            "problem_number": 1,
            "question": "Question text with LaTeX? For example: To rationalize the denominator of \\(\\frac{{3}}{{\\sqrt{{7}} - 1}}\\), what conjugate should be used?",
            "choices": {{
                "A": "First choice with LaTeX: \\(\\sqrt{{7}} + 1\\)",
                "B": "Second choice with LaTeX: \\(\\sqrt{{7}} - 1\\)",
                "C": "Third choice with LaTeX: \\(7 + \\sqrt{{1}}\\)",
                "D": "Fourth choice with LaTeX: \\(7 - \\sqrt{{1}}\\)"
            }},
            "correct_answer": "A",
            "explanation": "To rationalize the denominator \\(\\sqrt{{7}} - 1\\), we multiply both numerator and denominator by the conjugate \\(\\sqrt{{7}} + 1\\). The conjugate of a binomial \\(a - b\\) is \\(a + b\\). When we multiply \\((\\sqrt{{7}} - 1)(\\sqrt{{7}} + 1)\\), we get \\(7 - 1 = 6\\), which eliminates the radical from the denominator. Therefore, the conjugate \\(\\sqrt{{7}} + 1\\) (choice A) is correct. Choice B is the original denominator, not the conjugate. Choices C and D are incorrect as they don't follow the conjugate pattern.",
            "topic": "Topic name",
            "difficulty": "easy"
        }},
        {{
            "problem_number": 2,
            "question": "Another question with LaTeX? For example: Simplify \\(\\sqrt{{x^2 + 2x + 1}}\\).",
            "choices": {{
                "A": "Choice A with LaTeX: \\(x + 1\\)",
                "B": "Choice B with LaTeX: \\(x - 1\\)",
                "C": "Choice C with LaTeX: \\(x^2 + 1\\)",
                "D": "Choice D with LaTeX: \\(2x + 1\\)"
            }},
            "correct_answer": "B",
            "explanation": "To simplify \\(\\sqrt{{x^2 + 2x + 1}}\\), we first recognize that \\(x^2 + 2x + 1\\) is a perfect square trinomial. Factoring gives us \\((x+1)^2\\). Therefore, \\(\\sqrt{{x^2 + 2x + 1}} = \\sqrt{{(x+1)^2}} = |x+1|\\). Since the square root of a square is the absolute value, the answer is \\(|x+1|\\) (choice B). Choice A is incorrect because we cannot simply take \\(x+1\\) without the absolute value. Choices C and D are incorrect as they don't represent the simplified form.",
            "topic": "Topic",
            "difficulty": "medium"
        }}
    ]
}}

CRITICAL REQUIREMENTS:
- Generate exactly {num_problems} problems
- Each problem must have exactly 4 choices (A, B, C, D)
- Each problem must have exactly ONE correct answer
- The correct_answer must be one of: A, B, C, or D
- Each problem MUST include a detailed explanation that explains WHY the correct answer is correct
- Explanations should include step-by-step reasoning for mathematical problems
- Use LaTeX formatting for ALL mathematical expressions in questions, choices, and explanations
- Always escape curly braces in JSON strings by doubling them: {{ and }}
- Respond with ONLY the JSON object, no other text

LATEX EXAMPLES:
- Fractions: \\(\\frac{{a}}{{b}}\\), \\(\\frac{{3x + 2}}{{x - 1}}\\)
- Square roots: \\(\\sqrt{{x}}\\), \\(\\sqrt{{x^2 + 1}}\\)
- Powers: \\(x^2\\), \\(a^{{n+1}}\\)
- Complex expressions: \\(\\frac{{3}}{{\\sqrt{{7}} - 1}}\\), \\(\\sqrt{{\\frac{{a}}{{b}}}}\\)"""
        
        # Retry logic - try up to 3 times
        max_retries = 3
        problems = []
        
        for attempt in range(max_retries):
            try:
                response = await self.llm_client.complete(system=system_prompt, user=user_prompt)
                logger.info(f"Problem generation attempt {attempt + 1}", response_length=len(response))
                
                # Check if response is empty
                if not response or len(response.strip()) == 0:
                    logger.warning(f"Empty response from LLM (attempt {attempt + 1})")
                    if attempt < max_retries - 1:
                        # Increase wait time with each retry
                        wait_time = 2 * (attempt + 1)
                        logger.info(f"Waiting {wait_time} seconds before retry...")
                        await asyncio.sleep(wait_time)
                    continue
                
                # Extract problems from response
                # Try multiple JSON extraction methods
                json_data = None
                
                # Method 1: Try parsing the entire response (cleanest)
                try:
                    json_data = json.loads(response.strip())
                    logger.info(f"Successfully parsed JSON using method 1 (full response)")
                except json.JSONDecodeError as e:
                    logger.debug(f"Method 1 failed: {e}")
                    # Try to fix common JSON issues and retry
                    if "Unterminated string" in str(e) or "Expecting" in str(e) or "Invalid" in str(e):
                        try:
                            # Try to fix unterminated strings by finding the JSON object boundaries
                            fixed_response = self._try_fix_json(response)
                            if fixed_response:
                                json_data = json.loads(fixed_response)
                                logger.info(f"Successfully parsed JSON using method 1 after fixing")
                        except Exception as fix_error:
                            logger.debug(f"Failed to fix JSON: {fix_error}")
                            pass
                except Exception as e:
                    logger.debug(f"Method 1 failed with non-JSON error: {e}")
                    pass
                
                # Method 2: Look for JSON object with balanced braces (handles nested structures)
                if not json_data:
                    # Find the first { and then find the matching closing }
                    start_idx = response.find('{')
                    if start_idx != -1:
                        brace_count = 0
                        end_idx = start_idx
                        for i in range(start_idx, len(response)):
                            if response[i] == '{':
                                brace_count += 1
                            elif response[i] == '}':
                                brace_count -= 1
                                if brace_count == 0:
                                    end_idx = i + 1
                                    break
                        
                        if brace_count == 0:
                            try:
                                json_str = response[start_idx:end_idx]
                                json_data = json.loads(json_str)
                                logger.info(f"Successfully parsed JSON using method 2 (balanced braces), length={len(json_str)}")
                            except Exception as e:
                                logger.debug(f"Method 2 failed: {e}, json_str preview: {json_str[:200] if len(json_str) > 200 else json_str}")
                                pass
                
                # Method 3: Look for JSON in code blocks (markdown)
                if not json_data:
                    # Try to extract from markdown code blocks
                    code_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
                    if code_block_match:
                        try:
                            json_data = json.loads(code_block_match.group(1))
                            logger.info(f"Successfully parsed JSON using method 3 (code block)")
                        except Exception as e:
                            logger.debug(f"Method 3 failed: {e}")
                            pass
                
                # Method 4: Look for JSON object with "problems" key (more permissive)
                if not json_data:
                    # Find JSON object containing "problems"
                    json_match = re.search(r'\{[^{]*"problems"\s*:\s*\[', response, re.DOTALL)
                    if json_match:
                        start_idx = json_match.start()
                        # Find matching closing brace
                        brace_count = 0
                        end_idx = start_idx
                        for i in range(start_idx, len(response)):
                            if response[i] == '{':
                                brace_count += 1
                            elif response[i] == '}':
                                brace_count -= 1
                                if brace_count == 0:
                                    end_idx = i + 1
                                    break
                        
                        if brace_count == 0:
                            try:
                                json_str = response[start_idx:end_idx]
                                json_data = json.loads(json_str)
                            except Exception as e:
                                logger.debug(f"Failed to parse JSON from method 4: {e}")
                                pass
                
                # Method 5: Try to extract just the problems array and wrap it
                if not json_data:
                    # Find the problems array directly
                    array_match = re.search(r'"problems"\s*:\s*\[', response, re.DOTALL)
                    if array_match:
                        # Find the start of the array
                        array_start = response.find('[', array_match.end())
                        if array_start != -1:
                            # Find matching closing bracket (handle nested structures)
                            bracket_count = 0
                            array_end = array_start
                            in_string = False
                            escape_next = False
                            
                            for i in range(array_start, len(response)):
                                char = response[i]
                                
                                if escape_next:
                                    escape_next = False
                                    continue
                                
                                if char == '\\':
                                    escape_next = True
                                    continue
                                
                                if char == '"' and not escape_next:
                                    in_string = not in_string
                                    continue
                                
                                if not in_string:
                                    if char == '[':
                                        bracket_count += 1
                                    elif char == ']':
                                        bracket_count -= 1
                                        if bracket_count == 0:
                                            array_end = i + 1
                                            break
                            
                            if bracket_count == 0:
                                try:
                                    array_str = response[array_start:array_end]
                                    problems_list = json.loads(array_str)
                                    
                                    # Validate that we got a list of dictionaries
                                    if isinstance(problems_list, list) and len(problems_list) > 0:
                                        # Check if first element is a dict (problem object)
                                        if isinstance(problems_list[0], dict):
                                            # Wrap in expected format
                                            json_data = {"problems": problems_list}
                                            logger.info(f"Successfully extracted {len(problems_list)} problems using method 5")
                                        else:
                                            logger.warning(f"Method 5 extracted array but first element is not a dict: {type(problems_list[0])}")
                                    else:
                                        logger.warning(f"Method 5 extracted invalid array: {problems_list}")
                                except Exception as e:
                                    logger.debug(f"Failed to parse problems array: {e}, array_str preview: {array_str[:200] if 'array_str' in locals() else 'N/A'}")
                                    pass
                
                if json_data:
                    problem_list = json_data.get("problems", [])
                    logger.info(f"Extracted {len(problem_list)} problems from JSON")
                    
                    # Validate that problem_list is actually a list of dictionaries
                    if not isinstance(problem_list, list):
                        logger.error(f"Expected list but got {type(problem_list)}: {problem_list}")
                        problem_list = []
                    else:
                        # Filter out non-dict items
                        valid_problems = [p for p in problem_list if isinstance(p, dict)]
                        if len(valid_problems) != len(problem_list):
                            logger.warning(f"Filtered out {len(problem_list) - len(valid_problems)} non-dict items from problem list")
                            problem_list = valid_problems
                    
                    for i, p in enumerate(problem_list, 1):
                        try:
                            # Ensure p is a dictionary
                            if not isinstance(p, dict):
                                logger.warning(f"Problem {i} is not a dictionary (type: {type(p)}), skipping")
                                continue
                            
                            # Validate required fields
                            if not p.get("question") or not p.get("choices"):
                                logger.warning(f"Problem {i} missing required fields, skipping")
                                continue
                            
                            problem = ExamProblem(
                                problem_number=p.get("problem_number", i),
                                question=p.get("question", "").strip(),
                                choices=p.get("choices", {}),
                                correct_answer=p.get("correct_answer", "A").strip().upper(),
                                explanation=p.get("explanation", "").strip(),
                                topic=p.get("topic", "").strip(),
                                difficulty=p.get("difficulty", "medium").strip().lower()
                            )
                            
                            # Validate problem structure
                            if not problem.question:
                                logger.warning(f"Problem {i} has empty question, skipping")
                                continue
                            
                            if len(problem.choices) != 4:
                                logger.warning(f"Problem {i} has {len(problem.choices)} choices (expected 4), skipping")
                                continue
                            
                            if problem.correct_answer not in problem.choices:
                                logger.warning(f"Problem {i} has invalid correct_answer {problem.correct_answer}, skipping")
                                continue
                            
                            problems.append(problem)
                            logger.info(f"Added problem {problem.problem_number}: {problem.question[:50]}...")
                        except Exception as e:
                            logger.warning(f"Error creating problem {i}: {e}")
                            continue
                    
                    # If we got enough problems, break
                    if len(problems) >= num_problems:
                        problems = problems[:num_problems]  # Trim to exact number
                        logger.info(f"Successfully generated {len(problems)} problems, stopping retries")
                        break
                    elif len(problems) > 0:
                        # Got some problems but not enough - keep them and continue to next attempt
                        logger.warning(f"Only generated {len(problems)}/{num_problems} problems so far, continuing to accumulate...")
                        # Don't clear problems - accumulate across attempts
                else:
                    logger.warning(f"Could not extract JSON from response (attempt {attempt + 1})")
                    # Log more of the response for debugging
                    preview_length = min(1000, len(response))
                    logger.debug(f"Response preview (first {preview_length} chars): {response[:preview_length]}")
                    # Also try to find where JSON might start
                    json_start = response.find('{')
                    if json_start != -1:
                        logger.debug(f"Found '{{' at position {json_start}, showing context: {response[max(0, json_start-50):min(len(response), json_start+500)]}")
            
            except Exception as e:
                logger.error(f"Error generating problems (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)  # Wait before retry
        
        if not problems:
            logger.error(f"Failed to generate any problems after {max_retries} attempts")
            raise Exception(f"Failed to generate problems. The LLM did not return valid problem data after {max_retries} attempts.")
        
        logger.info(f"Successfully generated {len(problems)} problems")
        return problems


class ValidationAgent(BaseAgent):
    """Validates exam problems by taking the exam and checking correctness."""
    
    def __init__(self, llm_client: LLMClient):
        super().__init__("Validation Agent", "Exam Validator", llm_client)
    
    async def validate_problem(self, problem: ExamProblem, content: str) -> Dict[str, Any]:
        """Validate a single problem by attempting to answer it."""
        system_prompt = """You are a Validation Agent that takes exams to verify their correctness.
Your task is to:
1. Read the question carefully
2. Consider all answer choices
3. Select the answer you believe is correct based on the content
4. Verify that only ONE answer is correct
5. Check if the explanation is accurate
6. Report any issues or ambiguities"""
        
        user_prompt = f"""Please take this exam problem and validate it:

Content Reference:
{content[:1000]}...

Problem:
Question {problem.problem_number}: {problem.question}

Choices:
A. {problem.choices.get('A', '')}
B. {problem.choices.get('B', '')}
C. {problem.choices.get('C', '')}
D. {problem.choices.get('D', '')}

Marked Correct Answer: {problem.correct_answer}

Explanation: {problem.explanation}

Please:
1. Answer the question yourself (which choice would you select?)
2. Verify that the marked correct answer ({problem.correct_answer}) is indeed correct
3. Check if any other choices could also be considered correct
4. Verify the explanation is accurate
5. Report any issues

Respond in JSON format:
{{
    "selected_answer": "A|B|C|D",
    "matches_correct": true|false,
    "is_ambiguous": true|false,
    "other_correct_answers": [],
    "explanation_accurate": true|false,
    "issues": ["issue1", "issue2", ...],
    "validation_status": "valid|invalid|needs_revision"
}}"""
        
        response = await self.llm_client.complete(system=system_prompt, user=user_prompt)
        
        # Extract validation result
        validation = {
            "problem_number": problem.problem_number,
            "selected_answer": None,
            "matches_correct": False,
            "is_ambiguous": False,
            "other_correct_answers": [],
            "explanation_accurate": True,
            "issues": [],
            "validation_status": "unknown"
        }
        
        # Try multiple JSON extraction methods
        json_data = None
        
        # Method 1: Try parsing the entire response
        try:
            json_data = json.loads(response.strip())
        except:
            pass
        
        # Method 2: Extract JSON with balanced braces
        if not json_data:
            start_idx = response.find('{')
            if start_idx != -1:
                brace_count = 0
                end_idx = start_idx
                for i in range(start_idx, len(response)):
                    if response[i] == '{':
                        brace_count += 1
                    elif response[i] == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end_idx = i + 1
                            break
                
                if brace_count == 0:
                    try:
                        json_str = response[start_idx:end_idx]
                        json_data = json.loads(json_str)
                    except:
                        pass
        
        # Method 3: Try extracting from markdown code blocks
        if not json_data:
            code_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if code_block_match:
                try:
                    json_data = json.loads(code_block_match.group(1))
                except:
                    pass
        
        if json_data:
            validation.update(json_data)
        else:
            validation["issues"].append("Could not parse validation response")
        
        return validation
    
    async def validate_all_problems(self, problems: List[ExamProblem], content: str) -> List[Dict[str, Any]]:
        """Validate all problems."""
        results = []
        for problem in problems:
            result = await self.validate_problem(problem, content)
            results.append(result)
        return results


class ReviewAgent(BaseAgent):
    """Final review agent that ensures all problems meet quality standards."""
    
    def __init__(self, llm_client: LLMClient):
        super().__init__("Review Agent", "Final Quality Reviewer", llm_client)
    
    async def review_exam(self, problems: List[ExamProblem], validation_results: List[Dict[str, Any]], content: str) -> Dict[str, Any]:
        """Perform final review of the entire exam."""
        system_prompt = """You are a Review Agent responsible for final quality assurance of exam problems.
Your task is to:
1. Review all problems for consistency
2. Ensure all problems have exactly one correct answer
3. Verify explanations are accurate
4. Check for appropriate difficulty distribution
5. Ensure questions cover the content adequately
6. Identify any remaining issues"""
        
        # Count validation issues
        invalid_count = sum(1 for v in validation_results if v.get("validation_status") != "valid")
        ambiguous_count = sum(1 for v in validation_results if v.get("is_ambiguous", False))
        
        user_prompt = f"""Review the complete exam:

Content Length: {len(content)} characters
Number of Problems: {len(problems)}
Invalid Problems: {invalid_count}
Ambiguous Problems: {ambiguous_count}

Problems:
{json.dumps([p.to_dict() for p in problems], indent=2)}

Validation Results:
{json.dumps(validation_results, indent=2)}

Provide a comprehensive review in JSON format:
{{
    "overall_quality": "excellent|good|acceptable|needs_improvement",
    "issues_found": ["issue1", "issue2", ...],
    "problems_needing_revision": [<problem_numbers>],
    "recommendations": ["recommendation1", ...],
    "approval_status": "approved|needs_revision|rejected"
}}"""
        
        response = await self.llm_client.complete(system=system_prompt, user=user_prompt)
        
        review = {
            "overall_quality": "unknown",
            "issues_found": [],
            "problems_needing_revision": [],
            "recommendations": [],
            "approval_status": "unknown"
        }
        
        # Try multiple JSON extraction methods
        json_data = None
        
        # Method 1: Try parsing the entire response
        try:
            json_data = json.loads(response.strip())
        except:
            pass
        
        # Method 2: Extract JSON with balanced braces
        if not json_data:
            start_idx = response.find('{')
            if start_idx != -1:
                brace_count = 0
                end_idx = start_idx
                for i in range(start_idx, len(response)):
                    if response[i] == '{':
                        brace_count += 1
                    elif response[i] == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end_idx = i + 1
                            break
                
                if brace_count == 0:
                    try:
                        json_str = response[start_idx:end_idx]
                        json_data = json.loads(json_str)
                    except:
                        pass
        
        # Method 3: Try extracting from markdown code blocks
        if not json_data:
            code_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if code_block_match:
                try:
                    json_data = json.loads(code_block_match.group(1))
                except:
                    pass
        
        if json_data:
            review.update(json_data)
        else:
            review["issues_found"].append("Could not parse review response")
        
        return review


class ExamGeneratorCompany:
    """Main orchestrator for the Exam Generator system."""
    
    def __init__(self, model: Optional[str] = None):
        """Initialize the company with all agents."""
        agent_config = get_config()
        
        selected_model = model or agent_config.get("model", "qwen3:30b")
        if selected_model not in ["llama3:latest", "qwen3:30b"]:
            selected_model = agent_config.get("model", "qwen3:30b")
        
        self.llm_client = LLMClient(
            api_key=None,
            base_url=agent_config.get("base_url", "http://localhost:11434/v1"),
            model=selected_model,
            provider=agent_config.get("provider", "local")
        )
        
        # Create agents
        self.content_analyst = ContentAnalystAgent(self.llm_client)
        self.problem_generator = ProblemGeneratorAgent(self.llm_client)
        self.validation_agent = ValidationAgent(self.llm_client)
        self.review_agent = ReviewAgent(self.llm_client)
        
        self.project: Optional[ExamProject] = None
    
    async def generate_exam(self, project: ExamProject, max_iterations: int = 3, 
                           progress_callback: Optional[Callable[[str, int, str], None]] = None) -> Tuple[List[ExamProblem], Dict[str, Any]]:
        """
        Generate an exam from input content.
        
        Args:
            project: Exam project with input content
            max_iterations: Maximum number of validation iterations
            progress_callback: Optional callback function(phase, progress, message) for progress updates
            
        Returns:
            Tuple of (final_problems, final_review)
        """
        import structlog
        logger = structlog.get_logger(__name__)
        
        self.project = project
        
        def update_progress(phase: str, progress: int, message: str = ""):
            """Update progress if callback is provided."""
            if progress_callback:
                try:
                    progress_callback(phase, progress, message)
                except:
                    pass
        
        # Phase 1: Content Analysis
        project.current_phase = ExamPhase.CONTENT_ANALYSIS
        project.status = "in_progress"
        update_progress("content_analysis", 10, "Analyzing content structure and topics...")
        logger.info("Starting content analysis phase")
        
        analysis = await self.content_analyst.analyze_content(project.input_content)
        project.content_analysis = analysis
        logger.info("Content analysis complete", topics_count=len(analysis.get("key_topics", [])))
        update_progress("content_analysis", 25, f"Identified {len(analysis.get('key_topics', []))} key topics")
        
        # Extract learning objectives
        learning_objectives = analysis.get("learning_objectives", [])
        if not learning_objectives:
            # Fallback: extract from content directly
            learning_objectives = self.content_analyst._extract_learning_objectives(project.input_content)
            learning_objectives = [{"number": str(i+1), "objective": obj} for i, obj in enumerate(learning_objectives)]
        
        logger.info(f"Found {len(learning_objectives)} learning objectives")
        
        # num_problems now represents problems per objective, not total
        num_objectives = len(learning_objectives) if learning_objectives else 1
        problems_per_objective = project.num_problems  # This is now per objective
        total_problems = num_objectives * problems_per_objective
        
        logger.info(f"Generating {problems_per_objective} problems per objective for {num_objectives} objectives (total: {total_problems})")
        
        # Phase 2: Problem Generation
        project.current_phase = ExamPhase.PROBLEM_GENERATION
        update_progress("problem_generation", 30, f"Generating {problems_per_objective} problems per objective for {num_objectives} learning objectives (total: {total_problems})...")
        logger.info("Starting problem generation phase", problems_per_objective=problems_per_objective, num_objectives=num_objectives, total_problems=total_problems)
        
        all_problems = []
        for idx, objective in enumerate(learning_objectives):
            # Each objective gets the same number of problems
            num_probs_for_obj = problems_per_objective
            
            update_progress("problem_generation", 30 + int(50 * idx / num_objectives), 
                          f"Generating {num_probs_for_obj} problems for objective {idx + 1}/{num_objectives}: {objective.get('objective', objective)}")
            
            # Generate problems for this specific objective
            objective_problems = await self.problem_generator.generate_problems_for_objective(
                project.input_content,
                analysis,
                objective,
                num_probs_for_obj
            )
            
            all_problems.extend(objective_problems)
        
        problems = all_problems
        project.problems = problems
        
        if not problems:
            error_msg = "No problems were generated. Please check the input content and try again."
            logger.error(error_msg)
            project.status = "error"
            raise Exception(error_msg)
        
        logger.info(f"Generated {len(problems)} problems successfully")
        update_progress("problem_generation", 50, f"Generated {len(problems)} problems")
        
        # Phase 3: Validation (iterative)
        project.current_phase = ExamPhase.VALIDATION
        all_validation_results = []
        update_progress("validation", 55, "Starting validation phase...")
        logger.info("Starting validation phase", iterations=max_iterations)
        
        for iteration in range(max_iterations):
            update_progress("validation", 55 + (iteration * 10), f"Validation iteration {iteration + 1}/{max_iterations}...")
            logger.info(f"Validation iteration {iteration + 1}/{max_iterations}")
            
            validation_results = await self.validation_agent.validate_all_problems(
                problems,
                project.input_content
            )
            all_validation_results.append({
                "iteration": iteration + 1,
                "results": validation_results
            })
            
            # Check if all problems are valid
            invalid_problems = [
                v for v in validation_results
                if v.get("validation_status") != "valid" or v.get("is_ambiguous", False)
            ]
            
            valid_count = len(validation_results) - len(invalid_problems)
            logger.info(f"Iteration {iteration + 1}: {valid_count}/{len(validation_results)} problems valid")
            update_progress("validation", 60 + (iteration * 10), f"{valid_count}/{len(validation_results)} problems validated")
            
            if not invalid_problems:
                # All problems are valid, break early
                logger.info("All problems validated successfully")
                update_progress("validation", 85, "All problems validated successfully")
                break
            
            # Regenerate invalid problems
            if iteration < max_iterations - 1:
                invalid_indices = [v["problem_number"] - 1 for v in invalid_problems]
                logger.info(f"Regenerating {len(invalid_indices)} invalid problems")
                update_progress("validation", 70 + (iteration * 5), f"Regenerating {len(invalid_indices)} invalid problems...")
                
                for idx in invalid_indices:
                    if idx < len(problems):
                        # Regenerate this problem
                        new_problems = await self.problem_generator.generate_problems(
                            project.input_content,
                            analysis,
                            1
                        )
                        if new_problems:
                            problems[idx] = new_problems[0]
                            problems[idx].problem_number = idx + 1
                            logger.info(f"Regenerated problem {idx + 1}")
        
        project.validation_results = all_validation_results
        project.problems = problems
        
        # Phase 4: Final Review
        project.current_phase = ExamPhase.FINAL_REVIEW
        update_progress("final_review", 90, "Performing final quality review...")
        logger.info("Starting final review phase")
        
        final_validation = all_validation_results[-1]["results"] if all_validation_results else []
        review = await self.review_agent.review_exam(problems, final_validation, project.input_content)
        project.final_review = review
        logger.info("Final review complete", approval_status=review.get("approval_status"))
        update_progress("final_review", 95, f"Review status: {review.get('approval_status', 'unknown')}")
        
        # If review recommends revision, do one more pass
        if review.get("approval_status") == "needs_revision" and max_iterations > 0:
            # Regenerate problematic questions
            problems_to_revise = review.get("problems_needing_revision", [])
            if problems_to_revise:
                for prob_num in problems_to_revise:
                    idx = prob_num - 1
                    if 0 <= idx < len(problems):
                        new_problems = await self.problem_generator.generate_problems(
                            project.input_content,
                            analysis,
                            1
                        )
                        if new_problems:
                            problems[idx] = new_problems[0]
                            problems[idx].problem_number = idx + 1
                
                # Final validation
                final_validation = await self.validation_agent.validate_all_problems(
                    problems,
                    project.input_content
                )
                review = await self.review_agent.review_exam(problems, final_validation, project.input_content)
                project.final_review = review
        
        project.current_phase = ExamPhase.COMPLETE
        project.status = "complete"
        
        return problems, review
    
    def format_problems_file(self, problems: List[ExamProblem]) -> str:
        """Format problems for Problems.txt file."""
        lines = []
        lines.append("=" * 80)
        lines.append("EXAM PROBLEMS")
        lines.append("=" * 80)
        lines.append("")
        
        for problem in problems:
            lines.append(f"Problem {problem.problem_number}")
            lines.append("-" * 80)
            lines.append(f"Topic: {problem.topic}")
            lines.append(f"Difficulty: {problem.difficulty}")
            lines.append("")
            lines.append(f"Question: {problem.question}")
            lines.append("")
            lines.append("Choices:")
            for choice, text in sorted(problem.choices.items()):
                lines.append(f"  {choice}. {text}")
            lines.append("")
            lines.append("=" * 80)
            lines.append("")
        
        return "\n".join(lines)
    
    def format_solutions_file(self, problems: List[ExamProblem]) -> str:
        """Format solutions for Solutions.txt file."""
        lines = []
        lines.append("=" * 80)
        lines.append("EXAM SOLUTIONS")
        lines.append("=" * 80)
        lines.append("")
        
        for problem in problems:
            lines.append(f"Problem {problem.problem_number}")
            lines.append("-" * 80)
            lines.append(f"Correct Answer: {problem.correct_answer}")
            lines.append("")
            lines.append(f"Explanation:")
            lines.append(problem.explanation)
            lines.append("")
            lines.append("=" * 80)
            lines.append("")
        
        return "\n".join(lines)
    
    def format_combined_file(self, problems: List[ExamProblem]) -> str:
        """Format problems with solutions for Problems_with_solutions.txt file."""
        lines = []
        lines.append("=" * 80)
        lines.append("EXAM PROBLEMS WITH SOLUTIONS")
        lines.append("=" * 80)
        lines.append("")
        
        for problem in problems:
            lines.append(f"Problem {problem.problem_number}")
            lines.append("-" * 80)
            lines.append(f"Topic: {problem.topic}")
            lines.append(f"Difficulty: {problem.difficulty}")
            lines.append("")
            lines.append(f"Question: {problem.question}")
            lines.append("")
            lines.append("Choices:")
            for choice, text in sorted(problem.choices.items()):
                marker = " ✓" if choice == problem.correct_answer else ""
                lines.append(f"  {choice}. {text}{marker}")
            lines.append("")
            lines.append(f"Correct Answer: {problem.correct_answer}")
            lines.append("")
            lines.append(f"Explanation:")
            lines.append(problem.explanation)
            lines.append("")
            lines.append("=" * 80)
            lines.append("")
        
        return "\n".join(lines)
    
    async def save_exam_files(self, project: ExamProject, problems: List[ExamProblem]) -> Dict[str, str]:
        """Save exam files to disk."""
        import structlog
        logger = structlog.get_logger(__name__)
        
        if not problems:
            error_msg = "Cannot save files: No problems were generated"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        output_dir = Path(project.output_directory)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        project_id = project.project_id
        
        logger.info(f"Saving {len(problems)} problems to files", output_dir=str(output_dir))
        
        # Generate file contents
        problems_text = self.format_problems_file(problems)
        solutions_text = self.format_solutions_file(problems)
        combined_text = self.format_combined_file(problems)
        
        # Validate file contents are not empty
        if not problems_text.strip() or not solutions_text.strip() or not combined_text.strip():
            error_msg = "Generated file contents are empty. This should not happen."
            logger.error(error_msg, problems_count=len(problems))
            raise Exception(error_msg)
        
        # Save files
        problems_path = output_dir / f"{project_id}_Problems.txt"
        solutions_path = output_dir / f"{project_id}_Solutions.txt"
        combined_path = output_dir / f"{project_id}_Problems_with_solutions.txt"
        
        problems_path.write_text(problems_text, encoding='utf-8')
        solutions_path.write_text(solutions_text, encoding='utf-8')
        combined_path.write_text(combined_text, encoding='utf-8')
        
        logger.info("Files saved successfully", 
                   problems_file=str(problems_path),
                   solutions_file=str(solutions_path),
                   combined_file=str(combined_path))
        
        return {
            "problems": str(problems_path),
            "solutions": str(solutions_path),
            "combined": str(combined_path)
        }
