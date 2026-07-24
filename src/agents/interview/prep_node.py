"""
src/agents/interview/prep_node.py
Interview Prep Node — generates a role-specific preparation guide.
Prompts in prompts.py | LLM from core.llm | Search from core.search.
"""

from __future__ import annotations

from langchain.prompts import PromptTemplate
from langchain_core.messages import AIMessage

from src.state import AgentState
from src.config import NODE_INTERVIEW_PREP
from src.core.llm import get_llm
from src.core.search import get_search_tool
from .prompts import PREP_TEMPLATE


_prompt = PromptTemplate(
    input_variables=["job_title", "user_name", "user_experience", "user_request", "search_results"],
    template=PREP_TEMPLATE,
)


def interview_prep_node(state: AgentState) -> dict:
    """
    Reads: task_input.{job_title, user_experience, user_name, user_request}
    Writes: agent_output — structured Markdown prep guide
    """
    task    = state.get("task_input", {})
    profile = state.get("user_profile", {})

    job_title       = task.get("job_title", "") or task.get("interview_job_title", "")
    user_experience = task.get("user_experience", "") or profile.get("experience", "")
    user_name       = task.get("user_name", "") or profile.get("name", "Candidate")
    user_request    = task.get("user_request", "") or task.get("user_message", "")

    if not job_title:
        return {
            "needs_clarification": True,
            "clarification_question": "What job title are you interviewing for?",
            "current_agent": "clarifier",
            "graph_trace":  [NODE_INTERVIEW_PREP],
        }

    search_query = f"{job_title} interview questions trends 2026"
    try:
        tool           = get_search_tool()
        search_results = tool.func(search_query)
    except Exception as exc:
        search_results = f"Search unavailable: {exc}"

    try:
        llm    = get_llm("interview_prep")
        output = llm.invoke(_prompt.format(
            job_title=job_title,
            user_name=user_name,
            user_experience=user_experience or "Not specified",
            user_request=user_request or f"Comprehensive interview prep for {job_title}",
            search_results=search_results,
        ))

        return {
            "agent_output": output,
            "graph_trace":  [NODE_INTERVIEW_PREP],
            "messages":     [AIMessage(content=output)],
            "error":        None,
        }

    except Exception as exc:
        error_msg = f"Interview prep error: {exc}"
        print(f"[interview_prep] {error_msg}")
        return {
            "agent_output": f"❌ {error_msg}",
            "graph_trace":  [NODE_INTERVIEW_PREP],
            "messages":     [AIMessage(content=error_msg)],
            "error":        error_msg,
        }
