from app.mapgen.difficulty import MAX_DIFFICULTY, MIN_DIFFICULTY, profile_for_level, shift_difficulty


def _straight_weight(profile) -> float:
    return profile.beat_split_weights.get(1, 0.0)


def test_every_level_has_a_valid_profile() -> None:
    for level in range(MIN_DIFFICULTY, MAX_DIFFICULTY + 1):
        profile = profile_for_level(level)
        assert profile.beat_split_weights
        for split_n, weight in profile.beat_split_weights.items():
            assert split_n >= 1
            assert weight > 0


def test_higher_level_splits_beats_more_and_has_less_straight_bias() -> None:
    easy = profile_for_level(1)
    mid = profile_for_level(13)
    hard = profile_for_level(26)

    assert max(easy.beat_split_weights) <= max(mid.beat_split_weights) <= max(hard.beat_split_weights)
    assert _straight_weight(easy) > _straight_weight(mid) > _straight_weight(hard)
    assert easy.max_consecutive_repeat >= hard.max_consecutive_repeat
    assert easy.flip_probability < hard.flip_probability


def test_profile_for_level_clamps_out_of_range_values() -> None:
    assert profile_for_level(-5) == profile_for_level(1)
    assert profile_for_level(999) == profile_for_level(26)


def test_shift_difficulty_clamps_to_valid_range() -> None:
    assert shift_difficulty(1, -10) == MIN_DIFFICULTY
    assert shift_difficulty(26, 10) == MAX_DIFFICULTY
    assert shift_difficulty(10, 5) == 15
