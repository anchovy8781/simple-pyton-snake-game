from app.ai.gemini_client import GeminiClient
from app.ai.instruction_parser import parse_edit_instruction


def test_falls_back_to_rule_based_when_no_client_configured() -> None:
    result = parse_edit_instruction("20~35초를 더 어렵게", duration_sec=120.0)

    assert result.source == "rule_based"
    assert result.start_sec == 20.0
    assert result.end_sec == 35.0


def test_uses_gemini_when_configured_and_response_is_valid_json() -> None:
    fake_response = (
        '{"start_sec": 5, "end_sec": 10, "difficulty_delta": 1, '
        '"emphasize_flashy": true, "reduce_repetition": false, "tighten_timing": false}'
    )
    client = GeminiClient(api_key="fake-key", generate_fn=lambda prompt: fake_response)

    result = parse_edit_instruction("이 부분 신나게 해줘", duration_sec=60.0, client=client)

    assert result.source == "gemini"
    assert result.start_sec == 5.0
    assert result.end_sec == 10.0
    assert result.difficulty_delta == 1
    assert result.emphasize_flashy is True


def test_uses_gemini_response_wrapped_in_code_fence() -> None:
    fake_response = (
        "```json\n"
        '{"start_sec": 0, "end_sec": 60, "difficulty_delta": 0, '
        '"emphasize_flashy": false, "reduce_repetition": true, "tighten_timing": false}\n'
        "```"
    )
    client = GeminiClient(api_key="fake-key", generate_fn=lambda prompt: fake_response)

    result = parse_edit_instruction("반복 좀 줄여줘", duration_sec=60.0, client=client)

    assert result.source == "gemini"
    assert result.reduce_repetition is True


def test_falls_back_to_rule_based_when_gemini_call_fails() -> None:
    def _boom(prompt: str) -> str:
        raise RuntimeError("network down")

    client = GeminiClient(api_key="fake-key", generate_fn=_boom)

    result = parse_edit_instruction("20~35초를 더 어렵게", duration_sec=120.0, client=client)

    assert result.source == "rule_based"
    assert result.start_sec == 20.0


def test_falls_back_to_rule_based_when_gemini_response_is_not_json() -> None:
    client = GeminiClient(api_key="fake-key", generate_fn=lambda prompt: "이건 JSON이 아닙니다")

    result = parse_edit_instruction("후반부를 쉽게", duration_sec=100.0, client=client)

    assert result.source == "rule_based"
    assert result.start_sec == 50.0
