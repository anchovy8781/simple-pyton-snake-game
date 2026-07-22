import random
from dataclasses import replace

import pytest

from app.mapgen.difficulty import DIFFICULTY_PROFILES
from app.mapgen.models import Difficulty
from app.mapgen.schedule import build_tile_schedule
from app.models.audio import TempoChangePoint
from tests.mapgen_fixtures import make_analysis_result


def test_build_tile_schedule_marks_downbeats_and_drop_window() -> None:
    analysis = make_analysis_result(bpm=120.0, duration_sec=16.0, drop_time_sec=8.0)
    profile = DIFFICULTY_PROFILES[Difficulty.EASY]  # beat_split_weights={1: 1.0} -> 비트만 그대로

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


def test_build_tile_schedule_splits_beats_when_forced() -> None:
    analysis = make_analysis_result(bpm=120.0, duration_sec=8.0, drop_time_sec=None)
    base_profile = DIFFICULTY_PROFILES[Difficulty.EXTREME]
    forced_profile = replace(base_profile, beat_split_weights={2: 1.0})

    timings = build_tile_schedule(analysis, forced_profile, random.Random(1))

    # 매 박이 정확히 2등분되므로 원래 비트 수의 약 2배가 되어야 한다
    assert len(timings) == pytest.approx(len(analysis.beat_times) * 2, abs=2)
    # 첫 타일은 진입 전이가 없는 시작점이라 split_n이 의미 없다(항상 1) — 나머지만 확인한다.
    assert all(t.split_n == 2 for t in timings[1:])


def test_split_tiles_have_exact_equal_spacing_within_a_beat() -> None:
    bpm = 120.0
    analysis = make_analysis_result(bpm=bpm, duration_sec=8.0, drop_time_sec=None)
    base_profile = DIFFICULTY_PROFILES[Difficulty.HARD]
    forced_profile = replace(base_profile, beat_split_weights={3: 1.0})

    timings = build_tile_schedule(analysis, forced_profile, random.Random(2))

    beat_duration = 60.0 / bpm
    expected_gap = beat_duration / 3
    gaps = [b.time_sec - a.time_sec for a, b in zip(timings, timings[1:])]
    assert all(gap == pytest.approx(expected_gap, abs=1e-6) for gap in gaps)


def test_build_tile_schedule_respects_tempo_sections() -> None:
    analysis = make_analysis_result(bpm=120.0, duration_sec=16.0, drop_time_sec=None)
    analysis = analysis.model_copy(
        update={
            "tempo_changes": [
                TempoChangePoint(time_sec=0.0, bpm=120.0),
                TempoChangePoint(time_sec=8.0, bpm=180.0),
            ]
        }
    )
    profile = DIFFICULTY_PROFILES[Difficulty.EASY]

    timings = build_tile_schedule(analysis, profile, random.Random(0))

    # 타일의 bpm은 "그 타일에 도달하는 전이"에 사용된 값이므로, 경계 타일(8.0초)
    # 자체는 아직 이전 구간의 bpm(120)을 쓴다 — 이후 타일부터 180으로 바뀐다.
    before = [t for t in timings if t.time_sec <= 8.0]
    after = [t for t in timings if t.time_sec > 8.0]
    assert before and after
    assert all(t.bpm == 120.0 for t in before)
    assert all(t.bpm == 180.0 for t in after)
