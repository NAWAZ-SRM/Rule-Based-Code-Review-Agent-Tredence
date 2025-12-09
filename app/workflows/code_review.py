# app/workflows/code_review.py
""" 
    Implements the rule-based code review tools
    (extract functions, estimate complexity, detect issues, suggest improvements, evaluate quality)
    that form the sample workflow required by the assignment.
"""

import ast
from typing import List
from ..core.models import WorkflowState  
from ..core.models import WorkflowState
import asyncio


async def extract_functions(state: WorkflowState) -> WorkflowState:
    """
    Extract function names from the source code and store them in state.data.
    """
    source = state.data.get("source_code", "")
    function_names: List[str] = []

    try:
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                function_names.append(node.name)
    except SyntaxError:
        # If parsing fails, keep the list empty and move on.
        pass

    state.data["functions"] = function_names
    return state


async def check_complexity(state: WorkflowState) -> WorkflowState:
    """
    Very rough "complexity" heuristic based on function length.
    This is intentionally simple and rule-based.
    """
    await asyncio.sleep(0.2)
    lines = state.data.get("source_code", "").splitlines()
    total_lines = len(lines)

    # Simple heuristic: more lines leads to higher complexity.
    state.data["complexity_score"] = min(1.0, total_lines / 200.0)
    return state


async def detect_issues(state: WorkflowState) -> WorkflowState:
    """
    Detect a few basic issues using naive string checks.
    """
    source = state.data.get("source_code", "")
    issues: List[str] = []

    if "print(" in source:
        issues.append("Debug prints found")
    if "TODO" in source:
        issues.append("TODO comments present")
    if "eval(" in source:
        issues.append("Use of eval detected")

    state.data["issues"] = issues
    state.data["issue_count"] = len(issues)
    return state


async def suggest_improvements(state: WorkflowState) -> WorkflowState:
    """
    Suggest improvements based on the current issues and complexity.
    """
    suggestions: List[str] = []

    complexity = state.data.get("complexity_score", 0.0)
    if complexity > 0.7:
        suggestions.append("Consider splitting large functions into smaller units")

    for issue in state.data.get("issues", []):
        if "Debug prints" in issue:
            suggestions.append("Remove debug print statements or use logging instead")
        if "TODO" in issue:
            suggestions.append("Resolve or track TODO items before production")
        if "eval" in issue:
            suggestions.append("Avoid eval; consider safer alternatives")

    state.data["suggestions"] = suggestions
    return state


async def evaluate_quality(state: WorkflowState) -> WorkflowState:
    """
    Compute a simple quality_score and decide whether the workflow is done.
    """
    complexity = state.data.get("complexity_score", 0.0)
    issue_count = state.data.get("issue_count", 0)

    score = 1.0 - 0.4 * complexity - 0.1 * issue_count
    state.quality_score = max(0.0, min(1.0, score))

    threshold = state.data.get("quality_threshold", 0.8)
    state.done = state.quality_score >= threshold
    return state
