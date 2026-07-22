"""Google Gemini(무료 티어) API 클라이언트.

Claude API 대신 비용 없이 사용할 수 있는 Gemini 무료 티어를 사용한다.
GEMINI_API_KEY가 없거나 호출이 실패하는 환경(오프라인 테스트, 키 미발급 등)에서도
상위 계층(app/ai/instruction_parser.py)이 규칙 기반 파서로 자동 대체할 수 있도록,
설정 여부를 확인할 수 있는 is_configured와 실패 시 AIServiceError만 던지는
단순한 인터페이스로 감싼다.
"""

from collections.abc import Callable

from app.ai.exceptions import AIServiceError
from app.core.config import get_settings

DEFAULT_MODEL = "gemini-1.5-flash"


class GeminiClient:
    def __init__(
        self,
        api_key: str | None = None,
        model: str = DEFAULT_MODEL,
        generate_fn: Callable[[str], str] | None = None,
    ) -> None:
        """generate_fn을 주입하면 실제 Gemini SDK 호출 없이 동작을 대체할 수 있다
        (테스트, 또는 다른 백엔드로의 향후 교체 지점).
        """
        self._api_key = api_key if api_key is not None else get_settings().gemini_api_key
        self._model_name = model
        self._generate_fn = generate_fn

    @property
    def is_configured(self) -> bool:
        return bool(self._api_key)

    def generate_text(self, prompt: str) -> str:
        if not self.is_configured:
            raise AIServiceError("GEMINI_API_KEY가 설정되지 않았습니다")

        try:
            if self._generate_fn is not None:
                return self._generate_fn(prompt)
            return self._call_gemini_api(prompt)
        except AIServiceError:
            raise
        except Exception as exc:  # Gemini SDK/네트워크 오류를 모두 AIServiceError로 통일
            raise AIServiceError(f"Gemini API 호출 중 오류가 발생했습니다: {exc}") from exc

    def _call_gemini_api(self, prompt: str) -> str:
        import google.generativeai as genai

        genai.configure(api_key=self._api_key)
        model = genai.GenerativeModel(self._model_name)
        response = model.generate_content(prompt)
        return response.text
