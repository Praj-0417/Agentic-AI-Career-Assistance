"""
src/agents/router/node.py
─────────────────────────────────────────────────────────────────────────────
Router Node — classifies user intent and sets `current_agent` in state.

Imports prompts from prompts.py.
Imports LLM from src.core.llm.
Contains only routing logic — zero prompt strings, zero HTTP code.
"""

from __future__ import annotations

from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_core.messages import HumanMessage

from src.state import AgentState
from src.config import (
    NODE_RESUME, NODE_JOB_SEARCH, NODE_INTERVIEW_PREP,
    NODE_MOCK_INTERVIEW, NODE_TUTORIALS, NODE_GENERAL_QA,
    NODE_CLARIFIER, NODE_SALARY,
)
from src.core.llm import get_llm
from .prompts import ROUTING_TEMPLATE


# ── Routing table ─────────────────────────────────────────────────────────────

_ROUTE_MAP: dict[str, str] = {
    "resume_builder":    NODE_RESUME,
    "job_search":        NODE_JOB_SEARCH,
    "interview_prep":    NODE_INTERVIEW_PREP,
    "mock_interview":    NODE_MOCK_INTERVIEW,
    "tutorials":         NODE_TUTORIALS,
    "salary_negotiator": NODE_SALARY,
    "general_qa":        NODE_GENERAL_QA,
    "unclear":           NODE_CLARIFIER,
}

_routing_prompt = PromptTemplate(
    input_variables=["user_message", "user_profile", "recent_conversation"],
    template=ROUTING_TEMPLATE,
)


# ── Node function ──────────────────────────────────────────────────────────────

def router_node(state: AgentState) -> dict:
    """
    1. Check for `force_agent` override — skip LLM if set.
    2. Extract the latest human message.
    3. Run the routing prompt through a fast, zero-temperature LLM.
    4. Map the output to a valid node name.
    5. Return `current_agent` + graph trace.
    """
    task   = state.get("task_input", {}) or {}
    forced = task.get("force_agent")

    # ── Hard-coded routing override (API/UI use) ──────────────────────────
    if forced:
        print(f"[router] force_agent override → {forced}")
        return {
            "current_agent":    forced,
            "graph_trace":      ["router"],
            "needs_clarification": False,
            "task_input":       task,
        }

    # ── Extract last human message ────────────────────────────────────────
    user_message = ""
    for msg in reversed(state.get("messages", [])):
        if isinstance(msg, HumanMessage):
            user_message = msg.content
            break

    if not user_message:
        return {
            "current_agent":    NODE_GENERAL_QA,
            "graph_trace":      ["router"],
            "needs_clarification": False,
        }

    # ── Build short conversation context ──────────────────────────────────
    recent_msgs = state.get("messages", [])[-4:]
    recent_str  = "\n".join(
        f"{'User' if isinstance(m, HumanMessage) else 'Assistant'}: {m.content}"
        for m in recent_msgs
    )

    # ── LLM classification ────────────────────────────────────────────────
    llm    = get_llm("router")
    chain  = LLMChain(llm=llm, prompt=_routing_prompt)
    result = chain.invoke({
        "user_message":       user_message,
        "user_profile":       str(state.get("user_profile", {})),
        "recent_conversation": recent_str,
    })

    raw         = result.get("text", "UNCLEAR").strip().lower().replace(".", "").replace('"', "")
    destination = _ROUTE_MAP.get(raw, NODE_CLARIFIER)

    print(f"[router] '{user_message[:60]}…' → {destination}")

    return {
        "current_agent":    destination,
        "graph_trace":      ["router"],
        "needs_clarification": False,
        "task_input": {
            **task,
            "user_message": user_message,
        },
    }
