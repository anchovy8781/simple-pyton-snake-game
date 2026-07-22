from app.mapgen.difficulty import DIFFICULTY_PROFILES
from app.mapgen.models import Difficulty


def test_all_difficulties_have_profiles() -> None:
    for difficulty in Difficulty:
        assert difficulty in DIFFICULTY_PROFILES


def _straight_weight(profile) -> float:
    return profile.beat_split_weights.get(1, 0.0)


def test_higher_difficulty_splits_beats_more_and_has_less_straight_bias() -> None:
    easy = DIFFICULTY_PROFILES[Difficulty.EASY]
    normal = DIFFICULTY_PROFILES[Difficulty.NORMAL]
    hard = DIFFICULTY_PROFILES[Difficulty.HARD]
    extreme = DIFFICULTY_PROFILES[Difficulty.EXTREME]

    assert (
        max(easy.beat_split_weights)
        <= max(normal.beat_split_weights)
        <= max(hard.beat_split_weights)
        <= max(extreme.beat_split_weights)
    )
    assert _straight_weight(easy) > _straight_weight(normal) > _straight_weight(hard)
    assert easy.max_consecutive_repeat >= normal.max_consecutive_repeat >= extreme.max_consecutive_repeat


def test_beat_split_weights_are_positive() -> None:
    for profile in DIFFICULTY_PROFILES.values():
        assert profile.beat_split_weights
        for split_n, weight in profile.beat_split_weights.items():
            assert split_n >= 1
            assert weight > 0
