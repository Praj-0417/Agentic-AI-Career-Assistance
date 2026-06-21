import os
import uuid
import logging
from typing import Any, List, Dict, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# Import LangGraph and state
from src.state import make_initial_state
from src.graph.graph_builder import compile_graph
from src.graph.checkpointer import get_checkpointer
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

# Import direct specialist nodes
from src.graph.nodes.resume_builder_node import resume_builder_node
from src.graph.nodes.salary_negotiator_node import salary_negotiator_node
from src.graph.nodes.evaluation_node import evaluation_node

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("career-api")

app = FastAPI(title="career.ai API", version="1.0.0")

# Setup CORS for React dev server (typically port 5173 or 3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For local development, allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Central compiled graph
try:
    checkpointer = get_checkpointer()
    graph = compile_graph(checkpointer)
    logger.info("LangGraph compiled successfully.")
except Exception as e:
    logger.error(f"Error compiling LangGraph: {e}")
    graph = None

# Helper to invoke the graph
def run_agent_graph(
    user_text: str,
    extra_task: Optional[Dict[str, Any]] = None,
    thread_id: str = "default-thread",
    user_profile: Optional[Dict[str, str]] = None,
    interview_history: Optional[List[Dict[str, str]]] = None,
    interview_mode: str = "prep"
) -> Dict[str, Any]:
    if not graph:
        raise HTTPException(status_code=500, detail="LangGraph is not initialized.")
    
    # Formulate initial state
    state = make_initial_state()
    state["user_profile"] = user_profile or {
        "name": "", "job_title": "", "experience": "", "skills": "", "resume_content": ""
    }
    
    # Build list of LangChain messages
    messages = []
    # If we have history, we can populate it (e.g. for chat or mock interview tracking)
    if interview_history:
        for msg in interview_history:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))
    
    # Append latest message
    messages.append(HumanMessage(content=user_text))
    state["messages"] = messages
    
    # Task Inputs
    state["task_input"] = {
        "user_message": user_text,
        **(extra_task or {})
    }
    
    state["interview_history"] = interview_history or []
    state["interview_mode"] = interview_mode
    
    config = {"configurable": {"thread_id": thread_id}}
    
    # Invoke Graph
    result = graph.invoke(state, config)
    
    # Format message objects to serializable dicts
    serializable_history = []
    for msg in result.get("messages", []):
        if isinstance(msg, HumanMessage):
            serializable_history.append({"role": "user", "content": msg.content})
        elif isinstance(msg, AIMessage):
            serializable_history.append({"role": "assistant", "content": msg.content})
        elif isinstance(msg, BaseMessage):
            role = "user" if "human" in getattr(msg, "type", "") else "assistant"
            serializable_history.append({"role": role, "content": msg.content})
        elif isinstance(msg, dict):
            serializable_history.append(msg)

    # Return structured output
    return {
        "agent_output": result.get("agent_output", ""),
        "graph_trace": result.get("graph_trace", []),
        "user_profile": result.get("user_profile", {}),
        "task_input": result.get("task_input", {}),
        "interview_history": result.get("interview_history", []) or serializable_history,
        "interview_mode": result.get("interview_mode", "prep")
    }

# ── REQUEST MODELS ───────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    thread_id: str
    user_profile: Optional[Dict[str, str]] = None
    interview_history: Optional[List[Dict[str, str]]] = None
    interview_mode: Optional[str] = "prep"

class GenerateResumeRequest(BaseModel):
    job_description: str
    user_details: str

class RefineResumeRequest(BaseModel):
    previous_resume: str
    refinement_request: str
    job_description: Optional[str] = ""

class JobSearchRequest(BaseModel):
    job_title: str
    location: str
    job_type: str
    user_context: Optional[str] = ""
    thread_id: Optional[str] = "job-thread"

class PrepGuideRequest(BaseModel):
    job_title: str
    user_experience: Optional[str] = ""
    user_name: Optional[str] = "Candidate"
    focus_area: Optional[str] = ""
    thread_id: Optional[str] = "prep-thread"

class MockStartRequest(BaseModel):
    job_title: str
    user_experience: Optional[str] = ""
    user_name: Optional[str] = "Candidate"
    thread_id: str

class MockAnswerRequest(BaseModel):
    answer: str
    job_title: str
    user_experience: Optional[str] = ""
    user_name: Optional[str] = "Candidate"
    history: List[Dict[str, str]]
    thread_id: str

