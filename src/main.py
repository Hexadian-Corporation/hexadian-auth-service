import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import httpx
import uvicorn
from fastapi import FastAPI
from hexadian_auth_common.fastapi import (
    JWTAuthDependency,
    _stub_jwt_auth,
    register_exception_handlers,
)
from motor.motor_asyncio import AsyncIOMotorClient
from opyoid import Injector
from starlette.middleware.cors import CORSMiddleware

from src.application.ports.inbound.auth_service import AuthService
from src.application.ports.inbound.portal_settings_service import PortalSettingsService
from src.application.ports.inbound.rbac_service import RbacService
from src.infrastructure.adapters.inbound.api.auth_router import init_router, router
from src.infrastructure.adapters.inbound.api.rbac_router import init_rbac_router, rbac_router
from src.infrastructure.adapters.inbound.api.settings_router import init_settings_router, settings_router
from src.infrastructure.config.dependencies import AppModule
from src.infrastructure.config.settings import Settings
from src.infrastructure.seed import seed_rbac

logger = logging.getLogger(__name__)


async def _admin_exists(motor_client: AsyncIOMotorClient, settings: Settings) -> bool:
    """Return True if a user belonging to the 'Admins' group already exists."""
    db = motor_client[settings.mongo_db]
    admins_group = await db["groups"].find_one({"name": "Admins"})
    if not admins_group:
        return False
    return await db["users"].find_one({"group_ids": str(admins_group["_id"])}) is not None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings: Settings = app.state.settings
    motor_client: AsyncIOMotorClient = app.state.motor_client
    http_client: httpx.AsyncClient = app.state.http_client

    db = motor_client[settings.mongo_db]
    await db["users"].create_index("username", unique=True)
    await db["users"].create_index("rsi_handle", unique=True)
    await db["refresh_tokens"].create_index("token", unique=True)
    await db["refresh_tokens"].create_index("expires_at", expireAfterSeconds=0)
    await db["auth_codes"].create_index("code", unique=True)
    await db["auth_codes"].create_index("expires_at", expireAfterSeconds=0)
    await db["permissions"].create_index("code", unique=True)
    await db["roles"].create_index("name", unique=True)
    await db["groups"].create_index("name", unique=True)

    if await _admin_exists(motor_client, settings):
        logger.info("RBAC seed: skipped (admin exists)")
    else:
        await seed_rbac.seed(settings)
        logger.info("RBAC seed: completed")
    yield

    await http_client.aclose()
    motor_client.close()


def create_app() -> FastAPI:
    settings = Settings()
    http_client = httpx.AsyncClient()
    module = AppModule(settings, http_client)
    injector = Injector([module])

    auth_service = injector.inject(AuthService)
    init_router(auth_service)

    rbac_service = injector.inject(RbacService)
    init_rbac_router(rbac_service)

    portal_settings_service = injector.inject(PortalSettingsService)
    init_settings_router(portal_settings_service)

    jwt_auth = JWTAuthDependency(secret=settings.jwt_secret, algorithm=settings.jwt_algorithm)

    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.state.settings = settings
    app.state.motor_client = module.motor_client
    app.state.http_client = http_client
    app.dependency_overrides[_stub_jwt_auth] = jwt_auth
    register_exception_handlers(app)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)
    app.include_router(rbac_router)
    app.include_router(settings_router)

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "service": settings.app_name}

    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8006, reload=True)
