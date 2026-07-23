import numpy as np

import app.audio.beats as beats_module
from app.audio.beats import FALLBACK_BPM, compute_onset_envelope, detect_tempo_and_beats
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


def test_detect_tempo_and_beats_falls_back_when_librosa_returns_zero_bpm(monkeypatch) -> None:
    """드물게 librosa가 조용하거나 특이한 오디오에서 bpm=0을 반환하면, 이후
    schedule.py의 "60.0 / bpm"이 ZeroDivisionError로 죽는다(재현 확인됨,
    /mapgen/generate가 빈 500을 내려주던 원인 중 하나). 0/NaN을 그대로 흘려보내지
    않고 안전한 기본값으로 대체해야 한다."""

    def fake_beat_track(onset_envelope, sr, hop_length, trim):
        return 0.0, np.array([0, 10, 20])

    monkeypatch.setattr(beats_module.librosa.beat, "beat_track", fake_beat_track)

    sr = 22050
    y = np.zeros(sr * 2, dtype=np.float32)
    onset_env = compute_onset_envelope(y, sr)

    bpm, _ = detect_tempo_and_beats(y, sr, onset_env=onset_env)

    assert bpm == FALLBACK_BPM
