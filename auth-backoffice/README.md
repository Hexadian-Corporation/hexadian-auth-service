> **© 2026 Hexadian Corporation** — Licensed under [PolyForm Noncommercial 1.0.0 (Modified)](../LICENSE). No commercial use, no public deployment, no plagiarism. See [LICENSE](../LICENSE) for full terms.

# Auth Backoffice

Admin dashboard for the **Hexadian Auth Service**. Built with React, TypeScript, Vite, and Tailwind CSS.

## Quick Start

```bash
npm install
npm run dev        # http://localhost:3002
```

## Commands

| Command              | Description                  |
|----------------------|------------------------------|
| `npm run dev`        | Start dev server (port 3002) |
| `npm run build`      | Type-check + production build|
| `npm run type-check` | TypeScript type checking     |
| `npm run lint`       | ESLint                       |
| `npm test`           | Run tests (vitest)           |
| `npm run test:watch` | Run tests in watch mode      |
| `npm run preview`    | Preview production build     |

## Project Structure

```
src/
├── api/             # API client modules (auth, users, rbac)
├── layouts/         # Page layouts (DashboardLayout)
├── lib/             # Utilities (cn)
├── pages/           # Route pages
├── types/           # TypeScript interfaces
├── router.tsx       # Route definitions
├── main.tsx         # App entry point
└── __tests__/       # Tests
```

## Routes

| Path                  | Page              |
|-----------------------|-------------------|
| `/login`              | Login             |
| `/users`              | User list         |
| `/users/:id`          | User detail       |
| `/rbac/permissions`   | Permissions       |
| `/rbac/roles`         | Roles list        |
| `/rbac/roles/:id`     | Role detail       |
| `/rbac/groups`        | Groups list       |
| `/rbac/groups/:id`    | Group detail      |

## Docker

```bash
docker build -t auth-backoffice .
docker run -p 3002:3002 auth-backoffice
```

The nginx config proxies `/api/` requests to the auth service at `http://auth-service:8006/`.
