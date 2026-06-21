"""
General QA Node — handles greetings, off-topic questions, and
anything the router couldn't map to a specialized agent.
"""

from __future__ import annotations

from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_core.messages import AIMessage, HumanMessage

from src.state import AgentState
from src.config import NODE_GENERAL_QA
from src.guidance.agent import get_llm


_SYSTEM_PROMPT = """You are a friendly and knowledgeable AI Career Assistant.
You specialise in career guidance for software engineering and AI professionals.

You can help with:
- Career advice and strategy
- Resume tips (general)
- Job market insights
- Interview mindset and confidence
- Learning path recommendations

If the user asks a highly technical "how to code X" question, gently redirect them:
"For a detailed tutorial on that, try asking me in the Tutorials section!"

If the user asks for resume generation, job search, or a mock interview,
let them know those are available as dedicated features via the sidebar.

Keep your answers concise, warm, and encouraging.

Conversation so far:
{chat_history}

User: {user_message}
Assistant:"""

_prompt = PromptTemplate(
    input_variables=["chat_history", "user_message"],
    template=_SYSTEM_PROMPT,
)


def general_qa_node(state: AgentState) -> dict:
    """
    Friendly general Q&A fallback. Includes recent conversation context
    so responses feel natural and connected.
    """
    task     = state.get("task_input", {})
    messages = state.get("messages", [])

    user_message = task.get("user_message", "")
    if not user_message:
        # Fall back to last human message
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                user_message = msg.content
                break

    # Build short chat history for context
    recent = messages[-6:] if len(messages) > 6 else messages
    chat_history = "\n".join(
        f"{'User' if isinstance(m, HumanMessage) else 'Assistant'}: {m.content}"
        for m in recent
        if hasattr(m, "content")
    )

    try:
        llm   = get_llm("general_qa")
        chain = LLMChain(llm=llm, prompt=_prompt)
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
        print(f"[general_qa_node] {error_msg}")
        return {
            "agent_output": f"❌ {error_msg}",
            "graph_trace":  [NODE_GENERAL_QA],
            "messages":     [AIMessage(content=error_msg)],
            "error":        error_msg,
        }
