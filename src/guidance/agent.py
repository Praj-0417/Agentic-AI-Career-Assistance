"""
src/guidance/agent.py
─────────────────────────────────────────────────────────────────────────────
BACKWARD COMPATIBILITY SHIM — do not add logic here.

All LLM + search logic has moved to:
  src/core/llm.py    → get_llm()
  src/core/search.py → get_search_tool()

This file simply re-exports those functions so any old imports continue
to work during the refactor transition.

TODO (Commit 5): Delete this file once all imports are updated.
"""

from src.core.llm import get_llm          # noqa: F401 (re-export)
from src.core.search import get_search_tool  # noqa: F401 (re-export)

__all__ = ["get_llm", "get_search_tool"]
