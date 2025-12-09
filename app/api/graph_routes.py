# app/api/graph_routes.py
""" This file defines all HTTP and WebSocket endpoints 
    for the workflow engine, including creating graphs, 
    running them (sync/async), checking run state, and 
    serving the simple “paste code and review” API.
"""

import asyncio
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from app.core.engine import WorkflowGraph
from app.core.models import (
    GraphCreateRequest,
    GraphCreateResponse,
    GraphRunRequest,
    GraphRunResponse,
    GraphRunStateResponse,
    ExecutionLogEntry,
    WorkflowState,
    GraphDefinition,
)
from app.core.registry import ToolRegistry
from app.core.storage import GraphRepository, RunRepository


router = APIRouter(prefix="/graph", tags=["graph"])

_graph_repo = GraphRepository()
_run_repo = RunRepository()
_registry = ToolRegistry()


def _ensure_default_graph() -> str:
    """
    Ensure there is at least one default code-review graph available.
    Returns its graph_id.
    """
    # If we already have graphs, just reuse the first one.
    if _graph_repo._graphs:
        return next(iter(_graph_repo._graphs.keys()))

    # Otherwise, build a default code-review graph in code.
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
        },
        entry_node="extract",
        threshold=0.8,
    )

    graph = WorkflowGraph(definition=definition, registry=_registry)
    graph_id = _graph_repo.create(graph)
    return graph_id


class SimpleReviewRequest(BaseModel):
    """
    Request body for the convenience code review endpoint.
    """
    source_code: str
    quality_threshold: float = 0.8


@router.post("/create", response_model=GraphCreateResponse)
def create_graph(payload: GraphCreateRequest) -> GraphCreateResponse:
    """
    Create a new workflow graph from the given definition and
    return its generated identifier.
    """
    graph = WorkflowGraph(definition=payload.graph, registry=_registry)
    graph_id = _graph_repo.create(graph)
    return GraphCreateResponse(graph_id=graph_id)


@router.post("/run", response_model=GraphRunResponse)
async def run_graph(payload: GraphRunRequest) -> GraphRunResponse:
    """
    Run an existing graph with an initial state and return the
    final state along with a basic execution log.
    """
    graph = _graph_repo.get(payload.graph_id)
    if graph is None:
        raise HTTPException(status_code=404, detail="Graph not found")

    final_state, log = await graph.run(payload.initial_state)

    run_id = _run_repo.create(
        {
            "graph_id": payload.graph_id,
            "state": final_state,
            "log": [entry.model_dump() for entry in log],
        }
    )

    return GraphRunResponse(
        run_id=run_id,
        final_state=final_state,
        log=log,
    )


@router.post("/run/async", response_model=GraphRunResponse)
async def run_graph_async(payload: GraphRunRequest) -> GraphRunResponse:
    """
    Start a graph run in the background and return immediately.
    The client can poll /graph/state/{run_id} to inspect progress.
    """
    graph = _graph_repo.get(payload.graph_id)
    if graph is None:
        raise HTTPException(status_code=404, detail="Graph not found")

    # Create an initial run entry.
    run_id = _run_repo.create(
        {
            "graph_id": payload.graph_id,
            "state": payload.initial_state,
            "log": [],
        }
    )

    async def _run_workflow() -> None:
        final_state, log = await graph.run(payload.initial_state)
        _run_repo.update(
            run_id,
            {
                "state": final_state,
                "log": [entry.model_dump() for entry in log],
            },
        )

    asyncio.create_task(_run_workflow())

    # Return immediately with the run_id and initial snapshot.
    return GraphRunResponse(
        run_id=run_id,
        final_state=payload.initial_state,
        log=[],
    )


@router.get("/state/{run_id}", response_model=GraphRunStateResponse)
def get_run_state(run_id: str) -> GraphRunStateResponse:
    """
    Return the stored state and execution log for a run.
    """
    run = _run_repo.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")

    return GraphRunStateResponse(
        run_id=run_id,
        state=run["state"],
        log=[ExecutionLogEntry(**entry) for entry in run["log"]],
    )


@router.post("/review/simple", response_model=GraphRunResponse)
async def simple_code_review(payload: SimpleReviewRequest) -> GraphRunResponse:
    """
    Convenience endpoint for reviewers:
    takes raw source code and runs it through the default
    code review graph in a single call.
    """
    default_graph_id = _ensure_default_graph()
    graph = _graph_repo.get(default_graph_id)

    if graph is None:
        raise HTTPException(status_code=404, detail="Default graph not found")

    initial_state = WorkflowState(
        data={
            "source_code": payload.source_code,
            "quality_threshold": payload.quality_threshold,
        }
    )

    final_state, log = await graph.run(initial_state)

    run_id = _run_repo.create(
        {
            "graph_id": default_graph_id,
            "state": final_state,
            "log": [entry.model_dump() for entry in log],
        }
    )

    return GraphRunResponse(
        run_id=run_id,
        final_state=final_state,
        log=log,
    )


@router.websocket("/ws/logs/{run_id}")
async def logs_websocket(websocket: WebSocket, run_id: str) -> None:
    """
    Stream the execution log for a run over a WebSocket connection.

    The server sends the current log on connect and then periodically
    checks for updates. This is intentionally simple and polling-based.
    """
    await websocket.accept()

    try:
        last_length = 0

        while True:
            run = _run_repo.get(run_id)
            if run is None:
                await websocket.send_json(
                    {"type": "error", "message": "Run not found"}
                )
                break

            log_entries = run.get("log", [])
            new_entries = log_entries[last_length:]

            for entry in new_entries:
                await websocket.send_json(
                    {
                        "type": "log",
                        "run_id": run_id,
                        "entry": entry,
                    }
                )

            last_length = len(log_entries)

            state = run.get("state")
            if state is not None and getattr(state, "done", False):
                await websocket.send_json(
                    {
                        "type": "completed",
                        "run_id": run_id,
                        "quality_score": getattr(state, "quality_score", None),
                    }
                )
                break

            await asyncio.sleep(0.3)

    except WebSocketDisconnect:
        # Client disconnected; exit quietly.
        return
