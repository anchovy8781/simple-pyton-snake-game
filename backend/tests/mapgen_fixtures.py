"""맵 생성 엔진 테스트용 합성 AudioAnalysisResult 생성 유틸리티."""

from app.models.audio import AudioAnalysisResult, DropEvent, EnergyPoint, TempoChangePoint


def make_analysis_result(
    bpm: float = 120.0,
    duration_sec: float = 16.0,
    beats_per_bar: int = 4,
    drop_time_sec: float | None = 8.0,
) -> AudioAnalysisResult:
    interval = 60.0 / bpm
    beat_times = []
    t = 0.0
    while t < duration_sec:
        beat_times.append(round(t, 6))
        t += interval

    downbeat_times = beat_times[::beats_per_bar]

    energy_profile = [
        EnergyPoint(
            time_sec=round(i * 0.1, 3),
            rms_db=-6.0 if (drop_time_sec is not None and i * 0.1 >= drop_time_sec) else -30.0,
        )
        for i in range(int(duration_sec / 0.1))
    ]

    drops = [DropEvent(time_sec=drop_time_sec, strength=12.0)] if drop_time_sec is not None else []

    return AudioAnalysisResult(
        duration_sec=duration_sec,
        sample_rate=22050,
        bpm=bpm,
        beat_times=beat_times,
        downbeat_times=downbeat_times,
        energy_profile=energy_profile,
        tempo_changes=[TempoChangePoint(time_sec=0.0, bpm=bpm)],
        drops=drops,
    )
