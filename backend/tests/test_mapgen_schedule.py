import random
from dataclasses import replace

import pytest

from app.mapgen.difficulty import profile_for_level
from app.mapgen.models import MapStyle
from app.mapgen.schedule import build_tile_schedule
from app.models.audio import EnergyPoint, TempoChangePoint
from tests.mapgen_fixtures import make_analysis_result


def test_build_tile_schedule_marks_downbeats_and_drop_window() -> None:
    analysis = make_analysis_result(bpm=120.0, duration_sec=16.0, drop_time_sec=8.0)
    profile = profile_for_level(1)  # beat_split_weights={1: 1.0} -> 비트만 그대로

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
    base_profile = profile_for_level(26)
    forced_profile = replace(base_profile, beat_split_weights={2: 1.0})

    timings = build_tile_schedule(analysis, forced_profile, random.Random(1))

    # 매 박이 정확히 2등분되므로 원래 비트 수의 약 2배가 되어야 한다
    assert len(timings) == pytest.approx(len(analysis.beat_times) * 2, abs=2)
    # 첫 타일은 진입 전이가 없는 시작점이라 split_n이 의미 없다(항상 1) — 나머지만 확인한다.
    assert all(t.split_n == 2 for t in timings[1:])


def test_split_tiles_have_exact_equal_spacing_within_a_beat() -> None:
    bpm = 120.0
    analysis = make_analysis_result(bpm=bpm, duration_sec=8.0, drop_time_sec=None)
    base_profile = profile_for_level(18)
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
    profile = profile_for_level(1)

    timings = build_tile_schedule(analysis, profile, random.Random(0))

    # 타일의 bpm은 "그 타일에 도달하는 전이"에 사용된 값이므로, 경계 타일(8.0초)
    # 자체는 아직 이전 구간의 bpm(120)을 쓴다 — 이후 타일부터 180으로 바뀐다.
    before = [t for t in timings if t.time_sec <= 8.0]
    after = [t for t in timings if t.time_sec > 8.0]
    assert before and after
    assert all(t.bpm == 120.0 for t in before)
    assert all(t.bpm == 180.0 for t in after)


def test_enable_rush_avoids_split_one_in_high_energy_window() -> None:
    analysis = make_analysis_result(bpm=120.0, duration_sec=12.0, drop_time_sec=None)
    # 4~10초 구간을 고에너지(질주) 구간으로 만든다.
    energy_profile = [
        EnergyPoint(time_sec=round(i * 0.1, 3), rms_db=-6.0 if 4.0 <= i * 0.1 <= 10.0 else -40.0)
        for i in range(120)
    ]
    analysis = analysis.model_copy(update={"energy_profile": energy_profile})
    profile = profile_for_level(13)

    timings = build_tile_schedule(analysis, profile, random.Random(3), style=MapStyle(enable_rush=True))

    rush_tiles = [t for t in timings if 4.5 <= t.time_sec <= 9.5]
    assert rush_tiles
    assert all(t.split_n > 1 for t in rush_tiles)


def test_enable_slow_lowers_bpm_in_quiet_window() -> None:
    analysis = make_analysis_result(bpm=120.0, duration_sec=12.0, drop_time_sec=None)
    energy_profile = [
        EnergyPoint(time_sec=round(i * 0.1, 3), rms_db=-50.0 if 4.0 <= i * 0.1 <= 8.0 else -10.0)
        for i in range(120)
    ]
    analysis = analysis.model_copy(update={"energy_profile": energy_profile})
    profile = profile_for_level(1)

    timings = build_tile_schedule(analysis, profile, random.Random(4), style=MapStyle(enable_slow=True))

    quiet_tiles = [t for t in timings if 4.5 <= t.time_sec <= 7.5]
    assert quiet_tiles
    assert all(t.bpm < 120.0 for t in quiet_tiles)


def test_enable_slow_ramps_gradually_instead_of_jumping() -> None:
    """Change Speed처럼 슬로우 구간 진입이 한 번에 뚝 떨어지지 않고 여러
    단계로 점진적으로 느려져야 한다."""
    analysis = make_analysis_result(bpm=120.0, duration_sec=16.0, drop_time_sec=None)
    energy_profile = [
        EnergyPoint(time_sec=round(i * 0.1, 3), rms_db=-50.0 if 4.0 <= i * 0.1 <= 10.0 else -10.0)
        for i in range(160)
    ]
    analysis = analysis.model_copy(update={"energy_profile": energy_profile})
    profile = profile_for_level(1)

    timings = build_tile_schedule(
        analysis, profile, random.Random(5), style=MapStyle(enable_slow=True, slow_speed_factor=0.5)
    )

    entering = [t for t in timings if 4.0 <= t.time_sec <= 6.0]
    bpms = sorted({t.bpm for t in entering})
    # 순간적으로 120 -> 60으로 바뀌는 게 아니라 그 사이의 여러 단계가 있어야 한다.
    assert len(bpms) > 2
    assert all(60.0 <= b <= 120.0 for b in bpms)
