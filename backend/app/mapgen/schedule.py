"""오디오 분석 결과의 비트를 실제 타일 배치 타임라인으로 변환한다.

ADOFAI에서는 타일의 회전각이 곧 그 타일까지 걸리는 시간(박자)을 결정하기
때문에(180도=1박, 90도=반박 등), "언제 타일을 놓을지"와 "얼마나 꺾을지"는
독립적으로 정할 수 없다. 그래서 원시 비트 타임스탬프를 그대로 쓰는 대신,
구간별 BPM으로 이상적인 박자 그리드를 만들고 그 위에서 한 박을 몇 개의
동일한 길이의 타일로 나눌지(split)를 선택한다.

각 타일의 time_sec는 항상 `직전 타일 시각 + (1/split_n) * (60/bpm)`으로만
전진한다 — 절대 다른 방식으로(예: 다음 템포 구간의 시작 시각에 억지로
맞추는 식으로) 시간을 조정하지 않는다. 그래야 6단계(파일 저장)에서
split_n/bpm으로부터 역산한 실제 게임 내 타이밍이 여기서 기록한 time_sec와
정확히 일치한다. 그 결과 템포가 바뀌는 지점은 실제 정박이 아니라 그
근처의 가장 가까운 박 경계에서 적용된다 — 오차는 최대 한 박 이내로,
템포 변화 검출 자체도 근사치이므로 충분히 허용 가능한 수준이다.

MapStyle 옵션(질주맵/슬로우)도 여기서 반영한다:
- enable_rush(질주맵): 지속적으로 에너지가 높은 구간에서는 split=1(쉬는 타일
  없이 직진)을 후보에서 빼, 끊임없이 빠르게 이어지는 느낌을 만든다.
- enable_slow(슬로우): 곡에서 가장 조용하고 긴 구간을 찾아 그 구간만 BPM을
  낮춘 임시 템포 구간으로 쪼갠다(SetSpeed 액션으로 자연스럽게 이어진다).
"""

import random
from dataclasses import dataclass

from app.mapgen.difficulty import DifficultyProfile
from app.mapgen.models import MapStyle
from app.models.audio import AudioAnalysisResult, EnergyPoint, TempoChangePoint

DOWNBEAT_EPSILON_SEC = 0.05
DROP_EMPHASIS_WINDOW_SEC = 1.5
RUSH_ENERGY_THRESHOLD_DB = -15.0
RUSH_MIN_WINDOW_SEC = 2.0
SLOW_ENERGY_THRESHOLD_DB = -35.0
SLOW_MIN_WINDOW_SEC = 2.0
SLOW_TEMPO_FACTOR = 0.6
_MIN_STEP_SEC = 1e-6


@dataclass
class TileTiming:
    time_sec: float
    is_downbeat: bool
    is_drop: bool
    energy_db: float
    # 직전 타일에서 이 타일까지의 전이가 한 박을 몇 등분한 것인지 (1=한 박 그대로)
    split_n: int
    # 이 전이에 사용된 BPM
    bpm: float


def build_tile_schedule(
    analysis: AudioAnalysisResult,
    profile: DifficultyProfile,
    rng: random.Random,
    style: MapStyle | None = None,
) -> list[TileTiming]:
    """구간별 BPM 그리드 위에서, 난이도에 따라 각 박을 몇 개의 타일로
    나눌지 선택해 타임라인을 만든다. 드롭 구간과 높은 에너지 구간은 더
    잘게 나뉠 확률을 높여 음악의 강조 구간에서 패턴 밀도가 자연스럽게
    올라가게 한다.
    """
    if not analysis.beat_times:
        return []

    style = style or MapStyle()

    sections = _build_tempo_sections(analysis)
    if style.enable_slow:
        sections = _apply_slow_sections(sections, analysis.energy_profile)
    if not sections:
        return []

    downbeat_times = analysis.downbeat_times
    drop_times = [d.time_sec for d in analysis.drops]
    rush_windows = _find_windows(
        analysis.energy_profile, RUSH_ENERGY_THRESHOLD_DB, RUSH_MIN_WINDOW_SEC, above=True
    ) if style.enable_rush else []
    end_time = sections[-1][1]

    def bpm_at(t: float) -> float:
        for start, end, bpm in sections:
            if t < end:
                return bpm
        return sections[-1][2]

    def make_timing(t: float, bpm: float, split_n: int, near_drop: bool, energy_db: float) -> TileTiming:
        return TileTiming(
            time_sec=t,
            is_downbeat=_is_near_any(t, downbeat_times, DOWNBEAT_EPSILON_SEC),
            is_drop=near_drop,
            energy_db=energy_db,
            split_n=split_n,
            bpm=bpm,
        )

    t = sections[0][0]
    # 전체 시퀀스의 첫 타일은 진입 전이가 없는 시작점이다(split_n은 의미 없음).
    timings: list[TileTiming] = [
        make_timing(t, bpm_at(t), 1, False, _nearest_energy_db(t, analysis.energy_profile))
    ]

    while t < end_time - _MIN_STEP_SEC:
        bpm = bpm_at(t)
        beat_duration = 60.0 / bpm
        near_drop = _is_within_drop_window(t, drop_times, DROP_EMPHASIS_WINDOW_SEC)
        in_rush = _is_within_any_window(t, rush_windows)
        energy_db = _nearest_energy_db(t, analysis.energy_profile)
        split_n = _choose_split(profile, rng, near_drop, in_rush, energy_db)
        sub_duration = beat_duration / split_n

        for _ in range(split_n):
            t += sub_duration
            if t >= end_time - _MIN_STEP_SEC:
                break
            timings.append(make_timing(t, bpm, split_n, near_drop, energy_db))

    return timings


