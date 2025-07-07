import streamlit as st
import os
from dotenv import load_dotenv
from src.orchestrator.agent import OrchestratorAgent

# Load environment variables
load_dotenv()
together_api_key = os.getenv("TOGETHER_API_KEY")

if not together_api_key:
    st.error("Together API key not found. Please set it in the .env file.")
else:
    os.environ["TOGETHER_API_KEY"] = together_api_key

def is_latex_resume(text):
    if not text:
        return False
    text = text.strip()
    indicators = ["\\documentclass", "\\begin{document}", "\\end{document}", "\\section", "\\resumeItem"]
    return sum(1 for i in indicators if i in text) >= 3

# Helper to select the chat history
def get_chat_history_key():
    return {
        "RESUME_BUILDER": "resume_chat_history",
        "JOB_SEARCH": "job_search_chat_history",
        "INTERVIEW_PREP": "interview_chat_history",
        "TUTORIALS": "tutorials_chat_history"
    }.get(st.session_state.active_mode, "chat_history")

def main():
    st.set_page_config(page_title="AI Career Assistant", layout="wide")

    if "orchestrator" not in st.session_state:
        st.session_state.orchestrator = OrchestratorAgent()

    # Initialize state
    for key in ["chat_history", "resume_chat_history", "job_search_chat_history",
                "interview_chat_history", "tutorials_chat_history"]:
        st.session_state.setdefault(key, [])

    st.session_state.setdefault("current_view", "chat")
    st.session_state.setdefault("active_mode", None)
    st.session_state.setdefault("user_profile", {
        "name": "", "job_title": "", "experience": "", "skills": "", "resume_content": ""
    })

    with st.sidebar:
        st.title("🚀 AI Career Assistant")
        st.subheader("Navigation")
        col1, col2 = st.columns([1, 3])
        with col1:
            st.button("💬", key="icon_chat", help="Main Chat")
            st.button("📝", key="icon_resume", help="Resume Builder")
            st.button("🔍", key="icon_job", help="Job Search")
            st.button("🎯", key="icon_interview", help="Interview Prep")
            st.button("📚", key="icon_tutorials", help="Tutorials")
            st.button("👤", key="icon_profile", help="Your Profile")
        with col2:
            if st.button("Main Chat", key="btn_chat"): st.session_state.current_view, st.session_state.active_mode = "chat", None; st.rerun()
            if st.button("Resume Builder", key="btn_resume"): st.session_state.current_view, st.session_state.active_mode = "chat", "RESUME_BUILDER"; st.rerun()
            if st.button("Job Search", key="btn_job"): st.session_state.current_view, st.session_state.active_mode = "chat", "JOB_SEARCH"; st.rerun()
            if st.button("Interview Prep", key="btn_interview"): st.session_state.current_view, st.session_state.active_mode = "chat", "INTERVIEW_PREP"; st.rerun()
            if st.button("Tutorials", key="btn_tutorials"): st.session_state.current_view, st.session_state.active_mode = "chat", "TUTORIALS"; st.rerun()
            if st.button("Your Profile", key="btn_profile"): st.session_state.current_view = "profile"; st.rerun()

        st.divider()
        st.subheader("History")
        if st.button("📝 Resume History", key="history_resume"): st.session_state.current_view = "resume_history"; st.rerun()
        if st.button("🔍 Job Search History", key="history_job"): st.session_state.current_view = "job_search_history"; st.rerun()
        if st.button("🎯 Interview History", key="history_interview"): st.session_state.current_view = "interview_prep_history"; st.rerun()
        if st.button("📚 Tutorials History", key="history_tutorials"): st.session_state.current_view = "tutorials_history"; st.rerun()

        st.divider()
        with st.expander("ℹ️ About"):
            st.write("Helps with:\n- Resume building\n- Job search\n- Interview prep\n- Learning")

        st.button("🗑️ Clear All Chats", key="clear_chat", on_click=lambda: [
            st.session_state.update({k: [] for k in ["chat_history", "resume_chat_history", "job_search_chat_history",
                                                     "interview_chat_history", "tutorials_chat_history"]})
        ])

    # ========== MAIN CHAT ==========
    if st.session_state.current_view == "chat":
        current_history_key = get_chat_history_key()

        if st.session_state.active_mode:
            st.info(f"🔵 Active: {st.session_state.active_mode.replace('_', ' ').title()}")
            if st.button("Exit Mode", key="exit_mode"): st.session_state.active_mode = None; st.rerun()

        st.header("Chat with AI Career Assistant")

        for message in st.session_state[current_history_key]:
            st.chat_message("user" if message["role"] == "user" else "assistant").markdown(message["content"])

        user_input = st.chat_input("Type your message here...")
        if user_input:
            st.chat_message("user").write(user_input)
            st.session_state[current_history_key].append({"role": "user", "content": user_input})
            st.session_state.chat_history.append({"role": "user", "content": user_input})

            # ✅ Sync latest profile into orchestrator before processing
            for k, v in st.session_state.user_profile.items():
                st.session_state.orchestrator.update_user_profile(k, v)

            # ✅ Compose context based on active mode
            additional_context = {
                "job_title": st.session_state.user_profile.get("job_title", ""),
                "user_name": st.session_state.user_profile.get("name", ""),
                "user_experience": st.session_state.user_profile.get("experience", ""),
                "user_context": st.session_state.user_profile.get("skills", ""),
                "history": st.session_state.chat_history,
            }

            # Add mode-specific info
            if st.session_state.active_mode == "RESUME_BUILDER":
                additional_context.update({
                    "user_details": st.session_state.get("user_details", ""),
                    "job_description": st.session_state.get("job_description", ""),
                    "previous_resume": st.session_state.get("previous_resume", ""),
                })
            elif st.session_state.active_mode == "JOB_SEARCH":
                additional_context.update({
                    "job_title": st.session_state.get("job_title_search", ""),
                    "location": st.session_state.get("job_location", ""),
                    "job_type": st.session_state.get("job_type", ""),
                })
            elif st.session_state.active_mode == "INTERVIEW_PREP":
                additional_context.update({
                    "job_title": st.session_state.get("interview_job_title", ""),
                    "interview_mode": st.session_state.get("interview_agent_mode", "INTERVIEW_PREP")
                })

            with st.spinner("Thinking..."):
                response = st.session_state.orchestrator.process_message(
                    user_input,
                    agent_type=st.session_state.active_mode,
                    **additional_context
                )

            assistant_reply = response.get("output", "Sorry, I encountered an error.")
            classified_agent = response.get("agent_type", st.session_state.active_mode)

            # ✅ Save in appropriate history
            history_key = get_chat_history_key()
            st.session_state[history_key].append({"role": "assistant", "content": assistant_reply})
            st.session_state.chat_history.append({"role": "assistant", "content": assistant_reply})

            st.chat_message("assistant").markdown(assistant_reply)
            st.rerun()

    # ========== PROFILE TAB ==========
    elif st.session_state.current_view == "profile":
        st.header("Your Profile")
        col1, col2 = st.columns(2)
        with col1:
            st.session_state.user_profile["name"] = st.text_input("Your Name", st.session_state.user_profile["name"])
            st.session_state.user_profile["job_title"] = st.text_input("Target Job Title", st.session_state.user_profile["job_title"])
        with col2:
            st.subheader("Personalize your experience")

        st.subheader("Experience")
        st.session_state.user_profile["experience"] = st.text_area("Work & Education", st.session_state.user_profile["experience"], height=150)

        st.subheader("Skills")
        st.session_state.user_profile["skills"] = st.text_area("Skills & Tools", st.session_state.user_profile["skills"], height=150)

        if st.button("Save Profile"):
            for key, value in st.session_state.user_profile.items():
                st.session_state.orchestrator.update_user_profile(key, value)
            st.success("Profile updated!")

        if st.button("Return to Chat"):
            st.session_state.current_view = "chat"
            st.rerun()

    # ========== HISTORY VIEWS ==========
    else:
        category = st.session_state.current_view.replace("_history", "")
        st.header(f"{category.replace('_', ' ').title()} History")
        history_map = {
            "resume": st.session_state.resume_chat_history,
            "job_search": st.session_state.job_search_chat_history,
            "interview_prep": st.session_state.interview_chat_history,
            "tutorials": st.session_state.tutorials_chat_history
        }
        history = history_map.get(category, [])
        if not history:
            st.info(f"No {category} history yet.")
        else:
            for msg in history:
                with st.chat_message(msg["role"]): st.markdown(msg["content"])
        if st.button("Return to Chat"):
            st.session_state.current_view = "chat"
            st.rerun()

if __name__ == "__main__":
    main()
