"""
src/agents/interview/eval_node.py
Evaluation Node — produces a structured scorecard for a completed mock interview.
Prompts in prompts.py | LLM from core.llm.
"""

from __future__ import annotations

from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_core.messages import AIMessage

from src.state import AgentState
from src.config import NODE_EVALUATION
from src.core.llm import get_llm
from .prompts import EVALUATION_TEMPLATE


_prompt = PromptTemplate(
    input_variables=["job_title", "user_experience", "user_name", "history"],
    template=EVALUATION_TEMPLATE,
)


def _format_history(history: list[dict]) -> str:
    """Format interview history for the evaluation prompt."""
    lines = []
    for msg in history:
        role    = msg.get("role", "")
        content = msg.get("content", "")
        if role == "system":
            continue
        label = "Candidate" if role == "user" else "Interviewer"
        lines.append(f"**{label}:** {content}")
    return "\n\n".join(lines)


def evaluation_node(state: AgentState) -> dict:
    """
    Reads:
      interview_history                — session to evaluate
      task_input.interview_transcript  — raw pasted transcript (optional)
      task_input.{job_title, user_experience, user_name}

    Writes:
      agent_output                     — Markdown scorecard
    """
    task    = state.get("task_input", {})
    profile = state.get("user_profile", {})
    history = state.get("interview_history", [])

    job_title       = task.get("job_title", "") or task.get("interview_job_title", "")
    user_experience = task.get("user_experience", "") or profile.get("experience", "")
    user_name       = task.get("user_name", "") or profile.get("name", "Candidate")
    raw_transcript  = task.get("interview_transcript", "")

    formatted = raw_transcript if raw_transcript else _format_history(history)

    if not formatted:
        return {
            "agent_output": "❌ No interview transcript found to evaluate.",
            "graph_trace":  [NODE_EVALUATION],
            "messages":     [AIMessage(content="No transcript to evaluate.")],
            "error":        "No transcript",
        }

    try:
        llm   = get_llm("evaluation")
        chain = LLMChain(llm=llm, prompt=_prompt)
        result = chain.invoke({
            "job_title":       job_title or "Not specified",
            "user_experience": user_experience or "Not specified",
            "user_name":       user_name,
            "history":         formatted,
        })

        output = result.get("text", "").strip()

        return {
            "agent_output": output,
            "graph_trace":  [NODE_EVALUATION],
            "messages":     [AIMessage(content=output)],
            "error":        None,
        }

    except Exception as exc:
        error_msg = f"Evaluation error: {exc}"
        print(f"[evaluation] {error_msg}")
        return {
            "agent_output": f"❌ {error_msg}",
            "graph_trace":  [NODE_EVALUATION],
            "messages":     [AIMessage(content=error_msg)],
            "error":        error_msg,
        }
