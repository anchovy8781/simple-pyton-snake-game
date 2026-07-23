"""오디오 파일 로딩."""

from pathlib import Path

import audioread
import librosa
import numpy as np

from app.audio.exceptions import AudioLoadError, UnsupportedAudioFormatError
from app.audio.ffmpeg_setup import ensure_ffmpeg_on_path

SUPPORTED_EXTENSIONS = {".mp3", ".ogg", ".wav"}

# mp3처럼 압축된 포맷은 soundfile(libsndfile)이 실패하면 librosa가 내부적으로
# audioread로 넘어가는데, audioread는 PATH에 ffmpeg/avconv가 있어야 동작한다.
# 모듈을 불러오는 시점에 한 번만 시도해 이후의 모든 load_audio() 호출에 적용한다.
ensure_ffmpeg_on_path()


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
    except audioread.exceptions.NoBackendError as exc:
        raise AudioLoadError(
            f"이 오디오 파일을 디코딩할 수 없습니다(ffmpeg 백엔드 없음): {file_path} "
            "— 파일이 손상되었거나 지원하지 않는 인코딩일 수 있습니다. "
            "다른 mp3/wav/ogg 파일로 다시 시도해 보세요."
        ) from exc
    except Exception as exc:  # librosa/audioread/soundfile은 백엔드별로 다른 예외를 던진다
        raise AudioLoadError(f"오디오 파일을 불러오는 중 오류가 발생했습니다: {file_path}") from exc

    if y.size == 0:
        raise AudioLoadError(f"오디오 데이터가 비어 있습니다: {file_path}")

    return y, loaded_sr
