import io

import soundfile as sf
from fastapi.testclient import TestClient

from app.main import app
from tests.audio_fixtures import make_click_track

client = TestClient(app)


def _generate_map(difficulty: str = "normal", seed: int = 1) -> dict:
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


def test_edit_segment_endpoint_applies_rule_based_instruction() -> None:
    generated_map = _generate_map()

    response = client.post(
        "/ai/edit-segment",
        json={
            "existing_map": generated_map,
            "instruction": "2~6초를 더 어렵게",
            "seed": 7,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["parsed_instruction"]["source"] == "rule_based"
    assert data["parsed_instruction"]["start_sec"] == 2.0
    assert data["parsed_instruction"]["end_sec"] == 6.0
    assert data["map"]["difficulty"] == "hard"
    assert [t["time_sec"] for t in data["map"]["tiles"]] == [
        t["time_sec"] for t in generated_map["tiles"]
    ]


def test_edit_segment_endpoint_rejects_out_of_range_instruction() -> None:
    generated_map = _generate_map()

    response = client.post(
        "/ai/edit-segment",
        json={
            "existing_map": generated_map,
            "instruction": "500~600초를 더 어렵게",
        },
    )

    assert response.status_code == 400
