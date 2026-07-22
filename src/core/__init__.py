"""
src/core/__init__.py
Exports the core LLM and search factories for easy import.
"""
from .llm import get_llm
from .search import get_search_tool

__all__ = ["get_llm", "get_search_tool"]
