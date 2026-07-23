"""
src/agents/resume/node.py
─────────────────────────────────────────────────────────────────────────────
Resume Builder Node — generates or refines a LaTeX resume.

Two modes (selected automatically):
  • Fresh generation  — job_description + user_details → new LaTeX
  • Refinement        — previous_resume + user_request  → updated LaTeX

Prompts live in prompts.py.
LLM obtained from src.core.llm.
"""

from __future__ import annotations

from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_core.messages import AIMessage

from src.state import AgentState
from src.config import NODE_RESUME
from src.core.llm import get_llm
from .prompts import GENERATION_TEMPLATE, REFINEMENT_TEMPLATE


# ── Prompt objects (module-level, reused across calls) ─────────────────────

_gen_prompt = PromptTemplate(
    input_variables=["job_description", "user_details"],
    template=GENERATION_TEMPLATE,
)

_refine_prompt = PromptTemplate(
    input_variables=["previous_resume", "job_description", "user_request"],
    template=REFINEMENT_TEMPLATE,
)


# ── Helpers ────────────────────────────────────────────────────────────────

def _strip_fences(code: str) -> str:
    """Remove accidental markdown code fences from LLM output."""
    if code.startswith("```"):
        code = code.split("```", 2)[-1].lstrip("latex").strip()
    if code.endswith("```"):
        code = code[:-3].strip()
    return code


# ── Node function ──────────────────────────────────────────────────────────

def resume_builder_node(state: AgentState) -> dict:
    """
    Reads:
      task_input.job_description    — target JD
      task_input.user_details       — candidate background
      task_input.previous_resume    — existing LaTeX (refinement mode)
      task_input.user_request       — what to change (refinement mode)

    Writes:
      agent_output                  — LaTeX wrapped in ```latex fence
      user_profile.resume_content   — saved for future refinement turns
      task_input.generated_resume   — raw LaTeX for API callers
    """
    task    = state.get("task_input", {})
    profile = state.get("user_profile", {})

    job_description = task.get("job_description", "")
    user_details    = task.get("user_details", "") or task.get("resume_user_details", "")
    user_request    = task.get("user_request", "") or task.get("user_message", "")
    existing_resume = task.get("previous_resume", "") or profile.get("resume_content", "")

    llm = get_llm("resume_builder")

    try:
        if existing_resume:
            # ── Refinement ─────────────────────────────────────────────────
            chain  = LLMChain(llm=llm, prompt=_refine_prompt)
            result = chain.invoke({
                "previous_resume": existing_resume,
                "job_description": job_description,
                "user_request":    user_request,
            })
            latex_code = _strip_fences(result.get("text", "").strip())
            message    = "✅ Resume updated — here's the refined LaTeX."
        else:
            # ── Fresh generation ───────────────────────────────────────────
            chain  = LLMChain(llm=llm, prompt=_gen_prompt)
            result = chain.invoke({
                "job_description": job_description,
                "user_details":    user_details,
            })
            latex_code = _strip_fences(result.get("text", "").strip())
            message    = "✅ Resume generated — copy the LaTeX into Overleaf to compile your PDF."

        updated_profile = {**profile, "resume_content": latex_code}

        return {
            "agent_output": f"{message}\n\n```latex\n{latex_code}\n```",
            "user_profile": updated_profile,
            "graph_trace":  [NODE_RESUME],
            "messages":     [AIMessage(content=message)],
            "error":        None,
            "task_input":   {**task, "generated_resume": latex_code},
        }

    except Exception as exc:
        error_msg = f"Resume builder error: {exc}"
        print(f"[resume_builder] {error_msg}")
        return {
            "agent_output": f"❌ {error_msg}",
            "graph_trace":  [NODE_RESUME],
            "messages":     [AIMessage(content=error_msg)],
            "error":        error_msg,
        }
