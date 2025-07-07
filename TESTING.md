# Testing the AI Career Assistant

## Running the Application

To test the new AI Career Assistant with VS Code-style sidebar and direct mode access:

1. **Run the application:**

   ```
   streamlit run new_main.py
   ```

2. **Using the VS Code Style Interface:**
   - The left sidebar contains permanent navigation buttons with icons
   - Click on any of these buttons to activate a specific mode
   - The profile editor is accessible via the "Your Profile" button

## Testing Each Mode

### Main Chat (General Mode)

- Click the "Main Chat" button in the sidebar
- Type any query and the orchestrator will automatically route it to the appropriate agent
- Example: "I need help creating a resume" will be routed to the Resume Builder agent

### Resume Builder Mode

- Click the "Resume Builder" button in the sidebar
- This activates Resume Builder mode (indicated at the top of the chat)
- You MUST provide a job description in the required field
- Optionally, you can paste an existing resume for refinement
- All your messages will now be sent directly to the Resume Builder agent
- Example: "Create a resume for a software engineer with 5 years of experience"

### Job Search Mode

- Click the "Job Search" button in the sidebar
- This activates Job Search mode
- You MUST provide a job title and location in the required fields
- Select the appropriate job type from the dropdown
- All your messages will be sent directly to the Job Search agent
- Example: "Find me data science jobs in New York"

### Interview Prep Mode

- Click the "Interview Prep" button in the sidebar
- This activates Interview Prep mode
- You MUST provide a job title for the interview in the required field
- Select the desired interview mode (Preparation Guide, Mock Interview, or Interview Evaluation)
- All your messages will be sent directly to the Interview Prep agent
- Example: "I have an interview for a frontend developer position. What should I prepare?"
- Example: "Can you conduct a mock interview for a product manager role?"

### Tutorials Mode

- Click the "Tutorials" button in the sidebar
- This activates Tutorials mode
- All your messages will be sent directly to the Tutorials agent
- Example: "Create a tutorial on React hooks"

## User Profile

The user profile is crucial for personalizing the experience across all agents:

1. **Click the "Your Profile" button in the sidebar**
2. **Fill in the following information:**

   - Your Name: Used for personalizing responses and mock interviews
   - Target Job Title: Helps focus job searches and interview preparation
   - Work & Education Experience: Used for resume creation and interview responses
   - Skills & Technologies: Used to tailor job searches and learning resources

3. **Click "Save Profile" to update your information**

The profile information is shared across all agents to provide a consistent experience:

- Resume Builder uses your experience and skills to create tailored resumes
- Job Search uses your profile to find relevant job opportunities
- Interview Prep uses your experience to customize interview questions
- Tutorials uses your skills to recommend appropriate learning resources

For the best experience, complete your profile before using the specialized agents.

## Viewing History

- Click on any of the history buttons in the sidebar (Resume History, Job Search History, etc.)
- This will show all past conversations in that category
- Click "Return to Chat" to go back to the chat interface

## Profile Management

- Click on "Your Profile" in the sidebar
- Fill out your information to get more personalized responses
- Click "Save Profile" to update your shared context
- This information will be used by all agents

## Advanced Features

### Mock Interviews

- In Interview Prep mode, select "Mock Interview" from the radio buttons
- Provide a job title for the interview
- The agent will conduct a realistic interview, asking questions one at a time
- Your conversation history is maintained for the entire mock interview session

### Interview Evaluation

- In Interview Prep mode, select "Interview Evaluation" from the radio buttons
- Provide a job title for the interview
- After a mock interview or when describing a past interview, ask for evaluation
- The agent will provide detailed feedback on your performance

## Troubleshooting Common Errors

### Input Format Errors

- **Error:** "I encountered an error while processing your request: KeyError: 'input'"
- **Solution:** Some agents expect specific input formats. The orchestrator now handles this automatically, but if you encounter this error, try switching to the specific mode for that functionality.

### Missing Required Fields

- **Error:** You may see warnings about missing required fields
- **Solution:** Each agent now requires specific inputs. Make sure to fill in all required fields marked in the UI.

### Missing Profile Information

- **Error:** Vague or generic responses
- **Solution:** Fill out your profile information in the "Your Profile" section for more personalized responses.

### Agent Unavailable

- **Error:** "I'm having trouble accessing that functionality right now"
- **Solution:** This might be due to initialization issues. Try clearing the chat and restarting the application.

### Interview Mode Issues

- **Problem:** Mock interview giving multiple questions at once
- **Solution:** The interview agent has been updated to enforce one question at a time. If you still encounter this issue, try exiting and re-entering Interview Prep mode.

## Known Limitations

1. **Large Resume Content**: If your resume is very large, it may be truncated. Focus on the most relevant sections.
2. **Interview History**: Mock interview history is maintained only for the current session.
3. **Job Search Results**: The job search agent returns current listings that may expire over time.
4. **Tutorials Complexity**: Complex tutorial requests may be simplified or broken down into sections.

## Exiting a Mode

- When in a specific mode (Resume Builder, Job Search, etc.), click the "Exit Mode" button at the top of the chat
- This will return you to the general chat mode where queries are automatically routed
