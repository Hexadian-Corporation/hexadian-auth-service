# hexadian-auth-service

Authentication and user management microservice by **Hexadian Corporation**.

Designed as a standalone, reusable service across Hexadian projects. Includes RSI account verification for Star Citizen integration.

## Domain

Handles user registration, login, role-based access control, and RSI profile verification. Uses PBKDF2-SHA256 for password hashing.

## Stack

- Python 3.11+ / FastAPI
- MongoDB (database: `hexadian_auth`)
- opyoid (dependency injection)
- Hexagonal architecture (Ports & Adapters)

## Auth Portal (Frontend)

The `auth-portal/` directory contains the user-facing authentication portal built with:

- React 19 + TypeScript 5.9 + Vite 8
- React Router v7
- Tailwind CSS v4
- shadcn/ui + lucide-react

### Auth Portal Setup

```bash
cd auth-portal
npm install
npm run dev          # starts on port 3003
```

### Auth Portal Scripts

| Command | Description |
|---|---|
| `npm run dev` | Start dev server on port 3003 |
| `npm run build` | Type-check and build for production |
| `npm run lint` | ESLint check |
| `npm run type-check` | TypeScript type check |
| `npm test` | Run tests with Vitest |
| `npm run preview` | Preview production build |

### Auth Portal Environment Variables

| Variable | Default | Description |
|---|---|---|
| `VITE_AUTH_API_URL` | `http://localhost:8006` | Auth service API base URL |

## Prerequisites

