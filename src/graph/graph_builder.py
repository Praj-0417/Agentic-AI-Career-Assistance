"""
src/graph/graph_builder.py
─────────────────────────────────────────────────────────────────────────────
Graph Builder — wires all agent nodes into a LangGraph StateGraph.

Topology:
    [START] → router → {resume, job_search, interview_prep, mock_interview,
                        evaluation, tutorials, general_qa, clarifier,
                        salary_negotiator} → [END]

All node functions are imported from src/agents/<agent>/ packages.
All node name constants come from src/config.py.

Usage:
    from src.graph.graph_builder import compile_graph
    from src.graph.checkpointer import get_checkpointer

    graph = compile_graph(get_checkpointer())
    result = graph.invoke(state, {"configurable": {"thread_id": "abc"}})
"""

from __future__ import annotations

from typing import Literal

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.base import BaseCheckpointSaver

from src.state import AgentState
from src.config import (
    NODE_ROUTER, NODE_RESUME, NODE_JOB_SEARCH,
    NODE_INTERVIEW_PREP, NODE_MOCK_INTERVIEW, NODE_EVALUATION,
    NODE_TUTORIALS, NODE_GENERAL_QA, NODE_CLARIFIER, NODE_SALARY,
)

# ── Import from new agents/ package structure ─────────────────────────────────
from src.agents.router      import router_node
from src.agents.resume      import resume_builder_node
from src.agents.job_search  import job_search_node
from src.agents.interview   import interview_prep_node, mock_interview_node, evaluation_node
from src.agents.tutorials   import tutorials_node
from src.agents.salary      import salary_negotiator_node
from src.agents.general     import general_qa_node, clarifier_node


# ─── Conditional edge: router → specialist ────────────────────────────────────

_VALID_DESTINATIONS = {
    NODE_RESUME, NODE_JOB_SEARCH, NODE_INTERVIEW_PREP,
    NODE_MOCK_INTERVIEW, NODE_EVALUATION, NODE_TUTORIALS,
    NODE_GENERAL_QA, NODE_CLARIFIER, NODE_SALARY,
}


def _route_after_router(state: AgentState) -> Literal[
    "resume_builder", "job_search", "interview_prep",
    "mock_interview", "evaluation", "tutorials",
    "general_qa", "clarifier", "salary_negotiator"
]:
    """
    Reads `current_agent` set by router_node.
    Falls back to `general_qa` if the value is unrecognised.
    """
    destination = state.get("current_agent", NODE_GENERAL_QA)
    return destination if destination in _VALID_DESTINATIONS else NODE_GENERAL_QA


# ─── Graph construction ───────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    """Construct the StateGraph (uncompiled). Safe to call without a checkpointer."""
    builder = StateGraph(AgentState)

    # Register nodes
    builder.add_node(NODE_ROUTER,         router_node)
    builder.add_node(NODE_RESUME,         resume_builder_node)
    builder.add_node(NODE_JOB_SEARCH,     job_search_node)
    builder.add_node(NODE_INTERVIEW_PREP, interview_prep_node)
    builder.add_node(NODE_MOCK_INTERVIEW, mock_interview_node)
    builder.add_node(NODE_EVALUATION,     evaluation_node)
    builder.add_node(NODE_TUTORIALS,      tutorials_node)
    builder.add_node(NODE_GENERAL_QA,     general_qa_node)
    builder.add_node(NODE_CLARIFIER,      clarifier_node)
    builder.add_node(NODE_SALARY,         salary_negotiator_node)

    # Entry
    builder.add_edge(START, NODE_ROUTER)

    # Conditional routing
    builder.add_conditional_edges(
        NODE_ROUTER,
        _route_after_router,
        {
            NODE_RESUME:         NODE_RESUME,
            NODE_JOB_SEARCH:     NODE_JOB_SEARCH,
            NODE_INTERVIEW_PREP: NODE_INTERVIEW_PREP,
            NODE_MOCK_INTERVIEW: NODE_MOCK_INTERVIEW,
            NODE_EVALUATION:     NODE_EVALUATION,
            NODE_TUTORIALS:      NODE_TUTORIALS,
            NODE_GENERAL_QA:     NODE_GENERAL_QA,
            NODE_CLARIFIER:      NODE_CLARIFIER,
            NODE_SALARY:         NODE_SALARY,
        },
    )

    # All specialist nodes → END
    for node in _VALID_DESTINATIONS:
        builder.add_edge(node, END)

    return builder


def compile_graph(checkpointer: BaseCheckpointSaver | None = None):
    """
    Compile the StateGraph and optionally attach a checkpointer.

    Args:
        checkpointer: SqliteSaver or any LangGraph-compatible checkpointer.
                      Pass None for an in-memory-only (no persistence) graph.

    Returns:
        Compiled CompiledGraph ready for .invoke() / .stream()
    """
    builder = build_graph()
    if checkpointer:
        return builder.compile(checkpointer=checkpointer)
    return builder.compile()


def get_graph_mermaid() -> str:
    """Return a Mermaid diagram string of the current graph topology."""
    try:
        return compile_graph().get_graph().draw_mermaid()
    except Exception:
        return _FALLBACK_MERMAID


# ─── Fallback diagram ─────────────────────────────────────────────────────────
_FALLBACK_MERMAID = """
graph TD
    START([▶ START]) --> router
    router -->|resume| resume_builder
    router -->|jobs| job_search
    router -->|prep| interview_prep
    router -->|mock| mock_interview
    router -->|evaluate| evaluation
    router -->|learn| tutorials
    router -->|general| general_qa
    router -->|unclear| clarifier
    router -->|salary| salary_negotiator
    resume_builder --> END([⏹ END])
    job_search --> END
    interview_prep --> END
    mock_interview --> END
    evaluation --> END
    tutorials --> END
    general_qa --> END
    clarifier --> END
    salary_negotiator --> END

    style START fill:#4ade80,color:#000
    style END fill:#f87171,color:#000
    style router fill:#818cf8,color:#fff
"""
