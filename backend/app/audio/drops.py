"""드롭(빌드업 이후 에너지 급상승) 감지."""

import numpy as np

from app.audio.beats import DEFAULT_HOP_LENGTH
from app.models.audio import DropEvent


def detect_drops(
    times: np.ndarray,
    rms_db: np.ndarray,
    sr: int,
    hop_length: int = DEFAULT_HOP_LENGTH,
    smooth_sec: float = 1.0,
    sustain_sec: float = 2.0,
    min_jump_db: float = 6.0,
) -> list[DropEvent]:
    """에너지가 급격히 상승한 뒤 일정 시간 이상 높게 유지되는 지점을 드롭으로 추정한다.

    순간적인 타격음(스파이크)과 구분하기 위해, 상승 직후 `sustain_sec` 동안의
    평균 에너지가 상승 이전 대비 충분히 높게 유지되는 경우만 드롭으로 채택한다.
    """
    if len(rms_db) == 0:
        return []

    frame_rate = sr / hop_length
    smooth_frames = max(1, int(smooth_sec * frame_rate))
    sustain_frames = max(1, int(sustain_sec * frame_rate))

    smoothed = _moving_average(rms_db, smooth_frames)

    # 인접 프레임끼리의 미분은 smoothing 창(smooth_sec)에 상승분이 분산되어
    # 실제 dB 점프보다 훨씬 작게 나타난다. 대신 `smooth_frames`만큼 이전
    # 시점과 비교해 "최근 smooth_sec 동안 얼마나 올랐는지"를 측정한다.
    diffs = np.zeros_like(smoothed)
    diffs[smooth_frames:] = smoothed[smooth_frames:] - smoothed[:-smooth_frames]

    if diffs.std() == 0:
        return []

    threshold = max(float(diffs.mean() + 2 * diffs.std()), min_jump_db)
    candidates = np.where(diffs >= threshold)[0]

    drops: list[DropEvent] = []
    last_drop_frame = -sustain_frames
    for idx in candidates:
        if idx - last_drop_frame < sustain_frames:
            continue  # 같은 드롭 근처의 중복 후보는 건너뛴다

        sustain_end = min(len(smoothed), idx + sustain_frames)
        if sustain_end - idx < sustain_frames:
            continue  # 곡 끝 부근이라 지속 여부를 판단할 구간이 부족

        sustained_level = float(smoothed[idx:sustain_end].mean())
        if sustained_level < smoothed[idx] - min_jump_db / 2:
            continue  # 상승 후 바로 꺼지면 드롭이 아니라 순간 타격음으로 간주

        drops.append(DropEvent(time_sec=float(times[idx]), strength=float(diffs[idx])))
        last_drop_frame = idx

    return drops


def _moving_average(values: np.ndarray, window: int) -> np.ndarray:
    if window <= 1:
        return values
    kernel = np.ones(window) / window
    return np.convolve(values, kernel, mode="same")
