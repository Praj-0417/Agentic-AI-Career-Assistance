import os
import time
import requests
from typing import Any, List, Mapping, Optional

from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_community.tools import DuckDuckGoSearchRun
from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain.llms.base import LLM

load_dotenv()

# --- Start of Custom Wrapper ---

class ChatTogetherNative(LLM):
    """
    Custom LangChain wrapper for the native Together AI API.
    This bypasses the OpenAI-compatible endpoint to avoid its token limits.
    Includes retry logic for handling temporary API failures.
    """
    model: str = "deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free"
    together_api_key: str = os.environ.get("TOGETHER_API_KEY")
    temperature: float = 0.7
    max_tokens: int = 5000
    max_retries: int = 3
    initial_retry_delay: float = 1.0

    @property
    def _llm_type(self) -> str:
        return "together_ai_native"

    def _make_api_call(self, headers: dict, json_data: dict, retry_count: int = 0) -> str:
        """Make an API call with retry logic and rate limit handling."""
        try:
            response = requests.post(
                "https://api.together.xyz/v1/chat/completions",
                headers=headers,
                json=json_data,
                timeout=30  # Add a timeout
            )
            
            # Handle rate limiting specifically
            if response.status_code == 429:
                if retry_count < self.max_retries:
                    # For rate limits, use longer delays
                    delay = self.initial_retry_delay * (4 ** retry_count)  # Use 4 instead of 2 for longer delays
                    print(f"Rate limit hit, waiting {delay:.1f} seconds before retry... (Attempt {retry_count + 1}/{self.max_retries})")
                    time.sleep(delay)
                    return self._make_api_call(headers, json_data, retry_count + 1)
                else:
                    error_msg = (
                        "Rate limit exceeded. Please try:\n"
                        "1. Wait a few minutes before making another request\n"
                        "2. Check your API usage on together.ai\n"
                        "3. Consider using a different model from the free tier"
                    )
                    print(error_msg)
                    return error_msg
            
            # Handle other errors
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
            
        except requests.exceptions.RequestException as e:
            if retry_count < self.max_retries:
                # Calculate delay with exponential backoff
                delay = self.initial_retry_delay * (2 ** retry_count)
                print(f"API call failed, retrying in {delay:.1f} seconds... (Attempt {retry_count + 1}/{self.max_retries})")
                print(f"Error was: {str(e)}")
                time.sleep(delay)
                return self._make_api_call(headers, json_data, retry_count + 1)
            else:
                error_msg = f"Error: API request failed after {self.max_retries} retries: {str(e)}"
                print(error_msg)
                return error_msg
        except KeyError as e:
            error_msg = f"Error: Invalid response format from API: {str(e)}"
            print(error_msg)
            return error_msg

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        headers = {
            "Authorization": f"Bearer {self.together_api_key}",
            "Content-Type": "application/json",
        }

        json_data = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "messages": [{"role": "user", "content": prompt}],
        }

        if stop is not None:
            json_data["stop"] = stop

        return self._make_api_call(headers, json_data)

    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        """Get the identifying parameters."""
        return {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "max_retries": self.max_retries,
            "initial_retry_delay": self.initial_retry_delay,
        }

# --- End of Custom Wrapper ---


def get_qa_bot():
    """
    Initializes and returns a Q&A bot for career guidance.
    This bot uses a simple LLMChain for direct question answering.
    """
    llm = ChatTogetherNative(model="deepseek-ai/deepseek-coder-33b-instruct")

    prompt_template = """You are a helpful and friendly AI assistant specializing in career guidance for software development and AI. Your goal is to provide concise, accurate, and encouraging answers to user questions. Do not answer technical 'how-to' questions (e.g., 'how do I implement a linked list?'). Instead, guide users to the 'Tutorials Agent' for those. Focus on career advice, job market trends, interview tips, and learning strategies.

    User's Question: {question}

    Your Answer:"""
    
    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["question"]
    )

    # Use a simple LLMChain for direct Q&A
    chain = LLMChain(llm=llm, prompt=prompt)
    
    return chain

