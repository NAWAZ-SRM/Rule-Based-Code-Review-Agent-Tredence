# app/core/engine.py
"""
    Implements the WorkflowGraph class and execution logic
    that wires nodes to tools, walks edges, and produces 
    the final WorkflowState and execution log for each run.
"""

from typing import Awaitable, Callable, Dict, List, Tuple
from .models import WorkflowState, GraphDefinition, ExecutionLogEntry
from .registry import ToolRegistry


NodeFunc = Callable[[WorkflowState], Awaitable[WorkflowState]]


class WorkflowGraph:
    """
    Minimal workflow engine supporting:
    - nodes as async callables
    - simple edges for sequencing
    - basic loop based on quality_score and threshold
    """
    def __init__(
        self,
        definition: GraphDefinition,
        registry: ToolRegistry,
    ) -> None:
        self.definition = definition
        self.registry = registry
        self._nodes: Dict[str, NodeFunc] = self._bind_nodes(definition.nodes)

    def _bind_nodes(self, node_mapping: Dict[str, str]) -> Dict[str, NodeFunc]:
        bound: Dict[str, NodeFunc] = {}
        for logical_name, tool_name in node_mapping.items():
            bound[logical_name] = self.registry.get(tool_name)
        return bound

    async def run(self, state: WorkflowState) -> Tuple[WorkflowState, List[ExecutionLogEntry]]:
        log: List[ExecutionLogEntry] = []
        current = self.definition.entry_node

        while True:
            node_func = self._nodes[current]
            state = await node_func(state)

            log.append(
                ExecutionLogEntry(
                    node=current,
                    message=f"Executed node '{current}'",
                    state_snapshot=state.model_dump(),
                )
            )

            if state.done:
                break

            next_node = self.definition.edges.get(current)
            if next_node is None:
                break

            current = next_node

        return state, log
