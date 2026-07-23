"""구조화된 편집 지시(EditInstruction)를 맵 재생성 파라미터로 바꿔 적용한다."""

from dataclasses import replace

from app.ai.models import EditInstruction
from app.mapgen.difficulty import profile_for_level, shift_difficulty
from app.mapgen.engine import regenerate_segment
from app.mapgen.models import GeneratedMap

_FLASHY_FLIP_PROBABILITY_MULTIPLIER = 1.2
_TIGHTEN_FLIP_PROBABILITY_MULTIPLIER = 0.7
_MAX_FLIP_PROBABILITY = 0.95
_MIN_FLIP_PROBABILITY = 0.3


def apply_edit_instruction(
    existing_map: GeneratedMap, instruction: EditInstruction, seed: int | None = None
) -> GeneratedMap:
    """자연어에서 파싱된 편집 지시를 실제 맵 구간 재생성으로 옮긴다.

    구간 재생성(regenerate_segment)은 타일의 박자 배치(split_n, 시간)는
    그대로 두고 회전 "방향"만 다시 만든다 — ADOFAI에서는 회전각의 크기가
    곧 박자이므로, 크기를 바꾸면 음악과의 싱크가 깨진다. 따라서 편집 지시는
    방향 선택에 실제로 영향을 주는 두 파라미터만 조정한다:
    - max_consecutive_repeat: 같은 방향이 연속될 수 있는 한도 (반복 최소화)
    - flip_probability: 매 타일 직전과 반대 방향으로 꺾을 확률 (지그재그 정도)
    """
    target_difficulty = shift_difficulty(existing_map.difficulty, instruction.difficulty_delta)
    profile = profile_for_level(target_difficulty)

    if instruction.emphasize_flashy:
        profile = replace(
            profile,
            flip_probability=min(
                profile.flip_probability * _FLASHY_FLIP_PROBABILITY_MULTIPLIER, _MAX_FLIP_PROBABILITY
            ),
        )
    if instruction.reduce_repetition:
        profile = replace(profile, max_consecutive_repeat=max(1, profile.max_consecutive_repeat - 1))
    if instruction.tighten_timing:
        # 방향 전환을 더 예측 가능하게(덜 산만하게) 만들어 안정적인 느낌을 준다.
        # 타일의 실제 박자 배치는 엔진이 회전각=박자로 구성하므로 항상 정확하며,
        # 여기서 조정 가능한 것은 방향 전환의 변덕스러움뿐이다.
        profile = replace(
            profile,
            flip_probability=max(
                profile.flip_probability * _TIGHTEN_FLIP_PROBABILITY_MULTIPLIER, _MIN_FLIP_PROBABILITY
            ),
        )

    return regenerate_segment(
        existing_map,
        instruction.start_sec,
        instruction.end_sec,
        difficulty=target_difficulty,
        profile_override=profile,
        seed=seed,
    )
