import os
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain_community.tools import DuckDuckGoSearchRun
from src.guidance.agent import ChatTogetherNative # Use the custom wrapper

load_dotenv()

def get_tutorials_agent():
    """
    Initializes and returns a tutorials agent for learning resources
    """
    llm = ChatTogetherNative(
        model="mistralai/Mixtral-8x7B-Instruct-v0.1", 
        temperature=0.5,
        max_tokens=4096
    )
    
    search = DuckDuckGoSearchRun()
    tools = [
        Tool(
            name="DuckDuckGo Search",
            func=search.run,
            description="Useful for finding up-to-date learning resources, tutorials, documentation, and educational content on programming, data science, and technology topics."
        )
    ]

    template = """You are an expert educational content creator specializing in technology, programming, and professional development. Your goal is to create comprehensive, structured learning resources on any technical topic the user requests. You must use your search tool to find relevant, up-to-date information.

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
    Final Answer: 
    [Your complete, well-formatted tutorial here - do NOT include triple backticks around your answer]
    ```

    **User Request:**
    {user_message}

    **User Background:**
    {user_context}

    **Instructions for Final Answer:**
    1. **Introduction:** Start with an overview of the topic and its importance.
    2. **Prerequisites:** List any background knowledge or tools needed.
    3. **Core Content:** Break down the topic into logical sections with:
       - Clear explanations of concepts
       - Step-by-step tutorials where applicable
       - Code examples (if programming-related)
       - Best practices and common pitfalls
    4. **Practical Application:** Include exercises or project ideas for practice.
    5. **Resources:** Recommend books, courses, or other learning materials.
    6. **Format:** Your answer must be a well-organized document with proper markdown headers (# for titles, ## for sections).
    7. **IMPORTANT:** Do NOT wrap your final answer in triple backticks, and make sure your content appears directly after "Final Answer:" without any backticks.

    Begin!

    Thought: {agent_scratchpad}
    """

    prompt = PromptTemplate(
        input_variables=["user_message", "user_context", "agent_scratchpad", "tools", "tool_names"],
        template=template
    )

    agent = create_react_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent, 
        tools=tools, 
        verbose=True, 
        handle_parsing_errors=True,
        return_intermediate_steps=False  # Don't include intermediate steps in output
    )
    
    # Create a wrapper to properly format the response
    class TutorialsAgentWrapper:
        def __init__(self, agent_executor):
            self.agent_executor = agent_executor
            
        def invoke(self, inputs):
            # Process the message with the agent executor
            result = self.agent_executor.invoke(inputs)
            
            # Extract and clean the output
            output = result.get("output", "")
            
            # Clean up the output to remove any ReAct formatting
            # If the output contains "Final Answer:", extract everything after it
            if "Final Answer:" in output:
                output = output.split("Final Answer:")[1].strip()
            
            # Remove any markdown block indicators that might be causing the issue
            if output.startswith("```markdown"):
                output = output.replace("```markdown", "", 1)
                if output.endswith("```"):
                    output = output[:-3]
            elif output.startswith("```"):
                output = output.replace("```", "", 1)
                if output.endswith("```"):
                    output = output[:-3]
            
            # Remove any triple backticks at the beginning or end
            output = output.strip("```").strip()
            
            # Special case: if output is empty but we have a full result output, use that instead
            if not output.strip() and result.get("output", "").strip():
                # Try to extract content between thought and final answer
                raw_output = result.get("output", "")
                
                # Extract all content between thoughts
                import re
                matches = re.findall(r'Thought:.*?(?=Thought:|$)', raw_output, re.DOTALL)
                if matches:
                    # Use the last thought block which should have the content
                    last_match = matches[-1].strip()
                    # Clean up any remaining format markers
                    output = re.sub(r'Thought:.*?(?=\n)', '', last_match, flags=re.DOTALL).strip()
                    # Remove Action/Observation blocks
                    output = re.sub(r'Action:.*?Observation:.*?(?=\n|$)', '', output, flags=re.DOTALL).strip()
                    # Also remove tool markup
                    output = output.replace("Final Answer:", "").strip()
            
            # Ensure the output is properly formatted markdown
            # If it looks like plain text without markdown formatting, add basic formatting
            if not any(md_element in output for md_element in ["##", "**", "*", "```", "|", "1.", "-", ">"]):
                lines = output.split("\n")
                formatted_output = []
                current_section = None
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        formatted_output.append("")
                        continue
                        
                    # Try to detect section headers
                    if line.isupper() or (len(line) < 50 and line.endswith(":")):
                        current_section = line.strip(":")
                        formatted_output.append(f"## {current_section}")
                    else:
                        formatted_output.append(line)
                
                output = "\n".join(formatted_output)
            
            # Return properly formatted output
            return {"output": output}
    
    return TutorialsAgentWrapper(agent_executor)