def _build_tempo_sections(analysis: AudioAnalysisResult) -> list[tuple[float, float, float]]:
    """템포 변화 감지 결과를 [(시작 시각, 끝 시각, BPM), ...] 구간 목록으로 변환한다."""
    duration = analysis.duration_sec
    changes: list[TempoChangePoint] = sorted(analysis.tempo_changes, key=lambda c: c.time_sec)

    if not changes:
        start = analysis.beat_times[0] if analysis.beat_times else 0.0
        return [(start, duration, analysis.bpm)]

    sections: list[tuple[float, float, float]] = []
    for i, change in enumerate(changes):
        start = change.time_sec
        end = changes[i + 1].time_sec if i + 1 < len(changes) else duration
        if end <= start:
            continue
        bpm = change.bpm if change.bpm > 0 else analysis.bpm
        sections.append((start, end, bpm))

    if not sections:
        start = analysis.beat_times[0] if analysis.beat_times else 0.0
        return [(start, duration, analysis.bpm)]

    return sections


def _apply_slow_sections(
    sections: list[tuple[float, float, float]], energy_profile: list[EnergyPoint]
) -> list[tuple[float, float, float]]:
    """가장 길고 조용한 구간을 찾아 그 부분만 템포를 늦춘 구간으로 쪼갠다."""
    quiet_windows = _find_windows(energy_profile, SLOW_ENERGY_THRESHOLD_DB, SLOW_MIN_WINDOW_SEC, above=False)
    if not quiet_windows:
        return sections

    quiet_start, quiet_end = max(quiet_windows, key=lambda w: w[1] - w[0])

    new_sections: list[tuple[float, float, float]] = []
    for start, end, bpm in sections:
        overlap_start = max(start, quiet_start)
        overlap_end = min(end, quiet_end)
        if overlap_start >= overlap_end:
            new_sections.append((start, end, bpm))
            continue

        if start < overlap_start:
            new_sections.append((start, overlap_start, bpm))
        new_sections.append((overlap_start, overlap_end, bpm * SLOW_TEMPO_FACTOR))
        if overlap_end < end:
            new_sections.append((overlap_end, end, bpm))

    return new_sections


def _choose_split(
    profile: DifficultyProfile, rng: random.Random, near_drop: bool, in_rush: bool, energy_db: float
) -> int:
    normalized_energy = _normalize_energy(energy_db)
    energy_multiplier = 1.0 + profile.energy_bias_strength * normalized_energy

    splits = list(profile.beat_split_weights.keys())
    if in_rush and len(splits) > 1:
        # 질주맵: 쉬는 타일(split=1) 없이 계속 움직이게 한다.
        splits = [n for n in splits if n > 1] or splits

    weights = []
    for n in splits:
        w = profile.beat_split_weights.get(n, 1.0)
        if n > 1:
            w *= energy_multiplier
            if near_drop:
                w *= profile.drop_split_bonus
            if in_rush:
                w *= profile.drop_split_bonus
        weights.append(w)

    return rng.choices(splits, weights=weights, k=1)[0]


def _is_near_any(t: float, candidates: list[float], epsilon: float) -> bool:
    return any(abs(t - c) <= epsilon for c in candidates)


def _is_within_drop_window(t: float, drop_times: list[float], window_sec: float) -> bool:
    return any(0 <= t - d <= window_sec for d in drop_times)


def _is_within_any_window(t: float, windows: list[tuple[float, float]]) -> bool:
    return any(start <= t < end for start, end in windows)


def _find_windows(
    energy_profile: list[EnergyPoint], threshold_db: float, min_duration_sec: float, above: bool
) -> list[tuple[float, float]]:
    """에너지가 threshold_db보다 (above면 크거나, 아니면 작거나) 같은 상태가
    min_duration_sec 이상 지속되는 구간들을 찾는다.
    """
    if not energy_profile:
        return []

    points = sorted(energy_profile, key=lambda p: p.time_sec)
    windows: list[tuple[float, float]] = []
    run_start: float | None = None
    prev_t = points[0].time_sec

    for point in points:
        matches = point.rms_db >= threshold_db if above else point.rms_db <= threshold_db
        if matches and run_start is None:
            run_start = point.time_sec
        elif not matches and run_start is not None:
            if prev_t - run_start >= min_duration_sec:
                windows.append((run_start, prev_t))
            run_start = None
        prev_t = point.time_sec

    if run_start is not None and prev_t - run_start >= min_duration_sec:
        windows.append((run_start, prev_t))

    return windows


def _nearest_energy_db(t: float, energy_profile: list[EnergyPoint]) -> float:
    if not energy_profile:
        return -60.0
    closest = min(energy_profile, key=lambda p: abs(p.time_sec - t))
    return closest.rms_db


def _normalize_energy(rms_db: float) -> float:
    floor_db, ceil_db = -60.0, 0.0
    return max(0.0, min(1.0, (rms_db - floor_db) / (ceil_db - floor_db)))
