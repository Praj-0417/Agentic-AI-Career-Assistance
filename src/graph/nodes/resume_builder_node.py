"""
Resume Builder Node — generates and refines LaTeX resumes.

Handles two modes automatically:
  1. No previous resume → fresh generation using job description + user details
  2. Existing resume in state → iterative refinement based on user request
"""

from __future__ import annotations

from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_core.messages import AIMessage

from src.state import AgentState
from src.config import NODE_RESUME
from src.guidance.agent import get_llm


# ─── Prompts ──────────────────────────────────────────────────────────────────

_GENERATION_TEMPLATE = """You are an expert LaTeX resume writer. Your task is to generate a complete, professional, ATS-optimised LaTeX resume.

**Job Description (tailor the resume to this):**
{job_description}

**Candidate Details (experience, skills, projects, education):**
{user_details}

**Instructions:**
1. Output ONLY valid, complete LaTeX code — no conversational text, no explanations.
2. Use the standard article class with professional margins.
3. Include sections: Header, Summary, Experience, Education, Skills, Projects.
4. Use \\resumeItem, \\resumeSubheading style custom commands for clean formatting.
5. Quantify achievements wherever possible (percentages, numbers).
6. Keep it to one page unless experience warrants two.
7. Do NOT wrap in markdown code fences — output raw LaTeX only.

**Complete LaTeX Resume:**
"""

_REFINEMENT_TEMPLATE = """You are an expert LaTeX resume editor. Apply the requested changes precisely.

**Current LaTeX Resume:**
{previous_resume}

**Target Job Description (for context):**
{job_description}

**User's Modification Request:**
{user_request}

**Instructions:**
1. Apply ONLY the requested changes.
2. Keep all other sections intact.
3. Ensure the output is a complete, valid LaTeX document.
4. Output ONLY the updated LaTeX code — no explanations, no markdown fences.

**Updated LaTeX Resume:**
"""

_gen_prompt = PromptTemplate(
    input_variables=["job_description", "user_details"],
    template=_GENERATION_TEMPLATE,
)

_refine_prompt = PromptTemplate(
    input_variables=["previous_resume", "job_description", "user_request"],
    template=_REFINEMENT_TEMPLATE,
)


# ─── Node function ────────────────────────────────────────────────────────────

def resume_builder_node(state: AgentState) -> dict:
    """
    Generates or refines a LaTeX resume.

    Reads from state:
      - task_input.job_description
      - task_input.user_details
      - task_input.user_request  (for refinement)
      - user_profile.resume_content  (existing resume if any)

    Writes to state:
      - agent_output   → the LaTeX code
      - user_profile.resume_content → saved for future turns
      - messages       → AIMessage with the result
    """
    task = state.get("task_input", {})
    profile = state.get("user_profile", {})

    job_description = task.get("job_description", "")
    user_details    = task.get("user_details", "") or task.get("resume_user_details", "")
    user_request    = task.get("user_request", "") or task.get("user_message", "")
    existing_resume = task.get("previous_resume", "") or profile.get("resume_content", "")

    llm = get_llm("resume_builder")

    try:
        if existing_resume:
            # ── Refinement mode ─────────────────────────────────────────────
            chain = LLMChain(llm=llm, prompt=_refine_prompt)
            result = chain.invoke({
                "previous_resume": existing_resume,
                "job_description": job_description,
                "user_request": user_request,
            })
            latex_code = result.get("text", "").strip()
            message = "✅ Resume updated! Here's the refined LaTeX code."
        else:
            # ── Fresh generation mode ────────────────────────────────────────
            chain = LLMChain(llm=llm, prompt=_gen_prompt)
            result = chain.invoke({
                "job_description": job_description,
                "user_details": user_details,
            })
            latex_code = result.get("text", "").strip()
            message = "✅ Resume generated! Copy the LaTeX code into Overleaf to compile your PDF."

        # Strip accidental markdown fences
        if latex_code.startswith("```"):
            latex_code = latex_code.split("```", 2)[-1].lstrip("latex").strip()
        if latex_code.endswith("```"):
            latex_code = latex_code[:-3].strip()

        # Update profile
        updated_profile = {**profile, "resume_content": latex_code}

        return {
            "agent_output": f"{message}\n\n```latex\n{latex_code}\n```",
            "user_profile": updated_profile,
            "graph_trace": [NODE_RESUME],
            "messages": [AIMessage(content=message)],
            "error": None,
            "task_input": {**task, "generated_resume": latex_code},
        }

    except Exception as exc:
        error_msg = f"Resume builder error: {exc}"
        print(f"[resume_builder_node] {error_msg}")
        return {
            "agent_output": f"❌ {error_msg}",
            "graph_trace": [NODE_RESUME],
            "messages": [AIMessage(content=error_msg)],
            "error": error_msg,
        }
