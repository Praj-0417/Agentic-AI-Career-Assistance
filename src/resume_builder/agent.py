import os
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from src.guidance.agent import ChatTogetherNative  # Import the custom wrapper

load_dotenv()

# The user-provided LaTeX template is stored here as a base for generation.
# LATEX_RESUME_TEMPLATE = r"""
# \documentclass[letterpaper,11pt]{article}
# \usepackage{latexsym}
# \usepackage[empty]{fullpage}
# \usepackage{titlesec}
# \usepackage{marvosym}
# \usepackage[usenames,dvipsnames]{color}
# \usepackage{verbatim}
# \usepackage{enumitem}
# \usepackage[pdftex]{hyperref}
# \usepackage{fancyhdr}
# \usepackage[normalem]{ulem}

# \pagestyle{fancy}
# \fancyhf{} % Clear all header and footer fields
# \renewcommand{\headrulewidth}{0pt}
# \renewcommand{\footrulewidth}{0pt}

# % Adjust margins
# \addtolength{\oddsidemargin}{-0.375in}
# \addtolength{\evensidemargin}{-0.375in}
# \addtolength{\textwidth}{1in}
# \addtolength{\topmargin}{-.5in}
# \addtolength{\textheight}{1.0in}

# % URL style
# \urlstyle{same}

# \raggedbottom
# \raggedright
# \setlength{\tabcolsep}{0in}

# % Sections formatting
# \titleformat{\section}{
#   \vspace{-10pt}\scshape\raggedright\large
# }{}{0em}{}[\color{black}\titlerule \vspace{-5pt}]

# % Custom commands
# \newcommand{\resumeItem}[1]{
#   \item\small{
#     {#1 \vspace{-2pt}}
#   }
# }

# \newcommand{\resumeSubheading}[4]{
#   \vspace{-2pt}\item
#     \begin{tabular*}{0.97\textwidth}{l@{\extracolsep{\fill}}r}
#       \textbf{#1} & #2 \\
#       \textit{\small#3} & \textit{\small #4} \\
#     \end{tabular*}\vspace{-5pt}
# }

# \newcommand{\resumeSubItem}[2]{\resumeItem{#1}{#2}\vspace{-4pt}}
# \renewcommand{\labelitemii}{$\circ$}

# \newcommand{\resumeSubHeadingListStart}{\begin{itemize}[leftmargin=*, itemsep=0pt]}
# \newcommand{\resumeSubHeadingListEnd}{\end{itemize}}
# \newcommand{\resumeItemListStart}{\begin{itemize}}
# \newcommand{\resumeItemListEnd}{\end{itemize}\vspace{-5pt}}

# %-------------------------------------------
# %%%%%%  CV STARTS HERE  %%%%%%%%%%%%%%%%%%%%%%%%%%%%
# \begin{document}

# %----------HEADING-----------------
# % Placeholder for HEADING
# % Example:
# % \begin{tabular*}{\textwidth}{l@{\extracolsep{\fill}}r}
# %   \textbf{\Large YOUR NAME} & Email: \href{mailto:your.email@example.com}{your.email@example.com}\\
# %   \href{https://www.linkedin.com/in/your-linkedin/}{linkedin.com/in/your-linkedin} & +1 (123) 456-7890 \\
# %   \href{https://github.com/your-github}{github.com/your-github} & Portfolio: \href{https://your-portfolio.com}{your-portfolio.com}
# % \end{tabular*}

# %----------EDUCATION-----------------
# % Placeholder for EDUCATION
# % Example:
# % \section{Education}
# %   \resumeSubHeadingListStart
# %     \resumeSubheading
# %       {Your University}{City, State}
# %       {B.S. in Computer Science}{May 2020}
# %   \resumeSubHeadingListEnd

# %----------SKILLS-----------------
# % Placeholder for SKILLS
# % Example:
# % \section{Skills}
# %  \resumeSubHeadingListStart
# %    \item{\textbf{Languages}{: Python, Java, C++, SQL, JavaScript, HTML/CSS}}
# %    \item{\textbf{Frameworks}{: React, Node.js, Django, Flask, Spring Boot}}
# %    \item{\textbf{Developer Tools}{: Git, Docker, Jenkins, AWS, Google Cloud}}
# %  \resumeSubHeadingListEnd

