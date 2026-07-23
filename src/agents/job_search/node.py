"""
src/agents/job_search/node.py
─────────────────────────────────────────────────────────────────────────────
Job Search Node — finds live job postings and formats actionable listings.

Flow: search tool → LLM formatting → structured Markdown response.
Prompts in prompts.py | LLM from core.llm | Search from core.search.
"""

from __future__ import annotations

from langchain.prompts import PromptTemplate
from langchain_core.messages import AIMessage

from src.state import AgentState
from src.config import NODE_JOB_SEARCH
from src.core.llm import get_llm
from src.core.search import get_search_tool
from .prompts import JOB_SEARCH_TEMPLATE


_prompt = PromptTemplate(
    input_variables=["query", "search_results", "job_title", "location", "job_type", "user_context"],
    template=JOB_SEARCH_TEMPLATE,
)


def job_search_node(state: AgentState) -> dict:
    """
    Reads:
      task_input.job_title      — role to search for
      task_input.location       — city / remote / any
      task_input.job_type       — Full-time, Part-time, Remote, etc.
      task_input.user_context   — skills / requirements

    Writes:
      agent_output              — formatted Markdown job listings
    """
    task    = state.get("task_input", {})
    profile = state.get("user_profile", {})

    job_title    = task.get("job_title", "") or task.get("user_message", "")
    location     = task.get("location", "")
    job_type     = task.get("job_type", "Full-time")
    user_context = task.get("user_context", "") or profile.get("skills", "")

    if not job_title:
        return {
            "needs_clarification": True,
            "clarification_question": "What job title are you looking for, and in which location?",
            "current_agent": "clarifier",
            "graph_trace":  [NODE_JOB_SEARCH],
        }

    # ── Live search ───────────────────────────────────────────────────────
    search_query = f"{job_title} jobs {location} {job_type} 2026"
    try:
        tool           = get_search_tool()
        search_results = tool.func(search_query)
    except Exception as exc:
        search_results = f"Search unavailable: {exc}"

    # ── LLM formatting ────────────────────────────────────────────────────
    try:
        llm    = get_llm("job_search")
        output = llm.invoke(_prompt.format(
            query=search_query,
            search_results=search_results,
            job_title=job_title,
            location=location or "Remote / Any",
            job_type=job_type,
            user_context=user_context or "Not specified",
        ))

        return {
            "agent_output": output,
            "graph_trace":  [NODE_JOB_SEARCH],
            "messages":     [AIMessage(content=output)],
            "error":        None,
        }

    except Exception as exc:
        error_msg = f"Job search error: {exc}"
        print(f"[job_search] {error_msg}")
        return {
            "agent_output": f"❌ {error_msg}",
            "graph_trace":  [NODE_JOB_SEARCH],
            "messages":     [AIMessage(content=error_msg)],
            "error":        error_msg,
        }
