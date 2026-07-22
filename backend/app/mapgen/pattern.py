"""타일 타임라인에 대해 실제 회전각(턴) 패턴을 생성한다.

타일이 몇 박을 차지하는지(split_n)는 schedule.py에서 이미 정해졌으므로
(ADOFAI에서는 회전각이 곧 박자이기 때문에 이 둘을 분리할 수 없다), 여기서는
회전 "방향"(좌/우)만 고른다. 방향 선택은 박자에 영향을 주지 않으므로
자유롭게 자연스러운 흐름과 반복 최소화를 위해 조정할 수 있다.
"""

import random

from app.mapgen.schedule import TileTiming


def generate_angles(
    tile_timings: list[TileTiming],
    max_consecutive_repeat: int,
    rng: random.Random,
    force_first_straight: bool = True,
    initial_sign: int = 1,
    flip_probability: float = 0.7,
) -> list[float]:
    """각 타일의 직전 방향 대비 상대 회전각(도) 목록을 생성한다.

    각 타일의 회전 크기는 `180 * (1 - 1/split_n)`으로 고정된다(split_n=1이면
    0, 즉 직진 = 정확히 한 박). 방향(부호)만 선택하며, 직전과 반대 방향으로
    꺾는 경향을 둬 자연스러운 지그재그 흐름을 만들고, 동일한 (split_n, 방향)
    조합의 연속 반복을 난이도별 한도로 제한한다(반복 최소화).

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
    last_key: tuple[int, int] | None = None

    remaining = tile_timings
    if force_first_straight:
        angles.append(0.0)
        remaining = tile_timings[1:]

    for timing in remaining:
        magnitude = _magnitude_for_split(timing.split_n)

        if magnitude == 0.0:
            # split_n=1(한 박 그대로)은 항상 직진이며 방향 개념이 없다.
            sign = last_sign
        else:
            avoid_repeat = (
                last_key is not None
                and last_key == (timing.split_n, last_sign)
                and repeat_streak >= max_consecutive_repeat
            )
            if avoid_repeat:
                sign = -last_sign
            else:
                sign = -last_sign if rng.random() < flip_probability else last_sign

        key = (timing.split_n, sign)
        repeat_streak = repeat_streak + 1 if key == last_key else 0
        last_key = key
        if magnitude != 0.0:
            last_sign = sign

        angles.append(magnitude * sign)

    return angles


def _magnitude_for_split(split_n: int) -> float:
    if split_n <= 1:
        return 0.0
    return 180.0 * (1.0 - 1.0 / split_n)
