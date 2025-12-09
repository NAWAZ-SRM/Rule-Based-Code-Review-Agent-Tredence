```markdown
## How to run
```

```bash
pip install -r requirements.txt
python -m pytest -q
python -m uvicorn app.main:app --reload
```

Open the API docs at:

```bash
http://127.0.0.1:8000/docs
```

---

## What the workflow engine supports

- Defining a minimal workflow/graph with:
  - Nodes as async Python functions operating on a shared Pydantic state.
  - Edges to control node execution order.
  - A simple loop mechanism via a terminal node that sets `state.done`.
- A tool registry that maps node names to reusable code-review tools.
- FastAPI endpoints to:
  - Create graphs.
  - Run graphs synchronously or asynchronously.
  - Inspect run state and execution logs.
  - Run a “paste code and review” flow in a single call.

---

## What I would improve with more time

- Replace in-memory repositories with a small SQLite/SQLModel backend for persistent graphs and runs.
- Add more sophisticated, rule-based code checks (and possibly pluggable rule sets) for the code review workflow.
- Introduce better observability: structured logging, richer execution metadata, and more robust WebSocket streaming for live log updates.
- Generalize the workflow engine further (typed node inputs/outputs, branching based on conditions in the state, and support for multiple workflows out of the box).

## File Overview

- `/app/api/graph_routes.py`  
  Defines all HTTP and WebSocket endpoints for the workflow engine, including creating graphs, running them (sync/async), checking run state, and the simple “paste code and review” API.

- `/app/core/engine.py`  
  Implements the `WorkflowGraph` class and execution logic that wires nodes to tools, walks edges, and produces the final `WorkflowState` and execution log for each run.

- `/app/core/models.py`  
  Contains Pydantic models for the shared workflow state, graph definitions, and request/response schemas used by the FastAPI endpoints.

- `/app/core/registry.py`  
  Maintains the tool registry: a mapping from tool names to async Python functions so graphs can reference tools by name when defining nodes.

- `/app/core/storage.py`  
  Provides in-memory repositories for storing graphs and runs (including their state and logs), with a simple interface designed to be swappable with a future SQLite-backed implementation.

- `/app/workflows/code_review.py`  
  Implements the rule-based code review tools (extract functions, estimate complexity, detect issues, suggest improvements, evaluate quality) that form the sample workflow required by the assignment.

- `/app/main.py`  
  Creates and configures the FastAPI application, attaching the graph routes so the workflow engine can be accessed via HTTP and WebSocket endpoints.
