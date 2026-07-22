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
"""

import random
from dataclasses import dataclass

from app.mapgen.difficulty import DifficultyProfile
from app.models.audio import AudioAnalysisResult, EnergyPoint, TempoChangePoint

DOWNBEAT_EPSILON_SEC = 0.05
DROP_EMPHASIS_WINDOW_SEC = 1.5
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
    analysis: AudioAnalysisResult, profile: DifficultyProfile, rng: random.Random
) -> list[TileTiming]:
    """구간별 BPM 그리드 위에서, 난이도에 따라 각 박을 몇 개의 타일로
    나눌지 선택해 타임라인을 만든다. 드롭 구간과 높은 에너지 구간은 더
    잘게 나뉠 확률을 높여 음악의 강조 구간에서 패턴 밀도가 자연스럽게
    올라가게 한다.
    """
    if not analysis.beat_times:
        return []

    sections = _build_tempo_sections(analysis)
    if not sections:
        return []

    downbeat_times = analysis.downbeat_times
    drop_times = [d.time_sec for d in analysis.drops]
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
        energy_db = _nearest_energy_db(t, analysis.energy_profile)
        split_n = _choose_split(profile, rng, near_drop, energy_db)
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


def _choose_split(
    profile: DifficultyProfile, rng: random.Random, near_drop: bool, energy_db: float
) -> int:
    normalized_energy = _normalize_energy(energy_db)
    energy_multiplier = 1.0 + profile.energy_bias_strength * normalized_energy

    splits = list(profile.beat_split_weights.keys())
    weights = []
    for n in splits:
        w = profile.beat_split_weights[n]
        if n > 1:
            w *= energy_multiplier
            if near_drop:
                w *= profile.drop_split_bonus
        weights.append(w)

    return rng.choices(splits, weights=weights, k=1)[0]


def _is_near_any(t: float, candidates: list[float], epsilon: float) -> bool:
    return any(abs(t - c) <= epsilon for c in candidates)


def _is_within_drop_window(t: float, drop_times: list[float], window_sec: float) -> bool:
    return any(0 <= t - d <= window_sec for d in drop_times)


def _nearest_energy_db(t: float, energy_profile: list[EnergyPoint]) -> float:
    if not energy_profile:
        return -60.0
    closest = min(energy_profile, key=lambda p: abs(p.time_sec - t))
    return closest.rms_db


def _normalize_energy(rms_db: float) -> float:
    floor_db, ceil_db = -60.0, 0.0
    return max(0.0, min(1.0, (rms_db - floor_db) / (ceil_db - floor_db)))
