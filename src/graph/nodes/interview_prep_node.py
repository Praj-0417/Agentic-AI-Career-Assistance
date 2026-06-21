"""
Interview Prep Node — generates a comprehensive, role-specific interview
preparation guide using a direct search and LLM formatting flow.
"""

from __future__ import annotations

from langchain.prompts import PromptTemplate
from langchain_core.messages import AIMessage

from src.state import AgentState
from src.config import NODE_INTERVIEW_PREP
from src.guidance.agent import get_llm, get_search_tool


def interview_prep_node(state: AgentState) -> dict:
    """
    Generates a role-specific, personalized preparation guide by running the
    search tool directly and using a high-quality LLM for formatting.
    """
    task    = state.get("task_input", {})
    profile = state.get("user_profile", {})

    job_title      = task.get("job_title", "") or task.get("interview_job_title", "")
    user_experience = task.get("user_experience", "") or profile.get("experience", "")
    user_name      = task.get("user_name", "") or profile.get("name", "Candidate")
    user_request   = task.get("user_request", "") or task.get("user_message", "")

    if not job_title:
        return {
            "needs_clarification": True,
            "clarification_question": "What job title are you interviewing for?",
            "current_agent": "clarifier",
            "graph_trace": [NODE_INTERVIEW_PREP],
        }

    # Run the search tool directly to fetch current interview trends/questions
    search_query = f"{job_title} interview questions and trends 2026"
    search_results = ""
    try:
        tool = get_search_tool()
        search_results = tool.func(search_query)
    except Exception as e:
        search_results = f"Search failed: {e}"

    prompt_template = """You are an expert interview coach. Create a comprehensive, up-to-date
interview preparation guide based on the target job title and candidate's experience.

**Target Role:** {job_title}
**Candidate Name:** {user_name}
**Experience Level:** {user_experience}
**Additional Request:** {user_request}
**Search Results Context (current questions and trends):**
{search_results}

**Guide Requirements:**
1. **Role Overview** — Responsibilities, required skills, current market trends.
2. **Behavioral Questions (10-15)** — STAR method examples for each.
3. **Technical Questions (10-15)** — Role-specific, with difficulty levels.
4. **Mock Scenario** — One realistic case study or problem-solving exercise.
5. **Salary Negotiation Tips** — Current market ranges for the role.
6. **Questions to Ask the Interviewer** — 5 smart questions.

Format as clean, organized Markdown.

Response:"""

    try:
        llm = get_llm("interview_prep")
        prompt = PromptTemplate(
            input_variables=["job_title", "user_name", "user_experience", "user_request", "search_results"],
            template=prompt_template,
        )
        formatted = prompt.format(
            job_title=job_title,
            user_name=user_name,
            user_experience=user_experience or "Not specified",
            user_request=user_request or f"Comprehensive interview prep for {job_title}",
            search_results=search_results,
        )
        output = llm.invoke(formatted)

        return {
            "agent_output": output,
            "graph_trace": [NODE_INTERVIEW_PREP],
            "messages": [AIMessage(content=output)],
            "error": None,
        }

    except Exception as exc:
        error_msg = f"Interview prep error: {exc}"
        print(f"[interview_prep_node] {error_msg}")
        return {
            "agent_output": f"❌ {error_msg}",
            "graph_trace": [NODE_INTERVIEW_PREP],
            "messages": [AIMessage(content=error_msg)],
            "error": error_msg,
        }

