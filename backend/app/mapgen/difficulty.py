"""난이도별 패턴 생성 파라미터.

ADOFAI는 타일의 회전각이 곧 그 타일까지 걸리는 시간(박자)을 결정한다
(예: 상대 회전각 180도 = 1박, 90도 = 반박, 60도 = 1/3박). 즉 "한 박을
몇 개의 타일로 쪼개는가(split)"가 회전각과 박자 정확도를 동시에 결정하는
단일한 선택이다. 난이도는 이 split 개수의 분포로 표현한다: split이
클수록(한 박에 타일이 많을수록) 입력이 빨라지고 회전이 잦아져 어려워진다.
"""

from dataclasses import dataclass

from app.mapgen.models import Difficulty


@dataclass(frozen=True)
class DifficultyProfile:
    name: Difficulty
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


DIFFICULTY_PROFILES: dict[Difficulty, DifficultyProfile] = {
    Difficulty.EASY: DifficultyProfile(
        name=Difficulty.EASY,
        beat_split_weights={1: 1.0},
        max_consecutive_repeat=3,
        drop_split_bonus=1.0,
        energy_bias_strength=0.0,
    ),
    Difficulty.NORMAL: DifficultyProfile(
        name=Difficulty.NORMAL,
        beat_split_weights={1: 0.7, 2: 0.3},
        max_consecutive_repeat=2,
        drop_split_bonus=1.5,
        energy_bias_strength=0.3,
    ),
    Difficulty.HARD: DifficultyProfile(
        name=Difficulty.HARD,
        beat_split_weights={1: 0.4, 2: 0.4, 3: 0.2},
        max_consecutive_repeat=2,
        drop_split_bonus=1.8,
        energy_bias_strength=0.45,
    ),
    Difficulty.EXTREME: DifficultyProfile(
        name=Difficulty.EXTREME,
        beat_split_weights={1: 0.15, 2: 0.35, 3: 0.3, 4: 0.2},
        max_consecutive_repeat=1,
        drop_split_bonus=2.2,
        energy_bias_strength=0.6,
    ),
}