# %----------EXPERIENCE-----------------
# % Placeholder for EXPERIENCE
# % Example:
# % \section{Experience}
# %   \resumeSubHeadingListStart
# %     \resumeSubheading
# %       {Software Engineer}{June 2020 -- Present}
# %       {Tech Company Inc.}{San Francisco, CA}
# %     \resumeItemListStart
# %       \resumeItem{Developed a new feature that increased user engagement by 15\%}
# %       \resumeItem{Reduced server costs by 20\% by optimizing database queries}
# %     \resumeItemListEnd
# %   \resumeSubHeadingListEnd

# %----------PROJECTS-----------------
# % Placeholder for PROJECTS
# % Example:
# % \section{Projects}
# %     \resumeSubHeadingListStart
# %       \resumeSubheading
# %         {AI Career Assistant}{https://github.com/your-github/ai-career-assistant}
# %         {Personal Project}{}
# %       \resumeItemListStart
# %         \resumeItem{Built a web app using Streamlit and LangChain to provide AI-powered career guidance.}
# %         \resumeItem{Tech Stack: Python, Streamlit, LangChain, TogetherAI}
# %       \resumeItemListEnd
# %     \resumeSubHeadingListEnd

# %----------ACHIEVEMENTS-----------------
# % Placeholder for ACHIEVEMENTS
# % Example:
# % \section{Achievements}
# %   \resumeItemListStart
# %     \resumeItem{Winner, University Hackathon 2019}
# %     \resumeItem{Published paper on AI ethics at XYZ Conference}
# % \resumeItemListEnd

# \end{document}
# """


