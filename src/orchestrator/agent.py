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
        # Initialize the routing LLM
        self.routing_llm = ChatTogetherNative(
            model="mistralai/Mixtral-8x7B-Instruct-v0.1", 
            temperature=0.2,  # Lower temperature for more deterministic routing
            max_tokens=1024   # Shorter responses for routing
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
            }
        }
        
        # Create the routing chain
        self.routing_template = """
You are an intelligent routing agent for a career assistant app. Your job is to analyze the user's message and determine which specialized agent should handle it.

**User Message:** {user_message}

**Available Agents:**
1. Resume Builder - For creating, reviewing or improving resumes and CVs
2. Job Search - For finding job opportunities, application advice, and career guidance
3. Interview Prep - For interview preparation, mock interviews, and feedback
4. Tutorials - For learning resources and guides on specific skills or topics

**Current Context:**
User Profile: {user_profile}
Recent Conversation: {recent_conversation}

Based on the user's message, determine which agent is most appropriate to handle this request.
If the user is clearly switching topics or explicitly asking for a different service, route to the new agent.
If the user is continuing a previous conversation, prefer the same agent that handled the last message.
If the message is a general greeting or unclear, ask a clarifying question about what they need help with today.

Rules for resume-related messages:
- Route to RESUME_BUILDER if the user mentions resume, CV, portfolio, or job application in any way
- If the user includes a job description or listing, definitely route to RESUME_BUILDER
- If the user asks to update, improve, tailor, or create a resume, route to RESUME_BUILDER
- ANY message about creating, improving, or discussing resumes should go to RESUME_BUILDER

Rules for tutorials:
- Route to TUTORIALS if the user asks about learning a skill, wants a guide, tutorial, or educational material
- If the user asks how to do something technical or asks to learn about a topic, route to TUTORIALS

**Response Format:**
Return ONLY ONE of these exact strings: "RESUME_BUILDER", "JOB_SEARCH", "INTERVIEW_PREP", "TUTORIALS", or "UNCLEAR".
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
            "TUTORIALS": None
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
        
        # Extract the routing decision (the LLM should return just the agent name)
        raw_decision = routing_result["text"].strip().upper()
        
        # More robustly find the agent name in the response
        valid_routes = ["RESUME_BUILDER", "JOB_SEARCH", "INTERVIEW_PREP", "TUTORIALS", "UNCLEAR"]
        routing_decision = "UNCLEAR"  # Default
        for route in valid_routes:
            if route in raw_decision:
                routing_decision = route
                break
        
        # Validate the routing decision - this is now a fallback
        if routing_decision not in valid_routes:
            # Default to unclear if we get an invalid response
            routing_decision = "UNCLEAR"
            
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
                    
            return self.specialized_agents[agent_type]
        except Exception as e:
            raise Exception(f"Failed to initialize {agent_type} agent: {str(e)}")
    
    def process_message(self, user_message, agent_type=None, **kwargs):
        """
        Process a user message using the appropriate agent.
        If agent_type is provided, use that specific agent.
        Otherwise, route the message to determine the appropriate agent.
        """
        # Update conversation history
        self.shared_context["conversation_history"].append(user_message)
        
        # Determine which agent to use
        if agent_type is None:
            agent_type = self.route_message(user_message)
            print(f"DEBUG - Routed to agent: {agent_type}")
        
        # If the intent is unclear, return a clarifying message
        if agent_type == "UNCLEAR":
            clarifying_response = "I'd like to help you better. Could you please clarify what you're looking for? I can help with resumes, job searches, interview preparation, or tutorials for skill development."
            self.shared_context["conversation_history"].append(clarifying_response)
            return {"agent_type": "UNCLEAR", "response": clarifying_response}
        
        # Get or create the appropriate agent
        try:
            agent = self._get_or_create_agent(agent_type, **kwargs)
            
            # Prepare inputs for the agent, including shared context
            agent_inputs = {
                "user_message": user_message,
                **kwargs
            }
            
            # For specific agent types, map to their expected input format
            if agent_type == "RESUME_BUILDER":
                # Resume builder expects these specific input keys
                agent_inputs = {
                    "user_details": kwargs.get("user_details", ""),
                    "job_description": kwargs.get("job_description", ""),
                    "previous_resume": kwargs.get("previous_resume", ""),
                    "user_request": kwargs.get("user_request", user_message)
                }
                
                # If user_details is empty, try to construct from user_profile
                if not agent_inputs["user_details"] and "user_profile" in self.shared_context:
                    profile = self.shared_context["user_profile"]
                    user_details = ""
                    if "name" in profile and profile["name"]:
                        user_details += f"Name: {profile['name']}\n"
                    if "job_title" in profile and profile["job_title"]:
                        user_details += f"Target Job Title: {profile['job_title']}\n"
                    if "experience" in profile and profile["experience"]:
                        user_details += f"Experience: {profile['experience']}\n"
                    if "skills" in profile and profile["skills"]:
                        user_details += f"Skills: {profile['skills']}\n"
                    
                    if user_details:
                        agent_inputs["user_details"] = user_details
                
                # Debug info
                print(f"Resume Builder inputs: {agent_inputs.keys()}")
                print(f"User details present: {'Yes' if agent_inputs['user_details'] else 'No'}")
                print(f"Job description present: {'Yes' if agent_inputs['job_description'] else 'No'}")
            elif agent_type == "JOB_SEARCH":
                # Job search expects these specific keys
                agent_inputs = {
                    "job_title": kwargs.get("job_title", ""),
                    "location": kwargs.get("location", ""),
                    "job_type": kwargs.get("job_type", "Full-time"),
                    "user_context": kwargs.get("user_context", ""),
                    "input": user_message  # Keep original message for parsing
                }
            elif agent_type in ["INTERVIEW_PREP", "INTERVIEW_MOCK", "INTERVIEW_EVALUATE"]:
                # Interview prep expects these keys
                agent_inputs = {
                    "job_title": kwargs.get("job_title", ""),
                    "user_experience": kwargs.get("user_experience", ""),
                    "user_name": kwargs.get("user_name", "Candidate"),
                    "history": kwargs.get("history", []),
                    "input": user_message  # Keep original message for parsing
                }
            elif agent_type == "TUTORIALS":
                # Tutorials agent expects these keys
                agent_inputs = {
                    "user_message": user_message,
                    "user_context": kwargs.get("user_context", "")
                }
            
                # Add relevant shared context to the agent inputs
            if agent_type == "RESUME_BUILDER":
                # If we have a resume in user profile, make it available
                if "resume_content" in self.shared_context["user_profile"]:
                    agent_inputs["previous_resume"] = self.shared_context["user_profile"]["resume_content"]
                
                # If we previously got a job description from the user, save it to the profile
                if agent_inputs.get("job_description") and len(agent_inputs["job_description"]) > 100:
                    self.shared_context["user_profile"]["last_job_description"] = agent_inputs["job_description"]
                # If we don't have a job description but we had one before, use it
                elif "last_job_description" in self.shared_context["user_profile"]:
                    agent_inputs["job_description"] = self.shared_context["user_profile"]["last_job_description"]
            
            if agent_type == "JOB_SEARCH" and "skills" in self.shared_context["user_profile"]:
                agent_inputs["user_context"] = self.shared_context["user_profile"]["skills"]
            
            if agent_type in ["INTERVIEW_PREP", "INTERVIEW_MOCK", "INTERVIEW_EVALUATE"] and "experience" in self.shared_context["user_profile"]:
                agent_inputs["user_experience"] = self.shared_context["user_profile"]["experience"]
            
            # Process the message with the specialized agent
            # Validate required inputs before invoking the agent
            if agent_type == "RESUME_BUILDER":
                # If this is a direct request from main chat, it might be asking for a job description
                if not agent_inputs.get("job_description"):
                    # Check if the message itself contains a job description
                    if len(user_message) > 200 and any(kw in user_message.lower() for kw in 
                                                   ["requirements", "qualifications", "responsibilities", 
                                                    "job description", "position", "looking for"]):
                        # Use the message as a job description if it looks like one
                        agent_inputs["job_description"] = user_message
                        print(f"Using message as job description: {len(user_message)} chars")
                    else:
                        # If not, ask for a job description
                        return {"output": "I need a job description to create or tailor a resume. Please provide a job description, or switch to Resume Builder mode where you can enter all the required information."}
                
                # Make sure we have at least minimal user details
                if not agent_inputs.get("user_details"):
                    return {"output": "I need some information about you to create a resume. Please update your profile or provide details about your experience and skills."}
                
                # Print the inputs being provided to help with debugging
                print(f"DEBUG - Resume Builder agent inputs: {agent_inputs.keys()}")
                print(f"DEBUG - job_description length: {len(agent_inputs.get('job_description', ''))}")
                print(f"DEBUG - user_details length: {len(agent_inputs.get('user_details', ''))}")
            
            if agent_type == "JOB_SEARCH" and (not agent_inputs.get("job_title") or not agent_inputs.get("location")):
                missing = []
                if not agent_inputs.get("job_title"):
                    missing.append("job title")
                if not agent_inputs.get("location"):
                    missing.append("location")
                return {"output": f"I need {' and '.join(missing)} to search for jobs. Please provide this information."}
            
            if agent_type in ["INTERVIEW_PREP", "INTERVIEW_MOCK", "INTERVIEW_EVALUATE"] and not agent_inputs.get("job_title"):
                return {"output": "I need to know which job title you're interviewing for to provide relevant preparation. Please provide a job title."}
            
            # Invoke the agent with validated inputs
            try:
                result = agent.invoke(agent_inputs)
                response = result.get("output", "I'm having trouble processing that request. Could you try again?")
                print(f"DEBUG - Successfully invoked {agent_type} agent")
            except Exception as e:
                error_msg = str(e)
                print(f"ERROR invoking {agent_type} agent: {error_msg}")
                
                # More detailed error for resume builder
                if agent_type == "RESUME_BUILDER":
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
        elif category_key == "unclear":
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
            "response": response
        }
    
    def get_past_responses(self, category=None):
        """Get past responses, optionally filtered by category."""
        if category:
            return self.shared_context["past_responses"].get(category, [])
        return self.shared_context["past_responses"]
