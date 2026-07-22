"""오디오 분석 테스트용 합성 신호 생성 유틸리티.

실제 음원 파일 없이도 결정론적으로 BPM/드롭 등을 검증할 수 있도록,
알려진 박자 간격을 가진 "클릭 트랙"을 numpy로 직접 합성한다.
"""

import numpy as np


def make_click_track(
    bpm: float,
    duration_sec: float,
    sr: int = 22050,
    click_duration: float = 0.05,
    accent_every: int | None = None,
    accent_gain: float = 1.8,
) -> tuple[np.ndarray, np.ndarray]:
    """일정한 BPM으로 감쇠하는 톤(클릭)이 반복되는 신호를 생성한다.

    accent_every가 주어지면 그 배수 번째 클릭(다운비트 역할)의 진폭을
    accent_gain배로 키워, 다운비트 검출 테스트에 사용할 수 있게 한다.

    Returns:
        (y, beat_times): 합성된 파형과 실제 클릭이 배치된 시각(초) 배열.
    """
    interval = 60.0 / bpm
    n_samples = int(duration_sec * sr)
    y = np.zeros(n_samples, dtype=np.float32)

    t_click = np.arange(int(click_duration * sr)) / sr
    click_wave = (np.sin(2 * np.pi * 1200 * t_click) * np.exp(-t_click * 60)).astype(np.float32)

    beat_times = np.arange(0, duration_sec, interval)
    for i, bt in enumerate(beat_times):
        gain = 1.0
        if accent_every is not None and i % accent_every == 0:
            gain = accent_gain
        start = int(bt * sr)
        end = min(n_samples, start + len(click_wave))
        y[start:end] += gain * click_wave[: end - start]

    return y, beat_times


def make_two_tempo_track(
    bpm_a: float, bpm_b: float, duration_each_sec: float, sr: int = 22050
) -> np.ndarray:
    """서로 다른 두 BPM 구간을 이어붙인 신호를 생성한다 (템포 변화 감지 테스트용)."""
    y_a, _ = make_click_track(bpm_a, duration_each_sec, sr=sr)
    y_b, _ = make_click_track(bpm_b, duration_each_sec, sr=sr)
    return np.concatenate([y_a, y_b])
