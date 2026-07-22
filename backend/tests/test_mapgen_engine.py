import pytest

from app.mapgen.engine import generate_map, regenerate_segment
from app.mapgen.models import Difficulty
from tests.mapgen_fixtures import make_analysis_result


@pytest.mark.parametrize("difficulty", list(Difficulty))
def test_generate_map_produces_valid_map(difficulty: Difficulty) -> None:
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

    map_a = generate_map(analysis, Difficulty.HARD, seed=99)
    map_b = generate_map(analysis, Difficulty.HARD, seed=99)

    assert [t.turn_angle_deg for t in map_a.tiles] == [t.turn_angle_deg for t in map_b.tiles]


def test_regenerate_segment_keeps_timing_and_only_changes_segment_angles() -> None:
    analysis = make_analysis_result(duration_sec=16.0)
    original = generate_map(analysis, Difficulty.NORMAL, seed=1)

    start_sec, end_sec = 4.0, 8.0
    regenerated = regenerate_segment(original, start_sec, end_sec, seed=2)

    assert [t.time_sec for t in regenerated.tiles] == [t.time_sec for t in original.tiles]

    for original_tile, new_tile in zip(original.tiles, regenerated.tiles):
        if start_sec <= original_tile.time_sec <= end_sec:
            continue
        assert original_tile.turn_angle_deg == new_tile.turn_angle_deg


def test_regenerate_segment_rejects_invalid_range() -> None:
    analysis = make_analysis_result()
    original = generate_map(analysis, Difficulty.NORMAL, seed=1)

    with pytest.raises(ValueError):
        regenerate_segment(original, 8.0, 4.0)

    with pytest.raises(ValueError):
        regenerate_segment(original, 1000.0, 1001.0)


def test_regenerate_segment_can_override_difficulty() -> None:
    analysis = make_analysis_result()
    original = generate_map(analysis, Difficulty.EASY, seed=1)

    regenerated = regenerate_segment(original, 2.0, 6.0, difficulty=Difficulty.EXTREME, seed=1)

    assert regenerated.difficulty == Difficulty.EXTREME
