from app.audio.beats import compute_onset_envelope
from app.audio.tempo_changes import detect_tempo_changes
from tests.audio_fixtures import make_two_tempo_track


def test_detect_tempo_changes_finds_change_between_two_sections() -> None:
    sr = 22050
    y = make_two_tempo_track(bpm_a=85.0, bpm_b=170.0, duration_each_sec=10.0, sr=sr)

    onset_env = compute_onset_envelope(y, sr)
    changes = detect_tempo_changes(onset_env, sr)

    assert len(changes) >= 2
    bpms = [c.bpm for c in changes]
    assert max(bpms) - min(bpms) > 20.0