class MockEvaluateRequest(BaseModel):
    job_title: str
    user_experience: Optional[str] = ""
    user_name: Optional[str] = "Candidate"
    history: List[Dict[str, str]]

class TranscriptEvaluateRequest(BaseModel):
    job_title: str
    user_experience: Optional[str] = ""
    user_name: Optional[str] = "Candidate"
    transcript: str

class TutorialRequest(BaseModel):
    topic: str
    user_background: Optional[str] = ""
    thread_id: Optional[str] = "tutorial-thread"

class SalaryRequest(BaseModel):
    job_title: str
    location: Optional[str] = "Not specified"
    experience: Optional[str] = "Not specified"
    current_offer: Optional[str] = "Not provided"
    current_salary: Optional[str] = "Not provided"
    skills: Optional[str] = ""

class SettingsUpdate(BaseModel):
    together_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    google_cse_id: Optional[str] = None

# ── API ENDPOINTS ─────────────────────────────────────────────────────────────

@app.get("/api/health")
def health_check():
    return {"status": "ok", "graph_initialized": graph is not None}

@app.post("/api/chat")
def chat_turn(req: ChatRequest):
    try:
        res = run_agent_graph(
            user_text=req.message,
            thread_id=req.thread_id,
            user_profile=req.user_profile,
            interview_history=req.interview_history,
            interview_mode=req.interview_mode
        )
        return res
    except Exception as e:
        logger.exception("Error in chat turn")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/resume/generate")
def generate_resume(req: GenerateResumeRequest):
    try:
        # Run graph turn specifically requesting resume building
        res = run_agent_graph(
            user_text=f"Generate a LaTeX resume for: {req.job_description[:100]}",
            extra_task={
                "job_description": req.job_description,
                "user_details": req.user_details,
                "previous_resume": ""
            },
            thread_id=str(uuid.uuid4())
        )
        # Extract the resulting LaTeX content
        latex = res.get("task_input", {}).get("generated_resume", "") or \
                res.get("user_profile", {}).get("resume_content", "")
        return {"latex": latex, "graph_trace": res.get("graph_trace")}
    except Exception as e:
        logger.exception("Error generating resume")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/resume/refine")
def refine_resume(req: RefineResumeRequest):
    try:
        res = run_agent_graph(
            user_text=req.refinement_request,
            extra_task={
                "previous_resume": req.previous_resume,
                "job_description": req.job_description,
                "user_request": req.refinement_request
            },
            thread_id=str(uuid.uuid4())
        )
        latex = res.get("task_input", {}).get("generated_resume", "") or \
                res.get("user_profile", {}).get("resume_content", req.previous_resume)
        return {"latex": latex, "graph_trace": res.get("graph_trace")}
    except Exception as e:
        logger.exception("Error refining resume")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/job/search")
def find_jobs(req: JobSearchRequest):
    try:
        res = run_agent_graph(
            user_text=f"Find {req.job_type} {req.job_title} jobs in {req.location}",
            extra_task={
                "job_title": req.job_title,
                "location": req.location,
                "job_type": req.job_type,
                "user_context": req.user_context
            },
            thread_id=req.thread_id
        )
        return {"output": res.get("agent_output"), "graph_trace": res.get("graph_trace")}
    except Exception as e:
        logger.exception("Error performing job search")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/interview/prep")
def build_prep_guide(req: PrepGuideRequest):
    try:
        res = run_agent_graph(
            user_text=req.focus_area or f"Comprehensive interview preparation guide for {req.job_title}",
            extra_task={
                "job_title": req.job_title,
                "user_experience": req.user_experience,
                "user_name": req.user_name,
                "user_request": req.focus_area
            },
            thread_id=req.thread_id
        )
        return {"output": res.get("agent_output"), "graph_trace": res.get("graph_trace")}
    except Exception as e:
        logger.exception("Error generating prep guide")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/interview/mock/start")
def start_mock(req: MockStartRequest):
    try:
        res = run_agent_graph(
            user_text="Start the mock interview",
            extra_task={
                "job_title": req.job_title,
                "user_experience": req.user_experience,
                "user_name": req.user_name
            },
            thread_id=req.thread_id,
            interview_mode="mock"
        )
        return {"question": res.get("agent_output"), "history": res.get("interview_history")}
    except Exception as e:
        logger.exception("Error starting mock interview")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/interview/mock/answer")
