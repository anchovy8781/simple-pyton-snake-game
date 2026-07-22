"""자연어 편집 지시 -> EditInstruction 구조화.

Gemini API가 설정되어 있으면 이를 우선 사용해 더 자유로운 표현("이 부분
너무 밋밋한데 신나게 해줘" 등)까지 이해하려 시도하고, API 키가 없거나
호출/파싱이 실패하면 규칙 기반 파서로 자동 대체한다.
"""

import json
import logging

from app.ai.exceptions import AIServiceError, InstructionParseError
from app.ai.gemini_client import GeminiClient
from app.ai.models import EditInstruction
from app.ai.rule_based_parser import parse_instruction_rule_based

logger = logging.getLogger(__name__)

_PROMPT_TEMPLATE = """당신은 리듬 게임(A Dance of Fire and Ice) 맵 편집 도구의 지시 파서입니다.
사용자의 한국어 편집 요청을 분석해 아래 JSON 스키마로만 응답하세요. 다른 설명은 출력하지 마세요.

스키마:
{{"start_sec": number, "end_sec": number, "difficulty_delta": integer(-3~3),
  "emphasize_flashy": boolean, "reduce_repetition": boolean, "tighten_timing": boolean}}

- start_sec/end_sec: 요청이 가리키는 구간(초). 특정할 수 없으면 0 ~ {duration_sec}(곡 전체)로 응답하세요.
- difficulty_delta: 더 어렵게 요청하면 양수(아주 많이 어렵게는 +2~+3), 더 쉽게 요청하면 음수, 언급 없으면 0.
- emphasize_flashy: 화려하거나 인상적으로 만들어달라는 요청이면 true.
- reduce_repetition: 반복되는 패턴을 줄여달라는 요청이면 true.
- tighten_timing: 박자/타이밍을 더 정확하게 맞춰달라는 요청이면 true.

곡 길이: {duration_sec}초
알려진 드롭(강조 구간) 시각(초): {drop_times}
사용자 요청: "{instruction}"
"""


def parse_edit_instruction(
    instruction: str,
    duration_sec: float,
    drop_times_sec: list[float] | None = None,
    client: GeminiClient | None = None,
) -> EditInstruction:
    client = client or GeminiClient()

    if client.is_configured:
        try:
            return _parse_with_gemini(instruction, duration_sec, drop_times_sec or [], client)
        except (AIServiceError, InstructionParseError) as exc:
            logger.warning("Gemini 파싱 실패, 규칙 기반 파서로 대체합니다: %s", exc)

    return parse_instruction_rule_based(instruction, duration_sec, drop_times_sec)


def _parse_with_gemini(
    instruction: str, duration_sec: float, drop_times_sec: list[float], client: GeminiClient
) -> EditInstruction:
    prompt = _PROMPT_TEMPLATE.format(
        duration_sec=duration_sec, drop_times=drop_times_sec, instruction=instruction
    )
    raw_text = client.generate_text(prompt)

    try:
        data = json.loads(_strip_code_fence(raw_text))
    except json.JSONDecodeError as exc:
        raise InstructionParseError(f"Gemini 응답을 JSON으로 해석하지 못했습니다: {raw_text!r}") from exc

    try:
        return EditInstruction(
            start_sec=float(data["start_sec"]),
            end_sec=float(data["end_sec"]),
            difficulty_delta=int(data.get("difficulty_delta", 0)),
            emphasize_flashy=bool(data.get("emphasize_flashy", False)),
            reduce_repetition=bool(data.get("reduce_repetition", False)),
            tighten_timing=bool(data.get("tighten_timing", False)),
            raw_instruction=instruction,
            source="gemini",
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise InstructionParseError(f"Gemini 응답 필드가 올바르지 않습니다: {data}") from exc


def _strip_code_fence(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        if stripped.lower().startswith("json"):
            stripped = stripped[4:]
    return stripped.strip()
