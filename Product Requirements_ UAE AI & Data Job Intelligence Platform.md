# Product Requirements: UAE AI & Data Job Intelligence Platform

## 1. Introduction

This document outlines the core product requirements for the UAE AI & Data Job Intelligence Platform. Our aim is to deliver a comprehensive platform that provides actionable intelligence on the UAE job market for data and AI professionals, ultimately enabling more informed career and business decisions.

## 2. Functional Requirements

### 2.1 Data Ingestion & Processing

We will continuously collect job postings and related data from various online sources relevant to the UAE market. This process will support data ingestion through Python-based API calls and, where legally permissible and technically feasible, optional web scraping. All raw and processed job market data will be stored in structured databases, specifically PostgreSQL and DuckDB. To ensure data quality and consistency, we will perform data transformations using dbt Core to create robust analytical data models. The entire data pipeline, from ingestion to transformation, will be orchestrated using Prefect, which will handle scheduling, monitoring, and error management.

### 2.2 Data Analysis & Intelligence Generation

The platform will be capable of identifying and tracking the fastest-growing skills within UAE Data roles. We will analyze the impact of various technologies on salary uplift, pinpointing which technologies offer the largest financial benefits. Furthermore, the system will identify companies that are most actively hiring for AI and Data positions across the UAE and determine which cities exhibit the highest demand for these professionals. Based on these analyses, we will provide recommendations for skills and technologies that candidates should acquire to maximize their employability. To achieve advanced text analysis, such as skill extraction, job role classification, and trend prediction, we will leverage AI models like Ollama, Qwen 3 8B, or Gemma.

### 2.3 User Interface & Reporting

An interactive dashboard will be provided to allow users to explore job market intelligence. This dashboard, built using Streamlit, will display key metrics and visualizations related to skill trends, salary insights, hiring companies, and city-specific demand. Users will have the ability to filter and drill down into the data based on various parameters, such as job role, technology, or location.

## 3. Non-Functional Requirements

### 3.1 Performance

Our data ingestion and processing pipelines are designed to complete within a defined daily window. For user interactions, dashboard queries should respond within 5 seconds to ensure a smooth experience.

### 3.2 Scalability

The system architecture will support horizontal scaling to effectively accommodate increasing data volumes and user loads.

### 3.3 Security

We are committed to protecting all stored and transmitted data against unauthorized access. Additionally, all data scraping activities will strictly comply with legal and ethical guidelines.

### 3.4 Maintainability

The codebase will be thoroughly documented and adhere to established coding standards. The system is designed for easy deployment and management using Docker Compose.

### 3.5 Usability

We prioritize an intuitive and easy-to-navigate user interface for all our target users.

## 4. Constraints

Our project operates under several key constraints:

*   **Open Source First:** The project must prioritize open-source technologies and solutions.
*   **Local-First Development:** Development should primarily occur in a local environment.
*   **Docker Compose Integration:** The entire technology stack must run seamlessly through Docker Compose.
*   **No Paid APIs:** Core functionality should not require any paid API subscriptions.
*   **Easy Setup:** New users must be able to set up a working environment by simply running `docker compose up`.
*   **UAE Market Focus:** The platform's scope is strictly limited to the UAE job market.
