"""
Job Search Node — finds live job postings using a direct search and LLM formatting flow.
"""

from __future__ import annotations

from langchain.prompts import PromptTemplate
from langchain_core.messages import AIMessage

from src.state import AgentState
from src.config import NODE_JOB_SEARCH
from src.guidance.agent import get_llm, get_search_tool


def job_search_node(state: AgentState) -> dict:
    """
    Finds job postings by calling the search tool directly, and uses
    a high-quality LLM to format the response as structured Markdown.
    """
    task    = state.get("task_input", {})
    profile = state.get("user_profile", {})

    job_title   = task.get("job_title", "")
    location    = task.get("location", "")
    job_type    = task.get("job_type", "Full-time")
    user_context = task.get("user_context", profile.get("skills", ""))
    user_message = task.get("user_message", "")

    # If job_title not provided, ask for clarification
    if not job_title and not user_message:
        return {
            "needs_clarification": True,
            "clarification_question": "What job title are you looking for, and in which location?",
            "current_agent": "clarifier",
            "graph_trace": [NODE_JOB_SEARCH],
        }

    # Use user_message as fallback query if specific fields not set
    if not job_title:
        job_title = user_message

    # Run the search tool directly to fetch job postings
    search_query = f"{job_title} jobs {location} {job_type} 2026"
    search_results = ""
    try:
        tool = get_search_tool()
        search_results = tool.func(search_query)
    except Exception as e:
        search_results = f"Search failed: {e}"

    prompt_template = """You are an expert career advisor and job search strategist.
Your mission is to provide detailed, actionable, and personalized job search intelligence.

**Search Query:** {query}
**Search Results Context:**
{search_results}

**User Context:**
- Role: {job_title}
- Location: {location}
- Type: {job_type}
- User Profile: {user_context}

**Instructions for Response:**
1. List 3-5 specific, currently open positions with: company, title, location, direct application link, and why it matches the user. If links are not in search results, provide the main job boards (LinkedIn, Indeed) or company career page.
2. Include hiring season info for this role/industry.
3. Include 2-3 alternative strategies (networking, OSS, events).
4. Format as clean, organized Markdown.

Response:"""

    try:
        llm = get_llm("job_search")
        prompt = PromptTemplate(
            input_variables=["query", "search_results", "job_title", "location", "job_type", "user_context"],
            template=prompt_template,
        )
        formatted = prompt.format(
            query=search_query,
            search_results=search_results,
            job_title=job_title,
            location=location or "Remote / Any",
            job_type=job_type,
            user_context=user_context or "Not specified",
        )
        output = llm.invoke(formatted)

        return {
            "agent_output": output,
            "graph_trace": [NODE_JOB_SEARCH],
            "messages": [AIMessage(content=output)],
            "error": None,
        }

    except Exception as exc:
        error_msg = f"Job search error: {exc}"
        print(f"[job_search_node] {error_msg}")
        return {
            "agent_output": f"❌ {error_msg}",
            "graph_trace": [NODE_JOB_SEARCH],
            "messages": [AIMessage(content=error_msg)],
            "error": error_msg,
        }

