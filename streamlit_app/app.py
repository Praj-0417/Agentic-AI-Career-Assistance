import streamlit as st
import os

st.set_page_config(
    page_title="career.ai — Command Center",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS for premium glassmorphic dark UI ─────────────────────────────
st.markdown("""
<style>
    /* Dark mode global overrides */
    .stApp {
        background-color: #0d0e15;
        color: #e2e8f0;
    }
    
    /* Premium Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #12131c;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* Navigation custom style */
    .sidebar-header {
        font-size: 1.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #7c3aed, #0ea5e9);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1.5rem;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# ── Sidebar Navigation ────────────────────────────────────────────────────────
st.sidebar.markdown('<div class="sidebar-header">career.ai</div>', unsafe_allow_html=True)

page = st.sidebar.radio(
    "Navigation",
    ["Command Center", "AI Assistant", "Resume Builder", "Job Search", "Interview Prep", "Tech Tutorials", "Salary Coach", "Settings"]
)

# Active page dispatching
if page == "Command Center":
    st.title("⚡ Command Center")
    st.write("Welcome to your production-ready AI career companion.")
elif page == "AI Assistant":
    st.title("🤖 AI Assistant")
    st.write("Chat with the career router agent.")
elif page == "Resume Builder":
    st.title("📄 Resume Builder")
    st.write("Generate tailored LaTeX resumes.")
elif page == "Job Search":
    st.title("🔍 Job Search")
    st.write("Live jobs matching your profile.")
elif page == "Interview Prep":
    st.title("🎯 Interview Prep")
    st.write("Interview guides and mock sessions.")
elif page == "Tech Tutorials":
    st.title("📚 Tech Tutorials")
    st.write("Step-by-step guides on any stack.")
elif page == "Salary Coach":
    st.title("💰 Salary Coach")
    st.write("Compensation benchmarks and script negotiations.")
elif page == "Settings":
    st.title("⚙️ Settings")
    st.write("Configure keys.")
