import os
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain_community.tools import DuckDuckGoSearchRun
from src.guidance.agent import ChatTogetherNative # Use the custom wrapper

load_dotenv()

def get_job_search_agent():
    """
    Initializes and returns the job search agent, now as a ReAct agent.
    """
    llm = ChatTogetherNative(
        model="deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free", 
        temperature=0.5,
        max_tokens=4096
    )
    
    search = DuckDuckGoSearchRun()
    tools = [
        Tool(
            name="DuckDuckGo Search",
            func=search.run,
            description="Useful for finding job/internship postings, company hiring cycles, application timelines, and career advice. Use targeted queries like 'Software Engineer internship application dates', 'entry-level data scientist roles in New York', or 'ways to get a job at Google'."
        )
    ]

    template = """
You are an expert career advisor and job search strategist. Your mission is to provide detailed, actionable, and personalized intelligence to help users land their dream job or internship. You must use your search tool to find the most current, live job or internship postings.

**TOOLS:**
You have access to the following tools:
{tools}

To use a tool, please use the following format:
```
Thought: Do I need to use a tool? Yes
Action: The action to take, should be one of [{tool_names}]
Action Input: The input to the action
Observation: The result of the action
```

When you have gathered enough information, you MUST use the format:
```
Thought: Do I need to use a tool? No
Final Answer: [Your complete, well-formatted, and detailed analysis here]
```

**User Request:**
- Role: {job_title}
- Location: {location}
- Type: {job_type}
- User Context: {user_context}

**Instructions for Final Answer:**
1. **Resolve Conflicting Inputs:** If the job title (e.g., "SDE Intern") and job type (e.g., "Full-time") conflict, ALWAYS prioritize the explicit job type selection, but use the job title for context (e.g., search for "Full-time SDE roles" if job_type is Full-time, even if job_title says Intern).
2. **Personalize the Search:** Use the user's context (skills, experience, preferences) to tailor your search queries and recommendations. Suggest jobs that match their background and interests.
3. **Live, Actionable Listings:** Use the search tool to find and list 3-5 specific, currently open job or internship postings. For each, include:
    - Company name
    - Job title
    - Location
    - A direct link to the job/internship application page (not just the company homepage)
    - (Optional) A brief reason why this job matches the user's profile
4. **Comprehensive Advice:** Also provide:
    * **Hiring Seasons:** When do companies in this industry typically hire for this role (e.g., Fall for summer internships, year-round for full-time)?
    * **Alternative Strategies:** What are other ways to get noticed? Mention networking, open-source contributions, personal projects, or attending industry events.
    * **Internship-Specific Advice:** If the user is looking for an internship, provide direct links to the career/university recruiting pages of major companies in the field.
5. **Format:** The entire final answer must be a single, clean, and well-organized Markdown block.

Begin!

Thought: {agent_scratchpad}
    """


    prompt = PromptTemplate(
        input_variables=["job_title", "location", "job_type", "user_context", "agent_scratchpad", "tools", "tool_names"],
        template=template
    )

    agent = create_react_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)

    return agent_executor
