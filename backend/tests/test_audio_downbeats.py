from app.audio.beats import compute_onset_envelope, detect_tempo_and_beats
from app.audio.downbeats import detect_downbeats
from tests.audio_fixtures import make_click_track


def test_detect_downbeats_picks_accented_beats() -> None:
    sr = 22050
    beats_per_bar = 4
    y, _ = make_click_track(
        bpm=128.0, duration_sec=16.0, sr=sr, accent_every=beats_per_bar, accent_gain=2.2
    )

    onset_env = compute_onset_envelope(y, sr)
    _, beat_times = detect_tempo_and_beats(y, sr, onset_env=onset_env)
    downbeat_times = detect_downbeats(beat_times, onset_env, sr, beats_per_bar=beats_per_bar)

    assert len(downbeat_times) >= 2
    # 검출된 다운비트 사이의 간격이 한 마디(= 4박) 길이와 비슷해야 한다.
    beat_interval = 60.0 / 128.0
    bar_interval = beat_interval * beats_per_bar
    gaps = [b - a for a, b in zip(downbeat_times, downbeat_times[1:])]
    assert all(abs(gap - bar_interval) < beat_interval for gap in gaps)
