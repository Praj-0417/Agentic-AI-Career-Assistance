"""
src/schemas/__init__.py
Exports all task-input TypedDicts and re-exports AgentState for convenience.
"""
from .task_inputs import (
    RouterTaskInput,
    ResumeTaskInput,
    JobSearchTaskInput,
    InterviewPrepTaskInput,
    MockInterviewTaskInput,
    EvaluationTaskInput,
    TutorialTaskInput,
    SalaryTaskInput,
    GeneralQATaskInput,
)

__all__ = [
    "RouterTaskInput",
    "ResumeTaskInput",
    "JobSearchTaskInput",
    "InterviewPrepTaskInput",
    "MockInterviewTaskInput",
    "EvaluationTaskInput",
    "TutorialTaskInput",
    "SalaryTaskInput",
    "GeneralQATaskInput",
]
