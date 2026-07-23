"""난이도(1~26)별 패턴 생성 파라미터.

ADOFAI는 타일의 회전각이 곧 그 타일까지 걸리는 시간(박자)을 결정한다
(예: 상대 회전각 180도 = 1박, 90도 = 반박, 60도 = 1/3박). 즉 "한 박을
몇 개의 타일로 쪼개는가(split)"가 회전각과 박자 정확도를 동시에 결정하는
단일한 선택이다. 난이도는 이 split 개수의 분포로 표현한다: split이
클수록(한 박에 타일이 많을수록) 입력이 빨라지고 회전이 잦아져 어려워진다.

1~26 각 레벨마다 프로파일을 하나씩 만드는 대신, 몇 개의 기준점(anchor)
사이를 선형 보간해 연속적인 난이도 곡선을 만든다.
"""

from dataclasses import dataclass, replace

from app.mapgen.models import MAX_DIFFICULTY, MIN_DIFFICULTY, clamp_difficulty


@dataclass(frozen=True)
class DifficultyProfile:
    # 한 박을 몇 개의 동일 길이 타일로 나눌지에 대한 확률 가중치.
    # 예: {1: 0.6, 2: 0.4}이면 60% 확률로 1박 그대로(직진), 40% 확률로
    # 반박씩 2개 타일(회전)로 나눈다.
    beat_split_weights: dict[int, float]
    # 반복 최소화: 동일한 (split, 방향) 조합이 연속으로 허용되는 최대 횟수
    max_consecutive_repeat: int
    # 드롭 구간에서 더 큰 split(빠르고 화려한 회전)을 선호하게 만드는 가중치 배수
    drop_split_bonus: float
    # 에너지가 높을수록 더 큰 split을 선호하게 만드는 강도 (0~1)
    energy_bias_strength: float
    # 매 타일마다 직전과 반대 방향으로 꺾을 확률 (지그재그 정도, 0~1)
    flip_probability: float = 0.7


_ANCHORS: list[tuple[int, DifficultyProfile]] = [
    (
        1,
        DifficultyProfile(
            beat_split_weights={1: 1.0},
            max_consecutive_repeat=3,
            drop_split_bonus=1.0,
            energy_bias_strength=0.0,
            flip_probability=0.5,
        ),
    ),
    (
        9,
        DifficultyProfile(
            beat_split_weights={1: 0.7, 2: 0.3},
            max_consecutive_repeat=2,
            drop_split_bonus=1.5,
            energy_bias_strength=0.3,
            flip_probability=0.65,
        ),
    ),
    (
        18,
        DifficultyProfile(
            beat_split_weights={1: 0.4, 2: 0.4, 3: 0.2},
            max_consecutive_repeat=2,
            drop_split_bonus=1.8,
            energy_bias_strength=0.45,
            flip_probability=0.75,
        ),
    ),
    (
        26,
        DifficultyProfile(
            beat_split_weights={1: 0.05, 2: 0.2, 3: 0.3, 4: 0.3, 5: 0.15},
            max_consecutive_repeat=1,
            drop_split_bonus=2.4,
            energy_bias_strength=0.65,
            flip_probability=0.9,
        ),
    ),
]


def profile_for_level(level: int) -> DifficultyProfile:
    """1~26 사이의 정수 난이도를 실제 패턴 생성 파라미터로 변환한다."""
    level = clamp_difficulty(level)

    lower, upper = _ANCHORS[0], _ANCHORS[-1]
    for a, b in zip(_ANCHORS, _ANCHORS[1:]):
        if a[0] <= level <= b[0]:
            lower, upper = a, b
            break

    lo_level, lo = lower
    hi_level, hi = upper
    ratio = 0.0 if hi_level == lo_level else (level - lo_level) / (hi_level - lo_level)

    keys = set(lo.beat_split_weights) | set(hi.beat_split_weights)
    weights = {
        k: _lerp(lo.beat_split_weights.get(k, 0.0), hi.beat_split_weights.get(k, 0.0), ratio)
        for k in keys
    }
    weights = {k: w for k, w in weights.items() if w > 0.005}
    if not weights:
        weights = {1: 1.0}

    return DifficultyProfile(
        beat_split_weights=weights,
        max_consecutive_repeat=max(1, round(_lerp(lo.max_consecutive_repeat, hi.max_consecutive_repeat, ratio))),
        drop_split_bonus=_lerp(lo.drop_split_bonus, hi.drop_split_bonus, ratio),
        energy_bias_strength=_lerp(lo.energy_bias_strength, hi.energy_bias_strength, ratio),
        flip_probability=_lerp(lo.flip_probability, hi.flip_probability, ratio),
    )


def shift_difficulty(base: int, delta: int) -> int:
    return clamp_difficulty(base + delta)


def with_flip_probability(profile: DifficultyProfile, flip_probability: float) -> DifficultyProfile:
    return replace(profile, flip_probability=max(0.0, min(1.0, flip_probability)))


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


__all__ = [
    "MAX_DIFFICULTY",
    "MIN_DIFFICULTY",
    "DifficultyProfile",
    "profile_for_level",
    "shift_difficulty",
    "with_flip_probability",
]
