import io

import soundfile as sf
from fastapi.testclient import TestClient

from app.main import app
from tests.audio_fixtures import make_click_track

client = TestClient(app)


def test_analyze_endpoint_accepts_wav_upload() -> None:
    sr = 22050
    y, _ = make_click_track(bpm=120.0, duration_sec=8.0, sr=sr)
    buffer = io.BytesIO()
    sf.write(buffer, y, sr, format="WAV")
    buffer.seek(0)

    response = client.post(
        "/audio/analyze",
        files={"file": ("song.wav", buffer, "audio/wav")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["sample_rate"] == sr
    assert data["bpm"] > 0
    assert "beat_times" in data
    assert "energy_profile" in data


def test_analyze_endpoint_rejects_unsupported_extension() -> None:
    response = client.post(
        "/audio/analyze",
        files={"file": ("song.flac", io.BytesIO(b"not audio"), "audio/flac")},
    )

    assert response.status_code == 400
