"""
src/core/logging.py
─────────────────────────────────────────────────────────────────────────────
Structured JSON logging with correlation-ID tracing.

Design decisions:
  - JSON output for machine-parseable telemetry (ELK, Datadog, CloudWatch)
  - Correlation ID (trace_id) per request for distributed tracing
  - Thread-safe context via contextvars (not threading.local)
  - Zero coupling: no agent imports, no prompt awareness

Usage in nodes:
    from src.core.logging import get_logger, set_trace_id

    logger = get_logger("resume_builder")
    set_trace_id("req-abc-123")
    logger.info("Generation started", extra={"node": "resume_builder"})
"""

from __future__ import annotations

import json
import logging
import sys
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Dict, Optional


# ── Correlation ID context ────────────────────────────────────────────────────

_trace_id: ContextVar[str] = ContextVar("trace_id", default="no-trace")


def set_trace_id(tid: Optional[str] = None) -> str:
    """Set (or auto-generate) a trace ID for the current async/thread context."""
    tid = tid or f"trace-{uuid.uuid4().hex[:12]}"
    _trace_id.set(tid)
    return tid


def get_trace_id() -> str:
    """Retrieve the current trace ID."""
    return _trace_id.get()


# ── JSON Formatter ────────────────────────────────────────────────────────────

class _JSONFormatter(logging.Formatter):
    """
    Formats log records as single-line JSON objects.
    
    Extracts structured fields from `extra` dict:
      node, latency_ms, tokens, thread_id, event, error
    """

    _EXTRA_KEYS = frozenset({
        "node", "latency_ms", "tokens", "thread_id",
        "event", "error", "agent", "input_len", "output_len",
    })

    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "trace_id": _trace_id.get(),
            "msg": record.getMessage(),
        }

        # Pull structured extras
        for key in self._EXTRA_KEYS:
            val = getattr(record, key, None)
            if val is not None:
                log_obj[key] = val

        # Include exception info if present
        if record.exc_info and record.exc_info[1]:
            log_obj["exception"] = str(record.exc_info[1])

        return json.dumps(log_obj, default=str)


# ── Logger factory ────────────────────────────────────────────────────────────

_configured: set[str] = set()


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Return a structured JSON logger.

    Idempotent: calling with the same name returns the same logger
    without adding duplicate handlers.

    Args:
        name:  Logger name (typically the agent/module name).
        level: Minimum log level (default INFO).
    """
    logger = logging.getLogger(f"career.{name}")

    if name not in _configured:
        logger.setLevel(level)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(_JSONFormatter())
        logger.addHandler(handler)
        logger.propagate = False
        _configured.add(name)

    return logger
