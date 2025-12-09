# app/core/storage.py
"""Provides in-memory repositories for storing graphs and
   runs (including their state and logs), with a simple 
   interface designed to be swappable with a future 
   SQLite-backed implementation.
"""

from typing import Dict, Any, Optional
from uuid import uuid4

from .engine import WorkflowGraph

class GraphRepository:
    """
    Simple repository abstraction for storing workflow graphs.
    Starts with in-memory storage; can be replaced by a DB-backed
    implementation later without changing the rest of the code.
    """
    def __init__(self) -> None:
        self._graphs: Dict[str, WorkflowGraph] = {}

    def create(self, graph: WorkflowGraph) -> str:
        graph_id = str(uuid4())
        self._graphs[graph_id] = graph
        return graph_id

    def get(self, graph_id: str) -> Optional[WorkflowGraph]:
        return self._graphs.get(graph_id)


class RunRepository:
    """
    Stores individual workflow runs and their state.
    Same idea as GraphRepository – keep the interface small and focused.
    """
    def __init__(self) -> None:
        self._runs: Dict[str, Dict[str, Any]] = {}

    def create(self, payload: Dict[str, Any]) -> str:
        run_id = str(uuid4())
        self._runs[run_id] = payload
        return run_id

    def get(self, run_id: str) -> Optional[Dict[str, Any]]:
        return self._runs.get(run_id)

    def update(self, run_id: str, payload: Dict[str, Any]) -> None:
        if run_id in self._runs:
            self._runs[run_id].update(payload)
