import io

import soundfile as sf
from fastapi.testclient import TestClient

from app.main import app
from tests.audio_fixtures import make_click_track

client = TestClient(app)


def _make_wav_bytes(bpm: float = 120.0, duration_sec: float = 12.0) -> io.BytesIO:
    sr = 22050
    y, _ = make_click_track(bpm=bpm, duration_sec=duration_sec, sr=sr, accent_every=4)
    buffer = io.BytesIO()
    sf.write(buffer, y, sr, format="WAV")
    buffer.seek(0)
    return buffer


def test_generate_endpoint_returns_map_for_wav_upload() -> None:
    response = client.post(
        "/mapgen/generate",
        files={"file": ("song.wav", _make_wav_bytes(), "audio/wav")},
        data={"difficulty": "18", "seed": "5"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["difficulty"] == 18
    assert len(data["tiles"]) > 0
    assert data["tiles"][0]["turn_angle_deg"] == 0.0


def test_generate_endpoint_rejects_unsupported_extension() -> None:
    response = client.post(
        "/mapgen/generate",
        files={"file": ("song.flac", io.BytesIO(b"not audio"), "audio/flac")},
        data={"difficulty": "13"},
    )

    assert response.status_code == 400


def test_regenerate_segment_endpoint_updates_existing_map() -> None:
    generate_response = client.post(
        "/mapgen/generate",
        files={"file": ("song.wav", _make_wav_bytes(), "audio/wav")},
        data={"difficulty": "13", "seed": "1"},
    )
    assert generate_response.status_code == 200
    generated_map = generate_response.json()

    response = client.post(
        "/mapgen/regenerate-segment",
        json={
            "existing_map": generated_map,
            "start_sec": 2.0,
            "end_sec": 6.0,
            "seed": 2,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["tiles"]) == len(generated_map["tiles"])
    assert [t["time_sec"] for t in data["tiles"]] == [t["time_sec"] for t in generated_map["tiles"]]


def test_regenerate_segment_endpoint_rejects_invalid_range() -> None:
    generate_response = client.post(
        "/mapgen/generate",
        files={"file": ("song.wav", _make_wav_bytes(), "audio/wav")},
        data={"difficulty": "13", "seed": "1"},
    )
    generated_map = generate_response.json()

    response = client.post(
        "/mapgen/regenerate-segment",
        json={
            "existing_map": generated_map,
            "start_sec": 100.0,
            "end_sec": 101.0,
        },
    )

    assert response.status_code == 400
