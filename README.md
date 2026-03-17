# hexadian-auth-service

Centralized identity platform for **Hexadian Corporation** applications. Handles user authentication, JWT token management, RBAC (Groups → Roles → Permissions), RSI account verification, and authorization code flow for external apps.

Used across Hexadian projects including H³ (Hexadian Hauling Helper).

## Related Repositories

| Repo | Purpose |
|------|---------|
| [`hexadian-auth-common`](https://github.com/Hexadian-Corporation/hexadian-auth-common) | Shared Python library for JWT validation + FastAPI auth dependencies. Installed in all H³ Python services. |
| [`hexadian-auth-common-php`](https://github.com/Hexadian-Corporation/hexadian-auth-common-php) | PHP counterpart — same JWT contract, PSR-15 middleware. For PHP consumers. |

## Quick Start

```bash
uv run auth up
```

This single command builds and starts everything: auth API (`:8006`), MongoDB, auth-portal (`:3003`), and auth-backoffice (`:3002`).

## Auto-Seed / Default Admin

On **first startup** (no admin user in the database), the service automatically seeds the RBAC data:

- **22 permissions** (e.g., `hhh:contracts:read`, `auth:users:admin`, `auth:rbac:manage`)
- **9 roles** — Auth Admin, Auth User Manager, HHH Contracts/Locations/Commodities/Ships/Graphs/Routes Manager, HHH Viewer
- **3 groups** — Admins, Users, Content Managers
- **1 admin user** — username `admin`, password `admin`

The seed is **idempotent** — if an admin user already exists, the seed is skipped entirely. You will see one of these log messages on startup:

```
RBAC seed: completed        # first run — data was seeded
RBAC seed: skipped (admin exists)  # subsequent runs — nothing changed
```

### Overriding the Admin Password

The default password is set via the `admin_password` field in `src/infrastructure/config/settings.py`. Override it with the `HEXADIAN_AUTH_ADMIN_PASSWORD` environment variable:

```bash
HEXADIAN_AUTH_ADMIN_PASSWORD=my-secure-password uv run auth start
```

In Docker Compose, add the variable to the `auth-service` service:

```yaml
auth-service:
  environment:
    - HEXADIAN_AUTH_ADMIN_PASSWORD=my-secure-password
```

> **⚠️ Security Warning:** The default password (`admin`) is intended for local development only. **Always override `HEXADIAN_AUTH_ADMIN_PASSWORD` in staging, production, and any non-local environment.**

### Manual Seed (Fallback)

If you need to re-run the seed manually (e.g., after wiping the database), use:

```bash
uv run auth seed
# or directly:
uv run python -m src.infrastructure.seed.seed_rbac
```

The seed script lives at `src/infrastructure/seed/seed_rbac.py`.

## Architecture

Hexagonal architecture (Ports & Adapters) with two frontend SPAs in subdirectories:

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
    │   ├── inbound/api/             # FastAPI routers, DTOs (Pydantic), API mappers
    │   └── outbound/
    │       ├── persistence/         # MongoDB repositories, persistence mappers
    │       └── http/                # External HTTP adapters (RSI profile fetcher)
    └── seed/
        └── seed_rbac.py             # RBAC seed script

auth-portal/                         # User-facing frontend (port 3003)
auth-backoffice/                     # Admin frontend (port 3002)
```

## Stack

- Python 3.11+ / FastAPI / uvicorn
- MongoDB (database: `hexadian_auth`)
- opyoid (dependency injection)
- pymongo (MongoDB driver, no ODM)
- pydantic-settings (configuration)
- PyJWT (token management)
- hexadian-auth-common (shared JWT auth utilities)
- httpx (HTTP client for RSI profile fetching)

## Domain Models

| Model | Fields |
|---|---|
| **User** | `id`, `username`, `hashed_password`, `group_ids` (list), `is_active`, `rsi_handle`, `rsi_verified`, `rsi_verification_code` |
| **Permission** | `id`, `code`, `description` |
| **Role** | `id`, `name`, `description`, `permission_ids` (list) |
| **Group** | `id`, `name`, `description`, `role_ids` (list) |
| **RefreshToken** | `id`, `user_id`, `token`, `expires_at`, `revoked` |
| **AuthCode** | `id`, `code`, `user_id`, `redirect_uri`, `state`, `expires_at`, `used` |
| **TokenResponse** | `access_token`, `refresh_token`, `token_type`, `expires_in` |

All domain models are pure Python dataclasses — no Pydantic, no ORM.

## RBAC Model

Three-level hierarchy:

```
Users → Groups → Roles → Permissions
```

- **Users** belong to **Groups** (via `user.group_ids`)
- **Groups** contain **Roles** (via `group.role_ids`)
- **Roles** contain **Permissions** (via `role.permission_ids`)
- Permissions are resolved from the full hierarchy at token creation/refresh time and embedded in the JWT access token

### Seed Data

The seed script (`uv run auth seed`) creates:

- **22 permissions**: `hhh:contracts:read/write/delete`, `hhh:locations:read/write/delete`, `hhh:commodities:read/write/delete`, `hhh:ships:read/write/delete`, `hhh:graphs:read/write/delete`, `hhh:routes:read/write/delete`, `auth:users:read/write/admin`, `auth:rbac:manage`
- **9 roles**: Auth Admin (all `auth:*`), Auth User Manager (`auth:users:read/write`), HHH Contracts/Locations/Commodities/Ships/Graphs/Routes Manager (per-resource `hhh:*:read/write/delete`), HHH Viewer (all `hhh:*:read`)
- **3 groups**: Admins (Auth Admin + all HHH Managers), Users (HHH Viewer + HHH Contracts Manager — auto-assigned from `hhh-frontend`), Content Managers (Auth User Manager + all HHH Managers)
- **Admin user**: `admin` / password from `HEXADIAN_AUTH_ADMIN_PASSWORD` (default: `admin`)

The seed is idempotent and runs automatically on startup if no admin user exists.

## Token Architecture

**Access token** — JWT signed with HS256, 15-minute TTL.
Claims: `sub` (user_id), `username`, `groups`, `roles`, `permissions`, `rsi_handle`, `rsi_verified`, `iat`, `exp`.

**Refresh token** — Opaque UUID, 7-day TTL, stored in MongoDB with TTL index. Revocable. On refresh, permissions are re-resolved from the RBAC hierarchy.

**Auth middleware** — All endpoints (except `/health`, `/auth/register`, `/auth/login`, `/auth/token/*`, `/auth/authorize`) require a valid JWT. Implemented via `hexadian-auth-common` (`JWTAuthDependency`, `require_permission`).

## Authorization Code Flow

For redirect-based authentication from external apps (e.g., H³ frontends):

1. App redirects to `auth-portal/login?redirect_uri=<callback>&state=<random>`
2. User authenticates on auth-portal
3. `POST /auth/authorize` generates a single-use auth code (60s TTL), returns `{code, state, redirect_uri}`
4. Auth-portal redirects to `redirect_uri?code=<code>&state=<state>`
5. App calls `POST /auth/token/exchange {code, redirect_uri}` → `{access_token, refresh_token}`

`redirect_uri` is validated against `HEXADIAN_AUTH_ALLOWED_REDIRECT_ORIGINS`.

## RSI Verification Flow

Link a user account to a [Roberts Space Industries](https://robertsspaceindustries.com) profile:

1. `POST /auth/verify/start?user_id={id}` — body: `{"rsi_handle": "..."}`. Generates a verification string, stores it in `rsi_verification_code`.
2. User pastes the string into their RSI profile bio at `robertsspaceindustries.com/account/profile`.
3. `POST /auth/verify/confirm?user_id={id}` — scrapes the RSI profile page, checks the bio contains the verification string. Sets `rsi_verified = true` on success.

Handle validation: `^[A-Za-z0-9_-]{3,30}$`.

## API

### Auth Endpoints

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/auth/register` | None | Register a new user |
| `POST` | `/auth/login` | None | Authenticate and get tokens |
| `POST` | `/auth/token/refresh` | None | Refresh access token |
| `POST` | `/auth/token/revoke` | None | Revoke a refresh token |
| `POST` | `/auth/authorize` | None | Generate authorization code |
| `POST` | `/auth/token/exchange` | None | Exchange auth code for tokens |
| `POST` | `/auth/token/introspect` | None | Validate token and return claims |
| `GET` | `/auth/users/{user_id}` | JWT (self or `auth:users:read`) | Get user by ID |
| `GET` | `/auth/users` | `auth:users:read` | List all users |
| `PUT` | `/auth/users/{user_id}` | JWT (self or `auth:users:admin`) | Update user profile |
| `DELETE` | `/auth/users/{user_id}` | `auth:users:admin` | Delete a user |
| `POST` | `/auth/password/change` | JWT | Change own password |
| `POST` | `/auth/users/{user_id}/password-reset` | `auth:users:admin` | Admin password reset |
| `POST` | `/auth/verify/start` | JWT | Start RSI verification |
| `POST` | `/auth/verify/confirm` | JWT | Confirm RSI verification |
| `GET` | `/health` | None | Health check |

### RBAC Endpoints

| Method | Endpoint | Permission | Description |
|---|---|---|---|
| `POST` | `/rbac/permissions` | `auth:rbac:manage` | Create a permission |
| `GET` | `/rbac/permissions` | `auth:rbac:manage` | List all permissions |
| `GET` | `/rbac/permissions/{id}` | `auth:rbac:manage` | Get permission by ID |
| `PUT` | `/rbac/permissions/{id}` | `auth:rbac:manage` | Update a permission |
| `DELETE` | `/rbac/permissions/{id}` | `auth:rbac:manage` | Delete a permission |
| `POST` | `/rbac/roles` | `auth:rbac:manage` | Create a role |
| `GET` | `/rbac/roles` | `auth:rbac:manage` | List all roles |
| `GET` | `/rbac/roles/{id}` | `auth:rbac:manage` | Get role by ID |
| `PUT` | `/rbac/roles/{id}` | `auth:rbac:manage` | Update a role |
| `DELETE` | `/rbac/roles/{id}` | `auth:rbac:manage` | Delete a role |
| `POST` | `/rbac/groups` | `auth:rbac:manage` | Create a group |
| `GET` | `/rbac/groups` | `auth:rbac:manage` | List all groups |
| `GET` | `/rbac/groups/{id}` | `auth:rbac:manage` | Get group by ID |
| `PUT` | `/rbac/groups/{id}` | `auth:rbac:manage` | Update a group |
| `DELETE` | `/rbac/groups/{id}` | `auth:rbac:manage` | Delete a group |
| `POST` | `/rbac/users/{user_id}/groups` | `auth:users:admin` | Assign user to group |
| `DELETE` | `/rbac/users/{user_id}/groups/{group_id}` | `auth:users:admin` | Remove user from group |
| `GET` | `/rbac/users/{user_id}/permissions` | `auth:users:read` or self | Get resolved permissions |

## Auth Frontends

### Auth Portal (port 3003)

User-facing authentication SPA in `auth-portal/`. Handles login, registration, RSI verification, password change, and OAuth2 callback.

- React 19 + TypeScript 5.9 + Vite 8
- React Router v7
- Tailwind CSS v4 + shadcn/ui + lucide-react
- Vitest + Testing Library

| Command | Description |
|---|---|
| `cd auth-portal && npm install` | Install dependencies |
| `cd auth-portal && npm run dev` | Start dev server on port 3003 |
| `cd auth-portal && npm run build` | Type-check and build for production |
| `cd auth-portal && npm run lint` | ESLint check |
| `cd auth-portal && npm run type-check` | TypeScript type check |
| `cd auth-portal && npm test` | Run tests with Vitest |

| Variable | Default | Description |
|---|---|---|
| `VITE_AUTH_API_URL` | `http://localhost:8006` | Auth service API base URL |

### Auth Backoffice (port 3002)

Admin SPA in `auth-backoffice/`. Manages users, groups, roles, and permissions.

- React 19 + TypeScript 5.9 + Vite 8
- React Router v7
- Tailwind CSS v4 + shadcn/ui + lucide-react
- Vitest + Testing Library

| Command | Description |
|---|---|
| `cd auth-backoffice && npm install` | Install dependencies |
| `cd auth-backoffice && npm run dev` | Start dev server on port 3002 |
| `cd auth-backoffice && npm run build` | Type-check and build for production |
| `cd auth-backoffice && npm run lint` | ESLint check |
| `cd auth-backoffice && npm run type-check` | TypeScript type check |
| `cd auth-backoffice && npm test` | Run tests with Vitest |

The backoffice uses relative `/api/` paths, proxied via nginx to the auth service in production.

## Docker Compose

Standalone stack — no external dependencies:

```bash
uv run auth up        # or: docker compose up
```

| Service | Port | Description |
|---|---|---|
| `auth-service` | 8006 | FastAPI backend |
| `auth-mongo` | — | MongoDB 7 (internal only) |
| `auth-portal` | 3003 | User-facing SPA |
| `auth-backoffice` | 3002 | Admin SPA |

**Networks:**

- `hexadian-auth-inner-net` (internal) — auth-service ↔ auth-mongo only, no external access
- `hexadian-shared-net` — shared with other compose projects (e.g., H³ monorepo)

**Volumes:**

- `auth-data` — MongoDB data persistence

## Integration with H³

The H³ monorepo (`hexadian-hauling-helper`) auto-starts this service via `uv run hhh up`.
Clone this repo as a sibling of `hexadian-hauling-helper`:

```
hhh-workspace/
├── hexadian-hauling-helper/       # H³ monorepo
└── hexadian-auth-service/         # This repo (auto-started by hhh CLI)
```

The CLI detects whether auth is running and starts it automatically if needed.
To stop everything: `uv run hhh down` (stops both H³ and auth).

## Environment Variables

All settings use `HEXADIAN_AUTH_` prefix via pydantic-settings.

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
| `HEXADIAN_AUTH_ALLOWED_ORIGINS` | `["http://localhost:3000", ...]` | CORS allowed origins (JSON list) |
| `HEXADIAN_AUTH_ALLOWED_REDIRECT_ORIGINS` | `["http://localhost:3000", ...]` | Valid redirect URIs for auth code flow |
| `HEXADIAN_AUTH_ADMIN_PASSWORD` | `admin` | Initial admin user password (seed script) |
| `HEXADIAN_AUTH_APP_SIGNING_SECRET` | `change-me-in-production` | HMAC-SHA256 secret for verifying `app_id` signatures during registration |

## Development

### Prerequisites

- [uv](https://docs.astral.sh/uv/)
- MongoDB running on localhost:27017 (or use `uv run auth up` to start everything in Docker)

### CLI

All project commands are available via `uv run auth <command>`:

| Command | Description |
|---|---|
| `uv run auth up` | Build and start all containers (default if no command given) |
| `uv run auth down` | Stop all containers |
| `uv run auth setup` | Install backend and frontend dependencies (`uv sync` + `npm install`) |
| `uv run auth start` | Start auth API locally with hot-reload (ensures MongoDB is running) |
| `uv run auth logs [service]` | Follow container logs (optionally specify a service name) |
| `uv run auth ps` | Show status of all containers |
| `uv run auth seed` | Run RBAC seed script (permissions, roles, groups, admin user) |
| `uv run auth test` | Run pytest (extra args are forwarded, e.g. `uv run auth test -v`) |
| `uv run auth lint` | Run ruff linter |
| `uv run auth --help` | Show available commands |

### Manual Commands (Backend)

| Action | Command |
|---|---|
| Setup | `uv sync` (or `uv sync --all-extras` for dev deps) |
| Run (dev) | `uv run uvicorn src.main:app --reload --port 8006` |
| Test | `uv run pytest` |
| Lint | `uv run ruff check .` |
| Format | `uv run ruff format .` |
| Seed RBAC data | `uv run python -m src.infrastructure.seed.seed_rbac` |

## Quality Standards

- **Linting**: `ruff check .` + `ruff format --check .` must pass
- **Testing**: `pytest --cov=src` with ≥90% coverage on changed lines (`diff-cover`)
- **Type hints**: Required on all functions
- **Merge strategy**: Squash merge only — PR title becomes the commit message