- [uv](https://docs.astral.sh/uv/)
- MongoDB running on localhost:27017

## Setup

```bash
uv sync
```

## Run

```bash
uv run uvicorn src.main:app --reload --port 8006
```

## Test

```bash
uv run pytest
```

## Lint

```bash
uv run ruff check .
```

## Format

```bash
uv run ruff format .
```

## Run Standalone (Docker)

```bash
docker compose up
```

This starts the auth service, auth portal, and MongoDB — no external dependencies.
The auth portal is available on port 3003, the API on port 8006.
Both services are exposed on the `hexadian-net` Docker network so other compose projects can reach them.

## Integration with H³

The H³ monorepo (`hexadian-hauling-helper`) auto-starts this service via `uv run hhh up`.
Clone this repo as a sibling of `hexadian-hauling-helper`:

```
hhh-workspace/
├── hexadian-hauling-helper/       # H³ monorepo
└── hexadian-auth-service/     # This repo (auto-started by hhh CLI)
```

The CLI detects whether auth is running and starts it automatically if needed.
To stop everything: `uv run hhh down` (stops both H³ and auth).

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `HEXADIAN_AUTH_MONGO_URI` | `mongodb://localhost:27017` | MongoDB connection string |
| `HEXADIAN_AUTH_MONGO_DB` | `hexadian_auth` | Database name |
| `HEXADIAN_AUTH_PORT` | `8006` | Service port |
| `HEXADIAN_AUTH_JWT_SECRET` | `change-me-in-production` | JWT signing secret |
| `HEXADIAN_AUTH_JWT_ALGORITHM` | `HS256` | JWT algorithm |
| `HEXADIAN_AUTH_JWT_EXPIRATION_MINUTES` | `15` | Access token expiration (minutes) |
| `HEXADIAN_AUTH_JWT_REFRESH_EXPIRATION_DAYS` | `7` | Refresh token expiration (days) |
| `HEXADIAN_AUTH_ALLOWED_ORIGINS` | `["http://localhost:3000", ...]` | CORS allowed origins (JSON list) |

## API

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/auth/register` | Register a new user |
| `POST` | `/auth/login` | Authenticate and get access + refresh tokens |
| `POST` | `/auth/token/refresh` | Rotate tokens (new access + refresh, old refresh revoked) |
| `POST` | `/auth/token/revoke` | Revoke a refresh token |
| `GET` | `/auth/users/{id}` | Get user by ID |
| `GET` | `/auth/users` | List all users |
| `DELETE` | `/auth/users/{id}` | Delete a user |
| `POST` | `/auth/verify/start` | Start RSI verification |
| `POST` | `/auth/verify/confirm` | Confirm RSI verification |
| `GET` | `/health` | Health check |

## RSI Verification

Link a user account to a [Roberts Space Industries](https://robertsspaceindustries.com) profile.
The flow generates a unique code, the user places it in their RSI bio, and the service confirms the match.

### Prerequisites

- Auth service running on `http://localhost:8006` (see [Run](#run))
- A real RSI account at <https://robertsspaceindustries.com>

### Step 1 — Register a user

```bash
curl -s -X POST http://localhost:8006/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testpilot", "password": "s3cureP@ss", "rsi_handle": "TestPilot"}' | python -m json.tool
```

Example response:

```json
{
    "_id": "6649a2f1c...",
    "username": "testpilot",
    "roles": ["user"],
    "is_active": true,
    "rsi_handle": "TestPilot",
    "rsi_verified": false
}
```

Save the `_id` value — you will need it in the following steps.

### Step 2 — Start verification

```bash
curl -s -X POST "http://localhost:8006/auth/verify/start?user_id=<USER_ID>" \
  -H "Content-Type: application/json" \
  -d '{"rsi_handle": "YourRSIHandle"}' | python -m json.tool
```

Example response:

```json
{
    "verification_code": "Hexadian account validation code: alpha-brave-delta-ember-frost-ocean",
    "verified": false,
    "message": "Add the verification code to your RSI profile bio at https://robertsspaceindustries.com/account/profile and then call /auth/verify/confirm"
}
```

Copy the **full** `verification_code` string (including the `Hexadian account validation code:` prefix).

### Step 3 — Update your RSI profile

1. Go to <https://robertsspaceindustries.com/account/profile>
2. Paste the full verification string into the **Short Bio** field, for example:
   ```
   Hexadian account validation code: alpha-brave-delta-ember-frost-ocean
   ```
3. Click **Save**.
4. Confirm the text is publicly visible by visiting `https://robertsspaceindustries.com/citizens/YourRSIHandle` and checking the **Bio** section.

### Step 4 — Confirm verification

```bash
curl -s -X POST "http://localhost:8006/auth/verify/confirm?user_id=<USER_ID>" | python -m json.tool
```

**Success** — code found in bio:

```json
{
    "verification_code": null,
    "verified": true,
    "message": "RSI account verified successfully"
}
```

**Failure** — code not found in bio:

```json
{
    "verification_code": null,
    "verified": false,
    "message": "Verification code not found in RSI profile bio"
}
```

### Step 5 — Verify the result

```bash
curl -s http://localhost:8006/auth/users/<USER_ID> | python -m json.tool
```

The user should now show `rsi_verified: true`:

```json
{
    "_id": "6649a2f1c...",
    "username": "testpilot",
    "roles": ["user"],
    "is_active": true,
    "rsi_handle": "YourRSIHandle",
    "rsi_verified": true
}
```

### Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| `"Verification code not found in RSI profile bio"` | Bio is not publicly visible or the code was not saved | Visit `https://robertsspaceindustries.com/citizens/YourRSIHandle` and confirm the code appears in the Bio section |
| `"Verification code not found in RSI profile bio"` | Only part of the code was pasted | Make sure the **entire** string is in the bio, including the `Hexadian account validation code:` prefix |
| `422 Unprocessable Entity` on `/verify/start` | RSI handle does not match the required format | Handle must be 3–30 characters using only letters, digits, hyphens, and underscores (`^[A-Za-z0-9_-]{3,30}$`) |
| `404 Not Found` | Invalid `user_id` | Double-check the `_id` returned from `/auth/register` |
| Bio is too long after adding the code | RSI bio field has a character limit | Remove other bio text or shorten it so the verification string fits |
