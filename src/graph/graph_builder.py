"""
Graph Builder — wires all nodes into a LangGraph StateGraph.

The graph topology:

    [START] → router → {resume_builder, job_search, interview_prep,
                        mock_interview, evaluation, tutorials,
                        general_qa, clarifier} → [END]

Every node returns a partial state update; LangGraph merges it
using the reducers defined on AgentState.

Usage:
    from src.graph.graph_builder import compile_graph, get_graph_mermaid
    from src.graph.checkpointer import get_checkpointer

    checkpointer = get_checkpointer()
    graph = compile_graph(checkpointer)

    config = {"configurable": {"thread_id": "session-abc"}}
    result = graph.invoke(initial_state, config)
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

# ── Import all node functions ─────────────────────────────────────────────────
from src.graph.nodes.router_node        import router_node
from src.graph.nodes.resume_builder_node import resume_builder_node
from src.graph.nodes.job_search_node    import job_search_node
from src.graph.nodes.interview_prep_node import interview_prep_node
from src.graph.nodes.mock_interview_node import mock_interview_node
from src.graph.nodes.evaluation_node    import evaluation_node
from src.graph.nodes.tutorials_node     import tutorials_node
from src.graph.nodes.general_qa_node    import general_qa_node
from src.graph.nodes.clarifier_node     import clarifier_node
from src.graph.nodes.salary_negotiator_node import salary_negotiator_node   # NEW


# ─── Supervisor / conditional edge ───────────────────────────────────────────

def _route_after_router(state: AgentState) -> Literal[
    "resume_builder", "job_search", "interview_prep",
    "mock_interview", "evaluation", "tutorials",
    "general_qa", "clarifier", "salary_negotiator"
]:
    """
    Reads `current_agent` set by router_node and returns the next node name.
    This function is used as the conditional edge from router → specialist.
    """
    destination = state.get("current_agent", NODE_GENERAL_QA)
    valid = {
        NODE_RESUME, NODE_JOB_SEARCH, NODE_INTERVIEW_PREP,
        NODE_MOCK_INTERVIEW, NODE_EVALUATION, NODE_TUTORIALS,
        NODE_GENERAL_QA, NODE_CLARIFIER, NODE_SALARY,
    }
    return destination if destination in valid else NODE_GENERAL_QA


# ─── Graph builder ────────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    """
    Construct the StateGraph (uncompiled).
    Useful for visualisation without requiring a checkpointer.
    """
    builder = StateGraph(AgentState)

    # ── Register all nodes ───────────────────────────────────────────────────
    builder.add_node(NODE_ROUTER,         router_node)
    builder.add_node(NODE_RESUME,         resume_builder_node)
    builder.add_node(NODE_JOB_SEARCH,     job_search_node)
    builder.add_node(NODE_INTERVIEW_PREP, interview_prep_node)
    builder.add_node(NODE_MOCK_INTERVIEW, mock_interview_node)
    builder.add_node(NODE_EVALUATION,     evaluation_node)
    builder.add_node(NODE_TUTORIALS,      tutorials_node)
    builder.add_node(NODE_GENERAL_QA,     general_qa_node)
    builder.add_node(NODE_CLARIFIER,      clarifier_node)
    builder.add_node(NODE_SALARY,         salary_negotiator_node)   # NEW

    # ── Entry edge: START → router ───────────────────────────────────────────
    builder.add_edge(START, NODE_ROUTER)

    # ── Conditional edge: router → one of the specialist nodes ───────────────
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
            NODE_SALARY:         NODE_SALARY,         # NEW
        },
    )

    # ── Terminal edges: all specialist nodes → END ───────────────────────────
    for node in [
        NODE_RESUME, NODE_JOB_SEARCH, NODE_INTERVIEW_PREP,
        NODE_MOCK_INTERVIEW, NODE_EVALUATION, NODE_TUTORIALS,
        NODE_GENERAL_QA, NODE_CLARIFIER, NODE_SALARY,   # NEW
    ]:
        builder.add_edge(node, END)

    return builder


def compile_graph(checkpointer: BaseCheckpointSaver | None = None):
    """
    Compile the StateGraph and optionally attach a checkpointer
    for persistent memory across sessions.

    Args:
        checkpointer: A LangGraph checkpointer (e.g. SqliteSaver).
                      Pass None for an in-memory-only graph.

    Returns:
        Compiled graph (CompiledGraph) ready for .invoke() / .stream()
    """
    builder = build_graph()
    if checkpointer:
        return builder.compile(checkpointer=checkpointer)
    return builder.compile()


def get_graph_mermaid() -> str:
    """
    Return a Mermaid diagram string of the graph topology.
    Used by the Streamlit UI to render the live graph visualisation.
    """
    try:
        graph = compile_graph()   # No checkpointer needed for diagram
        return graph.get_graph().draw_mermaid()
    except Exception as exc:
        # Fallback static diagram if generation fails
        return _FALLBACK_MERMAID


# ─── Fallback Mermaid diagram (static) ───────────────────────────────────────
_FALLBACK_MERMAID = """
graph TD
    START([▶ START]) --> router
    router -->|resume| resume_builder
    router -->|jobs| job_search
    router -->|interview prep| interview_prep
    router -->|mock interview| mock_interview
    router -->|evaluate| evaluation
    router -->|tutorials| tutorials
    router -->|general| general_qa
    router -->|unclear| clarifier
    resume_builder --> END([⏹ END])
    job_search --> END
    interview_prep --> END
    mock_interview --> END
    evaluation --> END
    tutorials --> END
    general_qa --> END
    clarifier --> END

    style START fill:#4ade80,color:#000
    style END fill:#f87171,color:#000
    style router fill:#818cf8,color:#fff
    style resume_builder fill:#38bdf8,color:#000
    style job_search fill:#38bdf8,color:#000
    style interview_prep fill:#38bdf8,color:#000
    style mock_interview fill:#38bdf8,color:#000
    style evaluation fill:#38bdf8,color:#000
    style tutorials fill:#38bdf8,color:#000
    style general_qa fill:#38bdf8,color:#000
    style clarifier fill:#fb923c,color:#000
"""
