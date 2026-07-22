"""애플리케이션 설정.

환경 변수(.env)에서 값을 읽어온다. 실제 키/경로는 저장소에 커밋하지 않고
`.env.example`을 복사한 `.env` 파일을 통해 로컬에서 설정한다.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "ADOFAI Map Generator"

    # 4단계: AI 연동 (Google Gemini 무료 티어). 비어 있으면 규칙 기반 파서로 대체 동작한다.
    gemini_api_key: str = ""

    # 업로드/생성 결과 저장 위치
    storage_dir: Path = Path("./data")

    # CORS 허용 origin ("*" 또는 콤마로 구분된 목록)
    allowed_origins: str = "*"

    @property
    def allowed_origins_list(self) -> list[str]:
        if self.allowed_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
