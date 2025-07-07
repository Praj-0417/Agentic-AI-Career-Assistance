import os
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_community.tools import DuckDuckGoSearchRun
from langchain.agents import Tool, AgentExecutor, create_react_agent
from src.guidance.agent import ChatTogetherNative # Use the custom wrapper

load_dotenv()

def get_interview_prep_agent(mock=False, evaluate=False):
    """
    Initializes and returns the interview prep agent, now as a ReAct agent.
    If mock=True, it returns a special version for conducting mock interviews.
    If evaluate=True, it returns a special version for evaluating interview performance.
    """
    llm = ChatTogetherNative(
        model="mistralai/Mixtral-8x7B-Instruct-v0.1", 
        temperature=0.6,
        max_tokens=4096
    )
    
    if mock:
        # This is a specialized agent for conducting mock interviews
        mock_interview_template = """
You are an expert technical interviewer for a leading technology company. Your task is to conduct a realistic, professional mock interview for a job candidate. Treat this exactly like a real job interview - be professional, thoughtful, and evaluative, but also friendly and supportive.

**Context:**
- Candidate Name: {user_name}
- Position: {job_title}
- Candidate Experience: {user_experience}

**Interview Process Guidelines:**
1. If this is the beginning of the interview, introduce yourself briefly and ask your first question.
2. Ask ONE question at a time. Never ask multiple questions in a single response.
3. Evaluate the candidate's previous answer before asking the next question.
4. Ask follow-up questions if their answer needs clarification or is incomplete.
5. Conduct a realistic interview covering:
   - Technical questions specific to the role
   - Behavioral/situational questions
   - Problem-solving scenarios
6. Adjust difficulty based on how well the candidate answers.
7. If the candidate asks you a question about the company or role, provide a realistic answer.
8. When appropriate, provide a short closing with brief feedback on their interview performance.

**IMPORTANT FORMATTING RULES:**
- Keep your responses concise and focused (1-3 paragraphs max).
- Always ask just ONE question at a time, then wait for the candidate's response.
- NEVER provide multiple questions in a single response.
- NEVER answer your own questions or continue the conversation as if the candidate has responded.
- After asking a question, STOP and wait for the candidate to respond.
- Use a professional but conversational tone.
- DO NOT include phrases like "Based on the above" or "If this is the beginning of the interview" in your responses.
- DO NOT write "Candidate:" or predict what the candidate might say.
- DO NOT include any meta-instructions or model guidance in your responses.
- Respond ONLY as the interviewer, in the first person.

**Interview History:**
{history}
"""
        
        # Create a simple LLM chain for the mock interview (not a ReAct agent)
        mock_interview_prompt = PromptTemplate(
            input_variables=["job_title", "user_experience", "user_name", "history"],
            template=mock_interview_template
        )
        mock_interview_chain = LLMChain(
            llm=llm,
            prompt=mock_interview_prompt,
            verbose=True
        )
        
        # Wrap the LLM chain in a simple interface that matches our agent_executor
        class MockInterviewWrapper:
            def __init__(self, chain):
                self.chain = chain
                
            def invoke(self, inputs):
                # Process inputs for the mock interview
                processed_inputs = {
                    "job_title": inputs.get("job_title", ""),
                    "user_experience": inputs.get("user_experience", ""),
                    "user_name": inputs.get("user_name", "Candidate"),
                    "history": self._format_history(inputs.get("history", []))
                }
                
                # Run the chain
                result = self.chain.invoke(processed_inputs)
                
                # Clean the response to remove any unwanted text
                response_text = result["text"]
                # Remove common issues
                response_text = self._clean_response(response_text)
                
                # Return in the same format as agent_executor
                return {"output": response_text}
            
            def _clean_response(self, text):
                """Clean the response to remove any problematic patterns."""
                # Remove any instructions text that might have leaked
                patterns_to_remove = [
                    "Based on the above,",
                    "provide your next interview response.",
                    "If this is the beginning of the interview,",
                    "Candidate:",
                    "Interviewer:",
                ]
                
                cleaned_text = text
                for pattern in patterns_to_remove:
                    cleaned_text = cleaned_text.replace(pattern, "")
                
                # Remove any blank lines at the beginning or end
                cleaned_text = cleaned_text.strip()
                
                # Check if there are multiple questions in the response
                import re
                
                # Split on common question patterns (? followed by new sentence or newline)
                sentences = re.split(r'\?\s+(?=[A-Z])', cleaned_text)
                
                # If there are multiple sections with questions, only keep the first question
                if len(sentences) > 1:
                    # Look for the first question
                    for i, sentence in enumerate(sentences):
                        if '?' in sentence:
                            # Keep everything up to and including this first question
                            cleaned_text = ''.join(sentences[:i+1])
                            if not cleaned_text.endswith('?'):
                                cleaned_text += '?'
                            break
                
                return cleaned_text
                
            def _format_history(self, history):
                """Format the history into a readable format for the LLM."""
                formatted = ""
                for message in history:
                    role = message.get("role", "")
                    content = message.get("content", "")
                    
                    if role == "system":
                        continue  # Skip system messages
                    elif role == "user":
                        formatted += f"Candidate: {content}\n\n"
                    elif role == "assistant":
                        formatted += f"Interviewer: {content}\n\n"
                        
                return formatted.strip()
        
        return MockInterviewWrapper(mock_interview_chain)
    
    elif evaluate:
        # This is a specialized agent for evaluating mock interviews
        interview_evaluation_template = """
You are an expert interview evaluator and coach with years of experience in technical recruiting. Your task is to evaluate a completed mock interview and provide detailed, constructive feedback to the candidate.

**Candidate Information:**
- Name: {user_name}
- Position: {job_title}
- Experience Level: {user_experience}

**The Interview Transcript:**
{history}

**Evaluation Instructions:**
1. Review the entire interview transcript carefully.
2. Score the candidate's performance in the following areas (on a scale of 1-10):
   - Technical Knowledge: Understanding of concepts, technologies, and domain expertise
   - Communication Skills: Clarity, conciseness, and effectiveness of responses
   - Problem-Solving: Approach to technical challenges and reasoning ability
   - Behavioral/Soft Skills: Teamwork, leadership, conflict resolution
   - Overall Performance: Holistic assessment of interview performance

3. For each area, provide:
   - The numerical score (1-10)
   - Specific examples from the interview that justify the score
   - Actionable advice for improvement

4. Finally, provide an "Overall Assessment" section with:
   - A summary of the candidate's strengths
   - Key areas for improvement
   - Whether they would likely pass this round (be honest but constructive)
   - Next steps for preparation

Format your evaluation as a well-structured report using Markdown. Be honest but constructive - your goal is to help the candidate improve.
"""
        
        # Create a simple LLM chain for the interview evaluation
        evaluation_prompt = PromptTemplate(
            input_variables=["job_title", "user_experience", "user_name", "history"],
            template=interview_evaluation_template
        )
        evaluation_chain = LLMChain(
            llm=llm,
            prompt=evaluation_prompt,
            verbose=True
        )
        
        # Wrap the LLM chain in a simple interface that matches our agent_executor
        class EvaluationWrapper:
            def __init__(self, chain):
                self.chain = chain
                
            def invoke(self, inputs):
                # Process inputs for the evaluation
                processed_inputs = {
                    "job_title": inputs.get("job_title", ""),
                    "user_experience": inputs.get("user_experience", ""),
                    "user_name": inputs.get("user_name", "Candidate"),
                    "history": self._format_history(inputs.get("history", []))
                }
                
                # Run the chain
                result = self.chain.invoke(processed_inputs)
                
                # Return in the same format as agent_executor
                return {"output": result["text"]}
                
            def _format_history(self, history):
                """Format the history into a readable format for the LLM."""
                formatted = ""
                for message in history:
                    role = message.get("role", "")
                    content = message.get("content", "")
                    
                    if role == "system":
                        continue  # Skip system messages
                    elif role == "user":
                        formatted += f"Candidate: {content}\n\n"
                    elif role == "assistant":
                        formatted += f"Interviewer: {content}\n\n"
                        
                return formatted.strip()
        
        return EvaluationWrapper(evaluation_chain)
    
    # Standard interview prep agent (not mock interview)
    search = DuckDuckGoSearchRun()
    tools = [
        Tool(
            name="DuckDuckGo Search",
            func=search.run,
            description="Useful for searching the internet for the latest information on interview questions, company roles, and preparation strategies for a specific job title."
        )
    ]

    # This prompt is designed for a ReAct agent
    template = """You are an expert interview coach. Your goal is to create a comprehensive, up-to-date interview preparation guide based on a target job title and the user's experience. You must use your search tool to find relevant information.

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
    Final Answer: [Your complete, well-formatted markdown guide here]
    ```

    **User Experience:**
    {user_experience}

    **Target Job Title:**
    {job_title}

    **Instructions for Final Answer:**
    1.  **Research the Role:** Based on your search, describe the common responsibilities and required skills for the target job title.
    2.  **Behavioral Questions:** List 10-15 likely behavioral questions tailored to the role. For each, explain what the interviewer is looking for.
    3.  **Technical Questions:** List 10-15 potential technical questions or topics relevant to the role.
    4.  **Mock Interview Scenario:** Provide a detailed mock interview problem or case study.
    5.  **General Tips:** Offer advice on structuring answers (like the STAR method), questions to ask the interviewer, and follow-up best practices.
    6.  **Format:** The entire final answer must be a single, clean, well-organized Markdown block.

    Begin!

    Thought: {agent_scratchpad}
    """

    prompt = PromptTemplate(
        input_variables=["job_title", "user_experience", "agent_scratchpad", "tools", "tool_names"],
        template=template
    )

    agent = create_react_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)

    return agent_executor
