"""
src/core/llm.py
─────────────────────────────────────────────────────────────────────────────
LLM Factory — single responsibility: construct and return a configured LLM.

All HTTP, retry, and model-selection logic lives here.
Nodes import `get_llm(role)` and nothing else.
"""

from __future__ import annotations

import os
import time
import requests
from typing import Any, List, Optional

from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain.llms.base import LLM
from dotenv import load_dotenv

load_dotenv()


# ── Together AI Custom LLM Wrapper ──────────────────────────────────────────

class _TogetherLLM(LLM):
    """
    Thin LangChain-compatible wrapper around the Together AI
    /v1/chat/completions endpoint.

    Responsibilities:
    - Auth header injection
    - Exponential-backoff retry (rate limits + transient errors)
    - Stop-sequence enforcement (fallback if provider ignores them)
    - System message injection when `system_prompt` is set
    """

    model: str
    together_api_key: str = os.environ.get("TOGETHER_API_KEY", "")
    temperature: float = 0.7
    max_tokens: int = 4096
    max_retries: int = 3
    initial_retry_delay: float = 1.0
    system_prompt: str = ""          # Injected by caller for context

    @property
    def _llm_type(self) -> str:
        return "together_ai"

    # ── Internal HTTP call with retry ──────────────────────────────────────

    def _call_api(self, messages: list[dict], stop: list[str] | None, retry: int = 0) -> str:
        headers = {
            "Authorization": f"Bearer {self.together_api_key}",
            "Content-Type": "application/json",
        }
        payload: dict[str, Any] = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "messages": messages,
        }
        if stop:
            # Expand stop list: include both raw and stripped variants
            expanded = list(stop)
            for s in stop:
                s2 = s.strip()
                if s2 and s2 not in expanded:
                    expanded.append(s2)
            payload["stop"] = expanded

        try:
            resp = requests.post(
                "https://api.together.xyz/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=60,
            )

            if resp.status_code == 429:
                if retry < self.max_retries:
                    delay = self.initial_retry_delay * (4 ** retry)
                    print(f"[llm] rate-limited — retrying in {delay:.1f}s (attempt {retry+1})")
                    time.sleep(delay)
                    return self._call_api(messages, stop, retry + 1)
                return "⚠️ Rate limit exceeded. Please wait a moment and try again."

            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]

        except requests.RequestException as exc:
            if retry < self.max_retries:
                delay = self.initial_retry_delay * (2 ** retry)
                print(f"[llm] request error — retrying in {delay:.1f}s: {exc}")
                time.sleep(delay)
                return self._call_api(messages, stop, retry + 1)
            return f"⚠️ API unavailable after {self.max_retries} retries: {exc}"

        except (KeyError, IndexError) as exc:
            return f"⚠️ Unexpected API response format: {exc}"

    # ── LangChain _call interface ──────────────────────────────────────────

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        messages: list[dict] = []

        # Inject system prompt if provided
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})

        messages.append({"role": "user", "content": prompt})

        content = self._call_api(messages, stop)

        # Fallback stop enforcement (provider might ignore them)
        if stop:
            for seq in stop:
                idx = content.find(seq)
                if idx != -1:
                    content = content[:idx]

        return content.strip()


# ── Public factory ───────────────────────────────────────────────────────────

def get_llm(role: str, system_prompt: str = "") -> _TogetherLLM:
    """
    Return a configured `_TogetherLLM` for the given agent role.

    Args:
        role:          One of the keys in `LLM_MODELS` / `LLM_DEFAULTS`.
        system_prompt: Optional system-level context injected before every call.

    Returns:
        A ready-to-use LangChain-compatible LLM instance.
    """
    from src.config import LLM_MODELS, LLM_DEFAULTS

    model   = LLM_MODELS.get(role, LLM_MODELS.get("general_qa", ""))
    defaults = LLM_DEFAULTS.get(role, {"temperature": 0.7, "max_tokens": 2048})

    return _TogetherLLM(
        model=model,
        temperature=defaults.get("temperature", 0.7),
        max_tokens=defaults.get("max_tokens", 2048),
        system_prompt=system_prompt,
    )
