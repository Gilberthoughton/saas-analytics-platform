# Contributing

Thanks for your interest! This is a monorepo with a FastAPI **backend** and a
Next.js **frontend**.

## Prerequisites

- Python 3.12+, Node.js 20+
- Docker (optional, for the full stack with PostgreSQL + Redis)

## Quick start (Docker)

```bash
cp backend/.env.example backend/.env   # set a real SECRET_KEY
docker compose up --build
# frontend: http://localhost:3000 · backend docs: http://localhost:8000/docs
```

## Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

ruff check . && ruff format --check .   # lint
SECRET_KEY=dev pytest                    # tests (hermetic: SQLite + in-memory cache)
uvicorn app.main:app --reload            # run (needs PostgreSQL + Redis, or sqlite via .env)
```

## Frontend

```bash
cd frontend
npm install
npm run lint && npm run typecheck && npm test && npm run build
npm run dev      # http://localhost:3000
```

## Pre-commit hooks

This repo uses the [pre-commit](https://pre-commit.com) framework (Ruff for the
backend, ESLint for the frontend, plus hygiene checks):

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

## Commit messages

We follow [**Conventional Commits**](https://www.conventionalcommits.org):
`feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `ci`, `build`. Examples:

```
feat(events): add batch ingestion endpoint
fix(analytics): invalidate cache on ingest
docs(readme): add architecture diagram
```

## Pull requests

Branch off `main`, keep changes focused, ensure the quality gate (lint,
typecheck, tests, build) passes, and fill in the PR template.
