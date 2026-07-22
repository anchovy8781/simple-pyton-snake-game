"""헬스체크 라우터. 서버가 정상 기동했는지 확인하는 용도."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
