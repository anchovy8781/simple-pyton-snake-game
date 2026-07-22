"""자연어 편집 지시를 구조화한 데이터 모델."""

from pydantic import BaseModel


class EditInstruction(BaseModel):
    """자연어 편집 요청 하나를 구조화한 결과."""

    start_sec: float
    end_sec: float
    # 현재 난이도 대비 몇 단계 올리거나 내릴지 (예: +1 = 한 단계 어렵게)
    difficulty_delta: int = 0
    emphasize_flashy: bool = False
    reduce_repetition: bool = False
    tighten_timing: bool = False
    raw_instruction: str
    # 이 지시가 "gemini"(AI)로 해석됐는지 "rule_based"(규칙 기반 대체)로 해석됐는지
    source: str = "rule_based"
