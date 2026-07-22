"""구조화된 편집 지시(EditInstruction)를 맵 재생성 파라미터로 바꿔 적용한다."""

from dataclasses import replace

from app.ai.models import EditInstruction
from app.mapgen.difficulty import DIFFICULTY_PROFILES
from app.mapgen.engine import regenerate_segment
from app.mapgen.models import Difficulty, GeneratedMap

_DIFFICULTY_ORDER = [Difficulty.EASY, Difficulty.NORMAL, Difficulty.HARD, Difficulty.EXTREME]

_FLASHY_DROP_BONUS_MULTIPLIER = 1.5
_FLASHY_STRAIGHT_WEIGHT_MULTIPLIER = 0.7
_MIN_STRAIGHT_WEIGHT = 0.02
_TIGHTEN_SUBDIVISION_MULTIPLIER = 0.5


def apply_edit_instruction(
    existing_map: GeneratedMap, instruction: EditInstruction, seed: int | None = None
) -> GeneratedMap:
    """자연어에서 파싱된 편집 지시를 실제 맵 구간 재생성으로 옮긴다.

    난이도 조정(difficulty_delta)은 현재 난이도 프로파일을 기준으로 삼고,
    화려함/반복 최소화/타이밍 정밀도 요청은 해당 프로파일의 파라미터를
    부분적으로 조정한 임시 프로파일을 만들어 적용한다.
    """
    target_difficulty = _shift_difficulty(existing_map.difficulty, instruction.difficulty_delta)
    profile = DIFFICULTY_PROFILES[target_difficulty]

    if instruction.emphasize_flashy:
        profile = replace(
            profile,
            drop_sharp_turn_bonus=profile.drop_sharp_turn_bonus * _FLASHY_DROP_BONUS_MULTIPLIER,
            straight_weight=max(
                profile.straight_weight * _FLASHY_STRAIGHT_WEIGHT_MULTIPLIER, _MIN_STRAIGHT_WEIGHT
            ),
        )
    if instruction.reduce_repetition:
        profile = replace(profile, max_consecutive_repeat=max(1, profile.max_consecutive_repeat - 1))
    if instruction.tighten_timing:
        # 세분(subdivision) 타일을 줄여 원래 검출된 박자 그리드에 더 가깝게 만든다.
        profile = replace(
            profile, subdivision_probability=profile.subdivision_probability * _TIGHTEN_SUBDIVISION_MULTIPLIER
        )

    return regenerate_segment(
        existing_map,
        instruction.start_sec,
        instruction.end_sec,
        difficulty=target_difficulty,
        profile_override=profile,
        seed=seed,
    )


def _shift_difficulty(base: Difficulty, delta: int) -> Difficulty:
    index = _DIFFICULTY_ORDER.index(base)
    new_index = max(0, min(len(_DIFFICULTY_ORDER) - 1, index + delta))
    return _DIFFICULTY_ORDER[new_index]
