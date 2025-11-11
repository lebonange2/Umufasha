"""Task planner for multi-step code changes."""
from typing import Dict, Any, List, Optional
import structlog

from mcp.plugins.cursor_clone.llm.engine import LLMEngine

logger = structlog.get_logger(__name__)


class TaskPlanner:
    """Plans multi-step code changes."""
    
    def __init__(self, llm: LLMEngine, config: Dict[str, Any]):
        """Initialize task planner."""
        self.llm = llm
        self.config = config
    
    async def plan(
        self,
        goal: str,
        scope: Optional[str] = None,
        files: Optional[List[str]] = None,
        constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a plan for achieving the goal."""
        logger.info("Creating plan", goal=goal, scope=scope, files=files)
        
        # Build planning prompt
        prompt = self._build_planning_prompt(goal, scope, files, constraints)
        
        # Get system prompt
        system_prompt = self._get_system_prompt()
        
        # Generate plan
        response = await self.llm.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=self.config.get("llm", {}).get("max_tokens", 1024)
        )
        
        # Parse response
        plan = self._parse_plan(response)
        
        # Assess risks
        risks = self._assess_risks(plan, files)
        
        return {
            "plan": plan,
            "risks": risks,
            "steps": len(plan.get("steps", [])),
            "estimated_complexity": self._estimate_complexity(plan)
        }
    
    def _build_planning_prompt(
        self,
        goal: str,
        scope: Optional[str] = None,
        files: Optional[List[str]] = None,
        constraints: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build planning prompt."""
        prompt = f"Goal: {goal}\n\n"
        
        if scope:
            prompt += f"Scope: {scope}\n"
        
        if files:
            prompt += f"Files to consider: {', '.join(files)}\n"
        
        if constraints:
            prompt += f"Constraints: {constraints}\n"
        
        prompt += "\nCreate a step-by-step plan to achieve this goal. "
        prompt += "Include:\n"
        prompt += "1. Analysis of current code\n"
        prompt += "2. Required changes\n"
        prompt += "3. Testing strategy\n"
        prompt += "4. Rollback plan\n"
        
        return prompt
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for planning."""
        return """You are a code planning assistant. Create clear, actionable plans for code changes.
Follow these principles:
- Plan → Diff → Apply discipline
- Keep changes minimal and reversible
- Always consider testing
- Identify risks upfront
- Prefer standard libraries and existing patterns"""
    
    def _parse_plan(self, response: str) -> Dict[str, Any]:
        """Parse plan from LLM response."""
        # Simple parsing - in production, use structured output
        plan = {
            "description": response,
            "steps": []
        }
        
        # Extract steps (simple heuristic)
        lines = response.split("\n")
        current_step = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if it's a step header
            if line.startswith(("1.", "2.", "3.", "4.", "5.", "-", "*")):
                if current_step:
                    plan["steps"].append(current_step)
                current_step = {"description": line, "details": []}
            elif current_step:
                current_step["details"].append(line)
        
        if current_step:
            plan["steps"].append(current_step)
        
        return plan
    
    def _assess_risks(self, plan: Dict[str, Any], files: Optional[List[str]]) -> List[str]:
        """Assess risks of the plan."""
        risks = []
        
        # Check for destructive operations
        plan_text = str(plan).lower()
        if any(word in plan_text for word in ["delete", "remove", "drop", "truncate"]):
            risks.append("May involve destructive operations")
        
        # Check for external dependencies
        if "import" in plan_text or "require" in plan_text:
            risks.append("May introduce new dependencies")
        
        # Check for breaking changes
        if any(word in plan_text for word in ["refactor", "rename", "restructure"]):
            risks.append("May break dependent code")
        
        # Check for test coverage
        if "test" not in plan_text.lower():
            risks.append("May lack test coverage")
        
        return risks
    
    def _estimate_complexity(self, plan: Dict[str, Any]) -> str:
        """Estimate complexity of the plan."""
        steps = len(plan.get("steps", []))
        
        if steps <= 2:
            return "low"
        elif steps <= 5:
            return "medium"
        else:
            return "high"

