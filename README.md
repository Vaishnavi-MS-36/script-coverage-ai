# Script Coverage AI 🎬

An AI-powered screenplay analysis platform that generates professional "script coverage" reports — the same kind of evaluation film studios, production companies, and literary agencies use internally to assess whether a script is worth developing further.

Built as a personal full-stack project combining practical LLM integration with real-world film industry workflows.

---

## Table of Contents
- [The Problem](#the-problem)
- [What It Does](#what-it-does)
- [Live Demo](#live-demo)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [How the AI Analysis Works](#how-the-ai-analysis-works)
- [Getting Started](#getting-started)
- [API Overview](#api-overview)
- [Project Structure](#project-structure)
- [What I Learned / Challenges Solved](#what-i-learned--challenges-solved)
- [Future Improvements](#future-improvements)

---

## The Problem

In the film industry, "coverage" is a written evaluation of a screenplay — typically 1-2 pages covering the story's logline, genre, structure, character development, and a recommendation on whether it's worth pursuing. Studios and agencies pay professional "readers" to write these for every script submission, since executives don't have time to read every full screenplay themselves.

This project automates a first-pass version of that process using an LLM, giving writers and small production teams a fast, structured way to get feedback on a script before it goes to a professional reader — or simply as a self-assessment tool.

## What It Does

1. A user uploads a screenplay file (`.pdf` or `.txt`)
2. The system extracts the raw text from the file
3. The extracted script is sent to Google's Gemini API with a carefully structured prompt
4. Gemini returns a structured coverage report containing:
   - **Logline** — a one-sentence summary of the story
   - **Genre** classification
   - **Tone** description
   - **Marketability score** (out of 10) with reasoning
   - **Pacing notes** — structural/pacing feedback
   - **Character arc summary**
   - **Comparable films** — similar existing movies
   - **Strengths** and **weaknesses** of the script
5. The report is saved to the database and displayed in a clean dashboard
6. Users can view, revisit, or delete their past screenplay analyses at any time

## Live Demo

🔗 [screenplay.vaishverse.xyz](#) *(coming soon)*

## Tech Stack

**Backend**
- [FastAPI](https://fastapi.tiangolo.com) — Python web framework for the API
- [SQLModel](https://sqlmodel.tiangolo.com) — ORM combining SQLAlchemy + Pydantic
- [PostgreSQL](https://www.postgresql.org) — relational database
- [Alembic](https://alembic.sqlalchemy.org) — database migrations
- [pypdf](https://pypdf.readthedocs.io) — PDF text extraction
- [Google Gemini API](https://ai.google.dev) (`gemini-2.5-flash`) — LLM-powered script analysis

**Frontend**
- [React](https://react.dev) + [TypeScript](https://www.typescriptlang.org)
- [Vite](https://vitejs.dev) — build tool
- [TanStack Router](https://tanstack.com/router) — file-based routing
- [TanStack Query](https://tanstack.com/query) — server state management
- [Tailwind CSS](https://tailwindcss.com) + [shadcn/ui](https://ui.shadcn.com) — styling and components
- Auto-generated, fully-typed API client from the backend's OpenAPI schema

**Infrastructure**
- Docker Compose — local development environment (multi-container: backend, frontend, database, reverse proxy)
- Traefik — reverse proxy / routing
- JWT-based authentication with secure password hashing

## Architecture
┌─────────────┐      HTTP       ┌──────────────┐      SQL       ┌────────────┐
│   React     │ ─────────────►  │   FastAPI    │ ─────────────► │ PostgreSQL │
│  Frontend   │ ◄─────────────  │   Backend    │ ◄───────────── │            │
└─────────────┘   JSON/REST     └──────┬───────┘                └────────────┘
│
│ HTTPS
▼
┌───────────────┐
│  Gemini API   │
│ (Google AI)   │
└───────────────┘
- The frontend never talks to Gemini directly — all LLM calls happen server-side, keeping the API key secure and allowing for validation, caching, and cost control.
- Screenplay text and AI-generated reports are persisted in PostgreSQL, so reports don't need to be regenerated on every view.

## How the AI Analysis Works

The core of this project is prompt design and structured output handling:

1. Extracted screenplay text is truncated to a safe token limit and inserted into a system prompt that instructs Gemini to act as a professional script reader
2. The prompt explicitly requests a **strict JSON schema** as output (no markdown, no prose wrapper) to make parsing reliable
3. The backend parses the returned JSON, handles edge cases (e.g., Gemini occasionally wrapping output in code fences), and stores it as a native JSON column in PostgreSQL
4. If the AI call fails (rate limits, malformed output, etc.), the screenplay's status is marked `failed` with the error captured — so failures are visible and debuggable rather than silent

## Getting Started

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop)
- A free [Google Gemini API key](https://aistudio.google.com/apikey)

### Setup

```bash
git clone https://github.com/Vaishnavi-MS-36/script-coverage-ai.git
cd script-coverage-ai
cp .env.example .env
```

Edit `.env` and set:
- `SECRET_KEY`, `FIRST_SUPERUSER_PASSWORD`, `POSTGRES_PASSWORD` — generate each with:
```bash
  openssl rand -hex 32
```
- `GEMINI_API_KEY` — from Google AI Studio

Start everything:
```bash
docker compose watch
```

Visit:
- **Frontend:** http://localhost:5173
- **API docs (Swagger UI):** http://localhost:8000/docs
- **Database viewer (Adminer):** http://localhost:8080

## API Overview

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/screenplays/upload` | Upload a screenplay file and trigger AI analysis |
| `GET` | `/api/v1/screenplays/` | List all screenplays for the current user |
| `GET` | `/api/v1/screenplays/{id}` | Get a single screenplay's details/report |
| `DELETE` | `/api/v1/screenplays/{id}` | Delete a screenplay |

Full interactive API documentation is available at `/docs` when running locally.

## Project Structure
script-coverage-ai/
├── backend/
│   ├── app/
│   │   ├── api/routes/screenplays.py   # Screenplay endpoints + AI logic
│   │   ├── models.py                    # Database models (SQLModel)
│   │   ├── alembic/versions/            # Database migrations
│   │   └── core/config.py               # App settings/env config
├── frontend/
│   ├── src/
│   │   ├── routes/_layout/screenplays.tsx  # Main upload/dashboard page
│   │   └── client/                          # Auto-generated API client
└── compose.yml                           # Docker Compose services
## What I Learned / Challenges Solved

This project involved debugging a realistic set of full-stack/DevOps issues:
- Setting up a local multi-container Docker environment from scratch on Windows (WSL2 + Docker Desktop)
- Diagnosing and fixing Alembic migration state corruption after a file-sync issue between host and container
- Managing Python dependency locking (`uv.lock`) inside a workspace-based monorepo structure
- Handling LLM API integration robustly — structured prompt design, JSON parsing edge cases, and graceful failure handling for rate limits
- Wiring a fully-typed frontend API client generated from a live backend OpenAPI schema

## Future Improvements

- [ ] PDF export of the coverage report
- [ ] Support for longer screenplays via chunked analysis
- [ ] Comparison view across multiple drafts of the same script
- [ ] Deployment with CI/CD pipeline (GitHub Actions)

---

Built by [Vaishnavi](https://github.com/Vaishnavi-MS-36)