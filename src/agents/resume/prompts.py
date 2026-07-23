"""
src/agents/resume/prompts.py
All prompt templates for the resume builder agent.
"""

GENERATION_TEMPLATE = """\
You are an expert LaTeX resume writer. Generate a complete, professional, \
ATS-optimised LaTeX resume.

Job Description (tailor the resume to this):
{job_description}

Candidate Details (experience, skills, projects, education):
{user_details}

Instructions:
1. Output ONLY valid, complete LaTeX code — no conversational text, no explanations.
2. Use the standard article class with professional margins.
3. Include sections: Header, Summary, Experience, Education, Skills, Projects.
4. Use \\resumeItem, \\resumeSubheading style custom commands for clean formatting.
5. Quantify achievements wherever possible (percentages, numbers).
6. Keep it to one page unless experience warrants two.
7. Do NOT wrap in markdown code fences — output raw LaTeX only.

Complete LaTeX Resume:\
"""

REFINEMENT_TEMPLATE = """\
You are an expert LaTeX resume editor. Apply the requested changes precisely.

Current LaTeX Resume:
{previous_resume}

Target Job Description (for context):
{job_description}

User's Modification Request:
{user_request}

Instructions:
1. Apply ONLY the requested changes.
2. Keep all other sections intact.
3. Ensure the output is a complete, valid LaTeX document.
4. Output ONLY the updated LaTeX code — no explanations, no markdown fences.

Updated LaTeX Resume:\
"""
