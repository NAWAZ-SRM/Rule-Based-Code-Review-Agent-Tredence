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
```# Rule-Based-Code-Review-Agent-Tredence
