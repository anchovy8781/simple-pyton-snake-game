"""오디오 분석 결과를 표현하는 공용 데이터 모델."""

from pydantic import BaseModel


class EnergyPoint(BaseModel):
    """특정 시점의 음량(RMS, dB) 값."""

    time_sec: float
    rms_db: float


class TempoChangePoint(BaseModel):
    """템포가 유의미하게 바뀐 지점."""

    time_sec: float
    bpm: float


class DropEvent(BaseModel):
    """빌드업 이후 에너지가 급격히 상승하며 유지되는 '드롭' 추정 지점."""

    time_sec: float
    strength: float


class AudioAnalysisResult(BaseModel):
    """오디오 파일 하나를 분석한 전체 결과."""

    duration_sec: float
    sample_rate: int
    bpm: float
    beat_times: list[float]
    downbeat_times: list[float]
    energy_profile: list[EnergyPoint]
    tempo_changes: list[TempoChangePoint]
    drops: list[DropEvent]
