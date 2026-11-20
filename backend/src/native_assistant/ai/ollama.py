"""Ollama adapter restricted to a local loopback endpoint."""

import httpx
from pydantic import BaseModel, ValidationError

from native_assistant.ai.provider import GenerationRequest, GenerationResult, ProviderError


class OllamaReply(BaseModel):
    model: str
    response: str
    done: bool
    done_reason: str | None = None
    prompt_eval_count: int | None = None
    eval_count: int | None = None


class OllamaProvider:
    def __init__(
        self,
        model: str = "qwen3:4b",
        timeout: float = 300,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        if not model.strip() or timeout <= 0:
            raise ValueError("Model and positive timeout are required")
        self.model = model
        self.timeout = timeout
        self.transport = transport

    def generate(self, request: GenerationRequest) -> GenerationResult:
        payload = {
            "model": self.model,
            "system": request.system,
            "prompt": request.prompt,
            "format": request.json_schema,
            "stream": False,
            "think": False,
            "options": {"temperature": 0, "num_ctx": 4096, "num_predict": 768},
        }
        try:
            with httpx.Client(
                base_url="http://127.0.0.1:11434",
                timeout=self.timeout,
                transport=self.transport,
                trust_env=False,
            ) as client:
                response = client.post("/api/generate", json=payload)
                response.raise_for_status()
            reply = OllamaReply.model_validate(response.json())
            if not reply.done or reply.done_reason == "length" or not reply.response.strip():
                raise ProviderError("Ollama returned incomplete or empty output")
            return GenerationResult(
                content=reply.response,
                model=reply.model,
                prompt_tokens=reply.prompt_eval_count,
                output_tokens=reply.eval_count,
            )
        except (httpx.HTTPError, ValidationError, ValueError) as exc:
            raise ProviderError("Ollama request failed or returned an invalid response") from exc
