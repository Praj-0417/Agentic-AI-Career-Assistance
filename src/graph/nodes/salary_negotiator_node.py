"""
Salary Negotiator Node — provides personalised, data-driven salary
negotiation coaching using a direct search and LLM formatting flow.
"""

from __future__ import annotations

from langchain.prompts import PromptTemplate
from langchain_core.messages import AIMessage

from src.state import AgentState
from src.config import NODE_SALARY
from src.guidance.agent import get_llm, get_search_tool


def salary_negotiator_node(state: AgentState) -> dict:
    """
    Evaluates the candidate's offer by calling the search tool directly for market data,
    and uses a high-quality LLM to format a personalized playbook with scripts.
    """
    task    = state.get("task_input", {})
    profile = state.get("user_profile", {})

    job_title      = task.get("job_title", "") or task.get("user_message", "")
    location       = task.get("location", "")
    experience     = task.get("experience", "") or profile.get("experience", "")
    current_offer  = task.get("current_offer", "Not specified")
    current_salary = task.get("current_salary", "Not specified")
    skills         = task.get("skills", "") or profile.get("skills", "")

    if not job_title:
        return {
            "needs_clarification": True,
            "clarification_question": (
                "I'd love to help you negotiate! Please tell me:\n"
                "1. The job title\n"
                "2. The offer amount (if you have one)\n"
                "3. Your location\n"
                "4. Years of experience"
            ),
            "current_agent": "clarifier",
            "graph_trace": [NODE_SALARY],
        }

    # Run the search tool directly to fetch salary benchmarks
    search_query = f"{job_title} salary range {location} levels fyi glassdoor 2026"
    search_results = ""
    try:
        tool = get_search_tool()
        search_results = tool.func(search_query)
    except Exception as e:
        search_results = f"Search failed: {e}"

    prompt_template = """You are an expert salary negotiation coach with deep knowledge of
compensation benchmarks across the tech industry.

**Candidate Details:**
- Role: {job_title}
- Location: {location}
- Experience: {experience} years
- Current Offer: {current_offer}
- Current Salary / Expectation: {current_salary}
- Skills / Strengths: {skills}

**Search Results Context (salary benchmarks):**
{search_results}

**Instructions for Final Response:**

## 💰 Market Salary Research
- Give range for {job_title} in {location}.
- Give a specific P25/P50/P75 breakdown if available.
- Mention total comp (base + equity + bonus) not just base salary.

## 📊 Your Position & Target
- Evaluate current offer {current_offer} against market.
- Recommend a specific counter-offer number with justification.

## 🗣️ Negotiation Scripts
Provide 3 ready-to-use scripts:
1. **Email counter-offer** (formal, polite, firm)
2. **Phone / verbal counter** (conversational opener)
3. **Handling pushback** ("That's our best offer" response)

## 📦 Beyond Base Salary
List negotiable levers beyond base pay (equity, PTO, signing bonus, remote flexibility).

## ⚠️ Red Flags & Walk-Away Point
- Walk-away number and negotiation red flags.

## ✅ Quick Action Checklist
Numbered list of exact next steps.

Format everything as clean, actionable Markdown.

Response:"""

    try:
        llm = get_llm("salary_negotiator")
        prompt = PromptTemplate(
            input_variables=[
                "job_title", "location", "experience",
                "current_offer", "current_salary", "skills",
                "search_results"
            ],
            template=prompt_template,
        )
        formatted = prompt.format(
            job_title=job_title,
            location=location or "Remote / Not specified",
            experience=experience or "Not specified",
            current_offer=current_offer,
            current_salary=current_salary,
            skills=skills or "Not specified",
            search_results=search_results,
        )
        output = llm.invoke(formatted)

        return {
            "agent_output": output,
            "graph_trace":  [NODE_SALARY],
            "messages":     [AIMessage(content=output)],
            "error":        None,
        }

    except Exception as exc:
        error_msg = f"Salary negotiator error: {exc}"
        print(f"[salary_negotiator_node] {error_msg}")
        return {
            "agent_output": f"❌ {error_msg}",
            "graph_trace":  [NODE_SALARY],
            "messages":     [AIMessage(content=error_msg)],
            "error":        error_msg,
        }

