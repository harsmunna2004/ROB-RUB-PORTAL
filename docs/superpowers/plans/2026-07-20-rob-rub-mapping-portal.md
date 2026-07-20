# ROB/RUB Mapping Portal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and document a beginner-friendly React, FastAPI, Supabase mapping portal deployed as one Vercel project.

**Architecture:** A Vite React SPA calls FastAPI endpoints under `/api`. FastAPI owns hierarchy queries, ROB/RUB validation, duplicate checks, and Supabase writes using a server-only service key. Supabase SQL constraints preserve data integrity.

**Tech Stack:** React 18, Vite 5, Vitest, FastAPI, Pydantic, Supabase Python client, pytest, Vercel.

## Global Constraints

- No login or dashboard.
- RO, PIU, and project options come from the imported `projects` table.
- One project accepts multiple ROB/RUB entries through an add-row button.
- Both frontend and backend deploy in one Vercel project.
- Secrets never enter frontend code.

---

### Task 1: Backend API

**Files:**
- Create: `api/index.py`, `api/repository.py`, `api/models.py`, `api/config.py`, `requirements.txt`
- Test: `tests/backend/test_api.py`

**Interfaces:**
- Produces `GET /api/ros`, `GET /api/pius`, `GET /api/projects`, and `POST /api/mappings`.
- `POST /api/mappings` consumes `{upc: string, proposal_ids: string[]}` and produces per-ID statuses.

- [ ] Write API tests using an in-memory fake repository for hierarchy filtering and mapping outcomes.
- [ ] Run `pytest tests/backend -v` and confirm tests fail because API modules are absent.
- [ ] Implement configuration, models, repository abstraction, Supabase repository, and FastAPI routes.
- [ ] Run `pytest tests/backend -v` and confirm all backend tests pass.

### Task 2: React Mapping Form

**Files:**
- Create: `package.json`, `index.html`, `src/main.jsx`, `src/App.jsx`, `src/api.js`, `src/styles.css`, `vite.config.js`
- Test: `src/App.test.jsx`, `src/setupTests.js`

**Interfaces:**
- Consumes the four backend endpoints from Task 1.
- Produces dependent dropdowns, dynamic proposal-ID rows, submission feedback, and accessible loading/error states.

- [ ] Write component tests for hierarchy loading, dynamic rows, duplicates, and submission payloads.
- [ ] Run `npm test -- --run` and confirm tests fail because components are absent.
- [ ] Implement the API client and React form with minimal behavior required by tests.
- [ ] Run `npm test -- --run` and confirm frontend tests pass.

### Task 3: Database and Deployment

**Files:**
- Create: `supabase/schema.sql`, `sample-data/rob_rub_master_template.csv`, `sample-data/projects_template.csv`, `.env.example`, `.gitignore`, `vercel.json`

**Interfaces:**
- Database columns exactly match backend repository queries.
- Vercel routes `/api/*` to FastAPI and all other paths to the React build.

- [ ] Add idempotent PostgreSQL schema with keys, indexes, and table permissions.
- [ ] Add CSV templates matching import column names.
- [ ] Add environment and Vercel configuration without secrets.
- [ ] Run SQL/config consistency checks and frontend production build.

### Task 4: Beginner Guide and Final Verification

**Files:**
- Create: `README.md`

**Interfaces:**
- Documents prerequisites, Supabase setup/import, environment configuration, local terminals, tests, GitHub/Vercel deployment, and troubleshooting.

- [ ] Write numbered, copyable beginner instructions and explain every secret/URL placeholder.
- [ ] Run `pytest tests/backend -v`.
- [ ] Run `npm test -- --run`.
- [ ] Run `npm run build`.
- [ ] Review all files against the approved design and remove placeholders or leaked secrets.
