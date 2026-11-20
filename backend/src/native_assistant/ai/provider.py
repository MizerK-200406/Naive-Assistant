"""Small provider boundary for structured local model responses."""

from typing import Protocol

from pydantic import BaseModel, Field


class GenerationRequest(BaseModel):
    system: str = Field(min_length=1)
    prompt: str = Field(min_length=1)
    json_schema: dict


class GenerationResult(BaseModel):
    content: str = Field(min_length=1)
    model: str
    prompt_tokens: int | None = None
    output_tokens: int | None = None


class ProviderError(Exception):
    """A model provider could not produce a valid response."""


class LlmProvider(Protocol):
    def generate(self, request: GenerationRequest) -> GenerationResult: ...
