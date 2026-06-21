"""
Clarifier Node — handles ambiguous intent by asking the user a
targeted follow-up question.

When the router cannot determine intent (UNCLEAR), or when a specialized
node detects missing required information (e.g., no job title), the graph
routes here.  The clarifier sets `needs_clarification = True` and returns
a question for the UI to display.  On the next user turn, the router re-
classifies with the additional context.
"""

from __future__ import annotations

from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_core.messages import AIMessage, HumanMessage

from src.state import AgentState
from src.config import NODE_CLARIFIER
from src.guidance.agent import get_llm


_CLARIFIER_TEMPLATE = """You are a helpful AI Career Assistant.
The user sent a message that wasn't clear enough to route to the right feature.

Their message: "{user_message}"

Ask ONE short, friendly clarifying question to understand what they need.
The available features are:
- Resume Builder (create or improve a resume)
- Job Search (find open positions)
- Interview Prep (preparation guide for a role)
- Mock Interview (practice interview session)
- Tutorials (learn a technical topic step by step)
- General Career Q&A

Your clarifying question:"""


def clarifier_node(state: AgentState) -> dict:
    """
    Generates a targeted clarifying question based on the ambiguous message.
    Sets needs_clarification = True so the UI knows to show the question
    instead of a regular assistant response.
    """
    task     = state.get("task_input", {})
    messages = state.get("messages", [])

    user_message = task.get("user_message", "")
    if not user_message:
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                user_message = msg.content
                break

    # Use pre-set clarification question if a node already generated one
    preset_question = state.get("clarification_question", "")
    if preset_question:
        question = preset_question
    else:
        try:
            llm = get_llm("clarifier")
            prompt = PromptTemplate(
                input_variables=["user_message"],
                template=_CLARIFIER_TEMPLATE,
            )
            chain  = LLMChain(llm=llm, prompt=prompt)
            result = chain.invoke({"user_message": user_message})
            question = result.get("text", "").strip()
        except Exception as exc:
            question = (
                "I'm not sure what you need help with. Could you clarify? "
                "I can help with resumes, job search, interview prep, mock interviews, or tutorials."
            )

    return {
        "agent_output":          question,
        "needs_clarification":   True,
        "clarification_question": question,
        "graph_trace":           [NODE_CLARIFIER],
        "messages":              [AIMessage(content=question)],
        "error":                 None,
    }
