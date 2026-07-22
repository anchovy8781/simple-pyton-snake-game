"""음량(에너지) 곡선 계산."""

import librosa
import numpy as np

from app.audio.beats import DEFAULT_HOP_LENGTH
from app.models.audio import EnergyPoint


def compute_rms_curve(
    y: np.ndarray, sr: int, hop_length: int = DEFAULT_HOP_LENGTH
) -> tuple[np.ndarray, np.ndarray]:
    """프레임 단위의 (시간, RMS dB) 곡선을 계산한다.

    드롭/템포 변화 검출처럼 세밀한 시간 해상도가 필요한 내부 로직은
    이 원본 해상도의 곡선을 그대로 사용한다.
    """
    rms = librosa.feature.rms(y=y, hop_length=hop_length)[0]
    times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop_length)
    rms_db = librosa.amplitude_to_db(rms, ref=np.max)
    return times, rms_db


def downsample_curve(
    times: np.ndarray,
    values: np.ndarray,
    sr: int,
    hop_length: int,
    target_points_per_sec: float = 10.0,
) -> tuple[np.ndarray, np.ndarray]:
    """API 응답 크기를 줄이기 위해 곡선을 목표 해상도로 평균 다운샘플링한다."""
    frame_rate = sr / hop_length
    step = max(1, round(frame_rate / target_points_per_sec))
    if step <= 1 or len(values) == 0:
        return times, values

    n = (len(values) // step) * step
    if n == 0:
        return times, values

    values_ds = values[:n].reshape(-1, step).mean(axis=1)
    times_ds = times[:n].reshape(-1, step).mean(axis=1)
    return times_ds, values_ds


def build_energy_profile(
    times: np.ndarray,
    rms_db: np.ndarray,
    sr: int,
    hop_length: int = DEFAULT_HOP_LENGTH,
    target_points_per_sec: float = 10.0,
) -> list[EnergyPoint]:
    times_ds, rms_db_ds = downsample_curve(times, rms_db, sr, hop_length, target_points_per_sec)
    return [
        EnergyPoint(time_sec=float(t), rms_db=float(v)) for t, v in zip(times_ds, rms_db_ds, strict=True)
    ]
