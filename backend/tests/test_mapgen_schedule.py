import random
from dataclasses import replace

from app.mapgen.difficulty import DIFFICULTY_PROFILES
from app.mapgen.models import Difficulty
from app.mapgen.schedule import build_tile_schedule
from tests.mapgen_fixtures import make_analysis_result


def test_build_tile_schedule_marks_downbeats_and_drop_window() -> None:
    analysis = make_analysis_result(bpm=120.0, duration_sec=16.0, drop_time_sec=8.0)
    profile = DIFFICULTY_PROFILES[Difficulty.EASY]  # subdivision_probability=0 -> 비트만 그대로

    timings = build_tile_schedule(analysis, profile, random.Random(0))

    assert len(timings) == len(analysis.beat_times)
    downbeat_flags = [t.is_downbeat for t in timings]
    assert any(downbeat_flags)
    # 4박마다 다운비트이므로 인덱스 0,4,8...이 True여야 한다
    assert downbeat_flags[0] is True
    assert downbeat_flags[1] is False

    drop_flags = [t.is_drop for t in timings if 8.0 <= t.time_sec <= 9.5]
    assert any(drop_flags)
    before_drop_flags = [t.is_drop for t in timings if t.time_sec < 8.0]
    assert not any(before_drop_flags)


def test_build_tile_schedule_adds_subdivisions_when_probability_is_high() -> None:
    analysis = make_analysis_result(bpm=120.0, duration_sec=8.0, drop_time_sec=None)
    base_profile = DIFFICULTY_PROFILES[Difficulty.EXTREME]
    forced_profile = replace(base_profile, subdivision_probability=1.0)

    timings = build_tile_schedule(analysis, forced_profile, random.Random(1))

    # subdivision 확률이 1.0(사실상 min(.., 0.9)로 캡)이므로 원래 비트 수보다 많아야 한다
    assert len(timings) > len(analysis.beat_times)
