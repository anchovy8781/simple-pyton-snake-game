"""타일 타임라인에 대해 실제 회전각(턴) 패턴을 생성한다."""

import random

from app.mapgen.difficulty import DifficultyProfile
from app.mapgen.schedule import TileTiming

_ENERGY_FLOOR_DB = -60.0
_ENERGY_CEIL_DB = 0.0
_FLIP_PROBABILITY = 0.7


def generate_angles(
    tile_timings: list[TileTiming],
    profile: DifficultyProfile,
    rng: random.Random,
    force_first_straight: bool = True,
    initial_sign: int = 1,
) -> list[float]:
    """각 타일의 직전 방향 대비 상대 회전각(도) 목록을 생성한다.

    - 에너지가 높을수록 직진보다 회전을 선호하고(플레이 재미/강조 반영)
    - 드롭 구간에서는 큰 각도를 더 선호하며(화려함)
    - 직전과 반대 방향으로 꺾는 경향을 둬 자연스러운 지그재그 흐름을 만들고
    - 동일한 (각도, 방향) 조합의 연속 반복을 난이도별 한도로 제한한다(반복 최소화).

    force_first_straight=True(전체 맵 생성 기본값)면 첫 타일의 회전각을 0으로
    고정한다. 구간 재생성처럼 이미 진행 방향이 있는 중간 구간을 이어받을 때는
    force_first_straight=False와 initial_sign(직전 타일의 회전 방향)을 넘겨
    첫 타일도 자연스럽게 이어지는 회전을 생성하도록 한다.
    """
    if not tile_timings:
        return []

    angles: list[float] = []
    last_sign = initial_sign
    repeat_streak = 0
    last_angle_key: tuple[float, int] | None = None

    remaining = tile_timings
    if force_first_straight:
        angles.append(0.0)
        remaining = tile_timings[1:]

    for timing in remaining:
        normalized_energy = _normalize_energy(timing.energy_db)
        effective_straight_weight = profile.straight_weight * _clamp(
            1.0 - profile.energy_bias_strength * normalized_energy, 0.2, 1.4
        )

        if rng.random() < effective_straight_weight:
            angle, sign = 0.0, last_sign
        else:
            angle, sign = _pick_turn(profile, timing, rng, last_sign, last_angle_key, repeat_streak)

        key = (angle, sign)
        repeat_streak = repeat_streak + 1 if key == last_angle_key else 0
        last_angle_key = key
        if angle != 0.0:
            last_sign = sign

        angles.append(angle * sign)

    return angles


def _pick_turn(
    profile: DifficultyProfile,
    timing: TileTiming,
    rng: random.Random,
    last_sign: int,
    last_angle_key: tuple[float, int] | None,
    repeat_streak: int,
) -> tuple[float, int]:
    candidates = list(profile.allowed_turn_angles)

    # 반복 최소화: 직전과 같은 각도가 허용 한도만큼 연속됐다면 후보에서 제외한다.
    if last_angle_key is not None and repeat_streak >= profile.max_consecutive_repeat:
        filtered = [a for a in candidates if a != last_angle_key[0]]
        if filtered:
            candidates = filtered

    weights = [
        profile.drop_sharp_turn_bonus if (timing.is_drop and a >= 90.0) else 1.0 for a in candidates
    ]
    angle = rng.choices(candidates, weights=weights, k=1)[0]

    # 대부분은 직전과 반대 방향으로 꺾어 지그재그를 만들되, 가끔 같은 방향을
    # 유지해 완전히 예측 가능한 패턴이 되지 않게 한다.
    sign = -last_sign if rng.random() < _FLIP_PROBABILITY else last_sign

    return angle, sign


def _normalize_energy(rms_db: float) -> float:
    return _clamp((rms_db - _ENERGY_FLOOR_DB) / (_ENERGY_CEIL_DB - _ENERGY_FLOOR_DB), 0.0, 1.0)


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))
