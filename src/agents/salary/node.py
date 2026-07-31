"""
src/agents/salary/node.py
─────────────────────────────────────────────────────────────────────────────
Salary Negotiator Node — provides personalised, data-driven negotiation coaching.

Flow: search tool (salary benchmarks) → LLM formatting → Markdown playbook.
Prompts in prompts.py | LLM from core.llm | Search from core.search.
"""

from __future__ import annotations

from langchain.prompts import PromptTemplate
from langchain_core.messages import AIMessage

from src.state import AgentState
from src.config import NODE_SALARY
from src.core.llm import get_llm
from src.core.search import get_search_tool
from src.middleware.guardrails import guarded_node
from .prompts import SALARY_TEMPLATE


_prompt = PromptTemplate(
    input_variables=[
        "job_title", "location", "experience",
        "current_offer", "current_salary", "skills",
        "search_results",
    ],
    template=SALARY_TEMPLATE,
)


@guarded_node("salary_negotiator", output_validator="markdown")
def salary_negotiator_node(state: AgentState) -> dict:
    """
    Reads:
      task_input.{job_title, location, experience,
                  current_offer, current_salary, skills}

    Writes:
      agent_output — structured Markdown negotiation playbook
    """
    task    = state.get("task_input", {})
    profile = state.get("user_profile", {})

    job_title      = task.get("job_title", "") or task.get("user_message", "")
    location       = task.get("location", "")
    experience     = task.get("experience", "") or profile.get("experience", "")
    current_offer  = task.get("current_offer", "Not specified")
    current_salary = task.get("current_salary", "Not specified")
    skills         = task.get("skills", "") or profile.get("skills", "")

    if not job_title:
        return {
            "needs_clarification": True,
            "clarification_question": (
                "I'd love to help you negotiate! Please share:\n"
                "1. The job title\n"
                "2. The offer amount (if you have one)\n"
                "3. Your location\n"
                "4. Years of experience"
            ),
            "current_agent": "clarifier",
            "graph_trace":  [NODE_SALARY],
        }

    # ── Live salary benchmarks ────────────────────────────────────────────
    search_query = f"{job_title} salary range {location} levels.fyi glassdoor 2026"
    try:
        tool           = get_search_tool()
        search_results = tool.func(search_query)
    except Exception as exc:
        search_results = f"Search unavailable: {exc}"

    # ── LLM formatting ────────────────────────────────────────────────────
    try:
        llm    = get_llm("salary_negotiator")
        output = llm.invoke(_prompt.format(
            job_title=job_title,
            location=location or "Remote / Not specified",
            experience=experience or "Not specified",
            current_offer=current_offer,
            current_salary=current_salary,
            skills=skills or "Not specified",
            search_results=search_results,
        ))

        return {
            "agent_output": output,
            "graph_trace":  [NODE_SALARY],
            "messages":     [AIMessage(content=output)],
            "error":        None,
        }

    except Exception as exc:
        error_msg = f"Salary negotiator error: {exc}"
        print(f"[salary_negotiator] {error_msg}")
        return {
            "agent_output": f"❌ {error_msg}",
            "graph_trace":  [NODE_SALARY],
            "messages":     [AIMessage(content=error_msg)],
            "error":        error_msg,
        }
