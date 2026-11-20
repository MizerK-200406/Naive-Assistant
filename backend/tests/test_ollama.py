import json

import httpx
import pytest

from native_assistant.ai.ollama import OllamaProvider
from native_assistant.ai.provider import GenerationRequest, ProviderError


def request():
    return GenerationRequest(
        system="Answer safely", prompt="Question", json_schema={"type": "object"}
    )


def test_local_provider_request_and_usage() -> None:
    def handle(req):
        body = json.loads(req.content)
        assert str(req.url) == "http://127.0.0.1:11434/api/generate"
        assert body["think"] is False and body["stream"] is False
        return httpx.Response(
            200,
            json={
                "model": "qwen3:4b",
                "response": "{}",
                "done": True,
                "prompt_eval_count": 7,
                "eval_count": 3,
            },
        )

    result = OllamaProvider(transport=httpx.MockTransport(handle)).generate(request())
    assert result.output_tokens == 3


@pytest.mark.parametrize(
    "reply",
    [
        {"done": False, "model": "x", "response": "{}"},
        {"done": True, "model": "x", "response": "", "done_reason": "length"},
        {"done": True, "model": "x", "response": "partial output", "done_reason": "length"},
        {"error": "bad"},
    ],
)
def test_invalid_provider_reply(reply) -> None:
    provider = OllamaProvider(
        transport=httpx.MockTransport(lambda req: httpx.Response(200, json=reply))
    )
    with pytest.raises(ProviderError):
        provider.generate(request())


def test_timeout_is_reported() -> None:
    def fail(req):
        raise httpx.ReadTimeout("timeout", request=req)

    with pytest.raises(ProviderError):
        OllamaProvider(transport=httpx.MockTransport(fail)).generate(request())
