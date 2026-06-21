import streamlit as st
import os
from dotenv import load_dotenv
from src.guidance.agent import get_qa_bot, get_tutorial_agent
# Import both resume agents
from src.resume_builder.agent import get_resume_builder_agent, get_resume_refinement_agent
from src.interview_prep.agent import get_interview_prep_agent
from src.qna.agent import get_job_search_agent

# Load environment variables from .env file
load_dotenv()

# Set up Together API key
# Make sure to set your TOGETHER_API_KEY in a .env file in the root of your project
# TOGETHER_API_KEY="your_api_key_here"
together_api_key = os.getenv("TOGETHER_API_KEY")

if not together_api_key:
    # If the API key is not found, display an error message in the app.
    st.error("Together API key not found. Please set it in the .env file.")
else:
    os.environ["TOGETHER_API_KEY"] = together_api_key

def main():
    """
    Main function to run the AI Career Assistant Streamlit app.
    """
    st.set_page_config(page_title="AI Career Assistant", layout="wide")

    st.title("AI Career Assistant 🚀")
    st.write("Your ultimate guide to a career in Software and AI!")

    # Initialize session state for history
    if 'tutorial_history' not in st.session_state:
        st.session_state.tutorial_history = []
    if 'qa_history' not in st.session_state:
        st.session_state.qa_history = []
    if 'resume_history' not in st.session_state:
        st.session_state.resume_history = []
    # Add state for the new resume builder flow
    if 'generated_resume' not in st.session_state:
        st.session_state.generated_resume = ""
    if 'resume_chat_history' not in st.session_state:
        st.session_state.resume_chat_history = []
    if 'job_description' not in st.session_state:
        st.session_state.job_description = ""

    if 'interview_prep_history' not in st.session_state:
        st.session_state.interview_prep_history = []
    if 'job_search_history' not in st.session_state:
        st.session_state.job_search_history = []

    # Create the tabbed interface
    tab1, tab2, tab3, tab4 = st.tabs([
        "Learning Center",
        "Resume Builder",
        "Interview Prep",
        "Job Search"
    ])

    with tab1:
        st.header("Learning Center")
        st.write("Choose a learning mode:")
        
        # Use session state to keep track of the choice
        if 'learning_choice' not in st.session_state:
            st.session_state.learning_choice = 'Tutorials Agent'

        learning_choice = st.radio(
            "Select one:", 
            ('Tutorials Agent', 'Q&A Bot'), 
            horizontal=True,
            label_visibility="collapsed",
            key="learning_choice_radio" # Add a key to the radio button
        )
        st.session_state.learning_choice = learning_choice


        if st.session_state.learning_choice == 'Tutorials Agent':
            st.subheader("Tutorials Agent")
            st.write("Get detailed guides and blogs on any technical topic.")
            tutorial_query = st.text_input("What topic do you want a tutorial on?", key="tutorial_query")
            
            if st.button("Get Tutorial", key="tutorial_button"):
                if tutorial_query:
                    with st.spinner("Generating tutorial..."):
                        agent = get_tutorial_agent()
                        result = agent.invoke({"input": tutorial_query})
                        
                        output = ""
                        # The ReAct agent's final answer is in the 'output' key.
                        if isinstance(result, dict) and 'output' in result:
                            full_response = result['output']
                            
                            # New, more robust parsing logic:
                            # 1. Try to find the start of the tutorial by a common marker.
                            if "# Table of Contents" in full_response:
                                # Grab everything from the table of contents onwards.
                                output = full_response[full_response.find("# Table of Contents"):]
                            # 2. If that fails, fall back to the original 'Final Answer' split.
                            elif "Final Answer:" in full_response:
                                output = full_response.split("Final Answer:", 1)[-1].strip()
                            # 3. If all else fails, use the raw output.
                            else:
                                output = full_response
                        else:
                            # Fallback for truly unexpected output format
                            output = f"Error: Could not parse agent output. Full response: {result}"

                        st.session_state.tutorial_history.append({"query": tutorial_query, "result": output})
                else:
                    st.warning("Please enter a topic.")

            # Display tutorial history
            if st.session_state.tutorial_history:
                st.subheader("Tutorial History")
                if st.button("Clear Tutorial History"):
                    st.session_state.tutorial_history = []
                    st.rerun()

                for i, entry in enumerate(reversed(st.session_state.tutorial_history)):
                    with st.expander(f"**{len(st.session_state.tutorial_history) - i}. {entry['query']}**", expanded=False):
                        st.markdown(entry['result'])
                        if st.button("Delete", key=f"delete_tutorial_{i}"):
                            st.session_state.tutorial_history.pop(len(st.session_state.tutorial_history) - 1 - i)
                            st.rerun()

        elif st.session_state.learning_choice == 'Q&A Bot':
            st.subheader("Q&A Bot")
            st.write("Ask me any quick question about software development, AI, or career topics.")
            qa_query = st.text_input("What is your question?", key="qa_query")

            if st.button("Ask", key="qa_button"):
                if qa_query:
                    with st.spinner("Getting your answer..."):
                        chain = get_qa_bot()
                        result = chain.invoke({"question": qa_query})
                        st.session_state.qa_history.append({"query": qa_query, "result": result['text']})
                else:
                    st.warning("Please enter a question.")
            
            # Display Q&A history
            if st.session_state.qa_history:
                st.subheader("Q&A History")
                if st.button("Clear Q&A History"):
                    st.session_state.qa_history = []
                    st.rerun()
                
                for i, entry in enumerate(reversed(st.session_state.qa_history)):
                    with st.expander(f"**{len(st.session_state.qa_history) - i}. {entry['query']}**", expanded=True):
                        st.markdown(entry['result'])
                        if st.button("Delete", key=f"delete_qa_{i}"):
                            st.session_state.qa_history.pop(len(st.session_state.qa_history) - 1 - i)
                            st.rerun()

    with tab2:
        st.header("LaTeX Resume Builder")
        st.write("Generate and refine a professional, ATS-friendly resume in LaTeX format.")

        st.subheader("1. Target Job Description")
        job_desc_input = st.text_area(
            "Paste the job description here:", 
            height=150, 
            key="job_desc_input",
            value=st.session_state.job_description
        )
        
        st.subheader("2. Your Details")
        user_details = st.text_area("Paste your current resume, or list your experience, skills, and projects:", height=250, key="user_details")

        if st.button("Generate LaTeX Resume", key="resume_button"):
            if job_desc_input and user_details:
                # Store the job description in session state so the refinement agent can use it
                st.session_state.job_description = job_desc_input
                with st.spinner("Generating your tailored LaTeX resume..."):
                    agent = get_resume_builder_agent()
                    print("DEBUG: agent.input_keys =", agent.input_keys)
                    print("DEBUG: invoking with", {"job_description": st.session_state.job_description, "user_details": user_details})
                    print("DEBUG: type(agent) =", type(agent))
                    result = agent.invoke({"job_description": st.session_state.job_description, "user_details": user_details})

                    
                    if isinstance(result, dict) and 'resume' in result:
                        st.session_state.generated_resume = result['resume']
                        st.session_state.resume_chat_history = [{
                            "role": "assistant", 
                            "content": "Here is the LaTeX code for your resume. You can now ask for modifications below. For example: 'Add a new project called...'"
                        }]
                        st.rerun() # Rerun to display the results immediately
                    else:
                        st.error("Sorry, there was an error generating the resume. Please try again.")
                        st.session_state.generated_resume = f"Error: Could not parse agent output. Full response: {result}"
            else:
                st.warning("Please provide both the job description and your details.")

        # Display the generated resume and the refinement chat interface
        if st.session_state.generated_resume:
            st.subheader("3. Your Generated LaTeX Resume")
            st.info("Copy the code below and paste it into a LaTeX editor (like Overleaf) to compile your PDF.")
            st.code(st.session_state.generated_resume, language="latex")
            
            st.subheader("4. Refine Your Resume")

            # Display chat history for refinement
            for message in st.session_state.resume_chat_history:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            # Chat input for refinement, now fully functional
            if prompt := st.chat_input("e.g., 'Change the summary to be more focused on project management.'"):
                st.session_state.resume_chat_history.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)

                with st.spinner("Editing your LaTeX resume..."):
                    refinement_agent = get_resume_refinement_agent()
                    response = refinement_agent.invoke({
                        "job_description": st.session_state.job_description,
                        "previous_resume": st.session_state.generated_resume,
                        "user_request": prompt
                    })

                    with st.chat_message("assistant"):
                        if isinstance(response, dict) and 'resume' in response:
                            st.session_state.generated_resume = response['resume']
                            # We don't write a message here, we just rerun to show the updated code
                            st.rerun()
                        else:
                            error_message = f"Sorry, I couldn't make that change. Please try rephrasing your request. Error: {response}"
                            st.markdown(error_message)
                            st.session_state.resume_chat_history.append({"role": "assistant", "content": error_message})

    with tab3:
        st.header("Interview Prep")
        st.write("Get ready to ace your next interview with a guide generated by a research-powered AI agent, or simulate a real interview with an AI interviewer.")

        interview_mode = st.radio(
            "Choose your mode:",
            ("Get Prep Guide", "Simulate Mock Interview"),
            key="interview_mode",
            horizontal=True
        )

        job_title = st.text_input("What is the job title you are interviewing for?", key="job_title")
        user_experience = st.text_area("Briefly describe your experience level (e.g., entry-level, 5 years in Python, etc.):", key="user_experience")
        user_name = st.text_input("Your Name (optional):", key="user_name")

        if interview_mode == "Get Prep Guide":
            if st.button("Get Prep Guide", key="prep_guide_button"):
                if job_title and user_experience:
                    with st.spinner("Generating your interview prep guide... This may take a moment as the agent performs research."):
                        agent = get_interview_prep_agent()
                        # The new ReAct agent takes the same inputs but has a different output structure
                        result = agent.invoke({"job_title": job_title, "user_experience": user_experience})
                        
                        # The final answer from a ReAct agent is in the 'output' key
                        output = result.get('output', f"Error: Could not parse agent output. Full response: {result}")
                        st.session_state.interview_prep_history.append({"query": f"Prep Guide for {job_title}", "result": output})
                else:
                    st.warning("Please provide both the job title and your experience level.")

            # Display interview prep history
            if st.session_state.interview_prep_history:
                st.subheader("Interview Prep Guides")
                if st.button("Clear Prep Guide History"):
                    st.session_state.interview_prep_history = []
                    st.rerun()

                for i, entry in enumerate(reversed(st.session_state.interview_prep_history)):
                    with st.expander(f"**{len(st.session_state.interview_prep_history) - i}. {entry['query']}**", expanded=False):
                        st.markdown(entry['result'])
                        if st.button("Delete", key=f"delete_prep_{i}"):
                            st.session_state.interview_prep_history.pop(len(st.session_state.interview_prep_history) - 1 - i)
                            st.rerun()
        
        elif interview_mode == "Simulate Mock Interview":
            # Check if we have an evaluation to display
            if 'interview_evaluation' in st.session_state and st.session_state.interview_evaluation:
                st.subheader("Your Interview Evaluation")
                st.info("This evaluation is based on your performance in the mock interview. Use this feedback to improve your interview skills.")
                st.markdown(st.session_state.interview_evaluation)
                
                if st.button("Clear Evaluation & Start New Interview", key="clear_evaluation"):
                    st.session_state.interview_evaluation = None
                    st.session_state.mock_interview_started = False
                    st.session_state.mock_interview_history = []
                    st.rerun()
                    
            else:
                st.subheader("Mock Interview (Chat)")
                st.info("You are about to start a mock interview. The AI will ask you questions one by one. Answer as you would in a real interview!")
            
            # Initialize session state for mock interview
            if 'mock_interview_history' not in st.session_state:
                st.session_state.mock_interview_history = []
            if 'mock_interview_started' not in st.session_state:
                st.session_state.mock_interview_started = False

            if not st.session_state.mock_interview_started:
                if st.button("Start Mock Interview", key="start_mock_interview"):
                    if job_title and user_experience:
                        st.session_state.mock_interview_history = []
                        st.session_state.mock_interview_started = True
                        # Add system message to start the interview
                        st.session_state.mock_interview_history.append({
                            "role": "system",
                            "content": f"You are interviewing {user_name or 'a candidate'} for the role of {job_title}. The candidate has this experience: {user_experience}. Begin the interview with a brief introduction and your first question."
                        })
                        
                        # Immediately get the first interviewer message
                        with st.spinner("Starting the interview..."):
                            agent = get_interview_prep_agent(mock=True)
                            response = agent.invoke({
                                "job_title": job_title,
                                "user_experience": user_experience,
                                "user_name": user_name or "Candidate",
                                "history": st.session_state.mock_interview_history
                            })
                            ai_reply = response.get('output', "Hello! I'm your interviewer today. Let's begin with your background. Could you tell me a bit about your experience relevant to this role?")
                            st.session_state.mock_interview_history.append({"role": "assistant", "content": ai_reply})
                        
                        st.rerun()
                    else:
                        st.warning("Please provide both the job title and your experience level.")
            else:
                # Display chat history
                for message in st.session_state.mock_interview_history:
                    if message["role"] != "system":  # Skip system messages in the display
                        with st.chat_message(message["role"]):
                            st.markdown(message["content"])

                # User answers
                if prompt := st.chat_input("Type your answer and press Enter..."):
                    st.session_state.mock_interview_history.append({"role": "user", "content": prompt})
                    with st.chat_message("user"):
                        st.markdown(prompt)
                    with st.spinner("AI interviewer is thinking..."):
                        # Call the interview agent with full history
                        agent = get_interview_prep_agent(mock=True)
                        response = agent.invoke({
                            "job_title": job_title,
                            "user_experience": user_experience,
                            "user_name": user_name,
                            "history": st.session_state.mock_interview_history
                        })
                        ai_reply = response.get('output', f"Error: Could not parse agent output. Full response: {response}")
                        st.session_state.mock_interview_history.append({"role": "assistant", "content": ai_reply})
                        st.rerun()
                
                # Add buttons for ending the interview or starting a new one
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("End Interview", key="end_mock_interview"):
                        st.session_state.mock_interview_started = False
                        st.rerun()
                with col2:
                    if st.button("Start New Interview", key="new_mock_interview"):
                        st.session_state.mock_interview_started = False
                        st.session_state.mock_interview_history = []
                        st.rerun()
                with col3:
                    if st.button("End & Evaluate Interview", key="evaluate_mock_interview"):
                        st.session_state.mock_interview_started = False
                        
                        # Store the current history for evaluation
                        if 'interview_evaluation' not in st.session_state:
                            st.session_state.interview_evaluation = None
                            
                        # Get an evaluation of the interview
                        with st.spinner("Evaluating your interview performance..."):
                            eval_agent = get_interview_prep_agent(evaluate=True)
                            eval_result = eval_agent.invoke({
                                "job_title": job_title,
                                "user_experience": user_experience,
                                "user_name": user_name or "Candidate",
                                "history": st.session_state.mock_interview_history
                            })
                            st.session_state.interview_evaluation = eval_result.get('output', "Sorry, there was an error generating your evaluation.")
                            
                        st.rerun()

    with tab4:

        st.header("Job Search")
        st.write("Find relevant job opportunities based on your profile.")

        search_job_title = st.text_input("Enter a job title:", key="search_job_title")
        search_location = st.text_input("Enter a location (e.g., 'San Francisco, CA' or 'Remote'):", key="search_location")
        search_job_type = st.radio("Select job type:", ("Full-time", "Internship"), key="search_job_type", horizontal=True)
        user_context = st.text_area(
            "To personalize your search, briefly describe your skills, experience, and what you're looking for:",
            key="user_context", height=100)

        if st.button("Search for Jobs", key="job_search_button"):
            if search_job_title and search_location:
                with st.spinner("Searching for jobs... This may take a moment as the agent performs research."):
                    agent = get_job_search_agent()
                    # Pass user_context for personalization and improved prompt handling
                    result = agent.invoke({
                        "job_title": search_job_title,
                        "location": search_location,
                        "job_type": search_job_type,
                        "user_context": user_context
                    })
                    # The final answer from a ReAct agent is in the 'output' key
                    output = result.get('output', f"Error: Could not parse agent output. Full response: {result}")
                    st.session_state.job_search_history.append({
                        "query": f"{search_job_type} jobs for {search_job_title} in {search_location}",
                        "result": output
                    })
            else:
                st.warning("Please provide both a job title and a location.")

        # Display job search history
        if st.session_state.job_search_history:
            st.subheader("Job Search Results")
            if st.button("Clear Job Search History"):
                st.session_state.job_search_history = []
                st.rerun()

            for i, entry in enumerate(reversed(st.session_state.job_search_history)):
                with st.expander(f"**{len(st.session_state.job_search_history) - i}. {entry['query']}**", expanded=True):
                    st.markdown(entry['result'])
                    if st.button("Delete", key=f"delete_job_{i}"):
                        st.session_state.job_search_history.pop(len(st.session_state.job_search_history) - 1 - i)
                        st.rerun()


if __name__ == "__main__":
    main()
