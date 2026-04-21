"""Tiny HTTP client for a locally-running Ollama daemon.

We deliberately avoid the `ollama` Python package to keep dependencies
small and to make behaviour transparent for the technical appendix.
The client speaks Ollama's native REST API at /api/chat, which is
stable across 0.1.x -> 0.4.x.

Design notes:
  * Streaming is disabled (stream=False) because we want a single JSON
    response per call - simpler, no partial-response parsing.
  * The client retries transient network errors up to 3 times with
    exponential backoff. Retries are logged to the caller so the
    multi-solver pipeline can record them in eval manifests.
  * If the Ollama server is unreachable, calls raise OllamaError; the
    multi-solver orchestrator treats that as 'solver unavailable' and
    moves on (we never want one dead endpoint to crash the whole run).
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any

import requests  # type: ignore[import-untyped]


class OllamaError(RuntimeError):
    """Raised when an Ollama call cannot be completed."""


@dataclass(slots=True)
class ChatMessage:
    role: str  # "system" | "user" | "assistant"
    content: str

    def to_dict(self) -> dict[str, str]:
        return {"role": self.role, "content": self.content}


@dataclass(slots=True)
class ChatResponse:
    model: str
    content: str
    duration_ms: int
    eval_count: int | None
    raw: dict[str, Any]


class OllamaClient:
    """Synchronous client for a local Ollama server."""

    def __init__(self, host: str = "http://localhost:11434", default_timeout: int = 180) -> None:
        self.host = host.rstrip("/")
        self.default_timeout = default_timeout

    # ── Public API ──────────────────────────────────────────────

    def list_models(self) -> list[str]:
        """Return installed model tags (e.g. ['qwen2.5:7b', 'llama3:8b'])."""
        url = f"{self.host}/api/tags"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise OllamaError(f"Cannot reach Ollama at {self.host}: {exc}") from exc
        data = response.json()
        return [item.get("name", "") for item in data.get("models", [])]

    def chat(
        self,
        model: str,
        messages: list[ChatMessage] | list[dict[str, str]],
        *,
        temperature: float = 0.6,
        max_tokens: int = 1024,
        timeout: int | None = None,
        retries: int = 3,
        response_format_json: bool = False,
    ) -> ChatResponse:
        """Call /api/chat and return the assistant message.

        Parameters
        ----------
        model : str
            Ollama model tag.
        messages : list of ChatMessage or dict
            Chat history.
        response_format_json : bool
            When True, request strict JSON output (Ollama supports this
            via the "format": "json" field on 0.2+). We still parse
            leniently on the caller side.
        """

        payload_messages = [
            m.to_dict() if isinstance(m, ChatMessage) else m for m in messages
        ]

        payload: dict[str, Any] = {
            "model": model,
            "messages": payload_messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        if response_format_json:
            payload["format"] = "json"

        url = f"{self.host}/api/chat"
        deadline = timeout or self.default_timeout
        last_exc: Exception | None = None

        for attempt in range(retries):
            start = time.time()
            try:
                response = requests.post(url, json=payload, timeout=deadline)
                response.raise_for_status()
            except requests.RequestException as exc:
                last_exc = exc
                if attempt < retries - 1:
                    time.sleep(1.5 ** attempt)
                    continue
                raise OllamaError(
                    f"Ollama chat failed after {retries} attempts on model '{model}': {exc}"
                ) from exc

            data = response.json()
            message = data.get("message", {})
            content = str(message.get("content", ""))
            return ChatResponse(
                model=model,
                content=content,
                duration_ms=int((time.time() - start) * 1000),
                eval_count=data.get("eval_count"),
                raw=data,
            )

        raise OllamaError(f"Unreachable branch in chat() for {model}: {last_exc}")

    # ── Helpers ─────────────────────────────────────────────────

    def health(self) -> bool:
        try:
            self.list_models()
            return True
        except OllamaError:
            return False


def parse_json_relaxed(text: str) -> dict[str, Any] | None:
    """Parse JSON from a model response that may include stray prose.

    Strategy:
    1. Try plain json.loads.
    2. Look for the first '{' and last '}' and try to parse that slice.
    3. Return None on failure (caller decides how to handle).
    """
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None

    snippet = text[start : end + 1]
    try:
        return json.loads(snippet)
    except json.JSONDecodeError:
        return None
