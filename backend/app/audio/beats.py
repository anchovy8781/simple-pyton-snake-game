"""BPM 검출과 비트 트래킹."""

import librosa
import numpy as np

DEFAULT_HOP_LENGTH = 512
# librosa의 템포 추정이 극단적으로 조용하거나 짧은/특이한 오디오에서 드물게
# 0이나 NaN을 반환하는 경우가 있다. 이 값이 그대로 analysis.bpm으로
# 흘러가면 맵 생성 단계(schedule.py)에서 "60.0 / bpm"이 ZeroDivisionError로
# 죽는다 — 감지 자체가 실패했다는 뜻이므로 대중음악에서 흔한 중간값으로
# 대체한다.
FALLBACK_BPM = 120.0


def compute_onset_envelope(y: np.ndarray, sr: int, hop_length: int = DEFAULT_HOP_LENGTH) -> np.ndarray:
    """타격감(onset)의 강도를 프레임 단위로 나타내는 envelope.

    비트/다운비트/드롭 검출이 모두 이 envelope을 재사용하므로 한 번만 계산한다.
    """
    return librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop_length)


def detect_tempo_and_beats(
    y: np.ndarray,
    sr: int,
    onset_env: np.ndarray | None = None,
    hop_length: int = DEFAULT_HOP_LENGTH,
) -> tuple[float, np.ndarray]:
    """전역 BPM과 비트 타임스탬프(초)를 추정한다."""
    if onset_env is None:
        onset_env = compute_onset_envelope(y, sr, hop_length)

    tempo, beat_frames = librosa.beat.beat_track(
        onset_envelope=onset_env, sr=sr, hop_length=hop_length, trim=False
    )
    beat_times = librosa.frames_to_time(beat_frames, sr=sr, hop_length=hop_length)

    # librosa 버전에 따라 tempo가 스칼라 또는 길이 1 배열로 반환된다.
    bpm = float(np.atleast_1d(tempo)[0])
    if not np.isfinite(bpm) or bpm <= 0:
        bpm = FALLBACK_BPM

    return bpm, beat_times
