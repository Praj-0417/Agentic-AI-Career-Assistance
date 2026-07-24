"""
src/agents/interview/mock_node.py
Mock Interview Node — conducts a realistic multi-turn mock interview.
Prompts in prompts.py | LLM from core.llm.
"""

from __future__ import annotations

import re

from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_core.messages import AIMessage

from src.state import AgentState
from src.config import NODE_MOCK_INTERVIEW
from src.core.llm import get_llm
from .prompts import MOCK_TEMPLATE


_prompt = PromptTemplate(
    input_variables=["job_title", "user_experience", "user_name", "history"],
    template=MOCK_TEMPLATE,
)


# ── Helpers ────────────────────────────────────────────────────────────────

def _format_history(history: list[dict]) -> str:
    """Convert interview history list to readable string for prompt."""
    lines = []
    for msg in history:
        role    = msg.get("role", "")
        content = msg.get("content", "")
        if role == "system":
            continue
        label = "Candidate" if role == "user" else "Interviewer"
        lines.append(f"{label}: {content}")
    return "\n\n".join(lines)


def _enforce_single_question(text: str) -> str:
    """
    Remove meta-instruction leakage and enforce single-question rule.
    Keeps only up to the first complete question if multiple slipped through.
    """
    _NOISE = [
        "Based on the above,",
        "provide your next interview response.",
        "If this is the beginning of the interview,",
        "Candidate:",
        "Interviewer:",
        "**Interviewer Response:**",
    ]
    for noise in _NOISE:
        text = text.replace(noise, "")

    text = text.strip()

    # Keep only first question-ending sentence if there are multiple
    sentences = re.split(r"\?\s+(?=[A-Z])", text)
    if len(sentences) > 1:
        for i, sent in enumerate(sentences):
            if "?" in sent:
                text = "".join(sentences[: i + 1])
                if not text.endswith("?"):
                    text += "?"
                break

    return text.strip()


# ── Node function ──────────────────────────────────────────────────────────

def mock_interview_node(state: AgentState) -> dict:
    """
    Reads:
      interview_history           — full conversation so far
      task_input.{job_title, user_experience, user_name, user_message}

    Writes:
      agent_output                — interviewer's next turn
      interview_history           — updated with new interviewer message
    """
    task    = state.get("task_input", {})
    profile = state.get("user_profile", {})
    history = list(state.get("interview_history", []))

    job_title       = task.get("job_title", "") or task.get("interview_job_title", "")
    user_experience = task.get("user_experience", "") or profile.get("experience", "")
    user_name       = task.get("user_name", "") or profile.get("name", "Candidate")
    user_answer     = task.get("user_message", "")

    # Append candidate's latest answer before generating next question
    if user_answer and history:
        history = history + [{"role": "user", "content": user_answer}]

    if not job_title:
        return {
            "needs_clarification": True,
            "clarification_question": "What job title is this mock interview for?",
            "current_agent": "clarifier",
            "graph_trace":  [NODE_MOCK_INTERVIEW],
        }

    try:
        llm   = get_llm("mock_interview")
        chain = LLMChain(llm=llm, prompt=_prompt)
        result = chain.invoke({
            "job_title":       job_title,
            "user_experience": user_experience or "Not specified",
            "user_name":       user_name,
            "history":         _format_history(history),
        })

        ai_reply        = _enforce_single_question(result.get("text", "").strip())
        updated_history = history + [{"role": "assistant", "content": ai_reply}]

        return {
            "agent_output":      ai_reply,
            "interview_history": updated_history,
            "graph_trace":       [NODE_MOCK_INTERVIEW],
            "messages":          [AIMessage(content=ai_reply)],
            "error":             None,
        }

    except Exception as exc:
        error_msg = f"Mock interview error: {exc}"
        print(f"[mock_interview] {error_msg}")
        return {
            "agent_output": f"❌ {error_msg}",
            "graph_trace":  [NODE_MOCK_INTERVIEW],
            "messages":     [AIMessage(content=error_msg)],
            "error":        error_msg,
        }
