import numpy as np

from app.audio.energy import build_energy_profile, compute_rms_curve, downsample_curve


def test_compute_rms_curve_higher_for_louder_segment() -> None:
    sr = 22050
    quiet = 0.01 * np.sin(2 * np.pi * 440 * np.arange(sr * 2) / sr)
    loud = 0.8 * np.sin(2 * np.pi * 440 * np.arange(sr * 2) / sr)
    y = np.concatenate([quiet, loud]).astype(np.float32)

    times, rms_db = compute_rms_curve(y, sr)

    midpoint = len(rms_db) // 2
    quiet_mean = rms_db[: midpoint - 5].mean()
    loud_mean = rms_db[midpoint + 5 :].mean()

    assert loud_mean > quiet_mean
    assert len(times) == len(rms_db)


def test_downsample_curve_reduces_point_count() -> None:
    sr = 22050
    hop_length = 512
    frame_rate = sr / hop_length
    n = int(frame_rate * 10)  # 10초 분량
    times = np.arange(n) / frame_rate
    values = np.sin(times)

    times_ds, values_ds = downsample_curve(times, values, sr, hop_length, target_points_per_sec=10.0)

    assert len(times_ds) < len(times)
    assert len(times_ds) == len(values_ds)


def test_build_energy_profile_returns_energy_points() -> None:
    sr = 22050
    y = 0.5 * np.sin(2 * np.pi * 440 * np.arange(sr * 3) / sr).astype(np.float32)

    times, rms_db = compute_rms_curve(y, sr)
    profile = build_energy_profile(times, rms_db, sr)

    assert len(profile) > 0
    assert all(hasattr(p, "time_sec") and hasattr(p, "rms_db") for p in profile)
