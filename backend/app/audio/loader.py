"""오디오 파일 로딩."""

from pathlib import Path

import librosa
import numpy as np

from app.audio.exceptions import AudioLoadError, UnsupportedAudioFormatError

SUPPORTED_EXTENSIONS = {".mp3", ".ogg", ".wav"}


def load_audio(file_path: Path, sr: int | None = None) -> tuple[np.ndarray, int]:
    """오디오 파일을 모노 파형(y)과 샘플레이트(sr)로 불러온다.

    sr=None이면 원본 샘플레이트를 그대로 사용한다(librosa 기본값인
    22050Hz로의 불필요한 리샘플링을 피해 분석 속도를 높인다).
    """
    if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise UnsupportedAudioFormatError(
            f"지원하지 않는 오디오 형식입니다: {file_path.suffix} "
            f"(지원: {', '.join(sorted(SUPPORTED_EXTENSIONS))})"
        )
    if not file_path.exists():
        raise AudioLoadError(f"파일을 찾을 수 없습니다: {file_path}")

    try:
        y, loaded_sr = librosa.load(str(file_path), sr=sr, mono=True)
    except Exception as exc:  # librosa/audioread/soundfile은 백엔드별로 다른 예외를 던진다
        raise AudioLoadError(f"오디오 파일을 불러오는 중 오류가 발생했습니다: {file_path}") from exc

    if y.size == 0:
        raise AudioLoadError(f"오디오 데이터가 비어 있습니다: {file_path}")

    return y, loaded_sr
