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
    실제 게임 좌표계로의 변환(절대 각도, pathData 문자 등)은 6단계(파일 저장)에서 수행한다.
    """

    index: int
    time_sec: float
    turn_angle_deg: float
    is_downbeat: bool = False
    is_drop_emphasis: bool = False
    energy_db: float = 0.0


class GeneratedMap(BaseModel):
    bpm: float
    difficulty: Difficulty
    duration_sec: float
    tiles: list[Tile]
