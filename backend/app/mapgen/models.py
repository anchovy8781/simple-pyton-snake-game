"""맵 생성 엔진이 다루는 데이터 모델."""

from enum import Enum

from pydantic import BaseModel


class Difficulty(str, Enum):
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"
    EXTREME = "extreme"


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
    difficulty: Difficulty
    duration_sec: float
    tiles: list[Tile]
