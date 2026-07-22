from app.audio.beats import compute_onset_envelope, detect_tempo_and_beats
from tests.audio_fixtures import make_click_track


def test_detect_tempo_and_beats_matches_known_bpm() -> None:
    sr = 22050
    true_bpm = 120.0
    y, true_beat_times = make_click_track(true_bpm, duration_sec=16.0, sr=sr)

    onset_env = compute_onset_envelope(y, sr)
    bpm, beat_times = detect_tempo_and_beats(y, sr, onset_env=onset_env)

    # 옥타브 오차(절반/두 배 템포로 잡히는 경우)를 허용해 강건하게 검증한다.
    ratio = bpm / true_bpm
    assert any(abs(ratio - expected) < 0.08 for expected in (0.5, 1.0, 2.0))
    assert len(beat_times) >= len(true_beat_times) * 0.7
