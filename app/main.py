# app/main.py
"""Creates and configures the FastAPI application,
   attaching the graph routes so the workflow engine 
   can be accessed via HTTP and WebSocket endpoints."""

from fastapi import FastAPI
from app.api.graph_routes import router as graph_router


def create_app() -> FastAPI:
    """
    Application factory for the workflow engine API.
    """
    app = FastAPI(title="Workflow Engine")
    app.include_router(graph_router)
    return app


app = create_app()
