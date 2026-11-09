"""A small client for Claude's Messages API with tool use. No packages needed."""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request

API_URL = "https://api.anthropic.com/v1/messages"


class LLMError(Exception):
    pass


class Claude:
    def __init__(self, api_key: str, model: str, timeout: float = 180):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def create(self, system: list[dict], messages: list[dict], tools: list[dict], max_tokens: int = 4096) -> dict:
        body = {"model": self.model, "max_tokens": max_tokens, "system": system, "messages": messages}
        if tools:
            body["tools"] = tools
        data = json.dumps(body).encode()
        delay = 2.0
        for attempt in range(5):
            req = urllib.request.Request(API_URL, data=data, headers={
                "x-api-key": self.api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as r:
                    return json.load(r)
            except urllib.error.HTTPError as e:
                detail = _error_text(e)
                if e.code in (429, 500, 502, 503, 504, 529) and attempt < 4:
                    retry_after = e.headers.get("retry-after") if e.headers else None
                    time.sleep(float(retry_after) if retry_after and retry_after.isdigit() else delay)
                    delay *= 2
                    continue
                if e.code == 401:
                    raise LLMError("Claude rejected the API key. Check ANTHROPIC_API_KEY.") from e
                raise LLMError(f"Claude API error {e.code}: {detail}") from e
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                if attempt < 4:
                    time.sleep(delay)
                    delay *= 2
                    continue
                raise LLMError(f"couldn't reach Claude: {e}") from e
        raise LLMError("Claude is busy; try again in a minute.")


def _error_text(e: urllib.error.HTTPError) -> str:
    try:
        payload = json.loads(e.read().decode("utf-8", "replace"))
        return payload.get("error", {}).get("message", "") or str(payload)
    except Exception:
        return str(e)
