"""ADOFAI(.adofai) 레벨 파일 내보내기/불러오기 API."""

import json
import re

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel

from app.mapgen.models import GeneratedMap
from app.storage.adofai_reader import parse_adofai_document
from app.storage.adofai_writer import build_adofai_document
from app.storage.exceptions import AdofaiParseError

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


def _sanitize_filename(name: str) -> str:
    cleaned = _UNSAFE_FILENAME_CHARS.sub("", name).strip()
    return cleaned or "level"