LATEX_RESUME_TEMPLATE = r"""
\documentclass[letterpaper,11pt]{{article}}
\usepackage{{latexsym}}
\usepackage[empty]{{fullpage}}
\usepackage{{titlesec}}
\usepackage{{marvosym}}
\usepackage[usenames,dvipsnames]{{color}}
\usepackage{{verbatim}}
\usepackage{{enumitem}}
\usepackage[pdftex]{{hyperref}}
\usepackage{{fancyhdr}}
\usepackage[normalem]{{ulem}}

\pagestyle{{fancy}}
\fancyhf{{}} % Clear all header and footer fields
\renewcommand{{\headrulewidth}}{{0pt}}
\renewcommand{{\footrulewidth}}{{0pt}}

% Adjust margins
\addtolength{{\oddsidemargin}}{{-0.375in}}
\addtolength{{\evensidemargin}}{{-0.375in}}
\addtolength{{\textwidth}}{{1in}}
\addtolength{{\topmargin}}{{-.5in}}
\addtolength{{\textheight}}{{1.0in}}

% URL style
\urlstyle{{same}}

\raggedbottom
\raggedright
\setlength{{\tabcolsep}}{{0in}}

% Sections formatting
\titleformat{{\section}}{{%
  \vspace{{-10pt}}\scshape\raggedright\large
}}{{}}{{0em}}{{}}[\color{{black}}\titlerule \vspace{{-5pt}}]

% Custom commands
\newcommand{{\resumeItem}}[1]{{%
  \item\small{{
    #1 \vspace{{-2pt}}
  }}
}}

\newcommand{{\resumeSubheading}}[4]{{%
  \vspace{{-2pt}}\item
    \begin{{tabular*}}{{0.97\textwidth}}{{l@{{\extracolsep{{\fill}}}}r}}
      \textbf{{#1}} & #2 \\
      \textit{{\small#3}} & \textit{{\small #4}} \\
    \end{{tabular*}}\vspace{{-5pt}}
}}

\newcommand{{\resumeSubItem}}[2]{{\resumeItem{{#1}}{{#2}}\vspace{{-4pt}}}}
\renewcommand{{\labelitemii}}{{$\circ$}}

\newcommand{{\resumeSubHeadingListStart}}{{\begin{{itemize}}[leftmargin=*, itemsep=0pt]}}
\newcommand{{\resumeSubHeadingListEnd}}{{\end{{itemize}}}}
\newcommand{{\resumeItemListStart}}{{\begin{{itemize}}}}
\newcommand{{\resumeItemListEnd}}{{\end{{itemize}}\vspace{{-5pt}}}}

%-------------------------------------------
%%%%%%  CV STARTS HERE  %%%%%%%%%%%%%%%%%%%%%%%%%%%%
\begin{{document}}

%----------HEADING-----------------
% Placeholder for HEADING
% Example:
% \begin{{tabular*}}{{\textwidth}}{{l@{{\extracolsep{{\fill}}}}r}}
%   \textbf{{\Large YOUR NAME}} & Email: \href{{mailto:your.email@example.com}}{{your.email@example.com}}\\
%   \href{{https://www.linkedin.com/in/your-linkedin/}}{{linkedin.com/in/your-linkedin}} & +1 (123) 456-7890 \\
%   \href{{https://github.com/your-github}}{{github.com/your-github}} & Portfolio: \href{{https://your-portfolio.com}}{{your-portfolio.com}}
% \end{{tabular*}}

%----------EDUCATION-----------------
% Placeholder for EDUCATION
% Example:
% \section{{Education}}
%   \resumeSubHeadingListStart
%     \resumeSubheading
%       {{Your University}}{{City, State}}
%       {{B.S. in Computer Science}}{{May 2020}}
%   \resumeSubHeadingListEnd

%----------SKILLS-----------------
% Placeholder for SKILLS
% Example:
% \section{{Skills}}
%  \resumeSubHeadingListStart
%    \item{{\textbf{{Languages}}{{: Python, Java, C++, SQL, JavaScript, HTML/CSS}}}}
%    \item{{\textbf{{Frameworks}}{{: React, Node.js, Django, Flask, Spring Boot}}}}
%    \item{{\textbf{{Developer Tools}}{{: Git, Docker, Jenkins, AWS, Google Cloud}}}}
%  \resumeSubHeadingListEnd

%----------EXPERIENCE-----------------
% Placeholder for EXPERIENCE
#% Example:
#% \section{{Experience}}
#%   \resumeSubHeadingListStart
#%     \resumeSubheading
#%       {{Software Engineer}}{{June 2020 -- Present}}
#%       {{Tech Company Inc.}}{{San Francisco, CA}}
#%     \resumeItemListStart
#%       \resumeItem{{Developed a new feature that increased user engagement by 15\%}}
#%       \resumeItem{{Reduced server costs by 20\% by optimizing database queries}}
#%     \resumeItemListEnd
#%   \resumeSubHeadingListEnd

%----------PROJECTS-----------------
% Placeholder for PROJECTS
% Example:
% \section{{Projects}}
%     \resumeSubHeadingListStart
%       \resumeSubheading
%         {{AI Career Assistant}}{{https://github.com/your-github/ai-career-assistant}}
%         {{Personal Project}}{{}}
%       \resumeItemListStart
%         \resumeItem{{Built a web app using Streamlit and LangChain to provide AI-powered career guidance.}}
%         \resumeItem{{Tech Stack: Python, Streamlit, LangChain, TogetherAI}}
%       \resumeItemListEnd
%     \resumeSubHeadingListEnd

% %----------ACHIEVEMENTS-----------------
% % Placeholder for ACHIEVEMENTS
% % Example:
% % \section{{Achievements}}
% %   \resumeItemListStart
% %     \resumeItem{{Winner, University Hackathon 2019}}
% %     \resumeItem{{Published paper on AI ethics at XYZ Conference}}
% % \resumeItemListEnd

\end{{document}}
"""


