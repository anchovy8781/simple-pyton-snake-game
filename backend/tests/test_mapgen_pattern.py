import random
from dataclasses import replace

from app.mapgen.difficulty import DIFFICULTY_PROFILES
from app.mapgen.models import Difficulty
from app.mapgen.pattern import generate_angles
from app.mapgen.schedule import TileTiming


def _make_flat_timeline(n: int) -> list[TileTiming]:
    return [TileTiming(time_sec=i * 0.5, is_downbeat=False, is_drop=False, energy_db=-20.0) for i in range(n)]


def test_generate_angles_is_deterministic_for_same_seed() -> None:
    profile = DIFFICULTY_PROFILES[Difficulty.HARD]
    timings = _make_flat_timeline(40)

    angles_1 = generate_angles(timings, profile, random.Random(42))
    angles_2 = generate_angles(timings, profile, random.Random(42))

    assert angles_1 == angles_2


def test_generate_angles_first_tile_is_straight_by_default() -> None:
    profile = DIFFICULTY_PROFILES[Difficulty.EXTREME]
    timings = _make_flat_timeline(10)

    angles = generate_angles(timings, profile, random.Random(1))

    assert angles[0] == 0.0


def test_generate_angles_respects_max_consecutive_repeat() -> None:
    # 직진을 없애고(항상 회전), 각도 후보를 2개로 제한해 반복 억제 로직을 명확히 검증한다.
    base_profile = DIFFICULTY_PROFILES[Difficulty.HARD]
    profile = replace(
        base_profile,
        allowed_turn_angles=(60.0, 90.0),
        straight_weight=0.0,
        max_consecutive_repeat=2,
    )
    timings = _make_flat_timeline(60)

    angles = generate_angles(timings, profile, random.Random(7))

    max_run = 1
    current_run = 1
    for prev, curr in zip(angles, angles[1:]):
        if curr == prev:
            current_run += 1
            max_run = max(max_run, current_run)
        else:
            current_run = 1

    assert max_run <= profile.max_consecutive_repeat + 1


def test_generate_angles_without_force_first_straight_uses_initial_sign() -> None:
    profile = replace(
        DIFFICULTY_PROFILES[Difficulty.HARD], straight_weight=0.0, allowed_turn_angles=(90.0,)
    )
    timings = _make_flat_timeline(5)

    angles = generate_angles(
        timings, profile, random.Random(3), force_first_straight=False, initial_sign=-1
    )

    assert len(angles) == len(timings)
    assert angles[0] != 0.0
