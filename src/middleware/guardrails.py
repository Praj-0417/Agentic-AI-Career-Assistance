"""
src/middleware/guardrails.py
─────────────────────────────────────────────────────────────────────────────
Input sanitisation and output validation guardrails.

Design principles:
  - Open/Closed: new validators added as functions, registered in _OUTPUT_VALIDATORS
  - Single Responsibility: each function does ONE check
  - Interface Segregation: agents import only what they need (or use the decorator)
  - Zero coupling: guardrails know nothing about prompts or LLM internals

Input guardrails (run BEFORE the LLM):
  - Length limits (prevent abuse / runaway prompts)
  - Prompt injection detection (regex-based, fast)
  - Encoding safety (strip null bytes, control chars)

Output guardrails (run AFTER the LLM):
  - LaTeX structure validation (for resume_builder)
  - Markdown structure validation (for tutorials, interview_prep)
  - Empty/error output detection (all agents)

Usage as decorator:
    from src.middleware.guardrails import guarded_node

    @guarded_node("resume_builder", output_validator="latex")
    def resume_builder_node(state):
        ...

Usage as standalone functions:
    from src.middleware.guardrails import sanitise_input, validate_output
    clean = sanitise_input(raw_text)
    issues = validate_output(output, validator="latex")
"""

from __future__ import annotations

import re
import functools
import time
from typing import Any, Callable, Dict, List, Optional

from src.core.logging import get_logger, set_trace_id, get_trace_id
from src.core.metrics import registry

_logger = get_logger("guardrails")


# ═══════════════════════════════════════════════════════════════════════════════
#  INPUT GUARDRAILS
# ═══════════════════════════════════════════════════════════════════════════════

# Maximum allowed input length (characters)
MAX_INPUT_LENGTH = 15_000

# Patterns that suggest prompt injection attempts
_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(a|an)\s+", re.IGNORECASE),
    re.compile(r"system\s*:\s*", re.IGNORECASE),
    re.compile(r"<\|im_start\|>", re.IGNORECASE),
    re.compile(r"\[INST\]", re.IGNORECASE),
    re.compile(r"do\s+not\s+follow\s+(your|the)\s+(original|previous)", re.IGNORECASE),
    re.compile(r"forget\s+(everything|all|your)\s+(you|instructions|rules)", re.IGNORECASE),
    re.compile(r"act\s+as\s+if\s+you\s+have\s+no\s+restrictions", re.IGNORECASE),
]


def sanitise_input(text: str) -> str:
    """
    Clean and validate user input before it reaches the LLM.

    Steps:
      1. Strip null bytes and control characters
      2. Enforce length limit
      3. Return cleaned text

    Raises:
        ValueError: if input is empty after cleaning
    """
    if not text:
        raise ValueError("Empty input received")

    # Strip null bytes and non-printable control chars (keep newlines, tabs)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    # Enforce length limit
    if len(text) > MAX_INPUT_LENGTH:
        _logger.warning(
            "Input truncated",
            extra={"input_len": len(text), "event": "input_truncated"},
        )
        text = text[:MAX_INPUT_LENGTH]

    text = text.strip()
    if not text:
        raise ValueError("Input is empty after sanitisation")

    return text


def detect_injection(text: str) -> List[str]:
    """
    Scan input for prompt injection patterns.

    Returns:
        List of matched pattern descriptions. Empty list = safe.
    """
    findings = []
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(text):
            findings.append(f"Matched: {pattern.pattern}")

    if findings:
        _logger.warning(
            "Potential prompt injection detected",
            extra={"event": "injection_detected", "findings": len(findings)},
        )

    return findings


# ═══════════════════════════════════════════════════════════════════════════════
#  DOMAIN BOUNDARY GUARDRAILS
# ═══════════════════════════════════════════════════════════════════════════════

