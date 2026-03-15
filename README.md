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

This starts the auth service with its own MongoDB instance — no external dependencies.
The service is exposed on the `hexadian-net` Docker network so other compose projects can reach it.

## Integration with H³

The H³ monorepo (`hhh-main`) auto-starts this service via `uv run hhh up`.
Clone this repo as a sibling of `hhh-main`:

```
hhh-workspace/
├── hhh-main/                  # H³ monorepo
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
| `HEXADIAN_AUTH_JWT_EXPIRATION_MINUTES` | `60` | Token expiration |

## API

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/auth/register` | Register a new user |
| `POST` | `/auth/login` | Authenticate and get token |
| `GET` | `/auth/users/{id}` | Get user by ID |
| `GET` | `/auth/users` | List all users |
| `DELETE` | `/auth/users/{id}` | Delete a user |
| `GET` | `/health` | Health check |