def get_resume_builder_agent():
    """
    Initializes an interactive resume builder agent that supports continuous editing.
    """
    print("DEBUG: Initializing interactive resume builder agent")
    
    llm = ChatTogetherNative(
        model="mistralai/Mixtral-8x7B-Instruct-v0.1",
        temperature=0.2,
        max_tokens=4096
    )
    
    prompt = PromptTemplate(
        input_variables=["job_description", "user_details", "previous_resume", "user_request"],
        template="""You are an interactive resume editor that helps users build and refine their resumes through conversation.

Current State: {previous_resume}

User's Request: {user_request}

Job Description: {job_description}

User Details: {user_details}

Instructions:
1. If user says "end resume session", respond with: "END_SESSION: Your resume has been saved!"
2. Otherwise, help modify the resume based on their request
3. If no previous resume exists, create a new one using the LaTeX template
4. After each change, show the complete updated resume and these options:

What would you like to modify next?
1. Add/update work experience
2. Modify skills section
3. Add/edit projects
4. Update education details
5. Adjust formatting
6. Type "end resume session" when you're finished

Remember:
- Keep all LaTeX formatting intact
- Preserve existing sections unless asked to change
- Always respond with the complete resume after changes
- Make sure projects section includes ScrapSaathi and VeniScope
"""
    )
    
    # Create a wrapper to handle missing keys and format the response
    class ResumeBuilderAgentWrapper:
        def __init__(self, chain):
            self.chain = chain
            
        def invoke(self, inputs):
            # Handle missing keys with defaults
            if "previous_resume" not in inputs:
                inputs["previous_resume"] = ""
                
            if "user_request" not in inputs:
                inputs["user_request"] = "Create a new LaTeX resume"
                
            # Check if resume_user_details was provided instead of user_details
            if "resume_user_details" in inputs and "user_details" not in inputs:
                inputs["user_details"] = inputs["resume_user_details"]
                
            # Invoke the chain with complete inputs
            result = self.chain.invoke(inputs)
            
            # Format the response as a dict with 'resume' key if it's not already
            if isinstance(result, dict) and "output" in result:
                if "END_SESSION" in result["output"]:
                    return {"output": result["output"], "resume": inputs.get("previous_resume", "")}
                return {"output": result["output"], "resume": result["output"]}
            else:
                return {"output": "Error processing resume", "resume": inputs.get("previous_resume", "")}
    
    chain = LLMChain(llm=llm, prompt=prompt, output_key="output")
    return ResumeBuilderAgentWrapper(chain)

def get_resume_refinement_agent():
    """
    Initializes an agent for refining an existing LaTeX resume.
    """
    llm = ChatTogetherNative(
        model="mistralai/Mixtral-8x7B-Instruct-v0.1",
        temperature=0.3,
        max_tokens=4096
    )

    prompt = PromptTemplate(
        input_variables=["job_description", "previous_resume", "user_request"],
        template="""
        You are an expert LaTeX resume editor. Your task is to modify the provided LaTeX resume code based on the user's request.

        **Target Job Description (for context):**
        {job_description}

        **Current LaTeX Resume Code:**
        ```latex
        {previous_resume}
        ```

        **User's Modification Request:**
        "{user_request}"

        **Instructions:**
        1.  Carefully apply the user's requested changes directly to the LaTeX code.
        2.  Do NOT change other parts of the resume unless necessary for consistency.
        3.  Ensure the final output is a complete and valid LaTeX document.
        4.  Your entire response must be ONLY the new, complete, and updated LaTeX code. Do not add any conversational text, apologies, or markdown formatting like ```latex.

        **Final Output (Updated and Complete LaTeX Code):**
        """
    )

    # Create a wrapper to handle missing keys and format the response
    class ResumeRefinementAgentWrapper:
        def __init__(self, chain):
            self.chain = chain
            
        def invoke(self, inputs):
            # Handle missing keys with defaults
            if "previous_resume" not in inputs and "generated_resume" in inputs:
                inputs["previous_resume"] = inputs["generated_resume"]
                
            if "user_request" not in inputs and "refinement_request" in inputs:
                inputs["user_request"] = inputs["refinement_request"]
            
            # Invoke the chain with complete inputs
            result = self.chain.invoke(inputs)
            
            # Format the response
            if isinstance(result, dict) and "output" in result:
                return {"output": "Changes applied successfully.", "resume": result["output"]}
            else:
                return {"output": "Error processing resume changes", "resume": inputs.get("previous_resume", "")}

    chain = LLMChain(llm=llm, prompt=prompt, output_key="output")
    return ResumeRefinementAgentWrapper(chain)
