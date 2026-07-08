# CLAUDE.md — I Am a Manager

Football manager simulator. Monorepo with a **FastAPI backend** (`backend/`) and a **Next.js frontend** (`frontend/`), orchestrated with Docker Compose and deployed via Terraform on AWS ECS (`deploy/`).

This file defines the mandatory development rules. When generating or changing code, follow them without exception. If a rule must be broken, explain why in the PR and propose updating this document.

---

## 1. General principles

- **Language:** code, identifiers, and file names in **English**. End-user-facing messages (API errors, UI text) in **Portuguese**, as already done (`"Credenciais inválidas"`).
- **Fail fast, fail loud:** validate input at the boundary (Pydantic schemas / TS types) and fail early with explicit errors. Never swallow exceptions silently.
- **No dead code:** leave no unused imports, variables, functions, or endpoints. Do not comment out code "for later" — git history handles that.
- **Consistency over personal preference:** follow the pattern of the existing file/layer before introducing a new style.
- **No secrets in the repository.** Use `.env` (git-ignored) derived from `.env.example`. Every new config variable must be added to `.env.example` with a safe example value.

---

## 2. Architecture and layer separation

### 2.1 Backend (`backend/app/`)

**Unidirectional** dependency flow. A layer may only import from layers below it:

```
routers/       → HTTP: routes, status codes, Depends. NO business logic.
  ↓
services/      → Business logic and orchestration. Receive Session in __init__.
  ↓
models/        → SQLAlchemy entities (tables). NO business logic.
schemas/       → Pydantic request/response contracts.
database/      → Session, engine, Base.
config/        → Settings (pydantic-settings). Single source of configuration.
dependencies/  → Reusable FastAPI dependencies (e.g. get_current_user).
exceptions.py  → Standardized HTTPException factories.
```

Non-negotiable rules:

- **Routers are thin.** They only: extract dependencies, call service(s), and assemble the response model. No SQL queries or business branching inside a router.
- **All business logic lives in `services/`.** A service is a class that receives `db: Session` in its constructor (current pattern — keep it).
- **Data access only through services.** Routers **never** import `select`/`Session` to query directly; they delegate to a service.
- **`models/` must not import from `services/` or `routers/`.** If you need that, the modeling is wrong.
- **Schemas ≠ Models.** Never return a raw SQLAlchemy object in an HTTP response. Convert via `SchemaResponse.model_validate(orm_obj)`.
- **Configuration only through `config/settings.py`.** No `os.getenv` scattered across the code. Add the field to `Settings` and consume `get_settings()`.

### 2.2 Frontend (`frontend/`)

Next 14 App Router. Separate responsibilities:

```
app/            → Routes, layouts, and pages (Server Components by default).
components/      → Reusable, business-state-free UI components.
hooks/           → Reusable state/effect logic (e.g. useAuth).
lib/             → HTTP client (api.ts), pure utilities, shared types.
```

Rules:

- **All API access goes through `lib/api.ts`** (`apiFetch`). No raw `fetch` scattered across components.
- Use `'use client'` only when there is state, effect, or browser event. Prefer Server Components.
- Types mirroring API contracts live in `lib/` and must reflect the backend schemas.
- No heavy business logic in a page component — extract it into a hook or util.

---

## 3. Security (top priority)

- **Never** commit secrets, tokens, passwords, or a real `JWT_SECRET`. In production, `jwt_secret` **must** come from a secret manager (never the default `"local_dev_secret_change_in_production"`).
- **Passwords:** always with `bcrypt` (already in use). Never log, return in a response, or compare in plain text. The `password` field **never** appears in a response schema.
- **Authentication:** protected routes use `Depends(get_current_user)`. Any new endpoint exposing user data is protected by default — only make it public with explicit justification.
- **Authorization / IDOR:** all resource data must be filtered by `current_user.user_id`. Never accept a `user_id` from the client to fetch another user's data. (See `players.py` as reference.)
- **Input validation:** every body/query is validated by a Pydantic schema. No raw `dict` from the request. Apply limits (string length, numeric ranges) in the schemas.
- **SQL:** exclusively via SQLAlchemy ORM / `select()`. **No** SQL built by string concatenation.
- **CORS:** origins come from `settings.cors_origins_list`. In production, do not use a wildcard origin. Revisit `allow_methods=["*"]`/`allow_headers=["*"]` before going to production.
- **Frontend secrets:** only `NEXT_PUBLIC_*` variables are exposed to the browser — never put a secret in them. The token currently lives in `localStorage` (XSS risk): do not introduce `dangerouslySetInnerHTML` nor render third-party HTML without sanitization.
- **Error messages:** generic for the user (do not leak email existence, stack traces, or internal detail). Technical detail only in server logs.
- **Dependencies:** do not add a dependency without a real need. Prefer what already exists. New libs must be version-pinned for production.

---

## 4. Automated tests

