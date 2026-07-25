"""
src/agents/tutorials/node.py
─────────────────────────────────────────────────────────────────────────────
Tutorials Node — generates beginner-friendly, project-based tutorials.

STATE ISOLATION GUARANTEE:
  This node reads ONLY `task_input.tutorial_query` and `task_input.user_context`.
  It NEVER reads `user_profile.resume_content` or any resume-related key.
  This prevents the state-bleed bug where tutorial returned resume content.

Prompts in prompts.py | LLM from core.llm | Search from core.search.
"""

from __future__ import annotations

from langchain.prompts import PromptTemplate
from langchain_core.messages import AIMessage

from src.state import AgentState
from src.config import NODE_TUTORIALS
from src.core.llm import get_llm
from src.core.search import get_search_tool
from .prompts import TUTORIAL_TEMPLATE


_prompt = PromptTemplate(
    input_variables=["topic", "user_context", "search_results"],
    template=TUTORIAL_TEMPLATE,
)


def tutorials_node(state: AgentState) -> dict:
    """
    Reads (ONLY these keys — no resume bleed):
      task_input.tutorial_query    — topic to explain
      task_input.user_context      — background level
      task_input.background        — alias for user_context

    Writes:
      agent_output                 — full Markdown tutorial
    """
    task = state.get("task_input", {})

    # ── Strict key access — no fallback to user_profile ───────────────────
    topic        = (
        task.get("tutorial_query", "")
        or task.get("user_message", "")
    )
    user_context = (
        task.get("user_context", "")
        or task.get("background", "")
        # Intentionally NOT reading profile.resume_content or profile.skills
    )

    if not topic:
        return {
            "needs_clarification": True,
            "clarification_question": "What topic would you like a tutorial on?",
            "current_agent": "clarifier",
            "graph_trace":  [NODE_TUTORIALS],
        }

    # ── Live search for up-to-date best practices ─────────────────────────
    search_query = f"{topic} tutorial guide beginner 2026"
    try:
        tool           = get_search_tool()
        search_results = tool.func(search_query)
    except Exception as exc:
        search_results = f"Search unavailable: {exc}"

    # ── LLM generation ────────────────────────────────────────────────────
    try:
        llm    = get_llm("tutorials")
        output = llm.invoke(_prompt.format(
            topic=topic,
            user_context=user_context or "Beginner",
            search_results=search_results,
        ))

        # Strip ReAct-format leakage if present
        if "Final Answer:" in output:
            output = output.split("Final Answer:", 1)[-1].strip()

        return {
            "agent_output": output,
            "graph_trace":  [NODE_TUTORIALS],
            "messages":     [AIMessage(content=output)],
            "error":        None,
        }

    except Exception as exc:
        error_msg = f"Tutorials error: {exc}"
        print(f"[tutorials] {error_msg}")
        return {
            "agent_output": f"❌ {error_msg}",
            "graph_trace":  [NODE_TUTORIALS],
            "messages":     [AIMessage(content=error_msg)],
            "error":        error_msg,
        }