# Keywords that indicate the query IS within our career-assistance domain.
# Compiled as word-boundary regex patterns to prevent substring false positives
# (e.g. "hi" matching inside "this").
_IN_SCOPE_PATTERNS = [
    re.compile(
        r"\b(" + "|".join(kws) + r")\b", re.IGNORECASE
    )
    for kws in [
        # Resume
        ["resume", "cv", "cover letter", "portfolio", "latex"],
        # Job search
        ["job", "jobs", "hiring", "internship", "apply",
         "opening", "vacancy", "career", "position", "recruit"],
        # Interview
        ["interview", "mock interview", "behavioral", "behavioural",
         "technical question", "coding round", "hr round", "aptitude"],
        # Salary
        ["salary", "compensation", "negotiate", "offer letter", "ctc",
         "package", "hike", "raise", "equity", "bonus"],
        # Career guidance
        ["career", "switch career", "transition", "roadmap", "learning path",
         "upskill", "certification", "promotion", "appraisal"],
        # Tech tutorials (career-relevant)
        ["tutorial", "learn", "teach me", "how to code", "how to build",
         "python", "java", "javascript", "sql", "aws",
         "docker", "kubernetes", "machine learning", "data science",
         "system design", "dsa", "algorithm", "data structure",
         "backend", "frontend", "fullstack", "devops", "mlops",
         "git", "linux", "cloud", "microservice"],
        # General career
        ["linkedin", "github", "mentor", "freelance",
         "remote work", "work from home", "startup",
         "fresher", "entry level", "software engineer"],
        # Greetings (always in scope)
        ["hello", "hey there", "thanks", "thank you", "help me",
         "what can you do", "features"],
    ]
]

# Keywords that strongly indicate OFF-TOPIC queries
_OFF_TOPIC_PATTERNS = [
    # Health / Beauty / Medical
    re.compile(r"\b(cream|lotion|skin\s*care|acne|medicine|doctor|symptoms?|diseases?|weight\s*loss|diet|workout|gym|diabetes|blood\s*pressure)\b", re.IGNORECASE),
    # Food / Cooking
    re.compile(r"\b(recipe|cook|bake|ingredient|restaurant|food\s*delivery)\b", re.IGNORECASE),
    # Entertainment
    re.compile(r"\b(movie|song|music|game|play|watch|stream|netflix|spotify|anime|manga)\b", re.IGNORECASE),
    # Shopping
    re.compile(r"\b(buy|purchase|price|discount|coupon|amazon|flipkart|product\s*review)\b", re.IGNORECASE),
    # Travel
    re.compile(r"\b(flight|hotel|travel|vacation|tourism|visa\s*(?!interview))\b", re.IGNORECASE),
    # Social media (non-professional)
    re.compile(r"\b(instagram\s*reels?|tiktok|snapchat|dating|tinder)\b", re.IGNORECASE),
    # Homework / non-career code requests
    re.compile(r"\b(fix\s+(this|my)\s+(bug|code|error)|debug\s+(this|my)|solve\s+this\s+(problem|equation)|homework|assignment\s+(?!interview))\b", re.IGNORECASE),
    # Generic app building (not learning)
    re.compile(r"\b(build\s+(me\s+)?(a|an)\s+(app|website|game|bot)|create\s+(a|an)\s+(app|website|game))\b", re.IGNORECASE),
]

# Polite redirect message
_OUT_OF_SCOPE_MESSAGE = (
    "🎯 I'm **career.ai** — your AI career assistant! I specialise in:\n\n"
    "• 📄 **Resume Building** — Generate tailored LaTeX resumes\n"
    "• 🔍 **Job Search** — Find real-time job openings\n"
    "• 🎯 **Interview Prep** — Role-specific preparation guides\n"
    "• 🎤 **Mock Interviews** — Practice with AI interviewer\n"
    "• 📚 **Tech Tutorials** — Learn any tech topic step-by-step\n"
    "• 💰 **Salary Negotiation** — Data-driven counter-offer scripts\n\n"
    "Your question seems outside my expertise. "
    "Try rephrasing it as a career-related request, and I'll be happy to help! 🚀"
)


