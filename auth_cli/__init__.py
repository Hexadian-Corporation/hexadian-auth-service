"""CLI for hexadian-auth-service project orchestration.

Usage: uv run auth <command> [args...]

Commands are defined in COMMANDS and dispatched by main().
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# Always resolve relative to this file so docker compose finds the right
# docker-compose.yml regardless of the CWD the user invokes uv from.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

COMMANDS: dict[str, str] = {
    "up": "Build and start all containers (auth-service, auth-mongo, auth-portal, auth-backoffice)",
    "down": "Stop all containers",
    "setup": "Install backend and frontend dependencies (uv sync + npm install)",
    "start": "Start auth API locally with hot-reload (ensures MongoDB is running)",
    "logs": "Follow container logs (optionally specify a service name)",
    "ps": "Show status of all containers",
    "seed": "Run RBAC seed script (permissions, roles, groups, admin user)",
    "test": "Run pytest (extra args are forwarded)",
    "lint": "Run ruff linter",
}


def _run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    """Execute *cmd* and stream output to the terminal."""
    return subprocess.run(cmd, check=check)


def _compose(args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    """Run docker compose with the project directory pinned to PROJECT_ROOT."""
    return subprocess.run(
        ["docker", "compose", "--project-directory", str(PROJECT_ROOT), *args],
        check=check,
    )


def _print_help() -> None:
    print("Usage: uv run auth <command> [args...]\n")
    print("Commands:")
    for name, desc in COMMANDS.items():
        print(f"  {name:10s} {desc}")
    print(f"  {'--help':10s} Show this help message")


def cmd_up() -> None:
    _compose(["up", "--build", "-d"])
    print("\n✅ All services started:")
    print("   Auth API:       http://localhost:8006")
    print("   Auth Portal:    http://localhost:3003")
    print("   Auth Backoffice: http://localhost:3002")


def cmd_down() -> None:
    _compose(["down"])


def cmd_setup() -> None:
    _run(["uv", "sync"])
    _run(["npm", "install", "--prefix", "auth-portal"])
    _run(["npm", "install", "--prefix", "auth-backoffice"])


def cmd_start() -> None:
    # Ensure auth-mongo container is running
    result = subprocess.run(
        ["docker", "compose", "--project-directory", str(PROJECT_ROOT), "ps", "--status", "running", "--services"],
        capture_output=True,
        text=True,
        check=False,
    )
    if "auth-mongo" not in result.stdout.splitlines():
        print("Starting auth-mongo …")
        _compose(["up", "-d", "auth-mongo"])
    _run(["uv", "run", "uvicorn", "src.main:app", "--reload", "--host", "0.0.0.0", "--port", "8006"])


def cmd_logs(args: list[str]) -> None:
    _compose(["logs", "-f", *args], check=False)


def cmd_ps() -> None:
    _compose(["ps"])


def cmd_seed() -> None:
    _run(["uv", "run", "python", "-m", "src.infrastructure.seed.seed_rbac"])


def cmd_test(args: list[str]) -> None:
    _run(["uv", "run", "pytest", *args])


def cmd_lint() -> None:
    _run(["uv", "run", "ruff", "check", "."])


def main() -> None:
    args = sys.argv[1:]

    if not args:
        cmd_up()
        return

    if args[0] == "--help" or args[0] == "-h":
        _print_help()
        return

    command = args[0]
    extra = args[1:]

    if command == "up":
        cmd_up()
    elif command == "down":
        cmd_down()
    elif command == "setup":
        cmd_setup()
    elif command == "start":
        cmd_start()
    elif command == "logs":
        cmd_logs(extra)
    elif command == "ps":
        cmd_ps()
    elif command == "seed":
        cmd_seed()
    elif command == "test":
        cmd_test(extra)
    elif command == "lint":
        cmd_lint()
    else:
        print(f"Unknown command: {command}\n")
        _print_help()
        sys.exit(1)
