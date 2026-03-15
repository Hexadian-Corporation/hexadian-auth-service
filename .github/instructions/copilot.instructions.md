<critical>Note: This is a living document and will be updated as we refine our processes. Always refer back to this for the latest guidelines. Update whenever necessary. Anytime you discover a new bug or issue, document it here to maintain a comprehensive history.</critical>

# Copilot Instructions — hhh-auth-service

## Project Context

**H³ (Hexadian Hauling Helper)** is a Star Citizen companion app for managing hauling contracts, owned by **Hexadian Corporation** (GitHub org: `Hexadian-Corporation`).

This service handles **user authentication** — registration, login, JWT tokens, and RSI account verification.

- **Repo:** `Hexadian-Corporation/hhh-auth-service`
- **Port:** 8006
- **Stack:** Python · FastAPI · MongoDB · pymongo · opyoid (DI) · pydantic-settings

## Architecture — Hexagonal (Ports & Adapters)

```
src/
├── main.py                          # FastAPI app factory + uvicorn
├── domain/
│   ├── models/                      # Pure dataclasses (no framework deps)
│   └── exceptions/                  # Domain-specific exceptions
├── application/
│   ├── ports/
│   │   ├── inbound/                 # Service interfaces (ABC)
│   │   └── outbound/               # Repository interfaces (ABC)
│   └── services/                    # Implementations of inbound ports
└── infrastructure/
    ├── config/
    │   ├── settings.py              # pydantic-settings (env prefix: HHH_AUTH_)
    │   └── dependencies.py          # opyoid DI Module
    └── adapters/
        ├── inbound/api/             # FastAPI router, DTOs (Pydantic), API mappers
        └── outbound/persistence/    # MongoDB repository, persistence mappers
```

**Key conventions:**
- Domain models are **pure Python dataclasses** — no Pydantic, no ORM
- DTOs at the API boundary are **Pydantic BaseModel** subclasses
- Mappers are **static classes** (`to_domain`, `to_dto`, `to_document`)
- DI uses **opyoid** (`Module`, `Injector`, `SingletonScope`)
- Repositories use **pymongo** directly (no ODM)
- Router pattern: **`init_router(service)` + module-level `router`** (standard pattern)

## Domain Model

- **User** — `id`, `username`, `email`, `hashed_password`, `roles` (default: `["user"]`), `is_active`

**Future (AUTH-1):** Will add `rsi_handle: str | None = None` and `rsi_verified: bool = False` for RSI account verification.

## RSI Verification Flow (not yet implemented)

1. `POST /auth/verify/start` — generates a unique code, user puts it in their RSI profile bio
2. `POST /auth/verify/confirm` — service fetches `robertsspaceindustries.com/citizens/{handle}`, checks for the code
3. `User.rsi_verified` is set to `true` on success

Handle validation: `^[A-Za-z0-9_-]{3,30}$` (strict, to prevent SSRF).

## Issue & PR Title Format

**Format:** `<type>(auth): description`

- Example: `feat(auth): RSI verification`
- Example: `fix(auth): correct JWT expiration handling`

**Allowed types:** `chore`, `fix`, `ci`, `docs`, `feat`, `refactor`, `test`, `build`, `perf`, `style`, `revert`

The issue title and PR title must be **identical**. PR body must include `Fixes #N`.

## Quality Standards

- `ruff check .` + `ruff format --check .` must pass
- `pytest --cov=src` with ≥90% coverage on changed lines (`diff-cover`)
- Type hints on all functions
- Squash merge only — PR title becomes the commit message

## Tooling

| Tool | Command |
|------|---------|
| Run tests | `uv run pytest` |
| Lint | `uv run --with ruff ruff check .` |
| Format | `uv run --with ruff ruff format .` |
