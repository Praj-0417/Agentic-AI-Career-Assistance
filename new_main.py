import streamlit as st
import os
from dotenv import load_dotenv
from src.orchestrator.agent import OrchestratorAgent

# Load environment variables from .env file
load_dotenv()

# Set up Together API key
together_api_key = os.getenv("TOGETHER_API_KEY")

if not together_api_key:
    # If the API key is not found, display an error message in the app.
    st.error("Together API key not found. Please set it in the .env file.")
else:
    os.environ["TOGETHER_API_KEY"] = together_api_key

def is_latex_resume(text):
    """Check if the given text is a LaTeX resume."""
    if not text:
        return False
    
    text = text.strip()
    
    # Look for LaTeX document class indicators
    latex_indicators = [
        "\\documentclass",
        "\\begin{document}",
        "\\end{document}",
        "\\section",
        "\\resumeItem"
    ]
    
    # Check if at least 3 indicators are present
    count = sum(1 for indicator in latex_indicators if indicator in text)
    return count >= 3

def main():
    """
    Main function to run the AI Career Assistant Streamlit app with chat interface.
    """
    st.set_page_config(page_title="AI Career Assistant", layout="wide")

    # Initialize the orchestrator if it doesn't exist in session state
    if 'orchestrator' not in st.session_state:
        st.session_state.orchestrator = OrchestratorAgent()
    
    # Initialize chat histories for each agent if they don't exist
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    if 'resume_chat_history' not in st.session_state:
        st.session_state.resume_chat_history = []
        
    if 'job_search_chat_history' not in st.session_state:
        st.session_state.job_search_chat_history = []
        
    if 'interview_chat_history' not in st.session_state:
        st.session_state.interview_chat_history = []
        
    if 'tutorials_chat_history' not in st.session_state:
        st.session_state.tutorials_chat_history = []
    
    # Initialize current view if it doesn't exist
    if 'current_view' not in st.session_state:
        st.session_state.current_view = "chat"  # Default to chat view
        
    # Initialize active mode if it doesn't exist
    if 'active_mode' not in st.session_state:
        st.session_state.active_mode = None
    
    # Initialize user profile if it doesn't exist
    if 'user_profile' not in st.session_state:
        st.session_state.user_profile = {
            "name": "",
            "job_title": "",
            "experience": "",
            "skills": "",
            "resume_content": ""
        }
    
    # Fixed sidebar for navigation and user profile (VS Code style)
    with st.sidebar:
        # Logo and app name
        st.title("🚀 AI Career Assistant")
        
        # Navigation section with VS Code style
        st.subheader("Navigation")
        
        # Create a fixed sidebar with icons and clear labels
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.button("💬", key="icon_chat", help="Main Chat")
            st.button("📝", key="icon_resume", help="Resume Builder")
            st.button("🔍", key="icon_job", help="Job Search")
            st.button("🎯", key="icon_interview", help="Interview Prep")
            st.button("📚", key="icon_tutorials", help="Tutorials")
            st.button("👤", key="icon_profile", help="Your Profile")
        
        with col2:
            chat_btn = st.button("Main Chat", key="btn_chat", use_container_width=True)
            resume_btn = st.button("Resume Builder", key="btn_resume", use_container_width=True)
            job_btn = st.button("Job Search", key="btn_job", use_container_width=True)
            interview_btn = st.button("Interview Prep", key="btn_interview", use_container_width=True)
            tutorial_btn = st.button("Tutorials", key="btn_tutorials", use_container_width=True)
            profile_btn = st.button("Your Profile", key="btn_profile", use_container_width=True)
        
        # Handle navigation clicks
        if chat_btn or st.session_state.get("icon_chat", False):
            st.session_state.current_view = "chat"
            st.session_state.active_mode = None
            st.rerun()
        
        if resume_btn or st.session_state.get("icon_resume", False):
            st.session_state.current_view = "chat"
            st.session_state.active_mode = "RESUME_BUILDER"
            st.rerun()
            
        if job_btn or st.session_state.get("icon_job", False):
            st.session_state.current_view = "chat"
            st.session_state.active_mode = "JOB_SEARCH"
            st.rerun()
            
        if interview_btn or st.session_state.get("icon_interview", False):
            st.session_state.current_view = "chat"
            st.session_state.active_mode = "INTERVIEW_PREP"
            st.rerun()
            
        if tutorial_btn or st.session_state.get("icon_tutorials", False):
            st.session_state.current_view = "chat"
            st.session_state.active_mode = "TUTORIALS"
            st.rerun()
            
        if profile_btn or st.session_state.get("icon_profile", False):
            st.session_state.current_view = "profile"
            st.rerun()
        
        # Divider
        st.divider()
        
        # History navigation
        st.subheader("History")
        if st.button("📝 Resume History", key="history_resume"):
            st.session_state.current_view = "resume_history"
            st.rerun()
            
        if st.button("🔍 Job Search History", key="history_job"):
            st.session_state.current_view = "job_search_history"
            st.rerun()
            
        if st.button("🎯 Interview History", key="history_interview"):
            st.session_state.current_view = "interview_prep_history"
            st.rerun()
            
        if st.button("📚 Tutorials History", key="history_tutorials"):
            st.session_state.current_view = "tutorials_history"
            st.rerun()
        
        # Divider
        st.divider()
        
        # About section
        with st.expander("ℹ️ About", expanded=False):
            st.write("""
            AI Career Assistant helps you with:
            - Building professional resumes
            - Finding job opportunities
            - Preparing for interviews
            - Learning new skills
            """)
        
        # Clear chat button at the bottom
        st.button("🗑️ Clear All Chats", key="clear_chat", on_click=lambda: st.session_state.update({
            "chat_history": [],
            "resume_chat_history": [],
            "job_search_chat_history": [],
            "interview_chat_history": [],
            "tutorials_chat_history": []
        }))
    
    # Main content area
    if st.session_state.current_view == "chat":
        # Show active mode if any
        if st.session_state.active_mode:
            mode_labels = {
                "RESUME_BUILDER": "Resume Builder Mode",
                "JOB_SEARCH": "Job Search Mode",
                "INTERVIEW_PREP": "Interview Prep Mode",
                "TUTORIALS": "Tutorials Mode"
            }
            mode_label = mode_labels.get(st.session_state.active_mode, "")
            
            # Display active mode with option to exit
            col1, col2 = st.columns([10, 2])
            with col1:
                st.info(f"🔵 Active: {mode_label}")
            with col2:
                if st.button("Exit Mode", key="exit_mode"):
                    st.session_state.active_mode = None
                    st.rerun()
        
        # Display appropriate heading based on mode
        if st.session_state.active_mode:
            mode_headings = {
                "RESUME_BUILDER": "Resume Builder",
                "JOB_SEARCH": "Job Search Assistant",
                "INTERVIEW_PREP": "Interview Preparation",
                "TUTORIALS": "Learning & Tutorials"
            }
            st.header(mode_headings.get(st.session_state.active_mode, "Chat with AI Career Assistant"))
        else:
            st.header("Chat with AI Career Assistant")
        
        # Create a container for input fields that will stay fixed at the top
        input_container = st.container()
        
        # Create a container for chat history that will scroll
        chat_container = st.container()
        
        # Mode-specific instructions and input fields in the fixed top container
        with input_container:
            if st.session_state.active_mode == "RESUME_BUILDER":
                st.write("Ask me to create a resume, improve your existing resume, or tailor it to a specific job description.")
                
                # Add fields for resume builder
                col1, col2 = st.columns(2)
                
                with col1:
                    # Add job description field (required)
                    if "job_description" not in st.session_state:
                        st.session_state.job_description = ""
                    st.session_state.job_description = st.text_area("Job Description (Required)", 
                                                      st.session_state.job_description,
                                                      height=100,
                                                      help="Paste a job description to tailor your resume to this role")
                
                with col2:
                    # Add user details field (required)
                    user_details_help = "Enter information about your experience, skills, and background"
                    
                    # Use profile information if available
                    prefilled_details = ""
                    if st.session_state.user_profile.get("name"):
                        prefilled_details += f"Name: {st.session_state.user_profile.get('name')}\n"
                    if st.session_state.user_profile.get("job_title"):
                        prefilled_details += f"Target Job Title: {st.session_state.user_profile.get('job_title')}\n"
                    if st.session_state.user_profile.get("experience"):
                        prefilled_details += f"Experience: {st.session_state.user_profile.get('experience')}\n"
                    if st.session_state.user_profile.get("skills"):
                        prefilled_details += f"Skills: {st.session_state.user_profile.get('skills')}\n"
                    
                    # Initialize the user_details if not already in session state
                    if "user_details" not in st.session_state:
                        st.session_state.user_details = prefilled_details
                    
                    # Add the text area with prefilled or previously entered content
                    st.session_state.user_details = st.text_area("Your Details (Required)", 
                                                    st.session_state.user_details,
                                                    height=100,
                                                    help=user_details_help)
                
                # Add previous resume content field (optional)
                if "previous_resume" not in st.session_state:
                    # If we have a resume in the profile, use it
                    st.session_state.previous_resume = st.session_state.user_profile.get("resume_content", "")
                
                # Only show this if we have a previous resume or if they check a checkbox to show it
                if "show_previous_resume" not in st.session_state:
                    st.session_state.show_previous_resume = bool(st.session_state.previous_resume)
                
                st.session_state.show_previous_resume = st.checkbox("I want to improve an existing resume", 
                                                       value=st.session_state.show_previous_resume)
                
                if st.session_state.show_previous_resume:
                    st.session_state.previous_resume = st.text_area("Previous Resume (LaTeX or plain text)", 
                                                      st.session_state.previous_resume,
                                                      height=150,
                                                      help="Paste your existing resume if you want to improve it")
            elif st.session_state.active_mode == "JOB_SEARCH":
                st.write("Ask me to find job opportunities, provide application advice, or offer career guidance.")
                
                # Add fields for job search
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    # Add job title field for job search
                    if "job_title_search" not in st.session_state:
                        st.session_state.job_title_search = ""
                    st.session_state.job_title_search = st.text_input("Job Title (Required)", 
                                                        st.session_state.job_title_search,
                                                        help="Enter the job title you're searching for")
                
                with col2:
                    # Add location field for job search
                    if "job_location" not in st.session_state:
                        st.session_state.job_location = ""
                    st.session_state.job_location = st.text_input("Location (Required)", 
                                                      st.session_state.job_location,
                                                      help="Enter a city, state, or 'Remote'")
                
                with col3:
                    # Add job type field
                    if "job_type" not in st.session_state:
                        st.session_state.job_type = "Full-time"
                    st.session_state.job_type = st.selectbox("Job Type", 
                                                   ["Full-time", "Part-time", "Contract", "Internship"],
                                                   index=0)
            elif st.session_state.active_mode == "INTERVIEW_PREP":
                st.write("Ask me for interview preparation, request a mock interview, or get post-interview feedback.")
                
                # Initialize interview mode if not exists
                if "interview_mode" not in st.session_state:
                    st.session_state.interview_mode = "prep"
                    
                # Add interview mode selection
                st.session_state.interview_mode = st.radio(
                    "Interview Mode",
                    ["Preparation Guide", "Mock Interview", "Interview Evaluation"],
                    horizontal=True,
                    index=0 if st.session_state.interview_mode == "prep" else 
                          1 if st.session_state.interview_mode == "mock" else 2
                )
                
                # Map the radio selection to the agent mode
                if st.session_state.interview_mode == "Preparation Guide":
                    st.session_state.interview_agent_mode = "INTERVIEW_PREP"
                elif st.session_state.interview_mode == "Mock Interview":
                    st.session_state.interview_agent_mode = "INTERVIEW_MOCK"
                else:
                    st.session_state.interview_agent_mode = "INTERVIEW_EVALUATE"
                
                # Add job title field for interview prep
                col1, col2 = st.columns(2)
                
                with col1:
                    if "interview_job_title" not in st.session_state:
                        st.session_state.interview_job_title = ""
                    st.session_state.interview_job_title = st.text_input("Job Title for Interview (Required)", 
                                                           st.session_state.interview_job_title,
                                                           help="Enter the job title you're interviewing for")
                
                # Initialize interview history if not exists
                if "interview_history" not in st.session_state:
                    st.session_state.interview_history = []
            elif st.session_state.active_mode == "TUTORIALS":
                st.write("Ask me to create learning resources or tutorials on any technical topic.")
            else:
                st.write("Ask me anything about resumes, job search, interview prep, or learning resources!")
            
            # Add a divider to separate input fields from chat
            st.divider()
        
        # Display chat history based on active mode
        with chat_container:
            # Get the appropriate chat history based on active mode
            current_history_key = "chat_history"  # Default general chat
            
            if st.session_state.active_mode == "RESUME_BUILDER":
                current_history_key = "resume_chat_history"
            elif st.session_state.active_mode == "JOB_SEARCH":
                current_history_key = "job_search_chat_history"
            elif st.session_state.active_mode == "INTERVIEW_PREP":
                current_history_key = "interview_chat_history"
            elif st.session_state.active_mode == "TUTORIALS":
                current_history_key = "tutorials_chat_history"
            
            # Display the current history
            for message in st.session_state[current_history_key]:
                if message["role"] == "user":
                    st.chat_message("user").write(message["content"])
                else:
                    st.chat_message("assistant").markdown(message["content"])
        
        # Chat input
        user_input = st.chat_input("Type your message here...")
        if user_input:
            # If in a specific mode, validate required fields
            if st.session_state.active_mode == "RESUME_BUILDER":
                if not st.session_state.job_description:
                    st.error("Please provide a job description before submitting your request.")
                    st.stop()
                if not st.session_state.user_details:
                    st.error("Please provide your details before submitting your request.")
                    st.stop()
            
            elif st.session_state.active_mode == "JOB_SEARCH":
                if not st.session_state.job_title_search:
                    st.error("Please provide a job title for your search.")
                    st.stop()
                if not st.session_state.job_location:
                    st.error("Please provide a location for your job search.")
                    st.stop()
            
            elif st.session_state.active_mode == "INTERVIEW_PREP":
                if not st.session_state.interview_job_title:
                    st.error("Please provide a job title for your interview preparation.")
                    st.stop()

            # Display user message
            st.chat_message("user").write(user_input)
            
            # Add user message to the main chat history to have a complete record
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            
            # If in a specific mode, also add to that history
            if st.session_state.active_mode:
                st.session_state[current_history_key].append({"role": "user", "content": user_input})

            # Process the message using the orchestrator
            with st.spinner("Thinking..."):
                # Get additional context from session state
                additional_context = {
                    "job_title": st.session_state.user_profile.get("job_title", ""),
                    "user_name": st.session_state.user_profile.get("name", ""),
                    "user_experience": st.session_state.user_profile.get("experience", ""),
                    "user_context": st.session_state.user_profile.get("skills", ""),
                    "history": st.session_state.chat_history # Pass the main chat history
                }
                
                # Add specific context for different modes
                if st.session_state.active_mode == "RESUME_BUILDER":
                    additional_context["user_details"] = st.session_state.user_details
                    additional_context["job_description"] = st.session_state.job_description
                    if st.session_state.get("previous_resume"):
                        additional_context["previous_resume"] = st.session_state.previous_resume
                        
                elif st.session_state.active_mode == "JOB_SEARCH":
                    additional_context["job_title"] = st.session_state.job_title_search
                    additional_context["location"] = st.session_state.job_location
                    additional_context["job_type"] = st.session_state.job_type
                    
                elif st.session_state.active_mode == "INTERVIEW_PREP":
                    additional_context["job_title"] = st.session_state.interview_job_title
                    additional_context["interview_mode"] = st.session_state.get("interview_agent_mode", "INTERVIEW_PREP")

                # Determine agent type
                agent_type = st.session_state.active_mode  # Can be None if in main chat

                # Call the orchestrator
                response = st.session_state.orchestrator.invoke(
                    user_input,
                    agent_type=agent_type,
                    additional_context=additional_context
                )
                
                # Extract the agent's response and the classified agent type
                agent_response = response.get("output", "Sorry, I encountered an error.")
                classified_agent = response.get("agent_type", st.session_state.active_mode)

                # If the orchestrator classified the intent, update the history
                if classified_agent and classified_agent != "ORCHESTRATOR":
                    history_map = {
                        "RESUME_BUILDER": "resume_chat_history",
                        "JOB_SEARCH": "job_search_chat_history",
                        "INTERVIEW_PREP": "interview_chat_history",
                        "TUTORIALS": "tutorials_chat_history"
                    }
                    classified_history_key = history_map.get(classified_agent)
                    
                    # Add assistant response to the correct history
                    if classified_history_key:
                        # Add user message if not already there
                        if not any(m["role"] == "user" and m["content"] == user_input for m in st.session_state[classified_history_key]):
                            st.session_state[classified_history_key].append({"role": "user", "content": user_input})
                        st.session_state[classified_history_key].append({"role": "assistant", "content": agent_response})

                # Add assistant response to main history
                st.session_state.chat_history.append({"role": "assistant", "content": agent_response})
                
                # Display the response
                st.chat_message("assistant").markdown(agent_response)
                
                # Rerun to update the chat display
                st.rerun()

    elif st.session_state.current_view == "profile":
        st.header("Your Profile")
        st.write("Update your profile to get more personalized assistance for all modes.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.session_state.user_profile["name"] = st.text_input("Your Name", st.session_state.user_profile["name"])
            st.session_state.user_profile["job_title"] = st.text_input("Target Job Title", st.session_state.user_profile["job_title"])
        
        with col2:
            st.subheader("This information helps personalize:")
            st.write("- Resume Builder: Formats your experience appropriately")
            st.write("- Job Search: Finds relevant opportunities")
            st.write("- Interview Prep: Creates targeted practice questions")
            st.write("- Tutorials: Recommends resources at your level")
        
        # Experience section
        st.subheader("Your Experience")
        st.write("Include your work history, education, and relevant achievements. The more detail you provide, the better your results will be.")
        st.session_state.user_profile["experience"] = st.text_area("Work & Education Experience", st.session_state.user_profile["experience"], height=150)
        
        # Skills section
        st.subheader("Your Skills")
        st.write("List your technical and soft skills, programming languages, tools, and other relevant abilities.")
        st.session_state.user_profile["skills"] = st.text_area("Skills & Technologies", st.session_state.user_profile["skills"], height=150)
        
        # Update the orchestrator's shared context with the profile info
        if st.button("Save Profile"):
            for key, value in st.session_state.user_profile.items():
                st.session_state.orchestrator.update_user_profile(key, value)
            st.success("Profile updated! This information will be used to personalize all your interactions.")
            
        # Button to return to chat
        if st.button("Return to Chat"):
            st.session_state.current_view = "chat"
            st.rerun()
    
    else:
        # Display history for the selected view
        category = st.session_state.current_view.replace("_history", "")
        
        if category == "resume":
            st.header("Resume Builder History")
            history_to_display = st.session_state.resume_chat_history
        elif category == "job_search":
            st.header("Job Search History")
            history_to_display = st.session_state.job_search_chat_history
        elif category == "interview_prep":
            st.header("Interview Prep History")
            history_to_display = st.session_state.interview_chat_history
        elif category == "tutorials":
            st.header("Tutorials History")
            history_to_display = st.session_state.tutorials_chat_history
        
        # Display the chat history from session state
        if not history_to_display:
            st.info(f"No {category.replace('_', ' ')} history yet.")
        else:
            for i, message in enumerate(history_to_display):
                if message["role"] == "user":
                    with st.chat_message("user"):
                        st.write(message["content"])
                else:
                    with st.chat_message("assistant"):
                        st.markdown(message["content"])
        
        # Button to return to chat
        if st.button("Return to Chat"):
            st.session_state.current_view = "chat"
            st.rerun()

if __name__ == "__main__":
    main()
