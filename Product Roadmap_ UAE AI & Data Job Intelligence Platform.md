# Product Roadmap: UAE AI & Data Job Intelligence Platform

## 1. Introduction

This document outlines the strategic product roadmap for the UAE AI & Data Job Intelligence Platform. It details the planned evolution of the platform across different versions, providing a high-level overview of key features and initiatives. This roadmap serves to guide our development efforts and communicate the future direction to all stakeholders. It is a living document, and we expect it to be updated as the project progresses and new insights emerge.

## 2. Audience

This roadmap is a vital resource for several groups. **Human developers** will use it to understand the long-term vision and prioritize their development tasks effectively. **AI coding agents** will find it useful for understanding the phased delivery of features, allowing them to align their development efforts with the project's strategic goals. Ultimately, it fosters a shared understanding of the project's future direction and key milestones for everyone involved.

## 3. Product Evolution

### 3.1 Minimum Viable Product (MVP)

Our MVP focuses on establishing the core data pipeline and delivering foundational job market insights. The primary goal is to demonstrate end-to-end data ingestion, transformation, and basic visualization of UAE job market data. Key features for this phase include automated ingestion of job postings from at least two primary sources (e.g., LinkedIn Jobs, Indeed UAE) via Python scripts, with raw data stored in PostgreSQL. We will implement basic dbt Core transformations for cleaning and structuring job data, and store the curated data in DuckDB. Prefect will orchestrate daily data pipeline runs. The Streamlit dashboard will initially display the total number of job postings over time, the top 10 most in-demand skills (extracted via simple keyword matching), the top 10 companies hiring, and job distribution by city. A basic Docker Compose setup will ensure a smooth local-first development experience.

### 3.2 Version 1 (V1)

Version 1 builds upon the MVP by introducing more sophisticated, AI-driven insights and enhancing data coverage. Our goal for V1 is to provide actionable intelligence on skill growth, the impact of technology on salaries, and more refined market trends, all powered by local Large Language Models (LLMs). This phase will see the integration of Ollama with either Qwen 3 8B or Gemma for advanced text analysis. We will implement LLM-powered extraction and standardization of skills and technologies from job descriptions, enabling analysis of skill growth rates over time and correlation of technologies with salary uplift (where salary data is available). The Streamlit dashboard will be significantly enhanced with interactive charts for skill growth trends, visualizations showing the salary impact of specific technologies, detailed company hiring profiles, and advanced filtering and search capabilities. We will also focus on improved data quality checks and error handling within Prefect flows, and expand our data sources to include additional job boards or company career pages.

### 3.3 Version 2 (V2)

Version 2 shifts our focus towards predictive capabilities, user personalization, and further refinement of the intelligence provided. The overarching goal is to offer predictive insights into future job market trends and personalized recommendations for career development. Key features for V2 include the development of predictive models for forecasting future skill demands and salary trends. We will explore the implementation of a basic user profile system, if deemed necessary and aligned with our open-source principles, to enable personalized skill recommendations based on user-defined career goals or current skill sets. This phase will also involve integrating additional data sources, such as government labor statistics or educational course data, and deploying advanced AI models for more nuanced sentiment analysis or industry classification. Finally, we will enhance reporting features, allowing users to generate custom reports, and implement performance optimizations for large-scale data processing and dashboard responsiveness.

### 3.4 Stretch Goals

These represent aspirational features that we may consider in later stages, depending on available resources and the project's evolution. Potential stretch goals include exploring real-time data processing for critical data points, extending analysis to job postings in multiple languages prevalent in the UAE, and providing more granular geospatial insights into job demand at a district or neighborhood level. We might also consider community features, allowing users to share insights or collaborate, and implementing more mature MLOps practices for model versioning, deployment, and monitoring.
