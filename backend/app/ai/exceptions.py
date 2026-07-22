"""AI 연동 모듈 전용 예외."""


class AIServiceError(Exception):
    """Gemini API 호출 실패(키 없음, 네트워크 오류, API 오류 등)."""


class InstructionParseError(Exception):
    """AI 응답을 구조화된 편집 지시(EditInstruction)로 해석하지 못한 경우."""
