"""
Evaluation Node — evaluates a completed mock interview and produces a
structured scorecard with numerical scores and actionable advice.
"""

from __future__ import annotations

from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_core.messages import AIMessage

from src.state import AgentState
from src.config import NODE_EVALUATION
from src.guidance.agent import get_llm


_EVALUATION_TEMPLATE = """You are an expert interview evaluator and coach.
Evaluate the completed mock interview transcript below and provide a detailed,
constructive scorecard.

**Candidate Information:**
- Name: {user_name}
- Target Role: {job_title}
- Experience Level: {user_experience}

**Interview Transcript:**
{history}

**Evaluation Report (use Markdown):**

## 📊 Performance Scorecard

Score each area 1–10 with specific examples from the transcript and actionable advice.

### 1. Technical Knowledge (X/10)
- Score justification with transcript examples
- Improvement advice

### 2. Communication Skills (X/10)
- Score justification
- Improvement advice

### 3. Problem-Solving Approach (X/10)
- Score justification
- Improvement advice

### 4. Behavioral & Soft Skills (X/10)
- Score justification
- Improvement advice

### 5. Overall Impression (X/10)
- Holistic assessment

## 🏆 Overall Assessment
- **Total Score:** X/50
- **Strengths:** (bullet list)
- **Key Improvement Areas:** (bullet list)
- **Would likely pass this round?** Yes / No / Maybe — with brief rationale
- **Next Steps:** (specific, actionable prep recommendations)

Be honest but constructive. Your goal is to help the candidate grow.
"""


def _format_history(history: list) -> str:
    lines = []
    for msg in history:
        role    = msg.get("role", "")
        content = msg.get("content", "")
        if role == "system":
            continue
        label = "Candidate" if role == "user" else "Interviewer"
        lines.append(f"**{label}:** {content}")
    return "\n\n".join(lines)


def evaluation_node(state: AgentState) -> dict:
    """
    Evaluates the completed mock interview stored in interview_history.
    Returns a structured Markdown scorecard.
    """
    task    = state.get("task_input", {})
    profile = state.get("user_profile", {})
    history = state.get("interview_history", [])

    job_title       = task.get("job_title", "") or task.get("interview_job_title", "")
    user_experience = task.get("user_experience", "") or profile.get("experience", "")
    user_name       = task.get("user_name", "") or profile.get("name", "Candidate")

    # Also accept a raw transcript from task_input
    raw_transcript  = task.get("interview_transcript", "")

    formatted = raw_transcript if raw_transcript else _format_history(history)

    if not formatted:
        return {
            "agent_output": "❌ No interview transcript found to evaluate.",
            "graph_trace":  [NODE_EVALUATION],
            "messages":     [AIMessage(content="No transcript to evaluate.")],
            "error":        "No transcript",
        }

    try:
        llm = get_llm("evaluation")
        prompt = PromptTemplate(
            input_variables=["job_title", "user_experience", "user_name", "history"],
            template=_EVALUATION_TEMPLATE,
        )
        chain = LLMChain(llm=llm, prompt=prompt, verbose=True)

        result = chain.invoke({
            "job_title":       job_title or "Not specified",
            "user_experience": user_experience or "Not specified",
            "user_name":       user_name,
            "history":         formatted,
        })

        output = result.get("text", "").strip()

        return {
            "agent_output": output,
            "graph_trace":  [NODE_EVALUATION],
            "messages":     [AIMessage(content=output)],
            "error":        None,
        }

    except Exception as exc:
        error_msg = f"Evaluation error: {exc}"
        print(f"[evaluation_node] {error_msg}")
        return {
            "agent_output": f"❌ {error_msg}",
            "graph_trace":  [NODE_EVALUATION],
            "messages":     [AIMessage(content=error_msg)],
            "error":        error_msg,
        }
