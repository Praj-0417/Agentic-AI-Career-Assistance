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
% Example:
% \section{{Experience}}
%   \resumeSubHeadingListStart
%     \resumeSubheading
%       {{Software Engineer}}{{June 2020 -- Present}}
%       {{Tech Company Inc.}}{{San Francisco, CA}}
%     \resumeItemListStart
%       \resumeItem{{Developed a new feature that increased user engagement by 15\%}}
%       \resumeItem{{Reduced server costs by 20\% by optimizing database queries}}
%     \resumeItemListEnd
%   \resumeSubHeadingListEnd

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

%----------ACHIEVEMENTS-----------------
% Placeholder for ACHIEVEMENTS
% Example:
% \section{{Achievements}}
%   \resumeItemListStart
%     \resumeItem{{Winner, University Hackathon 2019}}
%     \resumeItem{{Published paper on AI ethics at XYZ Conference}}
% \resumeItemListEnd

\end{{document}}
"""


def get_resume_builder_agent():
    print("DEBUG: This is the correct get_resume_builder_agent from resume_builder/agent.py")
    """
    Initializes the resume builder agent to generate LaTeX code.
    """
    llm = ChatTogetherNative(
        model="deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free",
        temperature=0.4,
        max_tokens=4096
    )
    
    prompt = PromptTemplate(
        input_variables=["job_description", "user_details"],
        template="""
You are an expert LaTeX resume generator. Your task is to populate the provided LaTeX template with the user's information, tailored to the target job description.

**CRITICAL INSTRUCTIONS:**
1.  **Analyze User Details & Job Description:** Extract all relevant information from the user's details (experience, skills, projects, education) and identify keywords from the job description.
2.  **Populate the Template:** Fill in the sections of the LaTeX template below using the user's information. You MUST use the provided custom commands (`\resumeSubheading`, `\resumeItem`, etc.) as shown in the examples.
3.  **Tailor the Content:** Emphasize skills and experiences that are most relevant to the job description. Use action verbs and quantify achievements.
4.  **Output ONLY LaTeX Code:** Your entire response must be ONLY the complete, raw LaTeX code from `\documentclass` to '\end document'. Do not include any other text, explanations, or markdown formatting like '```latex'.

**User Details:**
{user_details}

**Target Job Description:**
{job_description}

**LaTeX Resume Template to Populate:**
{latex_template}
"""
    )
    
    # The template is now passed as a variable to the prompt, and input_variables are set explicitly to avoid 'document' key errors
    partial_prompt = prompt.partial(latex_template=LATEX_RESUME_TEMPLATE)
    partial_prompt.input_variables = ["job_description", "user_details"]
    chain = LLMChain(llm=llm, prompt=partial_prompt, output_key="resume")
    return chain

def get_resume_refinement_agent():
    """
    Initializes an agent for refining an existing LaTeX resume.
    """
    llm = ChatTogetherNative(
        model="deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free",
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

    chain = LLMChain(llm=llm, prompt=prompt, output_key="resume")

    return chain
