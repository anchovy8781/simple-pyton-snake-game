"""맵 생성 엔진 진입점: 오디오 분석 결과 -> ADOFAI 타일 시퀀스."""

import random

from app.mapgen.difficulty import DIFFICULTY_PROFILES, DifficultyProfile
from app.mapgen.models import Difficulty, GeneratedMap, Tile
from app.mapgen.pattern import generate_angles
from app.mapgen.schedule import TileTiming, build_tile_schedule
from app.models.audio import AudioAnalysisResult


def generate_map(
    analysis: AudioAnalysisResult, difficulty: Difficulty, seed: int | None = None
) -> GeneratedMap:
    """오디오 분석 결과 전체로부터 새 맵을 생성한다."""
    profile = DIFFICULTY_PROFILES[difficulty]
    rng = random.Random(seed)

    tile_timings = build_tile_schedule(analysis, profile, rng)
    turn_angles = generate_angles(
        tile_timings, profile.max_consecutive_repeat, rng, flip_probability=profile.flip_probability
    )

    tiles = [
        Tile(
            index=i,
            time_sec=timing.time_sec,
            turn_angle_deg=angle,
            is_downbeat=timing.is_downbeat,
            is_drop_emphasis=timing.is_drop,
            energy_db=timing.energy_db,
            split_n=timing.split_n,
            bpm=timing.bpm,
        )
        for i, (timing, angle) in enumerate(zip(tile_timings, turn_angles, strict=True))
    ]

    return GeneratedMap(
        bpm=analysis.bpm,
        difficulty=difficulty,
        duration_sec=analysis.duration_sec,
        tiles=tiles,
    )


def regenerate_segment(
    existing_map: GeneratedMap,
    start_sec: float,
    end_sec: float,
    difficulty: Difficulty | None = None,
    profile_override: DifficultyProfile | None = None,
    seed: int | None = None,
) -> GeneratedMap:
    """기존 맵 중 [start_sec, end_sec] 구간의 회전 "방향"만 새로 생성한다.

    타일의 박자 배치(시간)와 split_n(박 분할)은 그대로 유지하고 방향(부호)만
    다시 만들기 때문에 박자 정확도에는 영향이 없다 — ADOFAI에서는 회전각의
    크기가 곧 박자이므로, 크기를 바꾸지 않아야 타이밍이 보존된다. 구간
    경계 바깥과의 진입/퇴장 각도를 정교하게 맞추는 것은 4단계(AI 편집)에서
    자연어 지시에 맞춰 다듬을 여지로 남겨둔다.

    profile_override를 넘기면 난이도 프리셋 대신 그 프로파일을 그대로 사용한다.
    "반복을 줄여" 같은 자연어 편집 지시를 max_consecutive_repeat만 조정한
    임시 프로파일로 변환해 적용할 때 쓰인다(app/ai/edit_engine.py 참고).
    """
    if start_sec >= end_sec:
        raise ValueError("start_sec는 end_sec보다 작아야 합니다")

    segment_indices = [
        i for i, tile in enumerate(existing_map.tiles) if start_sec <= tile.time_sec <= end_sec
    ]
    if not segment_indices:
        raise ValueError("지정한 구간에 해당하는 타일이 없습니다")

    result_difficulty = difficulty if difficulty is not None else existing_map.difficulty
    profile = profile_override if profile_override is not None else DIFFICULTY_PROFILES[result_difficulty]
    rng = random.Random(seed)

    segment_timings = [
        TileTiming(
            time_sec=existing_map.tiles[i].time_sec,
            is_downbeat=existing_map.tiles[i].is_downbeat,
            is_drop=existing_map.tiles[i].is_drop_emphasis,
            energy_db=existing_map.tiles[i].energy_db,
            split_n=existing_map.tiles[i].split_n,
            bpm=existing_map.tiles[i].bpm,
        )
        for i in segment_indices
    ]

    first_idx = segment_indices[0]
    initial_sign = 1
    if first_idx > 0:
        prev_angle = existing_map.tiles[first_idx - 1].turn_angle_deg
        if prev_angle != 0:
            initial_sign = 1 if prev_angle > 0 else -1

    new_angles = generate_angles(
        segment_timings,
        profile.max_consecutive_repeat,
        rng,
        force_first_straight=False,
        initial_sign=initial_sign,
        flip_probability=profile.flip_probability,
    )

    new_tiles = list(existing_map.tiles)
    for offset, idx in enumerate(segment_indices):
        new_tiles[idx] = new_tiles[idx].model_copy(update={"turn_angle_deg": new_angles[offset]})

    return existing_map.model_copy(update={"tiles": new_tiles, "difficulty": result_difficulty})
