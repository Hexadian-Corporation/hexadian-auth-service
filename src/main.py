import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from hexadian_auth_common.fastapi import (
    JWTAuthDependency,
    _stub_jwt_auth,
    register_exception_handlers,
)
from opyoid import Injector
from pymongo import MongoClient
from starlette.middleware.cors import CORSMiddleware

from src.application.ports.inbound.auth_service import AuthService
from src.application.ports.inbound.rbac_service import RbacService
from src.infrastructure.adapters.inbound.api.auth_router import init_router, router
from src.infrastructure.adapters.inbound.api.rbac_router import init_rbac_router, rbac_router
from src.infrastructure.config.dependencies import AppModule
from src.infrastructure.config.settings import Settings
from src.infrastructure.seed import seed_rbac

logger = logging.getLogger(__name__)


def _admin_exists(settings: Settings) -> bool:
    """Return True if a user belonging to the 'Admins' group already exists."""
    client: MongoClient = MongoClient(settings.mongo_uri)
    try:
        db = client[settings.mongo_db]
        admins_group = db["groups"].find_one({"name": "Admins"})
        if not admins_group:
            return False
        return db["users"].find_one({"group_ids": str(admins_group["_id"])}) is not None
    finally:
        client.close()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings: Settings = app.state.settings
    if _admin_exists(settings):
        logger.info("RBAC seed: skipped (admin exists)")
    else:
        seed_rbac.seed(settings)
        logger.info("RBAC seed: completed")
    yield


def create_app() -> FastAPI:
    settings = Settings()
    injector = Injector([AppModule(settings)])

    auth_service = injector.inject(AuthService)
    init_router(auth_service)

    rbac_service = injector.inject(RbacService)
    init_rbac_router(rbac_service)

    jwt_auth = JWTAuthDependency(secret=settings.jwt_secret, algorithm=settings.jwt_algorithm)

    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.state.settings = settings
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

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "service": settings.app_name}

    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8006, reload=True)
