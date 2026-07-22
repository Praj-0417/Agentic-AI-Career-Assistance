"""
src/schemas/task_inputs.py
─────────────────────────────────────────────────────────────────────────────
Typed task-input schemas — one TypedDict per agent.

WHY THIS EXISTS:
  Previously `task_input` was `Dict[str, Any]`, which meant:
  - Any node could accidentally read any key left by a prior node
  - No IDE autocompletion, no runtime validation
  - The tutorial bug (reading resume_content) was caused by this

USAGE:
  Each node imports its own TypedDict and uses it to document which keys
  it reads. The node function still receives `state["task_input"]` as a
  plain dict (LangGraph doesn't enforce types at runtime), but having the
  TypedDict makes intent clear and enables static analysis.

  Example:
      task: ResumeTaskInput = state.get("task_input", {})  # type: ignore[assignment]
      job_desc = task.get("job_description", "")

ROUTING OVERRIDE:
  `force_agent` is the only key that ALL TypedDicts share. It is read
  exclusively by `router_node` and stripped before the task reaches a
  specialist node.
"""

from __future__ import annotations
from typing import Optional
from typing_extensions import TypedDict


# ─── Shared override key (router only) ──────────────────────────────────────

class _BaseTaskInput(TypedDict, total=False):
    """Keys shared across all task inputs."""
    force_agent: str          # Router override: skip LLM classification
    user_message: str         # Raw user message (always injected by router)


# ─── Per-agent typed schemas ─────────────────────────────────────────────────

class RouterTaskInput(_BaseTaskInput, total=False):
    """Keys the router reads from state."""
    # Router only reads `force_agent` and `user_message`
    pass


class ResumeTaskInput(_BaseTaskInput, total=False):
    """Keys the resume_builder node reads."""
    job_description: str      # Target job description to tailor resume
    user_details: str         # Candidate background (free-text)
    previous_resume: str      # Existing LaTeX for refinement mode
    user_request: str         # Specific refinement instruction
    # NOTE: this schema intentionally OMITS resume_content to prevent
    # the state-bleed bug where tutorial read the resume.


class JobSearchTaskInput(_BaseTaskInput, total=False):
    """Keys the job_search node reads."""
    job_title: str
    location: str
    job_type: str             # "Full-time" | "Part-time" | "Remote" | etc.
    user_context: str         # Additional requirements or skills


class InterviewPrepTaskInput(_BaseTaskInput, total=False):
    """Keys the interview_prep node reads."""
    job_title: str
    user_experience: str      # e.g. "5 years", "Senior"
    user_name: str
    user_request: str         # Specific focus area (optional)


class MockInterviewTaskInput(_BaseTaskInput, total=False):
    """Keys the mock_interview node reads."""
    job_title: str
    user_experience: str
    user_name: str
    # Note: interview_history lives on AgentState directly, not task_input


class EvaluationTaskInput(_BaseTaskInput, total=False):
    """Keys the evaluation node reads."""
    job_title: str
    user_experience: str
    user_name: str
    interview_transcript: str  # Raw transcript if evaluating a pasted session


class TutorialTaskInput(_BaseTaskInput, total=False):
    """
    Keys the tutorials node reads.

    CRITICAL: `resume_content` is intentionally NOT here.
    The tutorial node must never read resume_content from user_profile
    or any task_input key. Only these two keys are valid:
    """
    tutorial_query: str       # What topic to explain / build
    user_context: str         # Background level (e.g. "Beginner Python dev")
    background: str           # Alias for user_context


class SalaryTaskInput(_BaseTaskInput, total=False):
    """Keys the salary_negotiator node reads."""
    job_title: str
    location: str
    experience: str
    current_offer: str
    current_salary: str
    skills: str


class GeneralQATaskInput(_BaseTaskInput, total=False):
    """Keys the general_qa and clarifier nodes read."""
    # Only reads user_message (from base)
    pass
