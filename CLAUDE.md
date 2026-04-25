# Nimbus — Claude Code Context

## Project
Autonomous SWE agent. Backend: FastAPI (Python 3.12). Frontend: Next.js 14. Live at get-nimbus.com.

## Repo structure
backend/          FastAPI app, entry: main.py, run with: PYTHONPATH=. .venv/bin/python -m uvicorn main:app --reload
frontend/         Next.js 14 app
backend/.venv/    Python virtualenv (do not touch)

## Key backend modules
agent/orchestrator.py   — full task lifecycle
agent/planner.py        — Claude Opus plan generation
agent/implementer.py    — Claude Sonnet tool-use loop
services/rag.py         — BM25 + Voyage vector hybrid retrieval
models/task.py          — Task, Repo, Workspace SQLModel definitions
api/routes/tasks.py     — REST + WebSocket endpoints

## API base
Local: http://localhost:8000
All endpoints use JSON. Task WebSocket: ws://localhost:8000/tasks/{task_id}/ws

## Active build: NIM-1 (CLI)
Building a pip-installable CLI at backend/cli/
Entry point: nimbus run "task description"
Auto-detects GitHub remote, auto-registers workspace/repo, streams logs via WebSocket.

## Code style
- No comments in code
- Python type hints throughout
- Async everywhere in backend
- Never use em dashes in any output strings
