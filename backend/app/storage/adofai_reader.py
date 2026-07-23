"""ADOFAI 커스텀 레벨(.adofai, JSON)을 GeneratedMap으로 되돌린다.

adofai_writer.py가 만든 angleData/actions(SetSpeed, Twirl)를 정확히
역산하도록 구현했다 — 즉 "우리가 저장한 파일을 다시 불러와 이어서
편집"하는 용도로 신뢰할 수 있다. 이 왕복 변환이 원래 타일 시간과 정확히
일치하는지가 곧 회전각→박자 변환 공식이 올바른지를 검증하는 테스트가 된다
(tests/test_storage_adofai.py 참고).

임의의 외부(다른 도구로 만든) .adofai 파일도 열 수는 있지만, Pause/Hold/
Checkpoint 같은 이 도구가 만들지 않는 액션 종류는 무시되므로 그런 파일의
타이밍은 부정확할 수 있다.
"""

from app.mapgen.models import GeneratedMap, Tile, clamp_difficulty
from app.storage.exceptions import AdofaiParseError

_DEFAULT_DIFFICULTY = 13


def parse_adofai_document(document: dict) -> GeneratedMap:
    angle_data = document.get("angleData")
    if not angle_data:
        raise AdofaiParseError("angleData가 비어 있습니다")

    settings = document.get("settings", {})
    try:
        base_bpm = float(settings.get("bpm", 0))
    except (TypeError, ValueError) as exc:
        raise AdofaiParseError(f"settings.bpm 값이 올바르지 않습니다: {settings.get('bpm')!r}") from exc
    if base_bpm <= 0:
        raise AdofaiParseError(f"settings.bpm은 0보다 커야 합니다: {base_bpm}")

    set_speed_by_floor, twirl_floors = _index_actions(document.get("actions", []))

    tiles: list[Tile] = [
        Tile(index=0, time_sec=0.0, turn_angle_deg=0.0, bpm=base_bpm, split_n=1)
    ]

    current_time = 0.0
    current_bpm = base_bpm
    spin = 1

    for i in range(1, len(angle_data)):
        floor = i - 1
        if floor in set_speed_by_floor:
            current_bpm = set_speed_by_floor[floor]
        if floor in twirl_floors:
            spin = -spin

        turn = _shortest_turn(angle_data[i - 1], angle_data[i])

        raw_rel_angle = (180.0 - turn) % 360.0
        if raw_rel_angle == 0.0:
            raw_rel_angle = 360.0
        effective_rel_angle = raw_rel_angle if spin == 1 else (360.0 - raw_rel_angle)

        beats = effective_rel_angle / 180.0
        duration_sec = beats * (60.0 / current_bpm)
        current_time += duration_sec

        tiles.append(
            Tile(
                index=i,
                time_sec=current_time,
                turn_angle_deg=turn,
                bpm=current_bpm,
                split_n=_beats_to_split_n(beats),
            )
        )

    raw_difficulty = settings.get("difficulty")
    try:
        difficulty = clamp_difficulty(int(raw_difficulty))
    except (TypeError, ValueError):
        difficulty = _DEFAULT_DIFFICULTY

    return GeneratedMap(
        bpm=base_bpm,
        difficulty=difficulty,
        duration_sec=current_time,
        tiles=tiles,
    )


def _index_actions(actions: list[dict]) -> tuple[dict[int, float], set[int]]:
    set_speed_by_floor: dict[int, float] = {}
    twirl_floors: set[int] = set()

    for action in actions:
        floor = action.get("floor")
        event_type = action.get("eventType")
        if floor is None:
            continue
        if event_type == "SetSpeed" and action.get("speedType") == "Bpm":
            bpm_value = action.get("beatsPerMinute")
            if bpm_value:
                set_speed_by_floor[int(floor)] = float(bpm_value)
        elif event_type == "Twirl":
            twirl_floors.add(int(floor))

    return set_speed_by_floor, twirl_floors


def _shortest_turn(prev_angle: float, curr_angle: float) -> float:
    diff = (curr_angle - prev_angle) % 360.0
    return diff - 360.0 if diff > 180.0 else diff


def _beats_to_split_n(beats: float) -> int:
    if beats <= 0:
        return 1
    return max(1, round(1.0 / beats))
