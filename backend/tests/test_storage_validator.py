import copy

from app.mapgen.engine import generate_map
from app.mapgen.models import GeneratedMap, MapStyle, Tile
from app.storage.adofai_writer import build_adofai_document
from app.storage.validator import validate_adofai_document
from tests.mapgen_fixtures import make_analysis_result


def test_real_generated_map_is_playable() -> None:
    analysis = make_analysis_result(bpm=140.0, duration_sec=20.0, drop_time_sec=10.0)
    generated = generate_map(analysis, 18, seed=1)
    document = build_adofai_document(generated, song_filename="song.mp3")

    report = validate_adofai_document(document, original_map=generated)

    assert report.is_playable is True
    assert report.errors == []


def test_sync_hits_style_map_is_playable() -> None:
    analysis = make_analysis_result(bpm=140.0, duration_sec=20.0, drop_time_sec=10.0)
    generated = generate_map(analysis, 18, seed=1, style=MapStyle(enable_sync_hits=True))
    document = build_adofai_document(generated, song_filename="song.mp3")

    report = validate_adofai_document(document, original_map=generated)

    assert report.is_playable is True
    assert report.errors == []


def test_missing_angle_data_is_an_error() -> None:
    report = validate_adofai_document({"settings": {"bpm": 120, "songFilename": "a.mp3"}, "actions": []})

    assert report.is_playable is False
    assert any("angleData" in issue.message for issue in report.errors)


def test_single_tile_is_not_playable() -> None:
    report = validate_adofai_document(
        {"angleData": [0.0], "settings": {"bpm": 120, "songFilename": "a.mp3"}, "actions": []}
    )

    assert report.is_playable is False


def test_non_finite_angle_is_an_error() -> None:
    report = validate_adofai_document(
        {
            "angleData": [0.0, float("nan")],
            "settings": {"bpm": 120, "songFilename": "a.mp3"},
            "actions": [],
        }
    )

    assert report.is_playable is False
    assert any(issue.tile_index == 1 for issue in report.errors)


def test_non_positive_bpm_is_an_error() -> None:
    report = validate_adofai_document(
        {"angleData": [0.0, 180.0], "settings": {"bpm": 0, "songFilename": "a.mp3"}, "actions": []}
    )

    assert report.is_playable is False


def test_invalid_set_speed_action_is_an_error() -> None:
    report = validate_adofai_document(
        {
            "angleData": [0.0, 180.0, 90.0],
            "settings": {"bpm": 120, "songFilename": "a.mp3"},
            "actions": [{"floor": 0, "eventType": "SetSpeed", "speedType": "Bpm", "beatsPerMinute": -5}],
        }
    )

    assert report.is_playable is False


def test_tampered_angle_breaks_round_trip_and_is_caught() -> None:
    analysis = make_analysis_result(bpm=140.0, duration_sec=20.0, drop_time_sec=10.0)
    generated = generate_map(analysis, 18, seed=1)
    document = build_adofai_document(generated, song_filename="song.mp3")

    tampered = copy.deepcopy(document)
    tampered["angleData"][2] = (tampered["angleData"][2] + 37.0) % 360.0

    report = validate_adofai_document(tampered, original_map=generated)

    assert report.is_playable is False
    assert any("어긋납니다" in issue.message for issue in report.errors)


def test_extremely_short_gaps_produce_warning_not_error() -> None:
    tiles = [
        Tile(index=0, time_sec=0.0, turn_angle_deg=0.0, bpm=600.0, split_n=1),
        Tile(index=1, time_sec=0.0125, turn_angle_deg=157.5, bpm=600.0, split_n=8),
        Tile(index=2, time_sec=0.025, turn_angle_deg=-157.5, bpm=600.0, split_n=8),
    ]
    generated = GeneratedMap(bpm=600.0, difficulty=26, duration_sec=0.025, tiles=tiles)
    document = build_adofai_document(generated, song_filename="song.mp3")

    report = validate_adofai_document(document, original_map=generated)

    assert report.is_playable is True
    assert any("짧아" in issue.message for issue in report.warnings)


def test_extremely_long_gap_produces_warning() -> None:
    tiles = [
        Tile(index=0, time_sec=0.0, turn_angle_deg=0.0, bpm=2.0, split_n=1),
        Tile(index=1, time_sec=30.0, turn_angle_deg=0.0, bpm=2.0, split_n=1),
    ]
    generated = GeneratedMap(bpm=2.0, difficulty=1, duration_sec=30.0, tiles=tiles)
    document = build_adofai_document(generated, song_filename="song.mp3")

    report = validate_adofai_document(document, original_map=generated)

    assert report.is_playable is True
    assert any("길어" in issue.message for issue in report.warnings)
