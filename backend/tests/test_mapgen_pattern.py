import random

from app.mapgen.pattern import generate_angles
from app.mapgen.schedule import TileTiming


def _make_flat_timeline(n: int, split_n: int = 2) -> list[TileTiming]:
    return [
        TileTiming(
            time_sec=i * 0.5, is_downbeat=False, is_drop=False, energy_db=-20.0, split_n=split_n, bpm=120.0
        )
        for i in range(n)
    ]


def test_generate_angles_is_deterministic_for_same_seed() -> None:
    timings = _make_flat_timeline(40)

    angles_1 = generate_angles(timings, max_consecutive_repeat=2, rng=random.Random(42))
    angles_2 = generate_angles(timings, max_consecutive_repeat=2, rng=random.Random(42))

    assert angles_1 == angles_2


def test_generate_angles_first_tile_is_straight_by_default() -> None:
    timings = _make_flat_timeline(10)

    angles = generate_angles(timings, max_consecutive_repeat=1, rng=random.Random(1))

    assert angles[0] == 0.0


def test_generate_angles_magnitude_matches_split_n() -> None:
    timings = _make_flat_timeline(20, split_n=3)

    angles = generate_angles(timings, max_consecutive_repeat=2, rng=random.Random(5))

    expected_magnitude = 180.0 * (1 - 1 / 3)
    for angle in angles[1:]:
        assert abs(angle) == expected_magnitude


def test_split_n_one_is_always_straight_regardless_of_sign() -> None:
    timings = _make_flat_timeline(10, split_n=1)

    angles = generate_angles(
        timings, max_consecutive_repeat=1, rng=random.Random(9), force_first_straight=False
    )

    assert all(angle == 0.0 for angle in angles)


def test_generate_angles_respects_max_consecutive_repeat() -> None:
    timings = _make_flat_timeline(60)

    angles = generate_angles(
        timings, max_consecutive_repeat=2, rng=random.Random(7), flip_probability=0.5
    )

    max_run = 1
    current_run = 1
    for prev, curr in zip(angles, angles[1:]):
        if curr == prev:
            current_run += 1
            max_run = max(max_run, current_run)
        else:
            current_run = 1

    assert max_run <= 2 + 1


def test_generate_angles_without_force_first_straight_uses_initial_sign() -> None:
    timings = _make_flat_timeline(5)

    angles = generate_angles(
        timings, max_consecutive_repeat=1, rng=random.Random(3), force_first_straight=False, initial_sign=-1
    )

    assert len(angles) == len(timings)
    assert angles[0] != 0.0


def test_higher_flip_probability_produces_more_direction_changes() -> None:
    timings = _make_flat_timeline(200)

    steady = generate_angles(
        timings, max_consecutive_repeat=200, rng=random.Random(1), flip_probability=0.05
    )
    chaotic = generate_angles(
        timings, max_consecutive_repeat=200, rng=random.Random(1), flip_probability=0.95
    )

    def count_flips(angles: list[float]) -> int:
        signs = [1 if a > 0 else -1 for a in angles[1:]]
        return sum(1 for a, b in zip(signs, signs[1:]) if a != b)

    assert count_flips(chaotic) > count_flips(steady)
