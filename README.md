
## How to run


```bash
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Open the API docs at:

```bash
http://127.0.0.1:8000/docs
```



## Manual Execution via Swagger UI

You can exercise the full workflow step by step using the built-in docs at `http://127.0.0.1:8000/docs`.

### 1. Create a graph (`POST /graph/create`)

1. Start the server:

   ```bash
   python -m uvicorn app.main:app --reload
   ```

2. Open `http://127.0.0.1:8000/docs` in your browser.
3. Expand **POST /graph/create** and click **Try it out**.
4. Use this sample body as the graph definition:

   ```bash
   {
     "graph": {
       "nodes": {
         "extract": "extract_functions",
         "complexity": "check_complexity",
         "issues": "detect_issues",
         "suggest": "suggest_improvements",
         "evaluate": "evaluate_quality"
       },
       "edges": {
         "extract": "complexity",
         "complexity": "issues",
         "issues": "suggest",
         "suggest": "evaluate"
       },
       "entry_node": "extract",
       "threshold": 0.8
     }
   }
   ```

5. Click **Execute** and copy the `graph_id` from the response:

   ```bash
   {
     "graph_id": "YOUR_GRAPH_ID_HERE"
   }
   ```

---

### 2. Run the graph (`POST /graph/run`)

1. In the docs, expand **POST /graph/run** and click **Try it out**.
2. Paste the `graph_id` from the previous step into this request body:

   ```bash
   {
     "graph_id": "YOUR_GRAPH_ID_HERE",
     "initial_state": {
       "data": {
         "source_code": "def add(a, b):\n    print(\"debug\", a, b)\n    # TODO: handle edge cases\n    return a + b\n",
         "quality_threshold": 0.8
       },
       "quality_score": 0.0,
       "done": false
     }
   }
   ```

3. Click **Execute** and inspect the response.  
   You will get a `run_id`, the `final_state`, and an execution `log`:

   ```bash
   {
     "run_id": "YOUR_RUN_ID_HERE",
     "final_state": {
       "data": {
         "source_code": "...",
         "quality_threshold": 0.8,
         "functions": ["add"],
         "complexity_score": 0.01,
         "issues": [
           "Debug prints found",
           "TODO comments present"
         ],
         "issue_count": 2,
         "suggestions": [
           "Remove debug print statements or use logging instead",
           "Resolve or track TODO items before production"
         ]
       },
       "quality_score": 0.0,
       "done": true
     },
     "log": [
       { "node": "extract", "...": "..." },
       { "node": "complexity", "...": "..." },
       { "node": "issues", "...": "..." },
       { "node": "suggest", "...": "..." },
       { "node": "evaluate", "...": "..." }
     ]
   }
   ```

---

### 3. Inspect stored run state (`GET /graph/state/{run_id}`)

1. Copy the `run_id` from the `POST /graph/run` response.
2. In the docs, expand **GET /graph/state/{run_id}**.
3. Click **Try it out**, paste the `run_id` into the path parameter, and **Execute**.
4. The response returns the stored state and log for that run; it should match the data you saw from `POST /graph/run`.

---

## Single Execution (Simple Paste-and-Review)

If you only want to paste some Python code and get a review in a single call, use the convenience endpoint. No manual graph creation or `graph_id` handling is required.

### `POST /graph/review/simple`

1. In the docs, expand **POST /graph/review/simple** and click **Try it out**.
2. Use this sample body:

   ```bash
   {
     "source_code": "def add(a, b):\n    print(\"debug\", a, b)\n    # TODO: handle edge cases\n    return a + b\n\ncode = \"result = eval('1+2')\"\n",
     "quality_threshold": 0.8
   }
   ```

3. Click **Execute**.

The engine will:

- Ensure a default code-review graph exists (creating one in memory if needed).
- Run your code through the workflow (extract functions → complexity → issues → suggestions → quality).
- Return a single response with `run_id`, `final_state`, and the step-by-step `log`.

You will see issues such as debug prints, TODO comments, and usage of `eval`, along with corresponding suggestions and a computed `quality_score`.


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
