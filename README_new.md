# AI Career Assistant

An AI-powered career assistant application that helps users with resume building, job searching, interview preparation, and learning new skills.

## Features

### Orchestrated Chatbot Interface

- Single chat interface that routes queries to specialized agents
- Shared context between different functionality areas
- Sidebar navigation for quick access to history and user profile

### Resume Builder

- Create professional resumes with AI assistance
- Tailor resumes to specific job descriptions
- Get feedback and suggestions for improvement

### Job Search

- Find relevant job opportunities based on your skills and experience
- Get personalized job search advice
- Learn about hiring seasons and application strategies

### Interview Preparation

- Get comprehensive interview preparation guides
- Simulate mock interviews with AI
- Receive detailed evaluation and feedback after mock interviews

### Learning Resources

- Access tutorials and learning guides for any technical topic
- Personalized learning recommendations based on your background

## Getting Started

1. Clone the repository
2. Install dependencies with `pip install -r requirements.txt`
3. Create a `.env` file with your Together API key:
   ```
   TOGETHER_API_KEY=your_api_key_here
   ```
4. Run the application:
   ```
   streamlit run new_main.py
   ```

## Usage

### Direct Mode Access

The VS Code-style sidebar allows you to directly access any functionality mode:

- Click on "Resume Builder" to immediately enter the resume creation mode
- Click on "Job Search" to start looking for job opportunities
- Click on "Interview Prep" to prepare for interviews or have a mock interview
- Click on "Tutorials" to get learning resources on any topic

### Required Inputs

Each specialized mode requires specific inputs to function properly:

- **Resume Builder**: Requires a job description to tailor the resume
- **Job Search**: Requires job title and location to find relevant opportunities
- **Interview Prep**: Requires job title and interview mode selection
- **Tutorials**: No specific required inputs

### Chat Interface

Simply type your questions or requests into the chat input at the bottom of the screen. The AI will automatically route your query to the appropriate specialized agent.

### User Profile

Fill out your user profile in the sidebar to get more personalized responses:

- **Name**: Used for personalized greetings and mock interviews
- **Job Title**: Helps tailor job searches and interview preparation
- **Experience**: Used for resume creation and interview responses
- **Skills**: Used to customize job recommendations and tutorials

Your profile information is shared across all agents to provide a consistent experience.

### History Tracking

Each functionality area maintains its own history, which you can access from the sidebar:

- Resume Builder history
- Job Search history
- Interview Prep history
- Tutorials history
- Name: Your name for personalized interactions
- Target Job Title: The job you're targeting
- Experience: Your professional background
- Skills: Technical and soft skills you possess

### Navigation

Use the sidebar buttons to switch between:

- Chat: Main interface for all interactions
- Resume History: View past resume building conversations
- Job Search History: View past job search queries and results
- Interview Prep History: View past interview preparation content
- Tutorials History: View past learning resources

## Technical Architecture

The application uses an orchestrator pattern:

- Central orchestrator agent for routing and shared context
- Specialized agents for specific domains
- LangChain for creating AI agent workflows
- Streamlit for the user interface

## Future Enhancements

- Voice-based mock interviews
- PDF resume generation and parsing
- Job application tracking
- Career path planning and skill gap analysis