Tests are **mandatory** for every new business rule and every endpoint. A PR without a test for the new functionality is not done.

### Backend (pytest)
- Structure under `backend/tests/`, mirroring `app/` (`tests/services/test_auth_service.py`).
- **Services:** unit coverage mandatory — happy path + errors (invalid credentials, not found, authorization).
- **Routers:** integration tests with `TestClient`, using a test database (in-memory SQLite or an ephemeral Postgres) and **dependency overrides** (`app.dependency_overrides`).
- Every fixed bug is born with a regression test that fails before the fix.
- Never rely on the production `seed` in tests; use your own factories/fixtures.
- Coverage target: **≥ 80%** in `services/`.

### Frontend
- Components/hooks with logic: tests with Testing Library. Pure utils in `lib/` with unit tests.
- Do not test implementation details; test observable behavior.

### General rule
- Tests must be **deterministic and isolated** (no real network, no order dependency, no real clock — inject/`freeze` time).

---

## 5. Code quality and objective limits

These are hard limits (guardrails). When you exceed one, refactor before moving on.

| Metric | Limit |
|---|---|
| Cyclomatic complexity per function | **≤ 10** |
| Lines per function | **≤ 50** |
| Lines per file/module | **≤ 300** |
| Parameters per function | **≤ 5** (above that, use an object/keyword-only, as in `PlayersService.create`) |
| Nesting levels | **≤ 3** (prefer early-return / guard clauses) |
| Positional args in "wide" functions | use `*` to force keyword-only |

In addition:

- **One responsibility per function/class.** If the name needs "and", split it.
- **No magic numbers** — extract named constants (e.g. `ALGORITHM`, bcrypt `rounds`).
- **Mandatory typing:** type hints on all Python (params and return); TS in `strict` mode with no implicit `any`. No silencing the type-checker (`# type: ignore`, `as any`) without a comment justifying it.
- **No duplication (DRY),** but do not abstract too early: once duplicated 3×, extract.
- **Descriptive names.** No obscure abbreviations. Booleans with a prefix (`is_`, `has_`, `should_`).

---

## 6. Dependency structure

- **Backend:** dependencies in `requirements.txt`. Every new lib is added pinned to a compatible minimum version and justified in the PR. Do not introduce libs that duplicate something already present (e.g. `python-jose`, `passlib[bcrypt]`, `bcrypt` already exist).
- **Frontend:** `package.json` with versions locked via `package-lock.json` (committed). Do not run `npm install <pkg>` without a clear need; avoid heavy transitive dependencies.
- **No circular dependencies** between modules. The backend import graph must respect the hierarchy in section 2.1.
- **Dependency injection via FastAPI `Depends`** — do not instantiate global `Session`/services at module level inside routers.

---

## 7. Database and migrations

- Schema changes **always** via an Alembic migration in `backend/alembic/versions/`. Never edit the database manually nor alter an already-applied migration — create a new one.
- Every migration needs a working `upgrade` **and** `downgrade`.
- **Mind the column naming convention:** current models use camelCase (`teamName`, `userId`, `shirtNumber`) to match the frontend. **Keep each model's existing pattern**; do not mix snake/camel within the same table.
- Avoid N+1 queries: load required relations explicitly.

---

## 8. Error handling and logging

- HTTP errors via the factories in `app/exceptions.py` (e.g. `unauthorized(...)`) — do not instantiate `HTTPException` ad hoc across the code.
- The API error format is standardized by the handler in `main.py` (`{"message": ...}`). Respect it.
- **Logs:** use the standard `logging`. **Never** log passwords, tokens, JWTs, or PII. An error log includes enough context to diagnose, without sensitive data.
- Never use `print` for logging in production code.

---

## 9. Workflow

- **Branch:** work off `main`. One PR per logical unit of change.
- **Before finalizing a change, run and keep green:**
  - Backend: `pytest`, plus the project's linter/type-checker.
  - Frontend: `npm run lint` and `npm run build`.
- **Do not commit** artifacts: `__pycache__/`, `.env`, `node_modules/`, `.next/`. Verify `.gitignore`.
- Small, descriptive commits, in the imperative. Do not mix broad refactoring with a functional change in the same commit.
- When adding an endpoint, update the corresponding frontend types (`lib/`) in the same delivery to keep the contract in sync.

---

## 10. Checklist before considering a task done

- [ ] Layers respected (thin router, logic in the service, no data access outside a service).
- [ ] Inputs validated by schema; data filtered by `current_user`.
- [ ] No secret/PII in code, logs, or responses.
- [ ] New tests covering happy path and error path; full suite passing.
- [ ] Within the complexity/size limits (section 5).
- [ ] Complete typing; lint/type-check/build clean.
- [ ] Alembic migration created if the schema changed (with `downgrade`).
- [ ] `.env.example` updated if there is new configuration.
- [ ] Backend↔frontend contract consistent.