def check_domain_boundary(text: str) -> dict:
    """
    Check if the user's query falls within our career-assistance domain.

    Strategy (fast, no LLM needed):
      1. If any in-scope keyword matches (word boundary) → ALLOW
      2. If any off-topic pattern matches AND no in-scope keyword → BLOCK
      3. If nothing matches → ALLOW (let the router/LLM handle ambiguous cases)

    Returns:
        {"in_scope": True/False, "reason": str, "redirect_message": str or None}
    """
    # Step 1: Check if any in-scope pattern matches (word-boundary safe)
    for pattern in _IN_SCOPE_PATTERNS:
        if pattern.search(text):
            return {"in_scope": True, "reason": "in-scope keyword found", "redirect_message": None}

    # Step 2: Check off-topic patterns (only if no in-scope match)
    for pattern in _OFF_TOPIC_PATTERNS:
        if pattern.search(text):
            _logger.info(
                "Out-of-scope query blocked",
                extra={
                    "event": "domain_boundary_block",
                    "pattern": pattern.pattern,
                    "input_preview": text[:80],
                },
            )
            return {
                "in_scope": False,
                "reason": f"Off-topic pattern matched: {pattern.pattern}",
                "redirect_message": _OUT_OF_SCOPE_MESSAGE,
            }

    # Step 3: Ambiguous — let it through (router will handle)
    return {"in_scope": True, "reason": "no off-topic pattern matched", "redirect_message": None}


# ═══════════════════════════════════════════════════════════════════════════════
#  OUTPUT GUARDRAILS
# ═══════════════════════════════════════════════════════════════════════════════

def _validate_latex(output: str) -> List[str]:
    """
    Validate that resume builder output is structurally valid LaTeX.

    Checks:
      - Contains \\documentclass
      - Contains \\begin{document} and \\end{document}
      - Balanced braces (rough check)
    """
    issues = []

    # Strip markdown fences if present
    clean = output
    if "```latex" in clean:
        parts = clean.split("```latex", 1)
        if len(parts) > 1:
            clean = parts[1].split("```", 1)[0]
    elif "```" in clean:
        parts = clean.split("```", 1)
        if len(parts) > 1:
            clean = parts[1].split("```", 1)[0]

    if "\\documentclass" not in clean:
        issues.append("Missing \\documentclass declaration")
    if "\\begin{document}" not in clean:
        issues.append("Missing \\begin{document}")
    if "\\end{document}" not in clean:
        issues.append("Missing \\end{document}")

    # Rough brace balance
    open_count = clean.count("{")
    close_count = clean.count("}")
    if abs(open_count - close_count) > 5:
        issues.append(f"Brace imbalance: {open_count} open vs {close_count} close")

    return issues


def _validate_markdown(output: str) -> List[str]:
    """
    Validate that tutorial/prep output contains basic Markdown structure.

    Checks:
      - Contains at least one heading (# or ##)
      - Output is at least 200 chars (not a stub)
    """
    issues = []
    if not re.search(r"^#{1,3}\s+", output, re.MULTILINE):
        issues.append("Missing Markdown headings")
    if len(output.strip()) < 200:
        issues.append(f"Output too short ({len(output.strip())} chars), likely incomplete")
    return issues


def _validate_not_empty(output: str) -> List[str]:
    """Universal check: output should not be empty or just an error emoji."""
    issues = []
    stripped = output.strip()
    if not stripped:
        issues.append("Empty output")
    elif stripped.startswith("❌") and len(stripped) < 50:
        issues.append("Output is an error message only")
    return issues


# ── Validator registry ────────────────────────────────────────────────────────

_OUTPUT_VALIDATORS: Dict[str, Callable[[str], List[str]]] = {
    "latex":    _validate_latex,
    "markdown": _validate_markdown,
    "any":      _validate_not_empty,
}

# Map agent names to their expected output format
AGENT_VALIDATOR_MAP: Dict[str, str] = {
    "resume_builder":    "latex",
    "job_search":        "markdown",
    "interview_prep":    "markdown",
    "mock_interview":    "any",
    "evaluation":        "markdown",
    "tutorials":         "markdown",
    "salary_negotiator": "markdown",
    "general_qa":        "any",
    "clarifier":         "any",
}


def validate_output(output: str, validator: str = "any") -> List[str]:
    """
    Run the named output validator and return a list of issues.

    Args:
        output:    The LLM-generated text.
        validator: Key into _OUTPUT_VALIDATORS ("latex", "markdown", "any").

    Returns:
        Empty list if valid; list of issue descriptions otherwise.
    """
    # Always run the not-empty check first
    issues = _validate_not_empty(output)

    # Then run the specific validator
    specific = _OUTPUT_VALIDATORS.get(validator)
    if specific and specific != _validate_not_empty:
        issues.extend(specific(output))

    return issues


