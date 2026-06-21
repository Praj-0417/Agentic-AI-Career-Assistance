import streamlit as st
import os
from dotenv import load_dotenv
from src.orchestrator.agent import OrchestratorAgent
# Import specialized agents
from src.guidance.agent import get_qa_bot, get_tutorial_agent
from src.resume_builder.agent import get_resume_builder_agent, get_resume_refinement_agent
from src.interview_prep.agent import get_interview_prep_agent
from src.qna.agent import get_job_search_agent
from src.tutorials.agent import get_tutorials_agent

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
                # Initialize resume-related session state variables
                if "job_description" not in st.session_state:
                    st.session_state.job_description = ""
                if "resume_user_details" not in st.session_state:
                    st.session_state.resume_user_details = st.session_state.user_profile.get("experience", "") + "\n" + st.session_state.user_profile.get("skills", "")
                if "generated_resume" not in st.session_state:
                    st.session_state.generated_resume = st.session_state.user_profile.get("resume_content", "")
                
                # For Resume Builder, LaTeX is the only option now
                if "resume_builder_mode" not in st.session_state:
                    st.session_state.resume_builder_mode = "LaTeX Resume Builder"
                
                # Import the direct resume builder agents
                from src.resume_builder.agent import get_resume_builder_agent, get_resume_refinement_agent
                
                st.subheader("1. Target Job Description")
                job_desc_input = st.text_area(
                    "Paste the job description here:", 
                    height=150,
                    key="job_desc_input",
                    value=st.session_state.job_description
                )
                st.session_state.job_description = job_desc_input
                
                st.subheader("2. Your Details")
                user_details = st.text_area(
                    "Paste your current resume, or list your experience, skills, and projects:", 
                    height=150, 
                    key="user_details_input",
                    value=st.session_state.resume_user_details
                )
                st.session_state.resume_user_details = user_details
                    
                if st.button("Generate LaTeX Resume", key="latex_resume_button"):
                    if st.session_state.job_description and st.session_state.resume_user_details:
                        with st.spinner("Generating your tailored LaTeX resume..."):
                            agent = get_resume_builder_agent()
                            try:
                                result = agent.invoke({
                                    "job_description": st.session_state.job_description, 
                                    "resume_user_details": st.session_state.resume_user_details
                                })
                                
                                if isinstance(result, dict) and 'resume' in result:
                                    st.session_state.generated_resume = result['resume']
                                    # Save to user profile as well
                                    st.session_state.orchestrator.update_user_profile("resume_content", result['resume'])
                                    st.session_state.resume_chat_history = [{
                                        "role": "assistant", 
                                        "content": "Here is the LaTeX code for your resume. You can now ask for modifications below. For example: 'Add a new project called...'"
                                    }]
                                    st.rerun()
                                else:
                                    st.error("Sorry, there was an error generating the resume.")
                                    st.write(f"Error details: {result}")
                            except Exception as e:
                                st.error(f"An error occurred: {str(e)}")
                    else:
                        st.warning("Please provide both the job description and your details.")
                    
                # Display the generated resume and refinement interface
                if "generated_resume" in st.session_state and st.session_state.generated_resume:
                    st.subheader("3. Your Generated LaTeX Resume")
                    st.info("Copy the code below and paste it into a LaTeX editor (like Overleaf) to compile your PDF.")
                    st.code(st.session_state.generated_resume, language="latex")
                    
                    st.subheader("4. Refine Your Resume")
                    st.write("Need to make changes? Enter your refinement request below.")
                    
                    # Direct interface for refinement (no chat)
                    refinement_request = st.text_area(
                        "Describe the changes you want to make:",
                        placeholder="E.g., Add a new project called 'AI Career Assistant', change the summary to focus more on leadership, etc.",
                        key="refinement_request",
                        height=100
                    )
                    
                    if st.button("Apply Changes", key="apply_refinement"):
                        if refinement_request:
                            with st.spinner("Editing your LaTeX resume..."):
                                refinement_agent = get_resume_refinement_agent()
                                try:
                                    response = refinement_agent.invoke({
                                        "job_description": st.session_state.job_description,
                                        "previous_resume": st.session_state.generated_resume,
                                        "user_request": refinement_request
                                    })
                                    
                                    if isinstance(response, dict) and 'resume' in response:
                                        # Update the resume and save to user profile
                                        st.session_state.generated_resume = response['resume']
                                        st.session_state.orchestrator.update_user_profile("resume_content", response['resume'])
                                        st.success("✅ Resume updated successfully!")
                                        st.rerun()
                                    else:
                                        st.error(f"Sorry, I couldn't make that change. Please try rephrasing your request. Error: {response}")
                                except Exception as e:
                                    st.error(f"An error occurred during refinement: {str(e)}")
                        else:
                            st.warning("Please describe the changes you want to make.")
                    
                    # Display refinement history
                    if "resume_refinement_history" not in st.session_state:
                        st.session_state.resume_refinement_history = []
                    
                    if st.session_state.resume_refinement_history:
                        st.subheader("Refinement History")
                        if st.button("Clear Refinement History"):
                            st.session_state.resume_refinement_history = []
                            st.rerun()
                        
                        for i, entry in enumerate(reversed(st.session_state.resume_refinement_history)):
                            with st.expander(f"**{i+1}. {entry['request']}**", expanded=False):
                                st.markdown(entry['result'])
                                if st.button("Delete", key=f"delete_refine_{i}"):
                                    st.session_state.resume_refinement_history.pop(len(st.session_state.resume_refinement_history) - 1 - i)
                                    st.rerun()
                else:
                    # For conversational mode, show the previous resume field (optional)
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
                st.write("Find relevant job opportunities based on your profile.")
                
                # Import the direct job search agent
                from src.qna.agent import get_job_search_agent
                
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
                
                # Add user context field
                if "user_context" not in st.session_state:
                    st.session_state.user_context = st.session_state.user_profile.get("skills", "")
                
                st.session_state.user_context = st.text_area(
                    "To personalize your search, briefly describe your skills, experience, and what you're looking for:",
                    st.session_state.user_context,
                    height=100,
                    help="Enter skills, experience, or other details to personalize your job search"
                )
                    
                if st.button("Search for Jobs", key="direct_job_search"):
                    if st.session_state.job_title_search and st.session_state.job_location:
                        with st.spinner("Searching for jobs..."):
                            agent = get_job_search_agent()
                            result = agent.invoke({
                                "job_title": st.session_state.job_title_search,
                                "location": st.session_state.job_location,
                                "job_type": st.session_state.job_type,
                                "user_context": st.session_state.user_context
                            })
                            
                            output = result.get('output', f"Error: Could not find jobs matching your criteria.")
                            
                            # Store in history and display
                            if "job_search_direct_history" not in st.session_state:
                                st.session_state.job_search_direct_history = []
                            
                            st.session_state.job_search_direct_history.append({
                                "query": f"{st.session_state.job_type} jobs for {st.session_state.job_title_search} in {st.session_state.job_location}",
                                "result": output
                            })
                            
                            # Display results
                            st.subheader("Job Search Results")
                            st.markdown(output)
                    else:
                        st.warning("Please provide both a job title and a location.")
                
                # Display job search history
                if "job_search_direct_history" in st.session_state and st.session_state.job_search_direct_history:
                    st.subheader("Job Search Results")
                    if st.button("Clear Job Search History"):
                        st.session_state.job_search_direct_history = []
                        st.rerun()
                    
                    for i, entry in enumerate(reversed(st.session_state.job_search_direct_history)):
                        with st.expander(f"**{i+1}. {entry['query']}**", expanded=True):
                            st.markdown(entry['result'])
                            if st.button("Delete", key=f"delete_job_{i}"):
                                st.session_state.job_search_direct_history.pop(len(st.session_state.job_search_direct_history) - 1 - i)
                                st.rerun()
            elif st.session_state.active_mode == "INTERVIEW_PREP":
                st.write("Ask me for interview preparation, request a mock interview, or get post-interview feedback.")
                
                # Initialize interview-related session state variables
                if "interview_job_title" not in st.session_state:
                    st.session_state.interview_job_title = ""
                if "interview_experience" not in st.session_state:
                    st.session_state.interview_experience = ""
                
                # Create input fields for job title and experience
                job_title = st.text_input(
                    "Job Title You're Interviewing For (Required)",
                    value=st.session_state.interview_job_title,
                    key="interview_job_title_input",
                    help="Enter the exact job title you're interviewing for"
                )
                st.session_state.interview_job_title = job_title
                
                experience = st.text_area(
                    "Your Relevant Experience",
                    value=st.session_state.interview_experience,
                    key="interview_experience_input",
                    height=100,
                    help="Enter a brief summary of your experience relevant to this role"
                )
                st.session_state.interview_experience = experience
                
                # Add interview mode selection if not exists
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
                
                if st.session_state.interview_mode == "Preparation Guide":
                    st.session_state.interview_agent_mode = "INTERVIEW_PREP"
                    
                    # Add a clean, direct interface for the preparation guide matching main.py
                    st.subheader("Interview Preparation Guide")
                    st.write("Get ready to ace your next interview with personalized preparation tips.")
                    
                    # Import the interview prep agent directly to simplify the flow
                    from src.interview_prep.agent import get_interview_prep_agent
                    
                    # User can enter their specific query here
                    prep_query = st.text_input(
                        "What specific interview advice do you need?", 
                        placeholder="E.g., 'Common questions for this role', 'How to answer behavioral questions', etc.",
                        key="prep_query"
                    )
                    
                    if st.button("Generate Prep Guide", key="prep_guide_button"):
                        if st.session_state.interview_job_title:
                            with st.spinner("Generating your interview prep guide... This may take a moment."):
                                agent = get_interview_prep_agent()
                                result = agent.invoke({
                                    "job_title": st.session_state.interview_job_title,
                                    "user_experience": st.session_state.interview_experience,
                                    "user_name": st.session_state.user_profile.get("name", "Candidate"),
                                    "input": prep_query or f"Comprehensive interview preparation guide for {st.session_state.interview_job_title}"
                                })
                                
                                output = result.get('output', "Sorry, I couldn't generate the interview guide.")
                                
                                # Store in history
                                if "interview_prep_history" not in st.session_state:
                                    st.session_state.interview_prep_history = []
                                
                                st.session_state.interview_prep_history.append({
                                    "query": f"Prep Guide for {st.session_state.interview_job_title}: {prep_query if prep_query else 'Comprehensive guide'}",
                                    "result": output
                                })
                                
                                # Display the guide
                                st.subheader(f"Interview Guide: {st.session_state.interview_job_title}")
                                st.markdown(output)
                        else:
                            st.warning("Please provide the job title you're interviewing for.")
                    
                    # Display interview prep history
                    if "interview_prep_history" in st.session_state and st.session_state.interview_prep_history:
                        st.subheader("Your Interview Prep Guides")
                        if st.button("Clear Prep Guide History"):
                            st.session_state.interview_prep_history = []
                            st.rerun()
                        
                        for i, entry in enumerate(reversed(st.session_state.interview_prep_history)):
                            with st.expander(f"**{i+1}. {entry['query']}**", expanded=i==0):
                                st.markdown(entry['result'])
                                if st.button("Delete", key=f"delete_prep_{i}"):
                                    st.session_state.interview_prep_history.pop(len(st.session_state.interview_prep_history) - 1 - i)
                                    st.rerun()
                
                elif st.session_state.interview_mode == "Mock Interview":
                    st.session_state.interview_agent_mode = "INTERVIEW_MOCK"
                    
                    # Always use direct interview mode - no chat-based interviews
                    st.session_state.direct_interview_mode = True
                    
                    # Import directly to simplify flow
                    from src.interview_prep.agent import get_interview_prep_agent
                    
                    # Initialize direct mock interview session state
                    if 'mock_interview_history' not in st.session_state:
                        st.session_state.mock_interview_history = []
                    if 'mock_interview_started' not in st.session_state:
                        st.session_state.mock_interview_started = False
                    if 'interview_evaluation' not in st.session_state:
                        st.session_state.interview_evaluation = None
                    
                    # Check if we have the required interview job title
                    if not st.session_state.interview_job_title:
                        st.warning("Please provide a job title at the top of this page before starting a mock interview.")
                    
                    # Display the evaluation if we have one
                    if st.session_state.interview_evaluation:
                        st.subheader("Your Interview Evaluation")
                        st.info("This evaluation is based on your performance in the mock interview. Use this feedback to improve your interview skills.")
                        st.markdown(st.session_state.interview_evaluation)
                        
                        if st.button("Clear Evaluation & Start New Interview", key="clear_evaluation"):
                            st.session_state.interview_evaluation = None
                            st.session_state.mock_interview_started = False
                            st.session_state.mock_interview_history = []
                            st.rerun()
                    elif not st.session_state.mock_interview_started:
                        st.info("You are about to start a mock interview. The AI will ask you questions one by one. Answer as you would in a real interview!")
                        start_mock = st.button("Start Mock Interview", key="start_mock_direct")
                        
                        if start_mock:
                            if not st.session_state.interview_job_title:
                                st.error("Please provide the job title for your interview at the top of this page.")
                            else:
                                st.session_state.mock_interview_history = []
                                st.session_state.mock_interview_started = True
                                
                                # Add system message to start the interview
                                st.session_state.mock_interview_history.append({
                                    "role": "system",
                                    "content": f"You are interviewing {st.session_state.user_profile.get('name', 'a candidate')} for the role of {st.session_state.interview_job_title}. The candidate has this experience: {st.session_state.interview_experience}. Begin the interview with a brief introduction and your first question."
                                })
                                
                                # Get first interviewer message
                                with st.spinner("Starting the interview..."):
                                    agent = get_interview_prep_agent(mock=True)
                                    response = agent.invoke({
                                        "job_title": st.session_state.interview_job_title,
                                        "user_experience": st.session_state.interview_experience,
                                        "user_name": st.session_state.user_profile.get("name", "Candidate"),
                                        "history": st.session_state.mock_interview_history
                                    })
                                    ai_reply = response.get('output', "Hello! I'm your interviewer today. Let's begin with your background. Could you tell me about your experience?")
                                    st.session_state.mock_interview_history.append({"role": "assistant", "content": ai_reply})
                                
                                st.rerun()
                    else:
                        # Active mock interview in progress
                        st.subheader("Active Mock Interview")
                        
                        # Display chat history
                        for message in st.session_state.mock_interview_history:
                            if message["role"] != "system":  # Skip system messages
                                with st.chat_message(message["role"]):
                                    st.markdown(message["content"])

                        # User answers - using a chat input 
                        interview_answer = st.chat_input("Type your answer and press Enter...")
                        
                        if interview_answer:
                            st.session_state.mock_interview_history.append({"role": "user", "content": interview_answer})
                            with st.chat_message("user"):
                                st.markdown(interview_answer)
                                
                            with st.spinner("AI interviewer is thinking..."):
                                agent = get_interview_prep_agent(mock=True)
                                response = agent.invoke({
                                    "job_title": st.session_state.interview_job_title,
                                    "user_experience": st.session_state.interview_experience,
                                    "user_name": st.session_state.user_profile.get("name", "Candidate"),
                                    "history": st.session_state.mock_interview_history
                                })
                                ai_reply = response.get('output', "I couldn't process that response.")
                                st.session_state.mock_interview_history.append({"role": "assistant", "content": ai_reply})
                                st.rerun()
                        
                        # Add buttons for managing the interview - match main.py layout
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            if st.button("End Interview", key="end_mock_direct"):
                                st.session_state.mock_interview_started = False
                                st.rerun()
                        with col2:
                            if st.button("Start New Interview", key="new_mock_direct"):
                                st.session_state.mock_interview_started = False
                                st.session_state.mock_interview_history = []
                                st.rerun()
                        with col3:
                            if st.button("End & Evaluate Interview", key="evaluate_direct"):
                                with st.spinner("Evaluating your interview..."):
                                    eval_agent = get_interview_prep_agent(evaluate=True)
                                    eval_result = eval_agent.invoke({
                                        "job_title": st.session_state.interview_job_title,
                                        "user_experience": st.session_state.interview_experience,
                                        "user_name": st.session_state.user_profile.get("name", "Candidate"),
                                        "history": st.session_state.mock_interview_history
                                    })
                                    st.session_state.interview_evaluation = eval_result.get('output', "Error generating evaluation.")
                                    st.session_state.mock_interview_started = False
                                    st.rerun()
                else:
                    st.session_state.interview_agent_mode = "INTERVIEW_EVALUATE"
                    
                    # Check if we have the required interview job title
                    if not st.session_state.interview_job_title:
                        st.warning("Please provide a job title at the top of this page before submitting an interview for evaluation.")
                    
                    # Add direct interview evaluation interface
                    st.subheader("Interview Evaluation")
                    st.write("Get feedback on your past interview performance.")
                    
                    # Text area for interview transcript
                    interview_transcript = st.text_area(
                        "Paste your interview transcript or describe your interview experience:",
                        height=200,
                        key="interview_transcript",
                        placeholder="Example format:\nInterviewer: Tell me about yourself.\nMe: I am a software engineer with 5 years of experience...\nInterviewer: What projects have you worked on?..."
                    )
                    
                    if st.button("Evaluate Interview", key="evaluate_interview"):
                        if st.session_state.interview_job_title and interview_transcript:
                            with st.spinner("Analyzing your interview..."):
                                eval_agent = get_interview_prep_agent(evaluate=True)
                                result = eval_agent.invoke({
                                    "job_title": st.session_state.interview_job_title,
                                    "user_experience": st.session_state.interview_experience,
                                    "user_name": st.session_state.user_profile.get("name", "Candidate"),
                                    "input": interview_transcript
                                })
                                
                                evaluation = result.get('output', "Sorry, I couldn't generate an evaluation.")
                                
                                # Store in history
                                if "interview_evaluation_history" not in st.session_state:
                                    st.session_state.interview_evaluation_history = []
                                
                                st.session_state.interview_evaluation_history.append({
                                    "job_title": st.session_state.interview_job_title,
                                    "evaluation": evaluation
                                })
                                
                                # Display evaluation
                                st.subheader("Interview Evaluation")
                                st.markdown(evaluation)
                        else:
                            if not st.session_state.interview_job_title:
                                st.warning("Please provide a job title for your interview evaluation.")
                            if not interview_transcript:
                                st.warning("Please provide your interview transcript or experience.")
                    
                    # Display evaluation history
                    if "interview_evaluation_history" in st.session_state and st.session_state.interview_evaluation_history:
                        st.subheader("Previous Interview Evaluations")
                        if st.button("Clear Evaluation History"):
                            st.session_state.interview_evaluation_history = []
                            st.rerun()
                        
                        for i, entry in enumerate(reversed(st.session_state.interview_evaluation_history)):
                            with st.expander(f"**{i+1}. Evaluation for {entry['job_title']}**", expanded=False):
                                st.markdown(entry['evaluation'])
                                if st.button("Delete", key=f"delete_eval_{i}"):
                                    st.session_state.interview_evaluation_history.pop(len(st.session_state.interview_evaluation_history) - 1 - i)
                                    st.rerun()
            elif st.session_state.active_mode == "TUTORIALS":
                st.write("Ask me to create learning resources or tutorials on any technical topic.")
                
                # Add option for direct tutorial generation
                if "tutorial_mode" not in st.session_state:
                    st.session_state.tutorial_mode = "Detailed Tutorial"
                
                st.session_state.tutorial_mode = st.radio(
                    "Tutorial Mode",
                    ["Detailed Tutorial", "Quick Q&A"],  # Remove Conversational option
                    horizontal=True,
                    key="tutorial_mode_select"
                )
                
                # Always use direct mode for tutorials
                from src.tutorials.agent import get_tutorials_agent
                from src.guidance.agent import get_qa_bot
                
                if st.session_state.tutorial_mode == "Detailed Tutorial":
                    st.subheader("Tutorials Agent")
                    st.write("Get detailed guides and blogs on any technical topic.")
                    tutorial_query = st.text_input("What topic do you want a tutorial on?", key="direct_tutorial_query")
                    
                    if st.button("Get Tutorial", key="direct_tutorial_button"):
                        if tutorial_query:
                            with st.spinner("Generating comprehensive tutorial..."):
                                agent = get_tutorials_agent()
                                result = agent.invoke({
                                    "user_message": tutorial_query,
                                    "user_context": st.session_state.user_profile.get("skills", "")
                                })
                                
                                output = ""
                                if isinstance(result, dict) and 'output' in result:
                                    output = result['output'].strip()
                                    
                                    # Check if the output is empty but we have a result
                                    if not output and str(result):
                                        output = f"Error: Extracted output is empty. Using full response instead.\n\n{str(result)}"
                                else:
                                    output = f"Error: Could not parse agent output. Full response: {result}"

                                # Store in history and display
                                if "tutorial_history" not in st.session_state:
                                    st.session_state.tutorial_history = []
                                st.session_state.tutorial_history.append({"query": tutorial_query, "result": output})
                                
                                # Display tutorial
                                st.subheader(f"Tutorial: {tutorial_query}")
                                st.markdown(output)
                        else:
                            st.warning("Please enter a topic.")
                            
                    # Display tutorial history
                    if "tutorial_history" in st.session_state and st.session_state.tutorial_history:
                        st.subheader("Tutorial History")
                        if st.button("Clear Tutorial History"):
                            st.session_state.tutorial_history = []
                            st.rerun()
                        
                        for i, entry in enumerate(reversed(st.session_state.tutorial_history)):
                            with st.expander(f"**{i+1}. {entry['query']}**", expanded=False):
                                st.markdown(entry['result'])
                                if st.button("Delete", key=f"delete_tutorial_{i}"):
                                    st.session_state.tutorial_history.pop(len(st.session_state.tutorial_history) - 1 - i)
                                    st.rerun()
                
                elif st.session_state.tutorial_mode == "Quick Q&A":
                    st.subheader("Q&A Bot")
                    st.write("Ask me any quick question about software development, AI, or career topics.")
                    qa_query = st.text_input("What is your question?", key="qa_query")
                    
                    if st.button("Ask", key="qa_button"):
                        if qa_query:
                            with st.spinner("Getting your answer..."):
                                chain = get_qa_bot()
                                result = chain.invoke({"question": qa_query})
                                
                                if "qa_history" not in st.session_state:
                                    st.session_state.qa_history = []
                                
                                answer = ""
                                if isinstance(result, dict) and 'text' in result:
                                    answer = result['text']
                                else:
                                    answer = str(result) if result else "Sorry, I couldn't find an answer to that question."
                                    
                                st.session_state.qa_history.append({"query": qa_query, "result": answer})
                                
                                # Display answer
                                st.subheader("Answer")
                                st.markdown(answer)
                        else:
                            st.warning("Please enter a question.")
                            
                    # Display Q&A history
                    if "qa_history" in st.session_state and st.session_state.qa_history:
                        st.subheader("Q&A History")
                        if st.button("Clear Q&A History"):
                            st.session_state.qa_history = []
                            st.rerun()
                        
                        for i, entry in enumerate(reversed(st.session_state.qa_history)):
                            with st.expander(f"**{i+1}. {entry['query']}**", expanded=True):
                                st.markdown(entry['result'])
                                if st.button("Delete", key=f"delete_qa_{i}"):
                                    st.session_state.qa_history.pop(len(st.session_state.qa_history) - 1 - i)
                                    st.rerun()
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
        
        # Chat input - only show in general chat mode (when active_mode is None)
        if st.session_state.active_mode is None:
            user_input = st.chat_input("Type your message here...")
            if user_input:
                # Display user message
                st.chat_message("user").write(user_input)
                
                # Add user message to the main chat history
                st.session_state.chat_history.append({"role": "user", "content": user_input})

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
                    
                    # In main chat, allow routing to any specialized agent
                    response = st.session_state.orchestrator.process_message(
                        user_input,
                        agent_type=None,  # Uses routing to any agent type
                        **additional_context
                    )
                    
                    # Extract the agent's response
                    agent_response = response.get("output", "Sorry, I encountered an error.")
                    
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
