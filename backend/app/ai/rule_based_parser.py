"""규칙 기반(정규식/키워드) 자연어 편집 지시 파서.

Gemini API 키가 없거나 호출이 실패했을 때도 핵심 편집 기능이 항상 동작하도록
하는 오프라인 대체 경로다. 완전한 자연어 이해는 아니지만, 요구사항에 제시된
대표 패턴(시간 구간 지정, 난이도 조정, 화려함/반복/정확도 요청)은 처리한다.
"""

import re

from app.ai.models import EditInstruction

_RANGE_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*[~\-–]\s*(\d+(?:\.\d+)?)\s*초")

_HARDER_WORDS = ("어렵게", "어려운", "빡세게")
_EXTREME_WORDS = ("극악",)
_EASIER_WORDS = ("쉽게", "쉬운", "여유롭게")
_FLASHY_WORDS = ("화려", "화끈")
_REDUCE_REPETITION_WORDS = ("반복을 줄", "반복 줄", "반복하지")
_TIGHTEN_TIMING_WORDS = ("박자를 정확", "박자를 더 정확", "정확하게 맞춰", "타이밍을 정확")
_LATTER_HALF_WORDS = ("후반부", "후반", "뒷부분")
_FIRST_PART_WORDS = ("초반부", "초반", "도입부", "앞부분")
_DROP_WORDS = ("드롭",)
_WHOLE_SONG_WORDS = ("전체", "곡 전체", "전부")

_DROP_WINDOW_BEFORE_SEC = 2.0
_DROP_WINDOW_AFTER_SEC = 4.0


def parse_instruction_rule_based(
    instruction: str,
    duration_sec: float,
    drop_times_sec: list[float] | None = None,
) -> EditInstruction:
    text = instruction.strip()
    start_sec, end_sec = _extract_range(text, duration_sec, drop_times_sec or [])

    difficulty_delta = 0
    if any(w in text for w in _EXTREME_WORDS):
        difficulty_delta += 2
    elif any(w in text for w in _HARDER_WORDS):
        difficulty_delta += 1
    if any(w in text for w in _EASIER_WORDS):
        difficulty_delta -= 1

    return EditInstruction(
        start_sec=start_sec,
        end_sec=end_sec,
        difficulty_delta=difficulty_delta,
        emphasize_flashy=any(w in text for w in _FLASHY_WORDS),
        reduce_repetition=any(w in text for w in _REDUCE_REPETITION_WORDS),
        tighten_timing=any(w in text for w in _TIGHTEN_TIMING_WORDS),
        raw_instruction=instruction,
        source="rule_based",
    )


def _extract_range(text: str, duration_sec: float, drop_times_sec: list[float]) -> tuple[float, float]:
    match = _RANGE_PATTERN.search(text)
    if match:
        start_sec = float(match.group(1))
        end_sec = float(match.group(2))
        return max(0.0, start_sec), min(duration_sec, end_sec)

    if any(w in text for w in _DROP_WORDS) and drop_times_sec:
        drop_time = drop_times_sec[0]
        return (
            max(0.0, drop_time - _DROP_WINDOW_BEFORE_SEC),
            min(duration_sec, drop_time + _DROP_WINDOW_AFTER_SEC),
        )

    if any(w in text for w in _LATTER_HALF_WORDS):
        return duration_sec / 2, duration_sec

    if any(w in text for w in _FIRST_PART_WORDS):
        return 0.0, duration_sec / 4

    # "전체"가 명시되었거나 구간을 특정할 수 없으면 곡 전체를 대상으로 한다.
    return 0.0, duration_sec
