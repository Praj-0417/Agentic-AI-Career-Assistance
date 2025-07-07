# GenAI Career Assistant Agent – Your Ultimate Guide to a Career in Generative AI!🚀

## Overview
Meet the GenAI Career Assistant—an AI-powered mentor designed to simplify and support your journey in Generative AI learning, Resume preparation, Interview assistant and job hunting.
#### Tech Stack
I have used all free Open source.<br>
Langchain,Langgraph, Gemini LLM, DuckDuckGoSearchResult

## Motivation
As GenAI rapidly evolves, more people are eager to learn it for career advancement or transition. However, navigating the vast resources on the internet and platforms like YouTube can be overwhelming, with long videos and scattered, outdated materials making it hard to know where to begin in this busy life. Even using ChatGPT for coding help often yields deprecated code, as GenAI packages and methods—such as LangChain, LlamaIndex, and Hugging Face—are updated frequently.

### Key Features

1. **Learning & Content Creation:**
   - Offers tailored learning pathways in GenAI, covering key topics and skills.
   - Assists users in creating tutorials, blogs, and posts based on their interests or queries.
2. **Q&A Support:**
   - Provides on-demand Q&A sessions for users needing guidance on concepts or coding issues.
3. **Resume Building & Review:**
   - One-on-one resume consultations and guidance.
   - Crafts personalized, market-relevant resumes optimized for current job trends.
4. **Interview Preparation:**
   - Hosts Q&A sessions on common and technical interview questions.
   - Simulates real interview scenarios and conducts mock interviews.
5. **Job Search Assistance:**
   - Guides users through the job search process, offering tailored insights and support.
With the GenAI Career Assistant, your journey to a career in Generative AI becomes organized, personalized, and efficient!

<img src="https://i.imghippo.com/files/xrJV7042k.png" alt="agent" border="0" style="height:20%;width:90%">

## Key Components
1. **State Management**: Using TypedDict to define and manage the state of each customer interaction.
2. **Query Categorization**: Classifying users queries into Learning, Resume Preparation, Interview or Job Search.
3. **Sub Categorization**: Learning(Tutorial, Q&A), Interview(Interview prep,Mock interview).
4. **Response Generation**: Creating appropriate responses based on the query category. Create .md files for Tutorial Blogs, Resume, Mock interview etc.
6. **Workflow Graph**: Utilizing LangGraph to create a flexible and extensible workflow.

## Method Details
1. **Initialization**: Set up the environment and import necessary libraries.
2. **State Definition**: Create a structure to hold query information, category, sub-category, and response.
3. **Node Functions**: Implement separate functions for categorization, and response generation.
4. **Graph Construction**: Use StateGraph to define the workflow, adding nodes and edges to represent the support process.
5. **Conditional Routing**: Implement logic to route queries based on their category and sub- category.
6. **Workflow Compilation**: Compile the graph into an executable application.
7. **Execution**: Process users queries through the workflow and retrieve results.
