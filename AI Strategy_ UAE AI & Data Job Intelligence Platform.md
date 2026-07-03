# AI Strategy: UAE AI & Data Job Intelligence Platform

## 1. Explanation of Existence

This document details our strategy for integrating Artificial Intelligence (AI) and Machine Learning (ML) capabilities into the UAE AI & Data Job Intelligence Platform. It defines how AI will transform raw job market data into actionable insights, enhance data quality, and provide predictive analytics. This strategy is designed to ensure that AI is applied effectively and ethically to achieve the platform's overarching mission.

## 2. Consumers

This document is a key resource for both **human developers** and **AI coding agents**. Human developers will use it to understand the AI components, their integration points, and to guide their development and maintenance efforts. Similarly, AI coding agents will consult this document to grasp the objectives and constraints of AI model development, ensuring their generated code and configurations align with our strategic vision. Ultimately, it serves as a guiding principle for all AI-related decisions and implementations within the project.

## 3. Initial Version of the File

### 3.1 Core AI Objectives

Our primary objectives for integrating AI are multifaceted. We aim for **automated data enrichment**, which involves extracting structured information such as skills, technologies, and job roles from unstructured text found in job descriptions. This will lead to enhanced **insight generation**, allowing us to identify trends, patterns, and relationships in job market data that might not be immediately obvious through traditional analytics. Furthermore, we seek to implement **predictive analytics** to forecast future skill demands, salary trends, and emerging hiring hotspots. Finally, AI will power **recommendation systems** designed to suggest optimal learning paths and career moves for job seekers.

### 3.2 AI Technologies and Models

The platform will primarily leverage Large Language Models (LLMs) as its core AI technology, with a strong emphasis on local-first and open-source solutions. We will use **Ollama** to serve LLMs locally within our Docker Compose environment. This approach is crucial for ensuring data privacy, reducing latency, and eliminating dependencies on external paid APIs. For the LLMs themselves, we have selected **Qwen 3 8B** or **Gemma**. These models were chosen for their balanced performance, manageable size, and suitability for local deployment. They will enable a range of tasks, including **Named Entity Recognition (NER)** to identify and extract skills, technologies, company names, and locations from job descriptions; **Text Classification** to categorize job roles, industries, and experience levels; **Summarization** for job descriptions or trend reports; and potentially **Sentiment Analysis** if we integrate related news articles or company reviews.

### 3.3 AI Integration Points

AI capabilities will be seamlessly integrated at various stages of our data pipeline and application. During **Data Transformation (via dbt Core and Prefect)**, after raw job descriptions are ingested, Prefect-orchestrated tasks will invoke LLMs through the FastAPI backend. This process will extract and standardize lists of required skills and technologies, enriching our `fact_job_posting` table with `extracted_skills` and `extracted_technologies` (stored as JSONB fields). LLMs will also classify job descriptions into standardized job role categories to facilitate consistent analysis. Within the **FastAPI Backend**, we will expose API endpoints to interact with the locally served Ollama LLMs, allowing both Prefect flows and the Streamlit dashboard to utilize these AI capabilities. The backend can also dynamically invoke LLMs for specific user queries from the dashboard, providing on-demand analysis or explanations. Finally, the **Streamlit Dashboard** will display these LLM-generated insights, such as summaries of key trends, skill recommendations, or explanations of salary drivers, and enhance search capabilities by understanding natural language queries to provide more relevant results.

### 3.4 Ethical AI Considerations

We are committed to addressing ethical considerations in our AI implementation. This includes **bias detection and mitigation**, where we will regularly evaluate LLM outputs for potential biases in skill recommendations, salary predictions, or hiring patterns, and implement strategies to mitigate them. **Transparency** is also vital; we will clearly communicate to users when insights are AI-generated. We will rigorously uphold **data privacy**, ensuring that all data processed by AI models adheres to privacy regulations and is used only for its intended purposes. Lastly, we will strive for **fairness** in the insights provided, ensuring that our recommendations and analyses do not inadvertently disadvantage any group.

### 3.5 Future AI Enhancements

Looking ahead, we envision several enhancements to our AI capabilities. This includes developing more accurate **predictive models** to forecast future job market trends, skill demands, and salary changes. We also plan to offer more tailored career path and learning recommendations through **personalized recommendations**, based on individual user profiles and goals. **Anomaly detection** will help us identify unusual patterns in job postings, potentially indicating emerging roles or shifts in market dynamics. Finally, we will explore using **generative AI for content creation**, such as drafting summaries of market reports or synthesizing complex data into easily digestible narratives.
