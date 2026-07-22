import pytest

from app.mapgen.engine import generate_map
from app.mapgen.models import Difficulty, GeneratedMap, Tile
from app.storage.adofai_reader import parse_adofai_document
from app.storage.adofai_writer import build_adofai_document
from app.storage.exceptions import AdofaiParseError
from tests.mapgen_fixtures import make_analysis_result


def test_document_structure_is_valid() -> None:
    analysis = make_analysis_result(bpm=128.0, duration_sec=16.0)
    generated = generate_map(analysis, Difficulty.HARD, seed=1)

    document = build_adofai_document(generated, song_filename="song.mp3", artist="Someone")

    assert document["angleData"][0] == 0.0
    assert len(document["angleData"]) == len(generated.tiles)
    assert document["decorations"] == []

    settings = document["settings"]
    for key in ("version", "artist", "song", "author", "songFilename", "bpm", "offset", "pitch", "volume"):
        assert key in settings
    assert settings["songFilename"] == "song.mp3"
    assert settings["artist"] == "Someone"


@pytest.mark.parametrize("difficulty", list(Difficulty))
def test_round_trip_preserves_tile_timing(difficulty: Difficulty) -> None:
    analysis = make_analysis_result(bpm=140.0, duration_sec=20.0, drop_time_sec=10.0)
    generated = generate_map(analysis, difficulty, seed=42)

    document = build_adofai_document(generated, song_filename="song.wav")
    reconstructed = parse_adofai_document(document)

    assert len(reconstructed.tiles) == len(generated.tiles)
    for original, restored in zip(generated.tiles, reconstructed.tiles):
        assert restored.time_sec == pytest.approx(original.time_sec, abs=1e-4)


def test_round_trip_with_tempo_change_uses_set_speed() -> None:
    analysis = make_analysis_result(bpm=100.0, duration_sec=16.0, drop_time_sec=None)
    from app.models.audio import TempoChangePoint

    analysis = analysis.model_copy(
        update={
            "tempo_changes": [
                TempoChangePoint(time_sec=0.0, bpm=100.0),
                TempoChangePoint(time_sec=8.0, bpm=150.0),
            ]
        }
    )
    generated = generate_map(analysis, Difficulty.NORMAL, seed=3)

    document = build_adofai_document(generated, song_filename="song.wav")

    set_speed_actions = [a for a in document["actions"] if a["eventType"] == "SetSpeed"]
    assert len(set_speed_actions) >= 1
    assert any(abs(a["beatsPerMinute"] - 150.0) < 1e-6 for a in set_speed_actions)

    reconstructed = parse_adofai_document(document)
    for original, restored in zip(generated.tiles, reconstructed.tiles):
        assert restored.time_sec == pytest.approx(original.time_sec, abs=1e-4)


def test_writer_uses_twirl_when_sign_changes() -> None:
    tiles = [
        Tile(index=0, time_sec=0.0, turn_angle_deg=0.0, bpm=120.0, split_n=1),
        Tile(index=1, time_sec=0.25, turn_angle_deg=90.0, bpm=120.0, split_n=2),
        Tile(index=2, time_sec=0.5, turn_angle_deg=-90.0, bpm=120.0, split_n=2),
        Tile(index=3, time_sec=0.75, turn_angle_deg=-90.0, bpm=120.0, split_n=2),
    ]
    generated = GeneratedMap(bpm=120.0, difficulty=Difficulty.NORMAL, duration_sec=1.0, tiles=tiles)

    document = build_adofai_document(generated, song_filename="song.wav")

    twirl_floors = {a["floor"] for a in document["actions"] if a["eventType"] == "Twirl"}
    # tile 1(+90)->tile 2(-90)에서 방향이 바뀌므로 floor=1에 twirl이 있어야 하고,
    # tile 2(-90)->tile 3(-90)은 같은 방향이므로 추가 twirl이 없어야 한다.
    assert 1 in twirl_floors
    assert 2 not in twirl_floors


def test_reader_rejects_empty_angle_data() -> None:
    with pytest.raises(AdofaiParseError):
        parse_adofai_document({"angleData": [], "settings": {"bpm": 120}, "actions": []})


def test_reader_rejects_invalid_bpm() -> None:
    with pytest.raises(AdofaiParseError):
        parse_adofai_document({"angleData": [0.0, 180.0], "settings": {"bpm": 0}, "actions": []})
