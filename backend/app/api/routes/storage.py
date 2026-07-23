"""ADOFAI(.adofai) 레벨 파일 내보내기/불러오기/검증 API."""

import json
import re

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel

from app.mapgen.models import GeneratedMap
from app.storage.adofai_reader import parse_adofai_document
from app.storage.adofai_writer import build_adofai_document
from app.storage.exceptions import AdofaiParseError
from app.storage.validator import PlayabilityIssue, validate_adofai_document

router = APIRouter(prefix="/storage", tags=["storage"])

_UNSAFE_FILENAME_CHARS = re.compile(r"[^A-Za-z0-9 _\-.가-힣]")


class ExportRequest(BaseModel):
    existing_map: GeneratedMap
    song_filename: str
    song_name: str = ""
    artist: str = ""
    author: str = ""
    offset_ms: int = 0
    output_filename: str = "level"


class PlayabilityIssueResponse(BaseModel):
    severity: str
    message: str
    tile_index: int | None = None


class PlayabilityReportResponse(BaseModel):
    is_playable: bool
    issues: list[PlayabilityIssueResponse]


class ValidateRequest(BaseModel):
    existing_map: GeneratedMap
    song_filename: str = "song.mp3"


def _to_report_response(issues: list[PlayabilityIssue], is_playable: bool) -> PlayabilityReportResponse:
    return PlayabilityReportResponse(
        is_playable=is_playable,
        issues=[
            PlayabilityIssueResponse(severity=i.severity, message=i.message, tile_index=i.tile_index)
            for i in issues
        ],
    )


@router.post("/export")
async def export_adofai(request: ExportRequest) -> Response:
    document = build_adofai_document(
        request.existing_map,
        song_filename=request.song_filename,
        song_name=request.song_name,
        artist=request.artist,
        author=request.author,
        offset_ms=request.offset_ms,
    )

    # 내보내기 직전 자체 검증: 우리가 만든 파일이 실제로 원본과 정확히
    # 같은 타이밍으로 다시 읽히는지 확인한다. 여기서 오류(error)가 나오면
    # 절대 정상적인 경우가 아니므로(왕복 테스트로 이미 검증된 로직이다),
    # 깨진 파일을 그대로 내려주는 대신 500으로 막는다.
    report = validate_adofai_document(document, original_map=request.existing_map)
    if not report.is_playable:
        detail = "; ".join(i.message for i in report.errors)
        raise HTTPException(status_code=500, detail=f"생성된 파일이 플레이 가능성 검증에 실패했습니다: {detail}")

    content = json.dumps(document, ensure_ascii=False)
    filename = _sanitize_filename(request.output_filename)

    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}.adofai"'},
    )


@router.post("/import", response_model=GeneratedMap)
async def import_adofai(file: UploadFile = File(...)) -> GeneratedMap:
    raw = await file.read()
    try:
        document = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"올바른 JSON 파일이 아닙니다: {exc}") from exc

    try:
        return parse_adofai_document(document)
    except AdofaiParseError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/validate", response_model=PlayabilityReportResponse)
async def validate_map(request: ValidateRequest) -> PlayabilityReportResponse:
    """맵을 실제로 저장하지 않고, 플레이 가능성만 미리 점검한다."""
    document = build_adofai_document(request.existing_map, song_filename=request.song_filename)
    report = validate_adofai_document(document, original_map=request.existing_map)
    return _to_report_response(report.issues, report.is_playable)


def _sanitize_filename(name: str) -> str:
    cleaned = _UNSAFE_FILENAME_CHARS.sub("", name).strip()
    return cleaned or "level"
