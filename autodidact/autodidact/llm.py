"""Optional LLM. Everything works without it; with it, answers are written in prose
and the agent can read API documentation to teach itself new sources.

Set ANTHROPIC_API_KEY (and optionally AUTODIDACT_MODEL) to turn it on."""
from __future__ import annotations

import json
import os
import urllib.request

DEFAULT_MODEL = "claude-sonnet-5-5"


class Claude:
    def __init__(self, api_key: str, model: str | None = None):
        self.api_key = api_key
        self.model = model or os.environ.get("AUTODIDACT_MODEL", DEFAULT_MODEL)

    def complete(self, prompt: str, system: str = "", max_tokens: int = 1024) -> str:
        body = {"model": self.model, "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}]}
        if system:
            body["system"] = system
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages", data=json.dumps(body).encode(),
            headers={"x-api-key": self.api_key, "anthropic-version": "2023-06-01",
                     "content-type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                data = json.load(r)
        except Exception as e:  # network/auth problems: callers fall back to non-LLM paths
            return f"[llm error: {e}]"
        return "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")


def from_env():
    key = os.environ.get("ANTHROPIC_API_KEY")
    return Claude(key) if key else None
