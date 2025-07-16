import os
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from src.guidance.agent import ChatTogetherNative
from src.resume_builder.agent import get_resume_builder_agent
from src.qna.agent import get_job_search_agent
from src.interview_prep.agent import get_interview_prep_agent
from src.tutorials.agent import get_tutorials_agent

load_dotenv()

class OrchestratorAgent:
    """
    A central orchestrator that manages shared context and routes conversations
    to the appropriate specialized agents based on user intent.
    """
    
    def __init__(self):
        """Initialize the orchestrator with a routing LLM and specialized agents."""
        # Initialize the routing LLM with Mixtral for better classification
        self.routing_llm = ChatTogetherNative(
            model="mistralai/Mixtral-8x7B-Instruct-v0.1", 
            temperature=0.0,  # Zero temperature for deterministic routing
            max_tokens=50     # Short responses since we only need the category
        )
        
        # Shared context that will be passed between different agents
        self.shared_context = {
            "user_profile": {},
            "conversation_history": [],
            "past_responses": {
                "resume_builder": [],
                "job_search": [],
                "interview_prep": [],
                "tutorials": []
            },
            "data_gathering_state": None  # To track multi-turn data collection
        }
        
        # Create the routing chain with a more focused template
        self.routing_template = """You are a task classifier. Analyze the user's latest message and categorize it into exactly one category.

**Latest Message to Classify:**
"{user_message}"

**Valid Categories:**
- RESUME_BUILDER: For anything about creating, editing, or reviewing resumes/CVs
- JOB_SEARCH: For finding jobs, career advice, or application guidance
- INTERVIEW_PREP: For interview help, practice, or feedback
- INTERVIEW_MOCK: For starting a mock/practice interview session
- TUTORIALS: For learning materials and skill guides
- GENERAL_QNA: For greetings or general questions
- UNCLEAR: If the intent cannot be determined

**Context (Use Only If Latest Message Is Unclear):**
Prior Messages: {recent_conversation}
User Info: {user_profile}

**Classification Rules:**
1. Focus primarily on the latest message
2. If the message contains multiple intents, choose the most specific one
3. For messages with both a greeting ("hi", "hello") and a specific request, classify based on the specific request
4. Messages mentioning "resume", "CV", or "portfolio" -> RESUME_BUILDER
5. Questions about learning or how to do something -> TUTORIALS
6. Only use GENERAL_QNA for pure greetings or truly general questions
7. When in doubt, use UNCLEAR

Return only one category name. Example: RESUME_BUILDER

Rules for resume-related messages:
- Route to RESUME_BUILDER if the user mentions resume, CV, portfolio, or job application in any way
- If the user includes a job description or listing, definitely route to RESUME_BUILDER
- If the user asks to update, improve, tailor, or create a resume, route to RESUME_BUILDER
- ANY message about creating, improving, or discussing resumes should go to RESUME_BUILDER

Rules for interview-related messages:
- Route to INTERVIEW_MOCK if the user asks to "start a mock interview", "practice interview", "simulate interview", or "conduct a mock interview"
- Route to INTERVIEW_MOCK if they mention "mock" or "practice" along with "interview"
- Route to INTERVIEW_PREP for general interview advice, tips, or preparation that isn't a practice session

Rules for tutorials:
- Route to TUTORIALS if the user asks about learning a skill, wants a guide, tutorial, or educational material
- If the user asks how to do something technical or asks to learn about a topic, route to TUTORIALS

**Response Format:**
Return ONLY ONE of these exact strings: "RESUME_BUILDER", "JOB_SEARCH", "INTERVIEW_PREP", "INTERVIEW_MOCK", "TUTORIALS", "GENERAL_QNA", or "UNCLEAR".
"""
        
        self.routing_prompt = PromptTemplate(
            input_variables=["user_message", "user_profile", "recent_conversation"],
            template=self.routing_template
        )
        
        self.routing_chain = LLMChain(
            llm=self.routing_llm,
            prompt=self.routing_prompt,
            verbose=True
        )
        
        # Initialize specialized agents (we'll create them only when needed)
        self.specialized_agents = {
            "RESUME_BUILDER": None,
            "JOB_SEARCH": None,
            "INTERVIEW_PREP": None,
            "INTERVIEW_MOCK": None,
            "INTERVIEW_EVALUATE": None,
            "TUTORIALS": None,
            "GENERAL_QNA": None
        }
        
    def update_user_profile(self, key, value):
        """Update the user profile with new information."""
        self.shared_context["user_profile"][key] = value
        
    def get_user_profile(self):
        """Return the current user profile."""
        return self.shared_context["user_profile"]
        
    def route_message(self, user_message):
        """Determine which agent should handle the user's message."""
        # Get the recent conversation for context (last 3 turns)
        recent_conversation = self.shared_context["conversation_history"][-3:] if self.shared_context["conversation_history"] else []
        recent_conversation_str = "\n".join([f"{'User' if i%2==0 else 'Assistant'}: {msg}" for i, msg in enumerate(recent_conversation)])
        
        # Use the routing chain to determine the appropriate agent
        routing_result = self.routing_chain.invoke({
            "user_message": user_message,
            "user_profile": str(self.shared_context["user_profile"]),
            "recent_conversation": recent_conversation_str
        })
        
        # Get and validate the routing decision
        raw_decision = routing_result["text"].strip().upper()
        valid_routes = ["RESUME_BUILDER", "JOB_SEARCH", "INTERVIEW_PREP", "INTERVIEW_MOCK", "TUTORIALS", "GENERAL_QNA", "UNCLEAR"]
        
        # Clean up the response - remove any extra text, just get the category
        routing_decision = "UNCLEAR"
        for route in valid_routes:
            if route == raw_decision:  # Exact match only
                routing_decision = route
                break
            
        print(f"DEBUG - Raw routing decision: {raw_decision}")
        print(f"DEBUG - Final routing decision: {routing_decision}")
            
        return routing_decision
    
    def _get_or_create_agent(self, agent_type, **kwargs):
        """Get an existing agent or create a new one if it doesn't exist."""
        try:
            if self.specialized_agents[agent_type] is None:
                if agent_type == "RESUME_BUILDER":
                    self.specialized_agents[agent_type] = get_resume_builder_agent()
                elif agent_type == "JOB_SEARCH":
                    self.specialized_agents[agent_type] = get_job_search_agent()
                elif agent_type == "INTERVIEW_PREP":
                    self.specialized_agents[agent_type] = get_interview_prep_agent()
                elif agent_type == "INTERVIEW_MOCK":
                    self.specialized_agents[agent_type] = get_interview_prep_agent(mock=True)
                elif agent_type == "INTERVIEW_EVALUATE":
                    self.specialized_agents[agent_type] = get_interview_prep_agent(evaluate=True)
                elif agent_type == "TUTORIALS":
                    self.specialized_agents[agent_type] = get_tutorials_agent()
                elif agent_type == "GENERAL_QNA":
                    self.specialized_agents[agent_type] = ChatTogetherNative(
                        model="mistralai/Mixtral-8x7B-Instruct-v0.1",
                        temperature=0.7,
                        max_tokens=2048
                    )
                    
            return self.specialized_agents[agent_type]
        except Exception as e:
            raise Exception(f"Failed to initialize {agent_type} agent: {str(e)}")
    
    def _ask_for_missing_info(self, agent_type, missing_fields, collected_fields):
        """Starts a data gathering conversation or asks for the next piece of missing info."""
        self.shared_context['data_gathering_state'] = {
            "agent": agent_type,
            "missing_fields": missing_fields,
            "collected_fields": collected_fields
        }
        
        next_field_to_ask = missing_fields[0]
        
        # Create a more user-friendly question
        if next_field_to_ask == "job_description":
            question = "I can certainly help with that. To tailor the resume perfectly, could you please provide the job description?"
        elif next_field_to_ask == "user_details":
            question = "Thank you. Now, please provide your professional background, including work experience, skills, and education."
        elif next_field_to_ask == "job_title":
            question = "I can help with that. What is the job title you are interested in?"
        else:
            question = f"Great. Now, could you please provide the {next_field_to_ask.replace('_', ' ')}?"
            
        return {"agent_type": agent_type, "output": question}

    def process_message(self, user_message, agent_type=None, **kwargs):
        """
        Process a user message using the appropriate agent.
        Handles multi-turn conversations to gather required information.
        For all direct tab searches, agent_type must be provided and routing is skipped.
        Only the chat tab (agent_type=None) uses routing.
        """
        # Update conversation history
        self.shared_context["conversation_history"].append(user_message)

        # Check if we are in the middle of gathering data
        gathering_state = self.shared_context.get("data_gathering_state")
        if gathering_state:
            current_agent = gathering_state["agent"]
            field_to_collect = gathering_state["missing_fields"].pop(0)
            gathering_state["collected_fields"][field_to_collect] = user_message

            if not gathering_state["missing_fields"]:
                # All info collected, proceed to invoke the agent
                self.shared_context["data_gathering_state"] = None  # Clear state
                agent_type = current_agent
                # Pass collected fields to the agent
                kwargs.update(gathering_state["collected_fields"])
            else:
                # Still more info to collect, ask the next question
                return self._ask_for_missing_info(
                    current_agent,
                    gathering_state["missing_fields"],
                    gathering_state["collected_fields"]
                )

        # If agent_type is None, this is a chat attempt from the main chat tab
        if agent_type is None:
            # Route the message to the appropriate specialized agent
            routed_type = self.route_message(user_message)
            print(f"DEBUG - Routed to agent: {routed_type}")
            
            # In the main chat tab, we allow routing to any agent
            agent_type = routed_type

        # If the intent is unclear, return a clarifying message (only possible in chat)
        if agent_type == "UNCLEAR":
            clarifying_response = "I'd like to help you better. Could you please clarify what you're looking for? I can help with resumes, job searches, interview preparation, or tutorials for skill development."
            self.shared_context["conversation_history"].append(clarifying_response)
            return {"agent_type": "UNCLEAR", "output": clarifying_response}

        # Get or create the appropriate agent
        try:
            agent = self._get_or_create_agent(agent_type, **kwargs)

            # Prepare inputs for the agent, including shared context
            agent_inputs = {"user_message": user_message, **kwargs}

            # For specific agent types, map to their expected input format and check for missing info
            if agent_type == "RESUME_BUILDER":
                profile = self.get_user_profile()
                user_details = kwargs.get("resume_user_details") or kwargs.get("user_details") or profile.get("experience", "") + "\n" + profile.get("skills", "")
                resume_in_progress = profile.get("resume_content", "")

                agent_inputs = {
                    "user_details": user_details.strip(),
                    "job_description": kwargs.get("job_description", ""),
                    "previous_resume": resume_in_progress,
                    "user_request": user_message
                }

                # Check for session end request
                if "end resume session" in user_message.lower():
                    if resume_in_progress:
                        self.shared_context["data_gathering_state"] = None
                        return {
                            "agent_type": "RESUME_BUILDER",
                            "output": "Your resume session has ended. You can start a new session anytime!"
                        }

                # Only ask for missing fields on initial resume creation
                if not resume_in_progress:
                    missing_fields = []
                    if not agent_inputs["job_description"]:
                        missing_fields.append("job_description")
                    if not agent_inputs["user_details"]:
                        missing_fields.append("user_details")

                    if missing_fields:
                        return self._ask_for_missing_info(agent_type, missing_fields, agent_inputs)

            elif agent_type == "JOB_SEARCH":
                agent_inputs = {
                    "job_title": kwargs.get("job_title", ""),
                    "location": kwargs.get("location", ""),
                    "job_type": kwargs.get("job_type", "Full-time"),
                    "user_context": kwargs.get("user_context", self.get_user_profile().get("skills", "")),
                    "input": user_message
                }
                missing_fields = []
                if not agent_inputs["job_title"]:
                    missing_fields.append("job_title")
                if not agent_inputs["location"]:
                    missing_fields.append("location")

                if missing_fields:
                    return self._ask_for_missing_info(agent_type, missing_fields, agent_inputs)

            elif agent_type in ["INTERVIEW_PREP", "INTERVIEW_MOCK", "INTERVIEW_EVALUATE"]:
                profile = self.get_user_profile()
                agent_inputs = {
                    "job_title": kwargs.get("job_title", ""),
                    "user_experience": kwargs.get("user_experience", profile.get("experience", "")),
                    "user_name": kwargs.get("user_name", profile.get("name", "Candidate")),
                    "history": kwargs.get("history", []),
                    "input": user_message
                }
                if not agent_inputs["job_title"]:
                    return self._ask_for_missing_info(agent_type, ["job_title"], agent_inputs)

            elif agent_type == "TUTORIALS":
                agent_inputs = {
                    "user_message": user_message,
                    "user_context": kwargs.get("user_context", self.get_user_profile().get("skills", ""))
                }
            elif agent_type == "GENERAL_QNA":
                agent_inputs = {"user_input": user_message}

            # Invoke the agent with validated inputs
            try:
                if agent_type == "GENERAL_QNA":
                    # The base LLM is invoked directly with the user input string
                    result = agent.invoke(agent_inputs["user_input"])
                    response = result if isinstance(result, str) else "I'm having trouble processing that request."
                else:
                    result = agent.invoke(agent_inputs)
                    response = result.get("output", "I'm having trouble processing that request. Could you try again?")

                # For resume builder, save the latest resume
                if agent_type == "RESUME_BUILDER" and "END_SESSION" not in response:
                    self.update_user_profile("resume_content", response)

                print(f"DEBUG - Successfully invoked {agent_type} agent")
            except Exception as e:
                error_msg = str(e)
                print(f"ERROR invoking {agent_type} agent: {error_msg}")

                if "Rate limit exceeded" in error_msg:
                    response = (
                        "I apologize, but we're experiencing high traffic at the moment. Please:\n\n"
                        "1. Wait a few minutes before trying again\n"
                        "2. Try providing shorter, more focused responses\n"
                        "3. If the issue persists, you can save your progress and continue later\n\n"
                        "Your inputs have been saved and won't be lost."
                    )
                elif agent_type == "RESUME_BUILDER":
                    response = f"I encountered an error while creating your resume: {error_msg}\n\n"
                    response += "To create a resume, I need:\n"
                    response += "1. A job description (required)\n"
                    response += "2. Your professional details (experience, skills, education)\n\n"
                    response += "Please provide this information or switch to Resume Builder mode using the sidebar."
                else:
                    response = f"I encountered an error while processing your request: {error_msg}\n\nThis might be due to missing or incorrect input formats. Please check that you've provided all the required information."
        except Exception as e:
            error_msg = str(e)
            print(f"ERROR setting up {agent_type} agent: {error_msg}")
            response = f"I'm having trouble accessing that functionality right now: {error_msg}"

        # Update conversation history with the response
        self.shared_context["conversation_history"].append(response)

        # Store the response in past_responses
        category_key = agent_type.lower()
        if "interview" in category_key:
            category_key = "interview_prep"
        elif category_key == "unclear" or category_key == "general_qna":
            category_key = "other"

        # Make sure the category exists
        if category_key not in self.shared_context["past_responses"]:
            self.shared_context["past_responses"][category_key] = []

        # Store the response
        self.shared_context["past_responses"][category_key].append({
            "user_message": user_message,
            "response": response
        })

        # Create a debug log for tracking purposes
        print(f"DEBUG - Agent type: {agent_type}, Response stored in category: {category_key}")
        print(f"DEBUG - Response first 50 chars: {response[:50] if len(response) > 50 else response}")

        return {
            "agent_type": agent_type,
            "output": response
        }
    
    def get_past_responses(self, category=None):
        """Get past responses, optionally filtered by category."""
        if category:
            return self.shared_context["past_responses"].get(category, [])
        return self.shared_context["past_responses"]
