from app.ai.rule_based_parser import parse_instruction_rule_based


def test_parses_explicit_time_range_and_harder() -> None:
    result = parse_instruction_rule_based("20~35초를 더 어렵게", duration_sec=120.0)

    assert result.start_sec == 20.0
    assert result.end_sec == 35.0
    assert result.difficulty_delta == 1
    assert result.source == "rule_based"


def test_parses_extreme_keyword_as_bigger_delta() -> None:
    result = parse_instruction_rule_based("여기 극악으로 만들어줘", duration_sec=60.0)

    assert result.difficulty_delta == 2


def test_parses_drop_keyword_using_known_drop_time() -> None:
    result = parse_instruction_rule_based(
        "드롭 부분을 화려하게", duration_sec=120.0, drop_times_sec=[40.0]
    )

    assert result.start_sec == 38.0
    assert result.end_sec == 44.0
    assert result.emphasize_flashy is True


def test_parses_latter_half_and_easier() -> None:
    result = parse_instruction_rule_based("후반부를 쉽게", duration_sec=100.0)

    assert result.start_sec == 50.0
    assert result.end_sec == 100.0
    assert result.difficulty_delta == -1


def test_parses_first_part() -> None:
    result = parse_instruction_rule_based("초반부는 그대로 둬도 되는데 조금만 손봐줘", duration_sec=80.0)

    assert result.start_sec == 0.0
    assert result.end_sec == 20.0


def test_parses_reduce_repetition_defaults_to_whole_song() -> None:
    result = parse_instruction_rule_based("반복을 줄여줘", duration_sec=90.0)

    assert result.start_sec == 0.0
    assert result.end_sec == 90.0
    assert result.reduce_repetition is True


def test_parses_tighten_timing() -> None:
    result = parse_instruction_rule_based("박자를 더 정확하게 맞춰줘", duration_sec=30.0)

    assert result.tighten_timing is True


def test_unrecognized_instruction_defaults_to_whole_song_no_flags() -> None:
    result = parse_instruction_rule_based("그냥 전체적으로 다듬어줘", duration_sec=50.0)

    assert result.start_sec == 0.0
    assert result.end_sec == 50.0
    assert result.difficulty_delta == 0
    assert result.emphasize_flashy is False
