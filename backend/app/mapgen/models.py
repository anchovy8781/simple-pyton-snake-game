"""맵 생성 엔진이 다루는 데이터 모델."""

from pydantic import BaseModel, Field

MIN_DIFFICULTY = 1
MAX_DIFFICULTY = 26


def clamp_difficulty(level: int) -> int:
    return max(MIN_DIFFICULTY, min(MAX_DIFFICULTY, level))


class MapStyle(BaseModel):
    """패턴의 전체적인 모양을 바꾸는 선택적 스타일 옵션.

    난이도(회전 빈도/밀도)와는 독립적으로, 생성된 맵의 "느낌"을 바꾼다.
    """

    # 마법진: 방향을 항상 한쪽으로만 꺾어 나선/원형 모양의 경로를 만든다.
    magic_circle: bool = False
    # 질주맵: 지속적으로 에너지가 높은 구간에서 쉬는 타일(split=1) 없이
    # 빠른 연속 타일로 채운다.
    enable_rush: bool = False
    # 슬로우: 곡에서 가장 조용한 구간을 찾아 그 부분의 템포를 일시적으로 늦춘다.
    enable_slow: bool = False


class Tile(BaseModel):
    """하나의 ADOFAI 타일.

    turn_angle_deg는 "직전 타일까지의 진행 방향" 대비 상대 회전각이다.
    0 = 직진, 양수 = 좌회전(반시계), 음수 = 우회전(시계), 180(=-180) = 반전.

    ADOFAI에서는 이 회전각이 곧 박자(직전 타일부터 이 타일까지 걸리는 시간)를
    결정한다. split_n(이 타일이 속한 박을 몇 등분했는지)과 bpm(그 시점의
    박자 속도)을 함께 저장해두면, 6단계(파일 저장)에서 이미 정해진 시간을
    다시 계산하지 않고도 정확한 회전각/템포 변화 액션으로 변환할 수 있다.
    """

    index: int
    time_sec: float
    turn_angle_deg: float
    is_downbeat: bool = False
    is_drop_emphasis: bool = False
    energy_db: float = 0.0
    split_n: int = 1
    bpm: float = 0.0


class GeneratedMap(BaseModel):
    bpm: float
    # 난이도: 1(가장 쉬움) ~ 26(가장 어려움) 정수 스케일.
    difficulty: int = Field(ge=MIN_DIFFICULTY, le=MAX_DIFFICULTY)
    duration_sec: float
    tiles: list[Tile]
