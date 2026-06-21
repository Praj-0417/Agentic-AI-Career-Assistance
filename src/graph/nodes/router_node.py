"""
Router Node — the entry point of every user turn.

Classifies the user's latest message into a destination node name
using a fast, zero-temperature LLM call.  Returns a LangGraph
`Command` that tells the graph which node to visit next.
"""

from __future__ import annotations

from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_core.messages import HumanMessage

from src.state import AgentState
from src.config import (
    NODE_RESUME, NODE_JOB_SEARCH, NODE_INTERVIEW_PREP,
    NODE_MOCK_INTERVIEW, NODE_TUTORIALS, NODE_GENERAL_QA,
    NODE_CLARIFIER, NODE_SALARY, VALID_ROUTES,
)
from src.guidance.agent import get_llm


# ─── Routing prompt ──────────────────────────────────────────────────────────

_ROUTING_TEMPLATE = """You are a task classifier. Analyze the user's latest message and categorize it into exactly one category.

**Latest Message to Classify:**
"{user_message}"

**Valid Categories:**
- resume_builder     : Creating, editing, or reviewing resumes/CVs
- job_search         : Finding jobs, career advice, or application guidance
- interview_prep     : General interview advice, tips, or preparation guides
- mock_interview     : Starting or continuing a mock/practice interview session
- tutorials          : Learning materials, skill guides, or how-to tutorials
- salary_negotiator  : Salary negotiation, offer evaluation, counter-offers, compensation advice
- general_qa         : Greetings or general questions that don't fit other categories
- UNCLEAR            : Intent cannot be determined from the message

**Context (use only if the latest message is ambiguous):**
Prior Messages: {recent_conversation}
User Info: {user_profile}

**Classification Rules:**
1. Focus primarily on the latest message.
2. "resume", "CV", "portfolio" → resume_builder
3. "job", "internship", "hiring", "apply" → job_search
4. "mock interview", "practice interview", "simulate interview" → mock_interview
5. "interview tips", "prepare for interview", "common questions" → interview_prep
6. "tutorial", "learn", "how do I", "guide", "explain" → tutorials
7. "salary", "negotiate", "offer", "compensation", "counter offer", "raise", "pay" → salary_negotiator
8. Pure greetings or off-topic questions → general_qa
9. Anything else → UNCLEAR

Return ONLY one of these exact strings (no punctuation, no explanation):
resume_builder | job_search | interview_prep | mock_interview | tutorials | salary_negotiator | general_qa | UNCLEAR
"""

_routing_prompt = PromptTemplate(
    input_variables=["user_message", "user_profile", "recent_conversation"],
    template=_ROUTING_TEMPLATE,
)

# ─── Node function ────────────────────────────────────────────────────────────

def router_node(state: AgentState) -> dict:
    """
    Reads the latest human message, classifies intent, and sets
    `current_agent` in the state so the supervisor edge can route
    to the correct next node.
    """
    # Pull the last human message
    user_message = ""
    for msg in reversed(state.get("messages", [])):
        if isinstance(msg, HumanMessage):
            user_message = msg.content
            break

    if not user_message:
        return {
            "current_agent": NODE_GENERAL_QA,
            "graph_trace": ["router"],
            "needs_clarification": False,
        }

    # Build recent conversation context (last 4 messages)
    recent_msgs = state.get("messages", [])[-4:]
    recent_str = "\n".join(
        f"{'User' if isinstance(m, HumanMessage) else 'Assistant'}: {m.content}"
        for m in recent_msgs
    )

    # Run the routing chain
    llm = get_llm("router")
    chain = LLMChain(llm=llm, prompt=_routing_prompt)
    result = chain.invoke({
        "user_message": user_message,
        "user_profile": str(state.get("user_profile", {})),
        "recent_conversation": recent_str,
    })

    raw = result.get("text", "UNCLEAR").strip().lower().replace(".", "").replace("\"", "")

    # Normalize to a valid node name
    valid_node_names = {
        "resume_builder":    NODE_RESUME,
        "job_search":        NODE_JOB_SEARCH,
        "interview_prep":    NODE_INTERVIEW_PREP,
        "mock_interview":    NODE_MOCK_INTERVIEW,
        "tutorials":         NODE_TUTORIALS,
        "salary_negotiator": NODE_SALARY,
        "general_qa":        NODE_GENERAL_QA,
        "unclear":           NODE_CLARIFIER,
    }
    destination = valid_node_names.get(raw, NODE_CLARIFIER)

    print(f"[router] '{user_message[:60]}...' -> {destination}")

    return {
        "current_agent": destination,
        "graph_trace": ["router"],
        "needs_clarification": False,
        "task_input": {
            **state.get("task_input", {}),
            "user_message": user_message,
        },
    }
