from pathlib import Path

import soundfile as sf

from app.audio.analyzer import analyze_audio
from tests.audio_fixtures import make_click_track


def test_analyze_audio_end_to_end(tmp_path: Path) -> None:
    sr = 22050
    y, _ = make_click_track(bpm=120.0, duration_sec=12.0, sr=sr, accent_every=4)
    wav_path = tmp_path / "song.wav"
    sf.write(wav_path, y, sr)

    result = analyze_audio(wav_path)

    assert result.duration_sec > 11.0
    assert result.sample_rate == sr
    assert result.bpm > 0
    assert len(result.beat_times) > 0
    assert len(result.downbeat_times) > 0
    assert len(result.energy_profile) > 0
    assert len(result.tempo_changes) >= 1
