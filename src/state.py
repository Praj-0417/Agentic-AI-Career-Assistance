"""
AgentState — the single shared state TypedDict that flows through
every node in the LangGraph StateGraph.

All nodes read from and write to this state object.
LangGraph merges state updates automatically using the `Annotated` reducers.
"""

from __future__ import annotations

from typing import Annotated, Any, Dict, List, Optional
from typing_extensions import TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class UserProfile(TypedDict, total=False):
    """Persistent user profile carried across the entire session."""
    name: str
    job_title: str
    experience: str
    skills: str
    resume_content: str          # Latest generated LaTeX resume


class AgentState(TypedDict):
    """
    Central state object for the AI Career Assistant LangGraph.

    ─── Message History ───────────────────────────────────────────────────
    `messages` uses the `add_messages` reducer, which automatically
    appends new messages rather than replacing the list. This gives
    every node full conversation history.

    ─── Routing ───────────────────────────────────────────────────────────
    `current_agent` is set by the router and read by the supervisor
    edge to decide which node to call next.

    ─── Task Payloads ─────────────────────────────────────────────────────
    `task_input` carries node-specific parameters (job title, resume text,
    search query, etc.) without polluting the top-level state namespace.

    ─── Outputs ───────────────────────────────────────────────────────────
    `agent_output` holds the latest response string from the active node.
    Nodes overwrite this; the UI reads it to display the response.

    ─── Graph Trace ───────────────────────────────────────────────────────
    `graph_trace` is a list of node names visited in order.
    Used by the UI to highlight the active node in the graph visualization.
    Uses `add_graph_trace` reducer to append instead of replace.
    """

    # ── Conversation messages (auto-appended by reducer) ──────────────────
    messages: Annotated[List[BaseMessage], add_messages]

    # ── User profile (persisted across the session) ───────────────────────
    user_profile: UserProfile

    # ── Routing decision set by router_node ──────────────────────────────
    current_agent: str   # e.g. "resume_builder", "job_search", ...

    # ── Payload for the active node ───────────────────────────────────────
    task_input: Dict[str, Any]

    # ── Latest response from the active node ─────────────────────────────
    agent_output: str

    # ── Error if something went wrong ────────────────────────────────────
    error: Optional[str]

    # ── Flag: router couldn't determine intent, needs user clarification ──
    needs_clarification: bool

    # ── Clarification question to ask the user ────────────────────────────
    clarification_question: Optional[str]

    # ── Ordered list of node names visited (auto-appended by reducer) ─────
    graph_trace: Annotated[List[str], lambda a, b: a + b]

    # ── Interview-specific: conversation history for mock interview ────────
    interview_history: List[Dict[str, str]]

    # ── Mode flag: which interview sub-mode is active ─────────────────────
    # Values: "prep" | "mock" | "evaluate"
    interview_mode: str


def make_initial_state() -> AgentState:
    """
    Return a fresh AgentState with safe defaults.
    Call this when starting a brand new session.
    """
    return AgentState(
        messages=[],
        user_profile={},
        current_agent="",
        task_input={},
        agent_output="",
        error=None,
        needs_clarification=False,
        clarification_question=None,
        graph_trace=[],
        interview_history=[],
        interview_mode="prep",
    )
