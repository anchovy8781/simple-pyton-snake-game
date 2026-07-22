"""템포(BPM) 변화 감지."""

import librosa
import numpy as np

from app.audio.beats import DEFAULT_HOP_LENGTH
from app.models.audio import TempoChangePoint


def detect_tempo_changes(
    onset_env: np.ndarray,
    sr: int,
    hop_length: int = DEFAULT_HOP_LENGTH,
    window_sec: float = 4.0,
    bpm_change_threshold: float = 6.0,
) -> list[TempoChangePoint]:
    """구간별 로컬 템포를 추정해 이전 구간 대비 유의미하게(threshold 이상)
    바뀐 지점만 반환한다. 첫 항목은 곡 시작 시점의 기준 템포다.
    """
    local_tempo = librosa.feature.tempo(
        onset_envelope=onset_env, sr=sr, hop_length=hop_length, aggregate=None
    )
    if len(local_tempo) == 0:
        return []

    frame_rate = sr / hop_length
    window_frames = max(1, int(window_sec * frame_rate))

    changes: list[TempoChangePoint] = []
    prev_bpm: float | None = None
    for start in range(0, len(local_tempo), window_frames):
        segment = local_tempo[start : start + window_frames]
        if segment.size == 0:
            continue

        bpm = float(np.median(segment))
        time_sec = start / frame_rate
        if prev_bpm is None or abs(bpm - prev_bpm) >= bpm_change_threshold:
            changes.append(TempoChangePoint(time_sec=time_sec, bpm=bpm))
            prev_bpm = bpm

    return changes
