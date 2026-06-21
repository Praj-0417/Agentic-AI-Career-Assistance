"""
Mock Interview Node — conducts a realistic, multi-turn mock interview.

Reads the full interview_history from state and continues the conversation,
asking one question at a time. The history accumulates in state across turns.
"""

from __future__ import annotations

import re
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_core.messages import AIMessage

from src.state import AgentState
from src.config import NODE_MOCK_INTERVIEW
from src.guidance.agent import get_llm


_MOCK_TEMPLATE = """You are an expert technical interviewer at a leading technology company.
Conduct a realistic, professional mock interview for the following candidate.

**Context:**
- Candidate: {user_name}
- Role: {job_title}
- Candidate Experience: {user_experience}

**Interview Guidelines:**
1. If the history is empty, introduce yourself briefly and ask your FIRST question.
2. Ask ONE question per response. Never ask multiple questions at once.
3. Evaluate the candidate's last answer briefly (1 sentence), then ask the next question.
4. Cover: technical skills, behavioral/situational, problem-solving, and culture fit.
5. Adjust difficulty based on answer quality.
6. If the candidate asks about the company/role, give a realistic answer.
7. After 8+ exchanges, offer a closing statement and brief performance note.

**Formatting Rules:**
- Keep responses to 1-3 short paragraphs.
- Do NOT roleplay the candidate's answers.
- Do NOT include meta-instructions or model guidance.
- Respond ONLY as the interviewer, in first person.
- Do NOT predict what the candidate might say.

**Interview History:**
{history}

**Interviewer Response:**"""


def _format_history(history: list) -> str:
    lines = []
    for msg in history:
        role    = msg.get("role", "")
        content = msg.get("content", "")
        if role == "system":
            continue
        label = "Candidate" if role == "user" else "Interviewer"
        lines.append(f"{label}: {content}")
    return "\n\n".join(lines)


def _clean_response(text: str) -> str:
    """Remove leaked meta-instructions and enforce single-question rule."""
    remove_patterns = [
        "Based on the above,",
        "provide your next interview response.",
        "If this is the beginning of the interview,",
        "Candidate:",
        "Interviewer:",
        "**Interviewer Response:**",
    ]
    for pat in remove_patterns:
        text = text.replace(pat, "")

    text = text.strip()

    # Keep only first question if multiple questions slipped through
    sentences = re.split(r"\?\s+(?=[A-Z])", text)
    if len(sentences) > 1:
        for i, sent in enumerate(sentences):
            if "?" in sent:
                text = "".join(sentences[: i + 1])
                if not text.endswith("?"):
                    text += "?"
                break

    return text.strip()


def mock_interview_node(state: AgentState) -> dict:
    """
    Multi-turn mock interview. Reads interview_history from state,
    appends the new interviewer turn, and returns the updated history.
    """
    task    = state.get("task_input", {})
    profile = state.get("user_profile", {})
    history = state.get("interview_history", [])

    job_title       = task.get("job_title", "") or task.get("interview_job_title", "")
    user_experience = task.get("user_experience", "") or profile.get("experience", "")
    user_name       = task.get("user_name", "") or profile.get("name", "Candidate")
    user_answer     = task.get("user_message", "")

    # Append candidate's latest answer to history
    if user_answer and history:  # Only add if interview already started
        history = history + [{"role": "user", "content": user_answer}]

    if not job_title:
        return {
            "needs_clarification": True,
            "clarification_question": "What job title is this mock interview for?",
            "current_agent": "clarifier",
            "graph_trace": [NODE_MOCK_INTERVIEW],
        }

    try:
        llm = get_llm("mock_interview")
        prompt = PromptTemplate(
            input_variables=["job_title", "user_experience", "user_name", "history"],
            template=_MOCK_TEMPLATE,
        )
        chain = LLMChain(llm=llm, prompt=prompt, verbose=True)

        result = chain.invoke({
            "job_title":       job_title,
            "user_experience": user_experience or "Not specified",
            "user_name":       user_name,
            "history":         _format_history(history),
        })

        ai_reply = _clean_response(result.get("text", "").strip())

        # Append interviewer reply to history
        updated_history = history + [{"role": "assistant", "content": ai_reply}]

        return {
            "agent_output":     ai_reply,
            "interview_history": updated_history,
            "graph_trace":      [NODE_MOCK_INTERVIEW],
            "messages":         [AIMessage(content=ai_reply)],
            "error":            None,
        }

    except Exception as exc:
        error_msg = f"Mock interview error: {exc}"
        print(f"[mock_interview_node] {error_msg}")
        return {
            "agent_output": f"❌ {error_msg}",
            "graph_trace":  [NODE_MOCK_INTERVIEW],
            "messages":     [AIMessage(content=error_msg)],
            "error":        error_msg,
        }
