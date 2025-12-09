# app/core/registry.py
"""
Maintains the tool registry: a mapping from tool names to async Python functions
so graphs can reference tools by name when defining nodes.

"""
from typing import Awaitable, Callable, Dict
from .models import WorkflowState


ToolFunc = Callable[[WorkflowState], Awaitable[WorkflowState]]


class ToolRegistry:
    """
    Simple in-memory registry for tools that can be used as nodes
    in the workflow graph.
    """
    def __init__(self) -> None:
        self._tools: Dict[str, ToolFunc] = {}
        self._register_default_tools()

    def _register_default_tools(self) -> None:
        # Tools used by the code review workflow are registered here.
        from ..workflows.code_review import (
            extract_functions,
            check_complexity,
            detect_issues,
            suggest_improvements,
            evaluate_quality,
        )

        self.register("extract_functions", extract_functions)
        self.register("check_complexity", check_complexity)
        self.register("detect_issues", detect_issues)
        self.register("suggest_improvements", suggest_improvements)
        self.register("evaluate_quality", evaluate_quality)

    def register(self, name: str, func: ToolFunc) -> None:
        self._tools[name] = func

    def get(self, name: str) -> ToolFunc:
        try:
            return self._tools[name]
        except KeyError:
            raise KeyError(f"Tool '{name}' is not registered")
