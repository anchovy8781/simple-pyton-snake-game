import numpy as np

from app.audio.drops import detect_drops


def _make_energy_curve(sr: int, hop_length: int, quiet_sec: float, loud_sec: float) -> tuple[np.ndarray, np.ndarray]:
    frame_rate = sr / hop_length
    quiet_frames = int(quiet_sec * frame_rate)
    loud_frames = int(loud_sec * frame_rate)

    rms_db = np.concatenate(
        [np.full(quiet_frames, -40.0), np.full(loud_frames, -6.0)]
    )
    times = np.arange(len(rms_db)) / frame_rate
    return times, rms_db


def test_detect_drops_finds_sustained_energy_jump() -> None:
    sr = 22050
    hop_length = 512
    times, rms_db = _make_energy_curve(sr, hop_length, quiet_sec=8.0, loud_sec=8.0)

    drops = detect_drops(times, rms_db, sr, hop_length)

    assert len(drops) == 1
    assert abs(drops[0].time_sec - 8.0) < 0.5


def test_detect_drops_ignores_short_transient_spike() -> None:
    sr = 22050
    hop_length = 512
    frame_rate = sr / hop_length
    n = int(frame_rate * 10)
    rms_db = np.full(n, -40.0)

    # 짧은 스파이크(약 0.2초)만 삽입 — 지속되지 않으므로 드롭이 아니어야 한다.
    spike_start = int(frame_rate * 5)
    spike_len = int(frame_rate * 0.2)
    rms_db[spike_start : spike_start + spike_len] = -5.0
    times = np.arange(n) / frame_rate

    drops = detect_drops(times, rms_db, sr, hop_length)

    assert drops == []
