# app/core/models.py
"""  
    Contains Pydantic models for the shared workflow state,
    graph definitions, and request/response schemas used by
    the FastAPI endpoints.'
"""
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class WorkflowState(BaseModel):
    """
    Shared state passed between nodes in the workflow.
    You can extend this model as the code review workflow evolves.
    """
    data: Dict[str, Any] = Field(default_factory=dict)
    quality_score: float = 0.0
    done: bool = False


class GraphDefinition(BaseModel):
    """
    Representation of a graph as described in the assignment:
    - nodes are logical names
    - edges define order
    - entry_node is where execution starts
    """
    nodes: Dict[str, str]           # logical node name -> tool name
    edges: Dict[str, str]           # from_node -> to_node
    entry_node: str
    threshold: float = 0.8          # used in code-review loop


class GraphCreateRequest(BaseModel):
    graph: GraphDefinition


class GraphCreateResponse(BaseModel):
    graph_id: str


class GraphRunRequest(BaseModel):
    graph_id: str
    initial_state: WorkflowState


class ExecutionLogEntry(BaseModel):
    node: str
    message: str
    state_snapshot: Dict[str, Any]


class GraphRunResponse(BaseModel):
    run_id: str
    final_state: WorkflowState
    log: List[ExecutionLogEntry]


class GraphRunStateResponse(BaseModel):
    run_id: str
    state: WorkflowState
    log: List[ExecutionLogEntry]
