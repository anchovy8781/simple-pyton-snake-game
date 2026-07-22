"""GeneratedMap을 실제 ADOFAI 커스텀 레벨(.adofai, JSON) 포맷으로 변환한다.

.adofai 핵심 구조:
- angleData: 각 타일의 "절대" 진행 방향(도). 0도=오른쪽, 반시계 방향으로 증가.
  angleData[0]은 항상 0(시작 방향)이며, 배열 길이는 타일 개수와 같다.
- settings: bpm/오프셋/곡 파일명 등 레벨 메타데이터.
- actions: SetSpeed(구간별 BPM 변경), Twirl(회전 방향 반전) 등 이벤트.

ADOFAI의 근본 메커니즘상 "타일의 상대 회전각"이 곧 "그 타일까지 걸리는
박자"다(직전 타일 대비 상대각 180도=1박, 90도=반박, ...). 맵 생성 엔진
(app/mapgen)은 이미 회전각=박자로 일관되게 타일을 만들어두므로, 여기서는
1) 절대 각도를 누적하고, 2) 왼쪽(양수) 회전이 아닌 타일마다 Twirl 액션을
넣어 실제 재생 시간이 정확히 의도한 박자가 되도록 보정하고, 3) 구간별
BPM이 바뀌는 지점에만 SetSpeed 액션을 넣는다. 이렇게 하면 곡의 실제 박자와
어긋나지 않는(박자 정확도) 파일이 만들어진다.

주의: Twirl 액션의 정확한 JSON 필드 구성은 공식 문서가 아닌 커뮤니티
도구(ADOFAI-Map-Converter, adofai-angle-calculator)의 역공학 결과를 참고해
구현했다. 실제 게임/에디터에서 불러왔을 때 회전 "방향"이 의도와 다르게
보인다면 이 부분을 우선 의심하고 조정해야 한다 — 박자(타이밍) 자체는
Twirl 여부와 무관하게 이미 검증된 공식(아래 adofai_reader.py의 왕복 테스트
참고)으로 보장된다.
"""

from pathlib import Path

from app.mapgen.models import Difficulty, GeneratedMap

_BPM_CHANGE_TOLERANCE = 1e-6
_DIFFICULTY_TO_SETTINGS_VALUE = {
    Difficulty.EASY: 1,
    Difficulty.NORMAL: 3,
    Difficulty.HARD: 5,
    Difficulty.EXTREME: 7,
}


def build_adofai_document(
    generated_map: GeneratedMap,
    song_filename: str,
    song_name: str = "",
    artist: str = "",
    author: str = "",
    offset_ms: int = 0,
) -> dict:
    """GeneratedMap을 ADOFAI가 읽을 수 있는 JSON(dict)으로 변환한다."""
    tiles = generated_map.tiles
    angle_data, actions = _build_angle_data_and_actions(tiles)

    base_bpm = tiles[0].bpm if tiles and tiles[0].bpm > 0 else generated_map.bpm

    settings = {
        "version": 3,
        "artist": artist or "Unknown Artist",
        "song": song_name or Path(song_filename).stem,
        "author": author or "ADOFAI Map Generator",
        "songFilename": song_filename,
        "bpm": base_bpm,
        "offset": offset_ms,
        "pitch": 100,
        "volume": 100,
        "difficulty": _DIFFICULTY_TO_SETTINGS_VALUE[generated_map.difficulty],
        "trackColor": "debb7b",
        "secondaryTrackColor": "ffffff",
        "backgroundColor": "000000",
    }

    return {
        "angleData": angle_data,
        "settings": settings,
        "actions": actions,
        "decorations": [],
    }


def _build_angle_data_and_actions(tiles: list) -> tuple[list[float], list[dict]]:
    if not tiles:
        return [0.0], []

    angle_data: list[float] = [0.0]
    actions: list[dict] = []

    current_abs_angle = 0.0
    spin = 1  # 1=정상, -1=Twirl된 상태
    current_bpm = tiles[0].bpm if tiles[0].bpm > 0 else 0.0

    for i in range(1, len(tiles)):
        tile = tiles[i]
        floor = i - 1

        tile_bpm = tile.bpm if tile.bpm > 0 else current_bpm
        if current_bpm > 0 and abs(tile_bpm - current_bpm) > _BPM_CHANGE_TOLERANCE:
            actions.append(
                {
                    "floor": floor,
                    "eventType": "SetSpeed",
                    "speedType": "Bpm",
                    "beatsPerMinute": round(tile_bpm, 6),
                }
            )
        current_bpm = tile_bpm

        turn = tile.turn_angle_deg
        current_abs_angle = (current_abs_angle + turn) % 360.0
        angle_data.append(current_abs_angle)

        # 회전각이 0(직진)이면 어느 spin 상태에서든 정확히 1박이므로 twirl이 필요 없다.
        if turn != 0.0:
            desired_spin = 1 if turn > 0 else -1
            if desired_spin != spin:
                actions.append({"floor": floor, "eventType": "Twirl"})
                spin = desired_spin

    return angle_data, actions
