import uvicorn
from fastapi import FastAPI
from opyoid import Injector

from src.application.ports.inbound.auth_service import AuthService
from src.infrastructure.adapters.inbound.api.auth_router import init_router, router
from src.infrastructure.config.dependencies import AppModule
from src.infrastructure.config.settings import Settings


def create_app() -> FastAPI:
    settings = Settings()
    injector = Injector([AppModule(settings)])

    auth_service = injector.inject(AuthService)
    init_router(auth_service)

    app = FastAPI(title=settings.app_name)
    app.include_router(router)

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "service": settings.app_name}

    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8006, reload=True)
