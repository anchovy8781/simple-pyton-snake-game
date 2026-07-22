"""맵 생성/구간 재생성 API."""

import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from app.audio.analyzer import analyze_audio
from app.audio.exceptions import AudioAnalysisError, AudioLoadError, UnsupportedAudioFormatError
from app.audio.loader import SUPPORTED_EXTENSIONS
from app.mapgen.engine import generate_map, regenerate_segment
from app.mapgen.models import Difficulty, GeneratedMap

router = APIRouter(prefix="/mapgen", tags=["mapgen"])


@router.post("/generate", response_model=GeneratedMap)
async def generate_map_from_audio(
    file: UploadFile = File(...),
    difficulty: Difficulty = Form(Difficulty.NORMAL),
    seed: int | None = Form(None),
) -> GeneratedMap:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"지원하지 않는 오디오 형식입니다: {suffix or '(확장자 없음)'} "
                f"(지원: {', '.join(sorted(SUPPORTED_EXTENSIONS))})"
            ),
        )

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir) / f"upload{suffix}"
        with tmp_path.open("wb") as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)

        try:
            analysis = analyze_audio(tmp_path)
        except UnsupportedAudioFormatError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except AudioLoadError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except AudioAnalysisError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    return generate_map(analysis, difficulty, seed=seed)


class RegenerateSegmentRequest(BaseModel):
    existing_map: GeneratedMap
    start_sec: float
    end_sec: float
    difficulty: Difficulty | None = None
    seed: int | None = None


@router.post("/regenerate-segment", response_model=GeneratedMap)
async def regenerate_map_segment(request: RegenerateSegmentRequest) -> GeneratedMap:
    try:
        return regenerate_segment(
            request.existing_map,
            request.start_sec,
            request.end_sec,
            difficulty=request.difficulty,
            seed=request.seed,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
