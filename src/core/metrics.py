"""
src/core/metrics.py
─────────────────────────────────────────────────────────────────────────────
In-memory metrics registry for MLOps observability.

Tracks per-agent:
  - Call count, error count, success rate
  - Latency: total, min, max, P50, P95, P99 (via sorted insertion)
  - Token usage: prompt + completion

Design decisions:
  - Thread-safe via threading.Lock (FastAPI uses threads per request)
  - Singleton `registry` instance — import and use directly
  - `.snapshot()` returns a JSON-serialisable dict for /api/metrics endpoint
  - Zero coupling: no knowledge of agents, prompts, or LLM internals

Usage:
    from src.core.metrics import registry
    registry.record("resume_builder", latency_ms=1240.5, tokens=812, success=True)
    print(registry.snapshot())
"""

from __future__ import annotations

import bisect
import threading
from typing import Any, Dict, List


class _AgentMetrics:
    """Metrics for a single agent/node."""

    __slots__ = (
        "calls", "errors", "total_latency_ms",
        "total_tokens", "latencies", "lock",
    )

    def __init__(self):
        self.calls: int = 0
        self.errors: int = 0
        self.total_latency_ms: float = 0.0
        self.total_tokens: int = 0
        self.latencies: List[float] = []   # kept sorted for percentile calc
        self.lock = threading.Lock()

    def record(self, latency_ms: float, tokens: int = 0, success: bool = True):
        with self.lock:
            self.calls += 1
            self.total_latency_ms += latency_ms
            self.total_tokens += tokens
            bisect.insort(self.latencies, latency_ms)
            if not success:
                self.errors += 1

    def _percentile(self, p: float) -> float:
        """Return the p-th percentile (0–100) from sorted latencies."""
        n = len(self.latencies)
        if n == 0:
            return 0.0
        idx = int(n * p / 100.0)
        idx = min(idx, n - 1)
        return self.latencies[idx]

    def to_dict(self) -> Dict[str, Any]:
        with self.lock:
            count = self.calls
            return {
                "calls": count,
                "errors": self.errors,
                "success_rate": round((count - self.errors) / count, 4) if count else 0,
                "avg_latency_ms": round(self.total_latency_ms / count, 2) if count else 0,
                "p50_latency_ms": round(self._percentile(50), 2),
                "p95_latency_ms": round(self._percentile(95), 2),
                "p99_latency_ms": round(self._percentile(99), 2),
                "min_latency_ms": round(self.latencies[0], 2) if self.latencies else 0,
                "max_latency_ms": round(self.latencies[-1], 2) if self.latencies else 0,
                "total_tokens": self.total_tokens,
            }


class MetricsRegistry:
    """
    Global, thread-safe metrics registry.

    Each agent has its own _AgentMetrics instance, created on first access.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._agents: Dict[str, _AgentMetrics] = {}

    def _get_or_create(self, agent: str) -> _AgentMetrics:
        if agent not in self._agents:
            with self._lock:
                if agent not in self._agents:
                    self._agents[agent] = _AgentMetrics()
        return self._agents[agent]

    def record(self, agent: str, latency_ms: float, tokens: int = 0, success: bool = True):
        """Record a single invocation for the given agent."""
        self._get_or_create(agent).record(latency_ms, tokens, success)

    def snapshot(self) -> Dict[str, Any]:
        """Return a full JSON-serialisable snapshot of all agent metrics."""
        with self._lock:
            return {name: m.to_dict() for name, m in self._agents.items()}

    def reset(self):
        """Clear all metrics (useful for testing)."""
        with self._lock:
            self._agents.clear()


# ── Singleton ─────────────────────────────────────────────────────────────────
registry = MetricsRegistry()
