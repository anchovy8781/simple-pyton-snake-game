from app.mapgen.difficulty import DIFFICULTY_PROFILES
from app.mapgen.models import Difficulty


def test_all_difficulties_have_profiles() -> None:
    for difficulty in Difficulty:
        assert difficulty in DIFFICULTY_PROFILES


def test_higher_difficulty_has_more_angle_options_and_less_straight_bias() -> None:
    easy = DIFFICULTY_PROFILES[Difficulty.EASY]
    normal = DIFFICULTY_PROFILES[Difficulty.NORMAL]
    hard = DIFFICULTY_PROFILES[Difficulty.HARD]
    extreme = DIFFICULTY_PROFILES[Difficulty.EXTREME]

    assert (
        len(easy.allowed_turn_angles)
        <= len(normal.allowed_turn_angles)
        <= len(hard.allowed_turn_angles)
        <= len(extreme.allowed_turn_angles)
    )
    assert easy.straight_weight > normal.straight_weight > hard.straight_weight > extreme.straight_weight
    assert easy.max_consecutive_repeat >= normal.max_consecutive_repeat >= extreme.max_consecutive_repeat
