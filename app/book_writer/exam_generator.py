"""
Exam Generator - Multi-Agent Exam Creation System

This module implements an exam generation system using the Book Publishing House
multi-agent architecture to generate high-quality multiple choice questions from
input text files. The system includes rigorous validation with AI agents taking
the exam repeatedly to ensure correctness.
"""

from typing import Dict, List, Optional, Any, Tuple
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
    
    async def analyze_content(self, content: str) -> Dict[str, Any]:
        """Analyze the input content and identify key topics."""
        system_prompt = """You are a Content Analyst specializing in educational content analysis.
Your task is to analyze text content and identify:
1. Key topics and concepts
2. Important facts and details
3. Relationships between concepts
4. Difficulty levels of different topics
5. Suitable question types for each topic

Provide a structured analysis that will guide problem generation."""
        
        user_prompt = f"""Analyze the following content and provide a comprehensive analysis:

{content}

Provide your analysis in JSON format with the following structure:
{{
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
        try:
            # Look for JSON in the response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
            else:
                # Fallback: create basic structure
                analysis = {
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
        except json.JSONDecodeError:
            # Fallback structure
            analysis = {
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
        
        return analysis


class ProblemGeneratorAgent(BaseAgent):
    """Generates multiple choice problems from analyzed content."""
    
    def __init__(self, llm_client: LLMClient):
        super().__init__("Problem Generator", "Exam Problem Creator", llm_client)
    
    async def generate_problems(self, content: str, analysis: Dict[str, Any], num_problems: int) -> List[ExamProblem]:
        """Generate multiple choice problems based on content and analysis."""
        system_prompt = """You are a Problem Generator specializing in creating high-quality multiple choice exam questions.
Your task is to generate questions that:
1. Have exactly ONE correct answer
2. Have 4 answer choices (A, B, C, D)
3. Include plausible distractors (wrong answers that seem reasonable)
4. Test understanding, not just memorization
5. Are clear and unambiguous
6. Include appropriate difficulty levels

CRITICAL: Each question must have exactly ONE correct answer. All other choices must be clearly incorrect."""
        
        user_prompt = f"""Generate {num_problems} multiple choice questions based on the following content and analysis:

Content:
{content[:2000]}...

Analysis:
{json.dumps(analysis, indent=2)}

Generate questions in the following JSON format:
{{
    "problems": [
        {{
            "problem_number": 1,
            "question": "Question text here?",
            "choices": {{
                "A": "First choice",
                "B": "Second choice",
                "C": "Third choice",
                "D": "Fourth choice"
            }},
            "correct_answer": "A",
            "explanation": "Explanation of why the correct answer is correct",
            "topic": "Topic name",
            "difficulty": "easy|medium|hard"
        }},
        ...
    ]
}}

IMPORTANT: Ensure each question has exactly ONE correct answer. Verify that the correct_answer field matches one of the choices."""
        
        response = await self.llm_client.complete(system=system_prompt, user=user_prompt)
        
        # Extract problems from response
        problems = []
        try:
            # Look for JSON in the response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                problem_list = data.get("problems", [])
                
                for i, p in enumerate(problem_list, 1):
                    try:
                        problem = ExamProblem(
                            problem_number=p.get("problem_number", i),
                            question=p.get("question", ""),
                            choices=p.get("choices", {}),
                            correct_answer=p.get("correct_answer", "A"),
                            explanation=p.get("explanation", ""),
                            topic=p.get("topic", ""),
                            difficulty=p.get("difficulty", "medium")
                        )
                        # Validate problem
                        if problem.correct_answer in problem.choices and len(problem.choices) == 4:
                            problems.append(problem)
                    except Exception as e:
                        continue
        except json.JSONDecodeError:
            pass
        
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
        
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                validation.update(result)
        except json.JSONDecodeError:
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
        
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                review.update(result)
        except json.JSONDecodeError:
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
    
    async def generate_exam(self, project: ExamProject, max_iterations: int = 3) -> Tuple[List[ExamProblem], Dict[str, Any]]:
        """
        Generate an exam from input content.
        
        Args:
            project: Exam project with input content
            max_iterations: Maximum number of validation iterations
            
        Returns:
            Tuple of (final_problems, final_review)
        """
        self.project = project
        
        # Phase 1: Content Analysis
        project.current_phase = ExamPhase.CONTENT_ANALYSIS
        project.status = "in_progress"
        
        analysis = await self.content_analyst.analyze_content(project.input_content)
        project.content_analysis = analysis
        
        # Phase 2: Problem Generation
        project.current_phase = ExamPhase.PROBLEM_GENERATION
        problems = await self.problem_generator.generate_problems(
            project.input_content,
            analysis,
            project.num_problems
        )
        project.problems = problems
        
        # Phase 3: Validation (iterative)
        project.current_phase = ExamPhase.VALIDATION
        all_validation_results = []
        
        for iteration in range(max_iterations):
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
            
            if not invalid_problems:
                # All problems are valid, break early
                break
            
            # Regenerate invalid problems
            if iteration < max_iterations - 1:
                invalid_indices = [v["problem_number"] - 1 for v in invalid_problems]
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
        
        project.validation_results = all_validation_results
        project.problems = problems
        
        # Phase 4: Final Review
        project.current_phase = ExamPhase.FINAL_REVIEW
        final_validation = all_validation_results[-1]["results"] if all_validation_results else []
        review = await self.review_agent.review_exam(problems, final_validation, project.input_content)
        project.final_review = review
        
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
        output_dir = Path(project.output_directory)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        project_id = project.project_id
        
        # Generate file contents
        problems_text = self.format_problems_file(problems)
        solutions_text = self.format_solutions_file(problems)
        combined_text = self.format_combined_file(problems)
        
        # Save files
        problems_path = output_dir / f"{project_id}_Problems.txt"
        solutions_path = output_dir / f"{project_id}_Solutions.txt"
        combined_path = output_dir / f"{project_id}_Problems_with_solutions.txt"
        
        problems_path.write_text(problems_text, encoding='utf-8')
        solutions_path.write_text(solutions_text, encoding='utf-8')
        combined_path.write_text(combined_text, encoding='utf-8')
        
        return {
            "problems": str(problems_path),
            "solutions": str(solutions_path),
            "combined": str(combined_path)
        }
