"""FastAPI 앱 진입점."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import ai_edit, audio, health, mapgen, storage
from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(title=settings.app_name)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(audio.router)
    app.include_router(mapgen.router)
    app.include_router(ai_edit.router)
    app.include_router(storage.router)

    return app


app = create_app()
