import pytest

from app.mapgen.engine import generate_map, regenerate_segment
from app.mapgen.models import MapStyle
from tests.mapgen_fixtures import make_analysis_result


@pytest.mark.parametrize("difficulty", [1, 9, 13, 18, 26])
def test_generate_map_produces_valid_map(difficulty: int) -> None:
    analysis = make_analysis_result()

    result = generate_map(analysis, difficulty, seed=123)

    assert result.bpm == analysis.bpm
    assert result.difficulty == difficulty
    assert result.duration_sec == analysis.duration_sec
    assert len(result.tiles) >= len(analysis.beat_times)
    assert result.tiles[0].turn_angle_deg == 0.0
    assert [t.index for t in result.tiles] == list(range(len(result.tiles)))
    # 타일은 시간 순으로 정렬되어 있어야 한다
    times = [t.time_sec for t in result.tiles]
    assert times == sorted(times)


def test_generate_map_is_deterministic_for_same_seed() -> None:
    analysis = make_analysis_result()

    map_a = generate_map(analysis, 18, seed=99)
    map_b = generate_map(analysis, 18, seed=99)

    assert [t.turn_angle_deg for t in map_a.tiles] == [t.turn_angle_deg for t in map_b.tiles]


def test_magic_circle_style_never_flips_direction() -> None:
    analysis = make_analysis_result(duration_sec=16.0)

    result = generate_map(analysis, 18, seed=7, style=MapStyle(magic_circle=True))

    signs = [1 if t.turn_angle_deg > 0 else (-1 if t.turn_angle_deg < 0 else 0) for t in result.tiles[1:]]
    non_zero_signs = {s for s in signs if s != 0}
    assert len(non_zero_signs) <= 1


def test_regenerate_segment_keeps_timing_and_only_changes_segment_angles() -> None:
    analysis = make_analysis_result(duration_sec=16.0)
    original = generate_map(analysis, 13, seed=1)

    start_sec, end_sec = 4.0, 8.0
    regenerated = regenerate_segment(original, start_sec, end_sec, seed=2)

    assert [t.time_sec for t in regenerated.tiles] == [t.time_sec for t in original.tiles]

    for original_tile, new_tile in zip(original.tiles, regenerated.tiles):
        if start_sec <= original_tile.time_sec <= end_sec:
            continue
        assert original_tile.turn_angle_deg == new_tile.turn_angle_deg


def test_regenerate_segment_rejects_invalid_range() -> None:
    analysis = make_analysis_result()
    original = generate_map(analysis, 13, seed=1)

    with pytest.raises(ValueError):
        regenerate_segment(original, 8.0, 4.0)

    with pytest.raises(ValueError):
        regenerate_segment(original, 1000.0, 1001.0)


def test_regenerate_segment_can_override_difficulty() -> None:
    analysis = make_analysis_result()
    original = generate_map(analysis, 1, seed=1)

    regenerated = regenerate_segment(original, 2.0, 6.0, difficulty=26, seed=1)

    assert regenerated.difficulty == 26
