"""오디오 업로드/분석 API."""

import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.audio.analyzer import analyze_audio
from app.audio.exceptions import AudioAnalysisError, AudioLoadError, UnsupportedAudioFormatError
from app.audio.loader import SUPPORTED_EXTENSIONS
from app.models.audio import AudioAnalysisResult

router = APIRouter(prefix="/audio", tags=["audio"])


@router.post("/analyze", response_model=AudioAnalysisResult)
async def analyze_audio_file(file: UploadFile = File(...)) -> AudioAnalysisResult:
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
            return analyze_audio(tmp_path)
        except UnsupportedAudioFormatError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except AudioLoadError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except AudioAnalysisError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