# ═══════════════════════════════════════════════════════════════════════════════
#  NODE DECORATOR — inject logging, metrics, and guardrails into any node
# ═══════════════════════════════════════════════════════════════════════════════

def guarded_node(
    agent_name: str,
    output_validator: Optional[str] = None,
):
    """
    Decorator that wraps a LangGraph node function with:
      1. Trace ID generation
      2. Input sanitisation (on user_message in task_input)
      3. Latency + metrics recording
      4. Output validation + logging
      5. Error handling with structured logging

    The decorated function's signature is unchanged: (state) -> dict

    Args:
        agent_name:       Name for metrics and logging (e.g. "resume_builder")
        output_validator: Validator key ("latex", "markdown", "any", or None for auto)
    """
    validator = output_validator or AGENT_VALIDATOR_MAP.get(agent_name, "any")

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(state: Dict[str, Any]) -> Dict[str, Any]:
            # ── 1. Trace ID ───────────────────────────────────────────────
            trace_id = set_trace_id()
            logger = get_logger(agent_name)
            logger.info(
                f"Node invoked",
                extra={"node": agent_name, "event": "node_start", "trace_id": trace_id},
            )

            # ── 2. Input sanitisation ─────────────────────────────────────
            task = state.get("task_input", {})
            user_msg = task.get("user_message", "")
            if user_msg:
                try:
                    clean_msg = sanitise_input(user_msg)

                    # 2a. Prompt injection check
                    injections = detect_injection(clean_msg)
                    if injections:
                        logger.warning(
                            "Injection attempt blocked",
                            extra={"node": agent_name, "event": "injection_blocked"},
                        )
                        return {
                            "agent_output": (
                                "⚠️ Your input was flagged by our safety system. "
                                "Please rephrase your request."
                            ),
                            "graph_trace": [agent_name],
                            "error": "Input flagged by guardrails",
                        }

                    # 2b. Domain boundary check (skip for router — it handles routing)
                    if agent_name != "router":
                        domain_check = check_domain_boundary(clean_msg)
                        if not domain_check["in_scope"]:
                            logger.info(
                                "Off-topic query redirected",
                                extra={"node": agent_name, "event": "domain_redirect"},
                            )
                            return {
                                "agent_output": domain_check["redirect_message"],
                                "graph_trace": [agent_name],
                                "error": None,
                            }

                    # Update state with sanitised input
                    state = {
                        **state,
                        "task_input": {**task, "user_message": clean_msg},
                    }
                except ValueError as ve:
                    return {
                        "agent_output": f"⚠️ Invalid input: {ve}",
                        "graph_trace": [agent_name],
                        "error": str(ve),
                    }

            # ── 3. Execute node with timing ───────────────────────────────
            t0 = time.perf_counter()
            success = True
            tokens = 0
            try:
                result = func(state)
            except Exception as exc:
                success = False
                latency_ms = (time.perf_counter() - t0) * 1000
                registry.record(agent_name, latency_ms, tokens=0, success=False)
                logger.error(
                    f"Node failed: {exc}",
                    extra={"node": agent_name, "event": "node_error", "latency_ms": round(latency_ms, 2)},
                    exc_info=True,
                )
                raise

            latency_ms = (time.perf_counter() - t0) * 1000

            # ── 4. Output validation ──────────────────────────────────────
            output = result.get("agent_output", "")
            issues = validate_output(output, validator)

            if issues:
                logger.warning(
                    f"Output validation issues: {issues}",
                    extra={
                        "node": agent_name,
                        "event": "output_validation_warning",
                        "issues": len(issues),
                    },
                )

            # ── 5. Record metrics ─────────────────────────────────────────
            has_error = bool(result.get("error"))
            registry.record(
                agent_name,
                latency_ms=latency_ms,
                tokens=tokens,
                success=not has_error,
            )

            logger.info(
                f"Node completed",
                extra={
                    "node": agent_name,
                    "event": "node_end",
                    "latency_ms": round(latency_ms, 2),
                    "output_len": len(output),
                    "validation_issues": len(issues),
                },
            )

            return result

        return wrapper
    return decorator
