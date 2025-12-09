# tests/test_engine.py
import asyncio

from app.core.engine import WorkflowGraph
from app.core.models import (
    WorkflowState,
    GraphDefinition,
)
from app.core.registry import ToolRegistry


def test_code_review_workflow_reaches_done():
    """
    Basic integration test for the workflow engine.

    It wires the code review tools into a small linear graph:
    extract_functions -> check_complexity -> detect_issues
    -> suggest_improvements -> evaluate_quality

    The main check is that the engine runs without errors and
    that the final state indicates the workflow is done.
    """
    registry = ToolRegistry()

    definition = GraphDefinition(
        nodes={
            "extract": "extract_functions",
            "complexity": "check_complexity",
            "issues": "detect_issues",
            "suggest": "suggest_improvements",
            "evaluate": "evaluate_quality",
        },
        edges={
            "extract": "complexity",
            "complexity": "issues",
            "issues": "suggest",
            "suggest": "evaluate",
            # evaluate is the last node; it sets state.done
        },
        entry_node="extract",
        threshold=0.8,
    )

    graph = WorkflowGraph(definition=definition, registry=registry)

    initial_state = WorkflowState(
        data={
            "source_code": """
def add(a, b):
    return a + b
""",
            "quality_threshold": 0.5,
        }
    )

    final_state, log = asyncio.run(graph.run(initial_state))

    assert final_state.done is True
    assert 0.0 <= final_state.quality_score <= 1.0
    assert len(log) == 5  # one entry per node
