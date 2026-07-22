import pytest

from app.ai.exceptions import AIServiceError
from app.ai.gemini_client import GeminiClient


def test_is_configured_false_without_api_key() -> None:
    client = GeminiClient(api_key="")

    assert client.is_configured is False


def test_generate_text_raises_when_not_configured() -> None:
    client = GeminiClient(api_key="")

    with pytest.raises(AIServiceError):
        client.generate_text("hello")


def test_generate_text_uses_injected_generate_fn() -> None:
    client = GeminiClient(api_key="fake-key", generate_fn=lambda prompt: f"echo: {prompt}")

    result = client.generate_text("hello")

    assert result == "echo: hello"


def test_generate_text_wraps_generate_fn_exceptions() -> None:
    def _boom(prompt: str) -> str:
        raise RuntimeError("network down")

    client = GeminiClient(api_key="fake-key", generate_fn=_boom)

    with pytest.raises(AIServiceError):
        client.generate_text("hello")
