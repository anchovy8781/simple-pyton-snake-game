"""FastAPI 앱 진입점.

이후 단계에서 오디오 분석(2단계), 맵 생성(3단계), Claude 연동(4단계),
파일 저장(6단계) 라우터가 이 앱에 순차적으로 등록된다.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import audio, health
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

    return app


app = create_app()
