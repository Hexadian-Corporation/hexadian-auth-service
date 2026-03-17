<critical>Note: This is a living document and will be updated as we refine our processes. Always refer back to this for the latest guidelines. Update whenever necessary.</critical>

# Copilot Instructions — hexadian-auth-service

## Project Context

**Hexadian Auth Service** is a standalone centralized identity platform by **Hexadian Corporation** (GitHub org: `Hexadian-Corporation`). Used across Hexadian projects including H³ (Hexadian Hauling Helper).

This service handles **user authentication**, **JWT token management**, **RBAC (Groups → Roles → Permissions)**, **RSI account verification**, and **authorization code flow** for external apps.

- **Repo:** `Hexadian-Corporation/hexadian-auth-service`
- **Port:** 8006
- **Stack:** Python · FastAPI · MongoDB · pymongo · opyoid (DI) · pydantic-settings · PyJWT · hexadian-auth-common

## Related Repositories

| Repo | Purpose |
|------|---------|
| [`hexadian-auth-common`](https://github.com/Hexadian-Corporation/hexadian-auth-common) | Shared Python library for JWT validation + FastAPI auth dependencies. Installed in all H³ Python backend services. |
| [`hexadian-auth-common-php`](https://github.com/Hexadian-Corporation/hexadian-auth-common-php) | PHP counterpart of auth-common — same JWT contract, PSR-15 middleware. For PHP consumers. |

Both auth-common packages conform to `JWT_CONTRACT.md` (hosted in hexadian-auth-common) and validate the tokens this service issues.

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
│   │   └── outbound/               # Repository / external service interfaces (ABC)
│   └── services/                    # Implementations of inbound ports
└── infrastructure/
    ├── config/
    │   ├── settings.py              # pydantic-settings (env prefix: HEXADIAN_AUTH_)
    │   └── dependencies.py          # opyoid DI Module
    ├── adapters/
    │   ├── inbound/api/             # FastAPI router, DTOs (Pydantic), API mappers
    │   └── outbound/
    │       ├── persistence/         # MongoDB repositories, persistence mappers
    │       └── http/                # External HTTP adapters (RSI profile fetcher)
    └── seed/
        └── seed_rbac.py             # RBAC seed script (permissions, roles, groups, admin)
```

**Auth frontends (subdirectories in this repo):**

```
auth-portal/                         # User-facing frontend (port 3003)
├── src/
│   ├── pages/                       # LoginPage, RegisterPage, VerifyPage, ChangePasswordPage, CallbackPage
│   ├── api/                         # API client modules
│   ├── lib/                         # Token storage, authFetch helper
│   ├── layouts/
│   └── types/                       # TypeScript types (AuthorizeRequest, TokenResponse, User)
├── package.json                     # React 19, Vite, Tailwind, Vitest
└── Dockerfile

auth-backoffice/                     # Admin frontend (port 3002)
├── src/
│   ├── pages/                       # LoginPage, UsersPage, UserDetailPage, RolesPage, RoleDetailPage,
│   │                                # GroupsPage, GroupDetailPage, PermissionsPage
│   ├── api/
│   ├── lib/
│   ├── layouts/
│   └── types/
├── package.json                     # React 19, Vite, Tailwind, Vitest
└── Dockerfile
```

**Key conventions:**
- Domain models are **pure Python dataclasses** — no Pydantic, no ORM
- DTOs at the API boundary are **Pydantic BaseModel** subclasses
- Mappers are **static classes** (`to_domain`, `to_dto`, `to_document`)
- DI uses **opyoid** (`Module`, `Injector`, `SingletonScope`)
- Repositories use **pymongo** directly (no ODM)
- Router pattern: **`init_router(service)` + module-level `router`** (standard pattern)
- JWT auth uses **hexadian-auth-common[fastapi]** (`JWTAuthDependency`, `require_permission`, `_stub_jwt_auth`)

## Domain Models

- **User** — `id`, `username`, `hashed_password`, `group_ids` (list[str]), `is_active`, `rsi_handle`, `rsi_verified`, `rsi_verification_code`
- **Permission** — `id`, `code` (e.g., `contracts:read`), `description`
- **Role** — `id`, `name`, `description`, `permission_ids` (list[str])
- **Group** — `id`, `name`, `description`, `role_ids` (list[str])
- **RefreshToken** — `id`, `user_id`, `token` (opaque UUID), `expires_at`, `revoked`
- **AuthCode** — `id`, `code`, `user_id`, `redirect_uri`, `state`, `expires_at`, `used`
- **TokenResponse** — `access_token`, `refresh_token`, `token_type` (default: `"bearer"`), `expires_in` (seconds)

> **Note:** `email` field was removed (M12). `rsi_handle` is required on registration. `group_ids` replaces the old `roles` list.

## RBAC — 3-Level Hierarchy

```
Groups → Roles → Permissions
```

- **Users** belong to **Groups** (via `user.group_ids`)
- **Groups** contain **Roles** (via `group.role_ids`)
- **Roles** contain **Permissions** (via `role.permission_ids`)
- Permissions are **resolved at JWT refresh time** — the full permission set is embedded in the access token

**Seed data** (`uv run python -m src.infrastructure.seed.seed_rbac`):
- 22 permissions: `contracts:read/write/delete`, `locations:read/write/delete`, `commodities:read/write/delete`, `ships:read/write/delete`, `graphs:read/write/delete`, `routes:read/write/delete`, `users:read/write/admin`, `rbac:manage`
- 3 roles: Super Admin (all), Content Manager (read/write), Member (read-only + `contracts:write`)
- 2 groups: Admins (Super Admin role), Users (Member role — default for new registrations)
- Admin user: `admin` / `HEXADIAN_AUTH_ADMIN_PASSWORD` env var (default: `"admin"`)

## JWT / Token Architecture

**Access token** — JWT signed with HS256, 15-minute TTL.
Claims: `sub` (user_id), `username`, `groups`, `roles`, `permissions`, `rsi_handle`, `rsi_verified`, `iat`, `exp`. Permissions are resolved from the RBAC hierarchy at token creation/refresh and embedded in the JWT.

**Refresh token** — Opaque UUID, 7-day TTL, stored in MongoDB `refresh_tokens` collection with TTL index on `expires_at` and unique index on `token`. Revocable. On refresh, permissions are re-resolved from the database.

**Auth middleware:** All endpoints (except `/health`) require a valid JWT. Implemented via `hexadian-auth-common.fastapi.JWTAuthDependency`, injected through `app.dependency_overrides[_stub_jwt_auth]`. Permission checks use `require_permission()` dependency or manual `UserContext.permissions` inspection.

## Authorization Code Flow

For redirect-based authentication from external apps (e.g., H³ frontends):

1. App redirects to `auth-portal/login?redirect_uri=<callback>&state=<random>`
2. User authenticates on auth-portal
3. `POST /auth/authorize` generates a single-use auth code (60s TTL), returns `{code, state, redirect_uri}`
4. Auth-portal redirects to `redirect_uri?code=<code>&state=<state>`
5. App calls `POST /auth/token/exchange {code, redirect_uri}` → `{access_token, refresh_token}`

`redirect_uri` is validated against `HEXADIAN_AUTH_ALLOWED_REDIRECT_ORIGINS`.

## RSI Verification Flow

1. `POST /auth/verify/start?user_id={id}` — body: `{"rsi_handle": "..."}`. Generates verification string, stores in `rsi_verification_code`.
2. User pastes the string into their RSI profile bio.
3. `POST /auth/verify/confirm?user_id={id}` — scrapes RSI profile at `robertsspaceindustries.com/citizens/{handle}`, checks bio contains the string. Sets `rsi_verified = true`.

Handle validation: `^[A-Za-z0-9_-]{3,30}$` (strict, to prevent SSRF).

## Environment Variables

All settings use `HEXADIAN_AUTH_` prefix.

| Variable | Default | Description |
|---|---|---|
| `HEXADIAN_AUTH_MONGO_URI` | `mongodb://localhost:27017` | MongoDB connection string |
| `HEXADIAN_AUTH_MONGO_DB` | `hexadian_auth` | Database name |
| `HEXADIAN_AUTH_HOST` | `0.0.0.0` | Server bind host |
| `HEXADIAN_AUTH_PORT` | `8006` | Service port |
| `HEXADIAN_AUTH_JWT_SECRET` | `change-me-in-production` | JWT signing secret |
| `HEXADIAN_AUTH_JWT_ALGORITHM` | `HS256` | JWT algorithm |
| `HEXADIAN_AUTH_JWT_EXPIRATION_MINUTES` | `15` | Access token expiration (minutes) |
| `HEXADIAN_AUTH_JWT_REFRESH_EXPIRATION_DAYS` | `7` | Refresh token expiration (days) |
| `HEXADIAN_AUTH_ALLOWED_ORIGINS` | `["http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://localhost:3003"]` | CORS allowed origins |
| `HEXADIAN_AUTH_ALLOWED_REDIRECT_ORIGINS` | *(same as allowed_origins)* | Valid redirect URIs for auth code flow |
| `HEXADIAN_AUTH_ADMIN_PASSWORD` | `admin` | Initial admin user password (seed script) |

## API

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/auth/register` | None | Register a new user |
| `POST` | `/auth/login` | None | Authenticate and get access + refresh tokens |
| `POST` | `/auth/token/refresh` | None | Refresh access token using refresh token |
| `POST` | `/auth/token/revoke` | None | Revoke a refresh token |
| `POST` | `/auth/authorize` | None | Generate authorization code (redirect auth flow) |
| `POST` | `/auth/token/exchange` | None | Exchange authorization code for tokens |
| `GET` | `/auth/users/{user_id}` | JWT (self or `users:read`) | Get user by ID |
| `GET` | `/auth/users` | `users:read` | List all users |
| `DELETE` | `/auth/users/{user_id}` | `users:admin` | Delete a user |
| `POST` | `/auth/verify/start` | JWT | Start RSI verification (generates code) |
| `POST` | `/auth/verify/confirm` | JWT | Confirm RSI verification (checks profile bio) |
| `GET` | `/health` | None | Health check |

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

### CLI (recommended)

All project commands are available via `uv run auth <command>`:

| Action | Command |
|--------|---------|
| Start everything (Docker) | `uv run auth up` |
| Stop everything | `uv run auth down` |
| Install all deps | `uv run auth setup` |
| Local dev with hot-reload | `uv run auth start` |
| Follow logs | `uv run auth logs [service]` |
| Container status | `uv run auth ps` |
| Seed RBAC data | `uv run auth seed` |
| Test | `uv run auth test` |
| Lint | `uv run auth lint` |

### Backend (Python)

| Action | Command |
|--------|---------|
| Setup | `uv sync` |
| Setup (with dev deps) | `uv sync --all-extras` |
| Run (dev) | `uv run uvicorn src.main:app --reload --port 8006` |
| Run in Docker | `docker compose up` |
| Test | `uv run pytest` |
| Lint | `uv run ruff check .` |
| Format | `uv run ruff format .` |
| Seed RBAC data | `uv run python -m src.infrastructure.seed.seed_rbac` |

### Auth Portal Frontend (port 3003)

| Action | Command |
|--------|---------|
| Setup | `cd auth-portal && npm ci` |
| Dev | `cd auth-portal && npm run dev` |
| Build | `cd auth-portal && npm run build` |
| Test | `cd auth-portal && npm test` |
| Lint | `cd auth-portal && npm run lint` |
| Type check | `cd auth-portal && npm run type-check` |

### Auth Backoffice Frontend (port 3002)

| Action | Command |
|--------|---------|
| Setup | `cd auth-backoffice && npm ci` |
| Dev | `cd auth-backoffice && npm run dev` |
| Build | `cd auth-backoffice && npm run build` |
| Test | `cd auth-backoffice && npm test` |
| Lint | `cd auth-backoffice && npm run lint` |
| Type check | `cd auth-backoffice && npm run type-check` |

## Maintenance Rules

- **Keep the README up to date.** When you add, remove, or change commands, environment variables, API endpoints, domain models, or architecture — update `README.md`. The README is the source of truth for developers.
- **Keep the monorepo CLI service registry up to date.** When adding or removing a service, update `SERVICES`, `FRONTENDS`, `COMPOSE_SERVICE_MAP`, and `SERVICE_ALIASES` in `hexadian-hauling-helper/hhh_cli/__init__.py`, plus the `docker-compose.yml` entry.

## Organization Profile Maintenance

- **Keep the org profile README up to date.** When repositories, ports, architecture, workflows, security policy, or ownership change, update Hexadian-Corporation/.github/profile/README.md in the public .github repo.
- **Treat the org profile as canonical org summary.** Ensure descriptions in this repo remain consistent with the organization profile README.