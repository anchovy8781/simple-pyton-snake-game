"""오디오 분석 결과의 비트를 실제 타일 배치 타임라인으로 변환한다."""

import random
from dataclasses import dataclass

from app.mapgen.difficulty import DifficultyProfile
from app.models.audio import AudioAnalysisResult, EnergyPoint

DOWNBEAT_EPSILON_SEC = 0.05
DROP_EMPHASIS_WINDOW_SEC = 1.5


@dataclass
class TileTiming:
    time_sec: float
    is_downbeat: bool
    is_drop: bool
    energy_db: float


def build_tile_schedule(
    analysis: AudioAnalysisResult, profile: DifficultyProfile, rng: random.Random
) -> list[TileTiming]:
    """비트를 기본 그리드로 삼아, 난이도에 따라 박자 사이에 세분(subdivision)
    타일을 추가한 타임라인을 만든다. 드롭 구간 근처는 세분 확률을 높여
    음악의 강조 구간에서 패턴 밀도가 자연스럽게 올라가게 한다.
    """
    if not analysis.beat_times:
        return []

    downbeat_times = analysis.downbeat_times
    drop_times = [d.time_sec for d in analysis.drops]
    beats = analysis.beat_times

    timings: list[TileTiming] = []
    for i, t in enumerate(beats):
        near_drop = _is_within_drop_window(t, drop_times, DROP_EMPHASIS_WINDOW_SEC)
        timings.append(
            TileTiming(
                time_sec=t,
                is_downbeat=_is_near_any(t, downbeat_times, DOWNBEAT_EPSILON_SEC),
                is_drop=near_drop,
                energy_db=_nearest_energy_db(t, analysis.energy_profile),
            )
        )

        if i + 1 < len(beats) and profile.subdivision_probability > 0:
            next_t = beats[i + 1]
            probability = min(profile.subdivision_probability * (1.6 if near_drop else 1.0), 0.9)
            if rng.random() < probability:
                mid_t = (t + next_t) / 2
                timings.append(
                    TileTiming(
                        time_sec=mid_t,
                        is_downbeat=False,
                        is_drop=near_drop,
                        energy_db=_nearest_energy_db(mid_t, analysis.energy_profile),
                    )
                )

    timings.sort(key=lambda tt: tt.time_sec)
    return timings


def _is_near_any(t: float, candidates: list[float], epsilon: float) -> bool:
    return any(abs(t - c) <= epsilon for c in candidates)


def _is_within_drop_window(t: float, drop_times: list[float], window_sec: float) -> bool:
    return any(0 <= t - d <= window_sec for d in drop_times)


def _nearest_energy_db(t: float, energy_profile: list[EnergyPoint]) -> float:
    if not energy_profile:
        return -60.0
    closest = min(energy_profile, key=lambda p: abs(p.time_sec - t))
    return closest.rms_db
