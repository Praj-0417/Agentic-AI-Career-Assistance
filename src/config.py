"""
Centralized configuration for the AI Career Assistant.
Swap models here without touching any agent logic.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ─── API Keys ───────────────────────────────────────────────────────────────
TOGETHER_API_KEY: str = os.getenv("TOGETHER_API_KEY", "")

# ─── LLM Model Registry ─────────────────────────────────────────────────────
# Each key maps a logical role to a Together AI model string.
# Free-tier models are marked with (free).
# Together AI serverless model IDs (verified working as of June 2026)
_FAST_MODEL    = "meta-llama/Meta-Llama-3-8B-Instruct-Lite"   # Free, fast, good for classification
_QUALITY_MODEL = "meta-llama/Llama-3.3-70B-Instruct-Turbo"    # Paid/serverless, high quality

LLM_MODELS = {
    # Fast, deterministic routing — use lighter model for speed
    "router": _FAST_MODEL,

    # Resume generation — high quality, longer output
    "resume_builder": _QUALITY_MODEL,

    # Job search / ReAct agent
    "job_search": _QUALITY_MODEL,

    # Interview prep — ReAct agent with search
    "interview_prep": _QUALITY_MODEL,

    # Mock interview — conversational, multi-turn
    "mock_interview": _QUALITY_MODEL,

    # Interview evaluation — analytical, structured output
    "evaluation": _QUALITY_MODEL,

    # Tutorials — educational content with search
    "tutorials": _QUALITY_MODEL,

    # General Q&A / fallback
    "general_qa": _FAST_MODEL,

    # Clarifier — asks for missing info
    "clarifier": _FAST_MODEL,

    # Salary Negotiator — market research + negotiation coaching
    "salary_negotiator": _QUALITY_MODEL,
}

# ─── LLM Defaults ───────────────────────────────────────────────────────────
LLM_DEFAULTS = {
    "router":          {"temperature": 0.0, "max_tokens": 50},
    "resume_builder":  {"temperature": 0.2, "max_tokens": 4096},
    "job_search":      {"temperature": 0.5, "max_tokens": 4096},
    "interview_prep":  {"temperature": 0.6, "max_tokens": 4096},
    "mock_interview":  {"temperature": 0.7, "max_tokens": 2048},
    "evaluation":      {"temperature": 0.3, "max_tokens": 3000},
    "tutorials":       {"temperature": 0.5, "max_tokens": 4096},
    "general_qa":         {"temperature": 0.7, "max_tokens": 2048},
    "clarifier":          {"temperature": 0.3, "max_tokens": 256},
    "salary_negotiator":  {"temperature": 0.4, "max_tokens": 4096},
}

# ─── Graph Node Names ────────────────────────────────────────────────────────
# Single source of truth for node name strings used in routing
NODE_ROUTER         = "router"
NODE_RESUME         = "resume_builder"
NODE_JOB_SEARCH     = "job_search"
NODE_INTERVIEW_PREP = "interview_prep"
NODE_MOCK_INTERVIEW = "mock_interview"
NODE_EVALUATION     = "evaluation"
NODE_TUTORIALS      = "tutorials"
NODE_GENERAL_QA     = "general_qa"
NODE_CLARIFIER      = "clarifier"
NODE_SALARY         = "salary_negotiator"   # NEW
NODE_END            = "__end__"

# ─── Valid Routes ────────────────────────────────────────────────────────────
VALID_ROUTES = [
    NODE_RESUME,
    NODE_JOB_SEARCH,
    NODE_INTERVIEW_PREP,
    NODE_MOCK_INTERVIEW,
    NODE_TUTORIALS,
    NODE_SALARY,           # NEW
    NODE_GENERAL_QA,
    "UNCLEAR",
]

# ─── Persistence ─────────────────────────────────────────────────────────────
# SQLite database for LangGraph checkpointing
DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "data",
    "checkpoints.db"
)

# ─── UI Settings ─────────────────────────────────────────────────────────────
APP_TITLE       = "AI Career Assistant"
APP_ICON        = "🚀"
DEFAULT_USER    = "Candidate"
