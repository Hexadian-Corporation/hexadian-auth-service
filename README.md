# hhh-auth-service

Authentication and user management microservice for **H³ – Hexadian Hauling Helper**.

## Domain

Handles user registration, login, and role-based access control. Uses PBKDF2-SHA256 for password hashing.

## Stack

- Python 3.11+ / FastAPI
- MongoDB (database: `hhh_auth`)
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

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `HHH_AUTH_MONGO_URI` | `mongodb://localhost:27017` | MongoDB connection string |
| `HHH_AUTH_MONGO_DB` | `hhh_auth` | Database name |
| `HHH_AUTH_PORT` | `8006` | Service port |
| `HHH_AUTH_JWT_SECRET` | `change-me-in-production` | JWT signing secret |
| `HHH_AUTH_JWT_ALGORITHM` | `HS256` | JWT algorithm |
| `HHH_AUTH_JWT_EXPIRATION_MINUTES` | `60` | Token expiration |

## API

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/auth/register` | Register a new user |
| `POST` | `/auth/login` | Authenticate and get token |
| `GET` | `/auth/users/{id}` | Get user by ID |
| `GET` | `/auth/users` | List all users |
| `DELETE` | `/auth/users/{id}` | Delete a user |
| `GET` | `/health` | Health check |
