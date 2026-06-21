"""
SQLite checkpointer setup for LangGraph.

Provides `get_checkpointer()` which returns a SqliteSaver instance
connected to the local database file defined in config.
"""

from __future__ import annotations

import os
from langgraph.checkpoint.sqlite import SqliteSaver

from src.config import DB_PATH


def get_checkpointer() -> SqliteSaver:
    """
    Return a SqliteSaver checkpointer, creating the database directory
    if it does not exist.

    Usage:
        checkpointer = get_checkpointer()
        graph = compile_graph(checkpointer)
        config = {"configurable": {"thread_id": session_id}}
        result = graph.invoke(state, config)
    """
    import sqlite3
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    return SqliteSaver(conn)
