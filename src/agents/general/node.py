"""
src/agents/general/node.py
─────────────────────────────────────────────────────────────────────────────
General QA + Clarifier Nodes — friendly fallback and intent-clarifier.

Both nodes live here since they share prompt logic and have very similar
responsibilities (both handle low-info / ambiguous situations).

Prompts in prompts.py | LLM from core.llm.
"""

from __future__ import annotations

from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_core.messages import AIMessage, HumanMessage

from src.state import AgentState
from src.config import NODE_GENERAL_QA, NODE_CLARIFIER
from src.core.llm import get_llm
from src.middleware.guardrails import guarded_node
from .prompts import GENERAL_QA_TEMPLATE, CLARIFIER_TEMPLATE


# ── Prompt objects ─────────────────────────────────────────────────────────

_qa_prompt = PromptTemplate(
    input_variables=["chat_history", "user_message"],
    template=GENERAL_QA_TEMPLATE,
)

_clarifier_prompt = PromptTemplate(
    input_variables=["user_message"],
    template=CLARIFIER_TEMPLATE,
)


# ── Helpers ────────────────────────────────────────────────────────────────

def _get_user_message(state: AgentState) -> str:
    """Extract the latest user message from task_input or message history."""
    task = state.get("task_input", {})
    msg  = task.get("user_message", "")
    if msg:
        return msg
    for m in reversed(state.get("messages", [])):
        if isinstance(m, HumanMessage):
            return m.content
    return ""


def _build_chat_history(state: AgentState) -> str:
    """Build a short readable history string for context."""
    recent = state.get("messages", [])[-6:]
    return "\n".join(
        f"{'User' if isinstance(m, HumanMessage) else 'Assistant'}: {m.content}"
        for m in recent
        if hasattr(m, "content")
    )


# ── Node functions ─────────────────────────────────────────────────────────

@guarded_node("general_qa", output_validator="any")
def general_qa_node(state: AgentState) -> dict:
    """
    Friendly general-purpose career Q&A fallback.
    Includes recent conversation context for natural continuity.
    """
    user_message = _get_user_message(state)
    chat_history = _build_chat_history(state)

    try:
        llm   = get_llm("general_qa")
        chain = LLMChain(llm=llm, prompt=_qa_prompt)
        result = chain.invoke({
            "chat_history": chat_history,
            "user_message": user_message,
        })
        output = result.get("text", "").strip()

        return {
            "agent_output": output,
            "graph_trace":  [NODE_GENERAL_QA],
            "messages":     [AIMessage(content=output)],
            "error":        None,
        }

    except Exception as exc:
        error_msg = f"QA error: {exc}"
        print(f"[general_qa] {error_msg}")
        return {
            "agent_output": f"❌ {error_msg}",
            "graph_trace":  [NODE_GENERAL_QA],
            "messages":     [AIMessage(content=error_msg)],
            "error":        error_msg,
        }


@guarded_node("clarifier", output_validator="any")
def clarifier_node(state: AgentState) -> dict:
    """
    Asks a single targeted clarifying question when intent is UNCLEAR.

    If a specialist node already set `clarification_question` in state,
    uses that directly without calling the LLM.
    """
    user_message     = _get_user_message(state)
    preset_question  = state.get("clarification_question", "")

    if preset_question:
        question = preset_question
    else:
        try:
            llm   = get_llm("clarifier")
            chain = LLMChain(llm=llm, prompt=_clarifier_prompt)
            result = chain.invoke({"user_message": user_message})
            question = result.get("text", "").strip()
        except Exception:
            question = (
                "I'm not sure what you need help with. Could you clarify? "
                "I can help with resumes, job search, interview prep, "
                "mock interviews, tutorials, or salary negotiation."
            )

    return {
        "agent_output":           question,
        "needs_clarification":    True,
        "clarification_question": question,
        "graph_trace":            [NODE_CLARIFIER],
        "messages":               [AIMessage(content=question)],
        "error":                  None,
    }
