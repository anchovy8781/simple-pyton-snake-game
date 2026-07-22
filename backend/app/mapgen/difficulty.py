"""난이도별 패턴 생성 파라미터."""

from dataclasses import dataclass

from app.mapgen.models import Difficulty


@dataclass(frozen=True)
class DifficultyProfile:
    name: Difficulty
    # 선택 가능한 회전각(도). 0(직진)은 별도의 straight_weight로 다룬다.
    allowed_turn_angles: tuple[float, ...]
    # 매 타일마다 "직진"을 선택할 기본 확률 (에너지에 따라 보정됨)
    straight_weight: float
    # 두 박자 사이에 세분(subdivision) 타일을 추가할 확률
    subdivision_probability: float
    # 반복 최소화: 동일한 (각도, 방향) 조합이 연속으로 허용되는 최대 횟수
    max_consecutive_repeat: int
    # 드롭 구간에서 큰 각도(>=90도)를 더 선호하게 만드는 가중치 배수
    drop_sharp_turn_bonus: float
    # 에너지가 높을수록 직진 대신 회전을 선호하게 만드는 강도 (0~1)
    energy_bias_strength: float


DIFFICULTY_PROFILES: dict[Difficulty, DifficultyProfile] = {
    Difficulty.EASY: DifficultyProfile(
        name=Difficulty.EASY,
        allowed_turn_angles=(60.0, 120.0, 180.0),
        straight_weight=0.55,
        subdivision_probability=0.0,
        max_consecutive_repeat=3,
        drop_sharp_turn_bonus=1.2,
        energy_bias_strength=0.2,
    ),
    Difficulty.NORMAL: DifficultyProfile(
        name=Difficulty.NORMAL,
        allowed_turn_angles=(45.0, 60.0, 90.0, 120.0, 135.0, 180.0),
        straight_weight=0.35,
        subdivision_probability=0.08,
        max_consecutive_repeat=2,
        drop_sharp_turn_bonus=1.5,
        energy_bias_strength=0.35,
    ),
    Difficulty.HARD: DifficultyProfile(
        name=Difficulty.HARD,
        allowed_turn_angles=(30.0, 45.0, 60.0, 75.0, 90.0, 105.0, 120.0, 135.0, 150.0, 180.0),
        straight_weight=0.2,
        subdivision_probability=0.2,
        max_consecutive_repeat=2,
        drop_sharp_turn_bonus=1.8,
        energy_bias_strength=0.5,
    ),
    Difficulty.EXTREME: DifficultyProfile(
        name=Difficulty.EXTREME,
        allowed_turn_angles=(
            15.0, 30.0, 45.0, 60.0, 75.0, 90.0, 105.0, 120.0, 135.0, 150.0, 165.0, 180.0,
        ),
        straight_weight=0.08,
        subdivision_probability=0.35,
        max_consecutive_repeat=1,
        drop_sharp_turn_bonus=2.2,
        energy_bias_strength=0.65,
    ),
}
