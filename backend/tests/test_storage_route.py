import io
import json

import soundfile as sf
from fastapi.testclient import TestClient

from app.main import app
from tests.audio_fixtures import make_click_track

client = TestClient(app)


def _generate_map(difficulty: str = "18", seed: int = 1) -> dict:
    sr = 22050
    y, _ = make_click_track(bpm=120.0, duration_sec=12.0, sr=sr, accent_every=4)
    buffer = io.BytesIO()
    sf.write(buffer, y, sr, format="WAV")
    buffer.seek(0)

    response = client.post(
        "/mapgen/generate",
        files={"file": ("song.wav", buffer, "audio/wav")},
        data={"difficulty": difficulty, "seed": str(seed)},
    )
    assert response.status_code == 200
    return response.json()


def test_export_endpoint_returns_downloadable_adofai_file() -> None:
    generated_map = _generate_map()

    response = client.post(
        "/storage/export",
        json={
            "existing_map": generated_map,
            "song_filename": "song.mp3",
            "song_name": "My Song",
            "artist": "Someone",
            "output_filename": "my level!",
        },
    )

    assert response.status_code == 200
    assert "attachment" in response.headers["content-disposition"]
    assert "my level" in response.headers["content-disposition"]

    document = json.loads(response.content)
    assert document["settings"]["songFilename"] == "song.mp3"
    assert len(document["angleData"]) == len(generated_map["tiles"])


def test_export_then_import_round_trip_preserves_timing() -> None:
    generated_map = _generate_map(difficulty="26", seed=7)

    export_response = client.post(
        "/storage/export",
        json={"existing_map": generated_map, "song_filename": "song.mp3"},
    )
    assert export_response.status_code == 200

    import_response = client.post(
        "/storage/import",
        files={"file": ("song.adofai", io.BytesIO(export_response.content), "application/json")},
    )
    assert import_response.status_code == 200

    imported_map = import_response.json()
    assert len(imported_map["tiles"]) == len(generated_map["tiles"])
    for original, restored in zip(generated_map["tiles"], imported_map["tiles"]):
        assert abs(original["time_sec"] - restored["time_sec"]) < 1e-3


def test_import_endpoint_rejects_invalid_json() -> None:
    response = client.post(
        "/storage/import",
        files={"file": ("broken.adofai", io.BytesIO(b"not json"), "application/json")},
    )

    assert response.status_code == 400
