"""
app.py — AI Career Assistant
Industry-level Streamlit UI backed by a LangGraph multi-agent system.

Run with:  streamlit run app.py
"""

from __future__ import annotations

import os
import uuid
import time
from typing import Any

import streamlit as st
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

# ── Environment ───────────────────────────────────────────────────────────────
load_dotenv()

# ── Page config (MUST be first Streamlit call) ─────────────────────────────
st.set_page_config(
    page_title="AI Career Assistant",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Deferred imports (avoid cold-start cost on every rerun) ─────────────────
@st.cache_resource(show_spinner=False)
def _load_graph():
    from src.graph.graph_builder  import compile_graph, get_graph_mermaid
    from src.graph.checkpointer   import get_checkpointer
    checkpointer = get_checkpointer()
    graph        = compile_graph(checkpointer)
    mermaid      = get_graph_mermaid()
    return graph, mermaid


# ═══════════════════════════════════════════════════════════════════════════════
# CSS — Premium Product-Grade Dark UI
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<style>
/* ── Google Font ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ── Global ── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #090d16;
    color: #cbd5e1;
}
[data-testid="stAppViewContainer"] { background: #090d16; }
[data-testid="stSidebar"]          { background: #0f172a; border-right: 1px solid #1e293b; }
[data-testid="stSidebar"] * { font-family: 'Inter', sans-serif !important; }

/* ── Header ── */
.saas-header {
    background: transparent !important;
    box-shadow: none !important;
    border-bottom: 1px solid #1e293b;
    padding-bottom: 16px;
    margin-bottom: 28px;
}
.saas-header h1 {
    color: #f8fafc;
    font-size: 1.8rem;
    font-weight: 700;
    margin: 0;
    letter-spacing: -0.02em;
}
.saas-header p {
    color: #64748b;
    margin: 6px 0 0;
    font-size: 0.95rem;
}

/* Remove default focus red outline */
button:focus, button:active, button:focus-visible {
    outline: none !important;
    box-shadow: none !important;
    border-color: transparent !important;
}
[data-testid="stSidebar"] .stButton > button:focus {
    border-color: transparent !important;
    box-shadow: none !important;
    color: #a5b4fc !important;
}

/* ── Mode badge ── */
.mode-badge {
    display: inline-flex; align-items: center; gap: 8px;
    background: rgba(79, 70, 229, 0.08);
    border: 1px solid rgba(79, 70, 229, 0.3);
    border-radius: 6px;
    padding: 4px 12px;
    font-size: 0.8rem; font-weight: 500; color: #a5b4fc;
    margin-bottom: 16px;
}

/* ── Chat messages ── */
[data-testid="stChatMessage"] {
    border-radius: 8px !important;
    margin-bottom: 12px !important;
    border: 1px solid #1e293b !important;
    background: #0f172a !important;
}
[data-testid="stChatMessage"][data-testid*="user"] {
    background: rgba(79, 70, 229, 0.04) !important;
    border-color: rgba(79, 70, 229, 0.2) !important;
}

/* ── Input box ── */
[data-testid="stChatInput"] textarea {
    background: #1e293b !important;
    border: 1px solid #334155 !important;
    border-radius: 8px !important;
    color: #f8fafc !important;
    font-family: 'Inter', sans-serif !important;
}
[data-testid="stChatInput"] textarea:focus {
    border-color: #4f46e5 !important;
    box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.25) !important;
}

/* ── Sidebar nav buttons ── */
[data-testid="stSidebar"] .stButton > button {
    background: transparent !important;
    color: #94a3b8 !important;
    border: 1px solid transparent !important;
    text-align: left !important;
    justify-content: flex-start !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    padding: 8px 14px !important;
    border-radius: 6px !important;
    box-shadow: none !important;
    transform: none !important;
    margin-bottom: 2px !important;
    transition: all 0.15s ease !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: #1e293b !important;
    color: #f8fafc !important;
}

/* ── Cards ── */
.card {
    background: #121826; border: 1px solid #1e293b;
    border-radius: 12px; padding: 22px;
    margin-bottom: 20px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}
.card h3 { color: #f8fafc; margin-top: 0; font-size: 1.1rem; font-weight: 600; }

/* ── Graph viz container ── */
.graph-container {
    background: #090d16; border: 1px solid #1e293b;
    border-radius: 12px; padding: 16px;
    font-family: monospace; font-size: 0.78rem;
}

/* ── Action Buttons (Primary) ── */
.stButton > button {
    background: #4f46e5 !important;
    color: #ffffff !important; border: 1px solid #4338ca !important;
    border-radius: 8px !important; font-weight: 500 !important;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05) !important;
    transition: all 0.15s ease !important;
    padding: 8px 16px !important;
}
.stButton > button:hover {
    background: #5850ec !important;
    border-color: #4f46e5 !important;
    transform: translateY(0px) !important;
    box-shadow: 0 4px 12px rgba(79, 70, 229, 0.25) !important;
}