def get_tutorial_agent():
    """
    Initializes and returns the tutorial agent. Now uses a ReAct agent with a 
    search tool to generate high-quality, up-to-date tutorials.
    """
    llm = ChatTogetherNative(
        model="mistralai/Mixtral-8x7B-Instruct-v0.1", 
        temperature=0.5,
        max_tokens=8192,  # Using a large, stable token limit for the paid model.
    )
    
    search = DuckDuckGoSearchRun()
    tools = [
        Tool(
            name="DuckDuckGo Search",
            func=search.run,
            description="Useful for searching the internet for up-to-date information on a given topic to write a tutorial about. Use it to gather facts, code examples, and best practices."
        )
    ]

    # This is the new, robust prompt template specifically for the ReAct agent.
    template = '''You are an expert technical writer and educator. Your mission is to create the **best beginner-friendly, project-based tutorial on the web** for a given topic.
Your target audience is an absolute beginner, so you must explain everything clearly and assume no prior knowledge.

**YOUR PROCESS:**
1.  **Think & Research:** Your first step is to use the DuckDuckGo Search tool to find the best existing beginner tutorials on the requested topic. Use search queries like "[TOPIC] for beginners," "simple [TOPIC] project," and "getting started with [TOPIC]." Your goal is to understand how the best educators teach this topic.
2.  **Synthesize:** Do not just copy one tutorial. Find 2-3 high-quality sources and synthesize their best ideas, explanations, and code into a single, superior tutorial. Your final answer should be more comprehensive and easier to follow than any single source you found.
3.  **Structure the Final Answer:** After your research is complete, structure all your findings into a single, final answer that is a complete, well-formatted markdown tutorial. Your final answer must start with "# Table of Contents" and contain the full tutorial.

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

When you have gathered enough information and are ready to write the final tutorial, you MUST use the format:

```
Thought: Do I need to use a tool? No
Final Answer: [Your complete, well-formatted markdown tutorial here]
```

**CRITICAL OUTPUT FORMATTING:**
- Your final response to the user is ONLY the text that comes after "Final Answer:".
- The "Final Answer:" block MUST contain the entire, complete, final markdown tutorial.
- DO NOT write the tutorial outside of the "Final Answer:" block.
- DO NOT write references like "see the tutorial above" in the Final Answer block. This will fail.

**TUTORIAL REQUIREMENTS FOR THE FINAL ANSWER:**
-   **Beginner-Focused:** Explain every concept simply. Every line of code must be commented or explained.
-   **Project-Based:** The tutorial must walk the user through building one single, small, functional project from start to finish.
-   **Complete & Runnable:** All code must be in complete, copy-pastable markdown code blocks. The user must be able to run the code and have a working app.
-   **No Placeholders:** Do NOT use placeholder text like "Step 1: Install...". Provide the actual, complete commands and code.

**STRUCTURE:**
1.  **Table of Contents:** A detailed table of contents.
2.  **Introduction:** A compelling overview of the topic and the simple project they will build.
3.  **Prerequisites:** A list of required knowledge or tools with installation commands.
4.  **Core Concepts:** Clear, simple explanations of only the fundamental concepts needed for the project.
5.  **Step-by-Step Project Guide:** The main section. A detailed guide to building the project. This section must contain ALL the code, fully explained.
6.  **Running the Project:** Clear instructions on how to run the final code.
7.  **Summary:** A recap of key learning points.
8.  **Further Reading:** A list of 1-3 high-quality, relevant links from your research.
9.  **Continuation:** If the topic is broad, conclude with the exact line: `To continue this tutorial, please ask for '[TOPIC] Part 2'.`

Begin!

Question: {input}
{agent_scratchpad}'''

    prompt = PromptTemplate.from_template(template)
    
    agent = create_react_agent(llm, tools, prompt)

    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True, max_iterations=15, max_execution_time=900)

    return agent_executor
