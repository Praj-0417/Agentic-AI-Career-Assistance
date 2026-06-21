"""
Tutorials Node — generates comprehensive, project-based tutorials on any
technical topic using a direct search and LLM formatting flow.
"""

from __future__ import annotations

from langchain.prompts import PromptTemplate
from langchain_core.messages import AIMessage

from src.state import AgentState
from src.config import NODE_TUTORIALS
from src.guidance.agent import get_llm, get_search_tool


def tutorials_node(state: AgentState) -> dict:
    """
    Generates a beginner-friendly tutorial by running the search tool directly,
    and using a high-quality LLM to format the guide and copy-pasteable code.
    """
    task    = state.get("task_input", {})
    profile = state.get("user_profile", {})

    user_message = task.get("user_message", "") or task.get("tutorial_query", "")
    user_context = task.get("user_context", "") or profile.get("skills", "")

    if not user_message:
        return {
            "needs_clarification": True,
            "clarification_question": "What topic would you like a tutorial on?",
            "current_agent": "clarifier",
            "graph_trace": [NODE_TUTORIALS],
        }

    # Run the search tool directly to fetch technology best practices/guides
    search_query = f"{user_message} tutorial guide beginner"
    search_results = ""
    try:
        tool = get_search_tool()
        search_results = tool.func(search_query)
    except Exception as e:
        search_results = f"Search failed: {e}"

    prompt_template = """You are an expert technical writer and educator. Create the best
beginner-friendly, project-based tutorial on the requested topic.

**Requested Topic:** {user_message}
**User Background / Skills:** {user_context}
**Search Results Context (current best practices and examples):**
{search_results}

**Tutorial Requirements:**
1. **Table of Contents** — detailed with section links.
2. **Introduction** — what they'll build and why it matters.
3. **Prerequisites** — exact install commands included.
4. **Core Concepts** — simple explanations of only what's needed.
5. **Step-by-Step Project Guide** — ALL code fully explained, copy-pasteable.
6. **Running the Project** — exact commands to run the finished code.
7. **Summary** — key learning points.
8. **Further Reading** — 2-3 high-quality links.
9. **Continuation Line** (if topic is broad): `To continue, ask for '[TOPIC] Part 2'.`

Format as clean, organized Markdown. Do not include any triple backticks wrapper around the whole tutorial.

Response:"""

    try:
        llm = get_llm("tutorials")
        prompt = PromptTemplate(
            input_variables=["user_message", "user_context", "search_results"],
            template=prompt_template,
        )
        formatted = prompt.format(
            user_message=user_message,
            user_context=user_context or "Beginner",
            search_results=search_results,
        )
        output = llm.invoke(formatted)

        # Clean up any ReAct formatting if it leaks
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
        print(f"[tutorials_node] {error_msg}")
        return {
            "agent_output": f"❌ {error_msg}",
            "graph_trace":  [NODE_TUTORIALS],
            "messages":     [AIMessage(content=error_msg)],
            "error":        error_msg,
        }