def send_answer(req: MockAnswerRequest):
    try:
        res = run_agent_graph(
            user_text=req.answer,
            extra_task={
                "job_title": req.job_title,
                "user_experience": req.user_experience,
                "user_name": req.user_name
            },
            thread_id=req.thread_id,
            interview_history=req.history,
            interview_mode="mock"
        )
        return {"follow_up": res.get("agent_output"), "history": res.get("interview_history")}
    except Exception as e:
        logger.exception("Error answering mock interview question")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/interview/mock/evaluate")
def evaluate_mock_session(req: MockEvaluateRequest):
    try:
        # Construct evaluator state directly
        eval_state = make_initial_state()
        eval_state["task_input"] = {
            "job_title": req.job_title,
            "user_experience": req.user_experience,
            "user_name": req.user_name,
        }
        eval_state["interview_history"] = req.history
        
        # Invoke mock evaluator node
        res = evaluation_node(eval_state)
        return {"evaluation": res.get("agent_output", "No evaluation available.")}
    except Exception as e:
        logger.exception("Error evaluating mock interview")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/interview/evaluate_transcript")
def evaluate_custom_transcript(req: TranscriptEvaluateRequest):
    try:
        eval_state = make_initial_state()
        eval_state["task_input"] = {
            "job_title": req.job_title,
            "user_experience": req.user_experience,
            "user_name": req.user_name,
            "interview_transcript": req.transcript
        }
        res = evaluation_node(eval_state)
        return {"evaluation": res.get("agent_output", "No evaluation available.")}
    except Exception as e:
        logger.exception("Error evaluating custom transcript")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/tutorials")
def learn_topic(req: TutorialRequest):
    try:
        res = run_agent_graph(
            user_text=req.topic,
            extra_task={
                "user_message": req.topic,
                "user_context": req.user_background
            },
            thread_id=req.thread_id
        )
        return {"output": res.get("agent_output"), "graph_trace": res.get("graph_trace")}
    except Exception as e:
        logger.exception("Error generating tutorial")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/salary/playbook")
def CounterOfferPlaybook(req: SalaryRequest):
    try:
        eval_state = make_initial_state()
        eval_state["task_input"] = {
            "job_title": req.job_title,
            "location": req.location,
            "experience": req.experience,
            "current_offer": req.current_offer,
            "current_salary": req.current_salary,
            "skills": req.skills
        }
        
        # Invoke salary specialist directly
        res = salary_negotiator_node(eval_state)
        return {"output": res.get("agent_output", "Failed to build playbook.")}
    except Exception as e:
        logger.exception("Error constructing salary counter playbook")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/settings")
def get_settings():
    return {
        "TOGETHER_API_KEY": os.getenv("TOGETHER_API_KEY", ""),
        "GOOGLE_API_KEY": os.getenv("GOOGLE_API_KEY", ""),
        "GOOGLE_CSE_ID": os.getenv("GOOGLE_CSE_ID", "")
    }

@app.post("/api/settings")
def save_settings(settings: SettingsUpdate):
    try:
        # Load existing dotenv contents
        dotenv_path = os.path.join(os.getcwd(), ".env")
        lines = []
        if os.path.exists(dotenv_path):
            with open(dotenv_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        
        current_env = {}
        for line in lines:
            line_str = line.strip()
            if line_str and not line_str.startswith("#") and "=" in line_str:
                parts = line_str.split("=", 1)
                k = parts[0].strip()
                v = parts[1].strip().strip('"').strip("'")
                current_env[k] = v

        # Update environment and current dict
        if settings.together_api_key is not None:
            os.environ["TOGETHER_API_KEY"] = settings.together_api_key
            current_env["TOGETHER_API_KEY"] = settings.together_api_key
            
        if settings.google_api_key is not None:
            os.environ["GOOGLE_API_KEY"] = settings.google_api_key
            current_env["GOOGLE_API_KEY"] = settings.google_api_key
            
        if settings.google_cse_id is not None:
            os.environ["GOOGLE_CSE_ID"] = settings.google_cse_id
            current_env["GOOGLE_CSE_ID"] = settings.google_cse_id

        # Write fresh configurations to .env
        with open(dotenv_path, "w", encoding="utf-8") as f:
            for k, v in current_env.items():
                f.write(f'{k}="{v}"\n')
                
        return {"status": "success", "message": "Settings updated and saved to .env"}
    except Exception as e:
        logger.exception("Error saving settings")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)