/* ── Secondary/Reset/Clear Buttons ── */
div[data-testid*="Clear"] button, div[data-testid*="Reset"] button, div[data-testid*="End"] button {
    background: transparent !important;
    color: #94a3b8 !important;
    border: 1px solid #334155 !important;
}
div[data-testid*="Clear"] button:hover, div[data-testid*="Reset"] button:hover, div[data-testid*="End"] button:hover {
    background: #1e293b !important;
    color: #f8fafc !important;
    border-color: #4b5563 !important;
    box-shadow: none !important;
}

/* ── Textfields and Inputs ── */
.stTextInput > div > input,
.stTextArea > div > textarea,
.stSelectbox > div > div {
    background: #0f172a !important; color: #f8fafc !important;
    border: 1px solid #1e293b !important; border-radius: 8px !important;
    padding: 10px 14px !important;
}
.stTextInput > div > input:focus,
.stTextArea > div > textarea:focus {
    border-color: #4f46e5 !important;
    box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.2) !important;
}
.stRadio > div { background: transparent !important; }
label { color: #94a3b8 !important; font-size: 0.85rem !important; font-weight: 500 !important; }

/* ── Metric cards ── */
[data-testid="metric-container"] {
    background: #121826 !important; border: 1px solid #1e293b !important;
    border-radius: 10px !important; padding: 12px !important;
}

/* ── Spinner ── */
[data-testid="stSpinner"] { color: #4f46e5 !important; }

/* ── Divider ── */
hr { border-color: #1e293b !important; }

/* ── Expander ── */
.streamlit-expanderHeader {
    background: #121826 !important; border-radius: 8px !important;
    color: #94a3b8 !important;
    border: 1px solid #1e293b !important;
}

/* ── Success / Info / Warning banners ── */
.stAlert { border-radius: 8px !important; border: 1px solid transparent !important; }
div[data-testid="stNotification-success"] { background: rgba(16, 185, 129, 0.06) !important; border-color: rgba(16, 185, 129, 0.2) !important; color: #34d399 !important; }
div[data-testid="stNotification-warning"] { background: rgba(245, 158, 11, 0.06) !important; border-color: rgba(245, 158, 11, 0.2) !important; color: #fbbf24 !important; }
div[data-testid="stNotification-info"] { background: rgba(59, 130, 246, 0.06) !important; border-color: rgba(59, 130, 246, 0.2) !important; color: #60a5fa !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #090d16; }
::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #334155; }

/* ── Tab styling ── */
.stTabs [data-baseweb="tab-list"] { background: #0f172a; border-radius: 8px; border: 1px solid #1e293b; padding: 4px; }
.stTabs [data-baseweb="tab"] { color: #94a3b8; font-weight: 500; padding: 8px 16px; border-radius: 6px; }
.stTabs [aria-selected="true"] { color: #f8fafc !important; background: #1e293b !important; }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# Session state initialisation
# ═══════════════════════════════════════════════════════════════════════════════

def _init_session():
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = str(uuid.uuid4())
    if "messages" not in st.session_state:
        st.session_state.messages = []        # [{role, content, agent}]
    if "active_mode" not in st.session_state:
        st.session_state.active_mode = "chat" # chat | resume | job | interview | tutorials
    if "user_profile" not in st.session_state:
        st.session_state.user_profile = {
            "name": "", "job_title": "", "experience": "",
            "skills": "", "resume_content": "",
        }
    if "task_input" not in st.session_state:
        st.session_state.task_input = {}
    if "interview_history" not in st.session_state:
        st.session_state.interview_history = []
    if "mock_started" not in st.session_state:
        st.session_state.mock_started = False
    if "graph_trace" not in st.session_state:
        st.session_state.graph_trace = []
    if "interview_mode" not in st.session_state:
        st.session_state.interview_mode = "prep"


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════

NODE_COLORS = {
    "router":             "#818cf8",
    "resume_builder":    "#34d399",
    "job_search":        "#60a5fa",
    "interview_prep":   "#f59e0b",
    "mock_interview":   "#ec4899",
    "evaluation":       "#a78bfa",
    "tutorials":        "#38bdf8",
    "salary_negotiator": "#4ade80",   # NEW
    "general_qa":       "#94a3b8",
    "clarifier":        "#fb923c",
}

NODE_LABELS = {
    "router":             "🧭 Router",
    "resume_builder":    "📝 Resume Builder",
    "job_search":        "🔍 Job Search",
    "interview_prep":   "🎯 Interview Prep",
    "mock_interview":   "🎭 Mock Interview",
    "evaluation":       "📊 Evaluation",
    "tutorials":        "📚 Tutorials",
    "salary_negotiator": "💰 Salary Negotiator",   # NEW
    "general_qa":       "💬 General Q&A",
    "clarifier":        "❓ Clarifier",
}

AGENT_BADGE = {
    "resume_builder":    "📝 Resume Builder",
    "job_search":        "🔍 Job Search",
    "interview_prep":   "🎯 Interview Prep",
    "mock_interview":   "🎭 Mock Interview",
    "evaluation":       "📊 Evaluation",
    "tutorials":        "📚 Tutorials",
    "salary_negotiator": "💰 Salary Negotiator",   # NEW
    "general_qa":       "💬 General Q&A",
    "clarifier":        "❓ Clarifier",
    "router":           "🧭 Router",
}


def convert_markdown_to_html(text: str) -> str:
    import re
    html = text
    
    # Code blocks
    html = re.sub(r'```(?:\w+)?\n(.*?)\n```', r'<pre style="background:#0f1117;border:1px solid #1e293b;border-radius:8px;padding:12px;color:#e2e8f0;overflow-x:auto;font-family:monospace;font-size:0.85rem;margin-bottom:12px;">\1</pre>', html, flags=re.DOTALL)
    
    # Headers
    html = re.sub(r'^###\s+(.*?)$', r'<h4 style="color:#a5b4fc;margin-top:16px;margin-bottom:8px;font-size:1.08rem;font-weight:600;">\1</h4>', html, flags=re.MULTILINE)
    html = re.sub(r'^##\s+(.*?)$', r'<h3 style="color:#a5b4fc;margin-top:18px;margin-bottom:10px;font-size:1.2rem;font-weight:600;">\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^#\s+(.*?)$', r'<h2 style="color:#a5b4fc;margin-top:20px;margin-bottom:12px;font-size:1.35rem;font-weight:700;">\1</h2>', html, flags=re.MULTILINE)
    
    # Bold
    html = re.sub(r'\*\*(.*?)\*\*', r'<strong style="color:#ffffff;font-weight:600;">\1</strong>', html)
    
    # Italic
    html = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html)
    
    # Links
    html = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2" target="_blank" style="color:#818cf8;text-decoration:none;font-weight:500;border-bottom:1px dashed #818cf8;padding-bottom:1px;">\1</a>', html)
    
    # List parsing: line by line
    lines = html.split('\n')
    processed_lines = []
    in_list = False
    for line in lines:
        stripped = line.strip()
        list_match = re.match(r'^(\s*)[-*\u2022]\s+(.*?)$', line)
        if list_match:
            indent = len(list_match.group(1))
            content = list_match.group(2)
            style = "margin-bottom:6px;margin-left:20px;" if indent == 0 else f"margin-bottom:4px;margin-left:{20 + indent * 8}px;list-style-type:circle;"
            if not in_list:
                processed_lines.append('<ul style="margin-bottom:12px;padding-left:0;list-style-type:disc;color:#cbd5e1;">')
                in_list = True
            processed_lines.append(f'<li style="{style}">{content}</li>')
        else:
            if in_list:
                processed_lines.append('</ul>')
                in_list = False
            if stripped:
                if not stripped.startswith('<h') and not stripped.startswith('<u') and not stripped.startswith('</u') and not stripped.startswith('<li') and not stripped.startswith('<pre') and not stripped.startswith('</pre'):
                    if stripped.startswith('>'):
                        processed_lines.append(f'<blockquote style="border-left:4px solid #818cf8;padding-left:12px;color:#94a3b8;margin:8px 0;font-style:italic;">{stripped[1:].strip()}</blockquote>')
                    else:
                        processed_lines.append(f'<p style="margin-bottom:10px;line-height:1.6;color:#cbd5e1;">{stripped}</p>')
                else:
                    processed_lines.append(line)
            else:
                processed_lines.append('<div style="height:8px;"></div>')
    if in_list:
        processed_lines.append('</ul>')
        
    return '\n'.join(processed_lines)


def render_styled_card(title: str, markdown_content: str):
    html_content = convert_markdown_to_html(markdown_content)
    st.markdown(f"""
    <div class="card" style="background:#1a2035; border:1px solid #1e293b; border-radius:14px; padding:24px; margin-bottom:20px; box-shadow:0 4px 20px rgba(0,0,0,0.25);">
        <h3 style="color:#a5b4fc; font-family:\'Inter\',sans-serif; margin-top:0; border-bottom:1px solid #2d3748; padding-bottom:10px; margin-bottom:18px; font-size:1.12rem; font-weight:600;">{title}</h3>
        <div style="font-family:\'Inter\',sans-serif; font-size:0.92rem; color:#cbd5e1; line-height:1.6;">
            {html_content}
        </div>
    </div>
    """, unsafe_allow_html=True)


def _invoke_graph(user_text: str, extra_task: dict | None = None) -> dict[str, Any]:
    """
    Send a user message through the LangGraph pipeline.
    Returns the final state update dict.
    """
    from src.state import make_initial_state

    graph, _ = _load_graph()

    task = {
        **st.session_state.task_input,
        "user_message": user_text,
        **(extra_task or {}),
    }

    # Build the state snapshot for this turn
    state = make_initial_state()
    state["messages"]         = [HumanMessage(content=user_text)]
    state["user_profile"]     = dict(st.session_state.user_profile)
    state["task_input"]       = task
    state["interview_history"] = list(st.session_state.interview_history)
    state["interview_mode"]   = st.session_state.interview_mode

    config = {"configurable": {"thread_id": st.session_state.thread_id}}

    result = graph.invoke(state, config)
    return result


def _render_graph_viz(active_nodes: list[str]):
    """Render live LangGraph topology. Uses components.html for reliable HTML rendering."""
    import streamlit.components.v1 as components

    node_badges = ""
    for name, label in NODE_LABELS.items():
        color = NODE_COLORS.get(name, "#94a3b8")
        is_active = name in active_nodes
        if is_active:
            bg  = color + "33"
            bdr = "3px solid " + color
            glow = "box-shadow:0 0 14px " + color + "99;"
            fg  = "#ffffff"
            fw  = "700"
        else:
            bg  = "#1a2035"
            bdr = "1px solid #2d3748"
            glow = ""
            fg  = "#94a3b8"
            fw  = "400"

        node_badges += (
            "<span style='display:inline-flex;align-items:center;gap:5px;"
            "background:" + bg + ";border:" + bdr + ";"
            "border-radius:8px;padding:5px 13px;margin:3px;"
            "font-size:0.76rem;font-weight:" + fw + ";color:" + fg + ";"
            + glow + "transition:all 0.3s;'>" + label + "</span>"
        )

    html = (
        "<div style='background:#0d1320;border:1px solid #1e293b;"
        "border-radius:14px;padding:15px 18px;"
        "font-family:Inter,system-ui,sans-serif;'>"
        "<div style='font-size:0.68rem;color:#4b5563;text-transform:uppercase;"
        "letter-spacing:0.08em;margin-bottom:11px;font-weight:600;'>"
        "&#128279; Live Graph &mdash; Active Nodes Highlighted"
        "</div>"
        "<div style='display:flex;flex-wrap:wrap;gap:2px;align-items:center;'>"
        + node_badges +
        "</div>"
        "<div style='margin-top:10px;font-size:0.67rem;color:#374151;"
        "border-top:1px solid #1e293b;padding-top:8px;'>"
        "START &#x2192; router &#x2192; specialist node &#x2192; END"
        "</div>"
        "</div>"
    )
    components.html(html, height=135, scrolling=False)

def _sidebar_nav():
    """Render the sidebar with navigation and user profile."""
    with st.sidebar:
        # ── Logo ──────────────────────────────────────────────────────────────
        st.markdown("""
        <div style="padding: 12px 0 16px;">
            <div style="font-size:1.25rem; font-weight:700; color:#f8fafc; letter-spacing:-0.02em; display:flex; align-items:center; gap:10px;">
                <span style="background:linear-gradient(135deg, #4f46e5, #8b5cf6); width:28px; height:28px; border-radius:6px; display:inline-flex; align-items:center; justify-content:center; color:#ffffff; font-size:0.95rem; font-weight:bold; box-shadow:0 2px 8px rgba(79,70,229,0.3);">C</span>
                <span>career.ai</span>
            </div>
            <div style="font-size:0.78rem; color:#475569; margin-top:6px; font-weight:500; text-transform:uppercase; letter-spacing:0.05em; padding-left:2px;">
                Agentic Assistant
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.divider()

        # ── Navigation ────────────────────────────────────────────────────────
        st.markdown('<div style="font-size:0.75rem; color:#4b5563; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:8px;">Navigation</div>', unsafe_allow_html=True)

        nav_items = [
            ("chat",       "💬", "Chat Assistant",       "Talk to your AI career advisor"),
            ("resume",     "📝", "Resume Builder",        "Generate & refine LaTeX resumes"),
            ("job",        "🔍", "Job Search",            "Find live job postings"),
            ("interview",  "🎯", "Interview Prep",        "Prep guide + mock interview"),
            ("tutorials",  "📚", "Tutorials",             "Learn any tech topic"),
            ("salary",     "💰", "Salary Negotiator",     "Negotiate your best offer"),   # NEW
            ("profile",    "👤", "Your Profile",          "Manage your career profile"),
        ]

        for mode, icon, label, desc in nav_items:
            active = st.session_state.active_mode == mode
            if active:
                st.markdown(f"""
                <style>
                div[data-testid="stSidebar"] div.st-key-nav_{mode} button {{
                    background: rgba(79, 70, 229, 0.12) !important;
                    color: #a5b4fc !important;
                    border-left: 3px solid #4f46e5 !important;
                    border-radius: 0 6px 6px 0 !important;
                    padding-left: 11px !important;
                }}
                </style>
                """, unsafe_allow_html=True)
            if st.button(f"{icon}  {label}", key=f"nav_{mode}", use_container_width=True,
                         help=desc):
                st.session_state.active_mode = mode
                st.rerun()

        st.divider()

        # ── Graph trace ───────────────────────────────────────────────────────
        if st.session_state.graph_trace:
            st.markdown('<div style="font-size:0.75rem; color:#4b5563; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:8px;">Last Run</div>', unsafe_allow_html=True)
            for node in st.session_state.graph_trace[-6:]:
                color = NODE_COLORS.get(node, "#94a3b8")
                label = NODE_LABELS.get(node, node)
                st.markdown(f"""
                <div style="display:flex; align-items:center; gap:8px;
                            padding:4px 8px; margin-bottom:4px;">
                    <div style="width:8px; height:8px; border-radius:50%;
                                background:{color}; flex-shrink:0;"></div>
                    <span style="font-size:0.8rem; color:#94a3b8;">{label}</span>
                </div>""", unsafe_allow_html=True)
            st.divider()

        # ── Session info ─────────────────────────────────────────────────────
        with st.expander("⚙️ Session", expanded=False):
            st.caption(f"Thread: `{st.session_state.thread_id[:8]}...`")
            if st.button("🔄 New Session", use_container_width=True):
                import uuid
                st.session_state.thread_id        = str(uuid.uuid4())
                st.session_state.messages         = []
                st.session_state.interview_history = []
                st.session_state.mock_started     = False
                st.session_state.graph_trace      = []
                st.session_state.task_input       = {}
                st.rerun()
            if st.button("🗑️ Clear Chat", use_container_width=True):
                st.session_state.messages = []
                st.rerun()

        # ── Google Search MCP Settings ───────────────────────────────────────
        with st.expander("🔍 Web Search Settings", expanded=False):
            st.caption("Optional configuration for Google Search MCP server.")
            
            # Use environment variable as default
            google_api_key_env = os.getenv("GOOGLE_API_KEY", "")
            google_cse_id_env = os.getenv("GOOGLE_CSE_ID", "")
            
            # Input keys
            google_key_input = st.text_input(
                "Google API Key",
                value=google_api_key_env,
                type="password",
                help="Requires custom search JSON API key"
            )
            google_cse_input = st.text_input(
                "Google CSE ID",
                value=google_cse_id_env,
                help="Requires Google Custom Search Engine ID"
            )
            
            if st.button("💾 Apply Search Keys", use_container_width=True):
                if google_key_input.strip():
                    os.environ["GOOGLE_API_KEY"] = google_key_input.strip()
                    if google_cse_input.strip():
                        os.environ["GOOGLE_CSE_ID"] = google_cse_input.strip()
                    else:
                        if "GOOGLE_CSE_ID" in os.environ:
                            del os.environ["GOOGLE_CSE_ID"]
                    st.success("Google API Key configured!")
                else:
                    if "GOOGLE_API_KEY" in os.environ:
                        del os.environ["GOOGLE_API_KEY"]
                    if "GOOGLE_CSE_ID" in os.environ:
                        del os.environ["GOOGLE_CSE_ID"]
                    st.info("Reset to DuckDuckGo search fallback.")
                st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# View renderers
# ═══════════════════════════════════════════════════════════════════════════════

def _header(title: str, subtitle: str = ""):
    st.markdown(f"""
    <div class="saas-header">
        <h1>{title}</h1>
        {"<p>" + subtitle + "</p>" if subtitle else ""}
    </div>
    """, unsafe_allow_html=True)


def _chat_view():
    _header("💬 Chat Assistant",
            "Ask anything career-related — I'll route you to the right specialist automatically.")

    # Graph visualization
    _render_graph_viz(st.session_state.graph_trace)

    # Chat history
    for msg in st.session_state.messages:
        role  = msg["role"]
        agent = msg.get("agent", "")
        with st.chat_message(role):
            if role == "assistant" and agent:
                badge_color = NODE_COLORS.get(agent, "#94a3b8")
                badge_label = AGENT_BADGE.get(agent, agent)
                st.markdown(f"""<div style="font-size:0.72rem; color:{badge_color};
                    margin-bottom:6px; font-weight:500;">via {badge_label}</div>""",
                    unsafe_allow_html=True)
            st.markdown(msg["content"])

    # Input
    if prompt := st.chat_input("Ask me about your career, resume, jobs, interviews…"):
        # Show user message immediately
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                result = _invoke_graph(prompt)

            output     = result.get("agent_output", "Sorry, I couldn't process that.")
            agent_used = result.get("current_agent", "general_qa")
            trace      = result.get("graph_trace", [])

            # Update trace
            st.session_state.graph_trace = trace

            # Update interview history if mock was active
            if result.get("interview_history"):
                st.session_state.interview_history = result["interview_history"]

            # Update profile if changed
            if result.get("user_profile"):
                st.session_state.user_profile.update(result["user_profile"])

            badge_color = NODE_COLORS.get(agent_used, "#94a3b8")
            badge_label = AGENT_BADGE.get(agent_used, agent_used)
            st.markdown(f"""<div style="font-size:0.72rem; color:{badge_color};
                margin-bottom:6px; font-weight:500;">via {badge_label}</div>""",
                unsafe_allow_html=True)
            st.markdown(output)

        st.session_state.messages.append({
            "role": "assistant",
            "content": output,
            "agent": agent_used,
        })
        st.rerun()


def _resume_view():
    _header("📝 Resume Builder",
            "Generate ATS-optimised LaTeX resumes tailored to any job description.")

    tab1, tab2 = st.tabs(["✨ Generate", "✏️ Refine"])

    with tab1:
        col1, col2 = st.columns(2, gap="large")
        with col1:
            st.markdown("**Target Job Description**")
            job_desc = st.text_area(
                "Paste the job description here",
                height=200, key="resume_job_desc",
                placeholder="Paste the full job description including responsibilities, requirements, and preferred skills…",
            )
        with col2:
            st.markdown("**Your Details**")
            user_details = st.text_area(
                "Paste your current resume or list your experience",
                height=200, key="resume_user_details",
                placeholder="Work experience, skills, education, projects, certifications…",
            )

        if st.button("⚡ Generate LaTeX Resume", use_container_width=False):
            if job_desc and user_details:
                with st.spinner("Generating your tailored LaTeX resume…"):
                    st.session_state.task_input = {
                        "job_description": job_desc,
                        "user_details":    user_details,
                        "previous_resume": "",
                    }
                    result = _invoke_graph(
                        f"Generate a LaTeX resume for: {job_desc[:100]}",
                        extra_task={"job_description": job_desc, "user_details": user_details},
                    )
                    output = result.get("agent_output", "")
                    trace  = result.get("graph_trace", [])
                    st.session_state.graph_trace = trace
                    if result.get("user_profile", {}).get("resume_content"):
                        st.session_state.user_profile["resume_content"] = \
                            result["user_profile"]["resume_content"]

                st.success("✅ Resume generated!")
                # Extract LaTeX code
                latex = result.get("task_input", {}).get("generated_resume", "") or \
                        result.get("user_profile", {}).get("resume_content", "")
                if latex:
                    st.markdown("### 📄 Your LaTeX Resume")
                    st.info("Copy this code into [Overleaf](https://overleaf.com) to compile your PDF.")
                    st.code(latex, language="latex")
            else:
                st.warning("Please provide both the job description and your details.")

    with tab2:
        existing = st.session_state.user_profile.get("resume_content", "")
        if not existing:
            st.info("Generate a resume first in the **Generate** tab, then come back to refine it.")
        else:
            st.markdown("**Current Resume (click to expand)**")
            with st.expander("View LaTeX Code"):
                st.code(existing, language="latex")

            st.markdown("**Refinement Request**")
            refinement = st.text_area(
                "Describe the changes you want",
                height=120, key="refinement_req",
                placeholder="E.g., 'Add a projects section with my AI chatbot project', 'Make the summary more leadership-focused', 'Add Docker and Kubernetes to skills'…",
            )
            job_desc_ctx = st.text_input(
                "Job description context (optional)", key="refine_job_desc",
                placeholder="Paste the job description to keep refinements aligned…",
            )

            if st.button("🔧 Apply Changes"):
                if refinement:
                    with st.spinner("Refining your resume…"):
                        result = _invoke_graph(
                            refinement,
                            extra_task={
                                "previous_resume": existing,
                                "job_description": job_desc_ctx,
                                "user_request":    refinement,
                            },
                        )
                    latex = result.get("task_input", {}).get("generated_resume", "") or \
                            result.get("user_profile", {}).get("resume_content", existing)
                    if latex and latex != existing:
                        st.session_state.user_profile["resume_content"] = latex
                        st.success("✅ Resume updated!")
                        st.code(latex, language="latex")
                    else:
                        st.warning("No changes detected. Try rephrasing your request.")
                else:
                    st.warning("Please describe the changes you want.")


def _job_search_view():
    _header("🔍 Job Search", "Find live job openings tailored to your profile.")

    c1, c2, c3 = st.columns([2, 2, 1])
    with c1:
        job_title = st.text_input("Job Title *", key="js_title",
                                  placeholder="Software Engineer, Data Scientist…")
    with c2:
        location = st.text_input("Location *", key="js_location",
                                 placeholder="New York, Remote, London…")
    with c3:
        job_type = st.selectbox("Type", ["Full-time","Part-time","Contract","Internship"],
                                key="js_type")

    user_context = st.text_area(
        "Your Skills & Background (helps personalize results)",
        height=100, key="js_context",
        value=st.session_state.user_profile.get("skills", ""),
        placeholder="Python, machine learning, 3 years experience in fintech…",
    )

    if st.button("🚀 Search Jobs", use_container_width=False):
        if job_title and location:
            with st.spinner(f"Searching for {job_type} {job_title} roles in {location}…"):
                result = _invoke_graph(
                    f"Find {job_type} {job_title} jobs in {location}",
                    extra_task={
                        "job_title":    job_title,
                        "location":     location,
                        "job_type":     job_type,
                        "user_context": user_context,
                    },
                )
            st.session_state.graph_trace = result.get("graph_trace", [])
            output = result.get("agent_output", "No results found.")
            st.markdown("---")
            render_styled_card(f"🔍 Job Search Results: {job_title} ({location})", output)
        else:
            st.warning("Please provide a job title and location.")


def _interview_view():
    _header("🎯 Interview Prep", "Preparation guides, mock interviews, and scorecards.")

    # Common fields
    col1, col2 = st.columns(2)
    with col1:
        job_title = st.text_input("Job Title *", key="iv_title",
                                  placeholder="Software Engineer, Product Manager…")
    with col2:
        experience = st.text_area("Your Relevant Experience", height=80, key="iv_exp",
                                  placeholder="5 years backend engineering, Python, AWS…")

    mode = st.radio("Mode", ["📋 Prep Guide", "🎭 Mock Interview", "📊 Evaluate"],
                    horizontal=True, key="iv_mode")

    st.divider()

    if mode == "📋 Prep Guide":
        prep_q = st.text_input("Specific focus area (optional)",
                               placeholder="Behavioral questions, system design, salary negotiation…",
                               key="prep_focus")
        if st.button("Generate Prep Guide"):
            if job_title:
                with st.spinner("Researching and building your prep guide…"):
                    result = _invoke_graph(
                        prep_q or f"Comprehensive interview preparation guide for {job_title}",
                        extra_task={
                            "job_title":       job_title,
                            "user_experience": experience,
                            "user_name":       st.session_state.user_profile.get("name","Candidate"),
                            "user_request":    prep_q,
                        },
                    )
                st.session_state.graph_trace = result.get("graph_trace", [])
                render_styled_card(f"🎯 Interview Prep Guide: {job_title}", result.get("agent_output", ""))
            else:
                st.warning("Please provide a job title.")

    elif mode == "🎭 Mock Interview":
        st.session_state.interview_mode = "mock"

        if not st.session_state.mock_started:
            st.info("The AI will conduct a realistic mock interview — one question at a time. Answer as you would in a real interview!")
            if st.button("▶ Start Mock Interview"):
                if job_title:
                    st.session_state.interview_history = []
                    st.session_state.mock_started = True
                    # Get first question
                    with st.spinner("Starting the interview…"):
                        result = _invoke_graph(
                            "Start the mock interview",
                            extra_task={
                                "job_title":       job_title,
                                "user_experience": experience,
                                "user_name":       st.session_state.user_profile.get("name","Candidate"),
                            },
                        )
                    st.session_state.interview_history = result.get("interview_history", [])
                    st.session_state.graph_trace = result.get("graph_trace", [])
                    st.rerun()
                else:
                    st.warning("Please provide the job title.")
        else:
            # Display conversation
            st.subheader(f"🎭 Mock Interview — {job_title}")
            for msg in st.session_state.interview_history:
                role    = msg.get("role", "")
                content = msg.get("content", "")
                if role == "system":
                    continue
                with st.chat_message("user" if role == "user" else "assistant"):
                    st.markdown(content)

            answer = st.chat_input("Your answer…")
            if answer:
                with st.spinner("Interviewer is thinking…"):
                    result = _invoke_graph(
                        answer,
                        extra_task={
                            "job_title":       job_title,
                            "user_experience": experience,
                            "user_name":       st.session_state.user_profile.get("name","Candidate"),
                        },
                    )
                st.session_state.interview_history = result.get("interview_history", [])
                st.session_state.graph_trace = result.get("graph_trace", [])
                st.rerun()

            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("⏹ End Interview"):
                    st.session_state.mock_started = False
                    st.session_state.interview_history = []
                    st.rerun()
            with c2:
                if st.button("🔄 Restart"):
                    st.session_state.mock_started = False
                    st.rerun()
            with c3:
                if st.button("📊 End & Evaluate"):
                    with st.spinner("Evaluating your performance…"):
                        result = _invoke_graph(
                            "Evaluate this interview",
                            extra_task={
                                "job_title":       job_title,
                                "user_experience": experience,
                                "user_name":       st.session_state.user_profile.get("name","Candidate"),
                            },
                        )
                    # Force evaluation node
                    from src.state import make_initial_state
                    from src.graph.nodes.evaluation_node import evaluation_node
                    eval_state = make_initial_state()
                    eval_state["task_input"] = {
                        "job_title": job_title,
                        "user_experience": experience,
                        "user_name": st.session_state.user_profile.get("name", "Candidate"),
                    }
                    eval_state["interview_history"] = st.session_state.interview_history
                    eval_result = evaluation_node(eval_state)
                    st.session_state.mock_started = False
                    st.divider()
                    render_styled_card("📊 Mock Interview Evaluation", eval_result.get("agent_output", ""))
        
    else:  # Evaluate
        transcript = st.text_area(
            "Paste your interview transcript",
            height=250, key="eval_transcript",
            placeholder="Interviewer: Tell me about yourself.\nMe: I'm a software engineer with 5 years…",
        )
        if st.button("📊 Evaluate Interview"):
            if job_title and transcript:
                from src.state import make_initial_state
                from src.graph.nodes.evaluation_node import evaluation_node
                with st.spinner("Analysing your interview…"):
                    eval_state = make_initial_state()
                    eval_state["task_input"] = {
                        "job_title":            job_title,
                        "user_experience":      experience,
                        "user_name":            st.session_state.user_profile.get("name","Candidate"),
                        "interview_transcript":  transcript,
                    }
                    eval_result = evaluation_node(eval_state)
                render_styled_card("📊 Interview Evaluation", eval_result.get("agent_output", ""))
            else:
                st.warning("Please provide job title and transcript.")


def _tutorials_view():
    _header("📚 Tutorials", "Deep-dive, project-based learning on any tech topic.")

    topic = st.text_input("What do you want to learn?", key="tut_topic",
                          placeholder="LangGraph agents, React hooks, Docker, System Design…")
    user_bg = st.text_input("Your background (optional)", key="tut_bg",
                            value=st.session_state.user_profile.get("skills",""),
                            placeholder="Python beginner, 2 years JavaScript…")

    if st.button("📖 Generate Tutorial"):
        if topic:
            with st.spinner(f"Building a comprehensive tutorial on '{topic}'…"):
                result = _invoke_graph(
                    topic,
                    extra_task={"user_message": topic, "user_context": user_bg},
                )
            st.session_state.graph_trace = result.get("graph_trace", [])
            output = result.get("agent_output", "")
            if output:
                render_styled_card(f"📚 Tutorial: {topic}", output)
            else:
                st.warning("Couldn't generate tutorial. Please try again.")
        else:
            st.warning("Please enter a topic.")


def _salary_view():
    _header("💰 Salary Negotiator",
            "Get real-time market data, a counter-offer strategy, and word-for-word negotiation scripts.")

    # Tip banner
    st.markdown("""
    <div style="background:rgba(74,222,128,0.08); border:1px solid rgba(74,222,128,0.3);
                border-radius:12px; padding:14px 18px; margin-bottom:20px;">
        <span style="color:#4ade80; font-weight:600;">💡 Tip:</span>
        <span style="color:#94a3b8; font-size:0.9rem;">
        Fill in as many details as you know — even partial info gives a much stronger report.
        </span>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        job_title    = st.text_input("Job Title *", key="sal_title",
                                     placeholder="Senior Software Engineer, ML Engineer…")
        location     = st.text_input("Location", key="sal_loc",
                                     placeholder="San Francisco, Remote, London…")
        experience   = st.text_input("Years of Experience", key="sal_exp",
                                     placeholder="3, 5, 10+…")
    with col2:
        current_offer  = st.text_input("Their Offer (optional)", key="sal_offer",
                                       placeholder="$140,000 base + $20k signing + 0.1% equity…")
        current_salary = st.text_input("Your Current/Expected Salary (optional)", key="sal_current",
                                       placeholder="$120,000…")
        skills         = st.text_area("Key Strengths / Differentiators", key="sal_skills",
                                      height=80,
                                      value=st.session_state.user_profile.get("skills", ""),
                                      placeholder="Led team of 8, 5 years Kubernetes, open-source contributor…")

    if st.button("💰 Generate Negotiation Playbook", use_container_width=False):
        if job_title:
            with st.spinner("Researching market rates and building your negotiation strategy…"):
                from src.state import make_initial_state
                from src.graph.nodes.salary_negotiator_node import salary_negotiator_node

                sal_state = make_initial_state()
                sal_state["task_input"] = {
                    "job_title":      job_title,
                    "location":       location or "Not specified",
                    "experience":     experience or "Not specified",
                    "current_offer":  current_offer or "Not provided",
                    "current_salary": current_salary or "Not provided",
                    "skills":         skills or st.session_state.user_profile.get("skills", ""),
                }
                sal_state["user_profile"] = dict(st.session_state.user_profile)
                result = salary_negotiator_node(sal_state)

            st.session_state.graph_trace = ["router", "salary_negotiator"]
            output = result.get("agent_output", "")
            if output and not output.startswith("❌"):
                st.success("✅ Negotiation playbook ready!")
                st.divider()
                render_styled_card(f"💰 Salary Negotiation Playbook: {job_title}", output)
            else:
                st.error(output or "Something went wrong. Please try again.")
        else:
            st.warning("Please provide at least the job title.")

    st.divider()
    st.caption("📌 You can also ask salary questions directly in the **Chat Assistant** — the router will detect and route them here automatically.")


def _profile_view():
    _header("👤 Your Profile", "Your career profile is shared across all agents.")

    p = st.session_state.user_profile

    col1, col2 = st.columns(2)
    with col1:
        p["name"]      = st.text_input("Full Name",       value=p.get("name",""),      key="p_name")
        p["job_title"] = st.text_input("Current Title",   value=p.get("job_title",""), key="p_title")
        p["experience"]= st.text_area("Work Experience",  value=p.get("experience",""),height=150, key="p_exp")
    with col2:
        p["skills"]    = st.text_area("Skills",           value=p.get("skills",""),    height=100, key="p_skills")

        if p.get("resume_content"):
            st.markdown("**Saved Resume**")
            with st.expander("View LaTeX Code"):
                st.code(p["resume_content"], language="latex")
            if st.button("🗑️ Clear Saved Resume"):
                p["resume_content"] = ""
                st.rerun()

    st.session_state.user_profile = p

    if st.button("💾 Save Profile"):
        st.success("✅ Profile saved! All agents will use this context.")

    # Graph overview
    st.divider()
    st.subheader("🔗 System Architecture")
    _, mermaid = _load_graph()
    st.code(mermaid, language="text")
    st.caption("This is the live LangGraph topology. Each message flows through the router and is dispatched to the appropriate specialist node.")


# ═══════════════════════════════════════════════════════════════════════════════
# Main entry point
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    _init_session()
    _sidebar_nav()

    mode = st.session_state.active_mode

    if mode == "chat":
        _chat_view()
    elif mode == "resume":
        _resume_view()
    elif mode == "job":
        _job_search_view()
    elif mode == "interview":
        _interview_view()
    elif mode == "tutorials":
        _tutorials_view()
    elif mode == "salary":
        _salary_view()
    elif mode == "profile":
        _profile_view()
    else:
        _chat_view()


if __name__ == "__main__":
    main()
