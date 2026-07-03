# Technology Stack: UAE AI & Data Job Intelligence Platform

## 1. Introduction

This document details the technology stack selected for the UAE AI & Data Job Intelligence Platform. Our choices were primarily driven by a commitment to open-source tools, a local-first development approach, and seamless containerization via Docker Compose. This aligns perfectly with the project's core constraints and ensures a robust, scalable, and maintainable system. The stack is comprehensively designed to support every aspect of the platform, from data ingestion and storage to transformation, orchestration, backend services, the user interface, and advanced AI capabilities.

## 2. Core Technologies

The following table provides a detailed overview of the core technologies employed across the various layers of our platform:

| Layer | Technology | Description | Justification |
| :--- | :--- | :--- | :--- |
| **Data Ingestion** | Python | Our primary language for scripting data collection from APIs and web scraping. | Python's versatility and extensive libraries make it ideal for data manipulation and web interaction. |
| **Data Ingestion** | `requests`, `BeautifulSoup` | Essential Python libraries for making HTTP requests and parsing HTML content. | These are standard, powerful tools for efficient API interaction and web scraping. |
| **Raw Data Storage** | PostgreSQL | A robust relational database chosen for storing raw, untransformed job market data. | PostgreSQL is known for its reliability, open-source nature, and widespread community support. |
| **Curated Data Storage** | DuckDB | An in-process SQL OLAP database, perfect for storing transformed analytical models. | It offers high performance for analytical queries, is lightweight, and integrates seamlessly with Python and dbt. |
| **Data Transformation** | dbt Core | The Data Build Tool (dbt) Core is used for defining and executing data transformations using SQL. | As an industry standard, dbt promotes modularity, rigorous testing, and clear documentation in our data pipelines. |
| **Orchestration** | Prefect | Our workflow orchestration tool for scheduling and managing complex data pipelines. | Prefect is Python-native, provides modern orchestration capabilities, and is straightforward to set up in a local environment. |
| **Backend API** | FastAPI | A high-performance web framework for building our APIs with Python. | FastAPI is celebrated for its speed, modern features, automatic interactive API documentation, and excellent asynchronous support. |
| **Dashboard** | Streamlit | A Python library dedicated to creating interactive web applications for data science and machine learning. | It enables rapid development of intuitive data dashboards and integrates easily with other Python data tools. |
| **AI Services** | Ollama | A crucial tool for running large language models locally within our infrastructure. | Ollama facilitates local, private execution of LLMs, reducing latency and eliminating reliance on external paid APIs. |
| **AI Models** | Qwen 3 8B or Gemma | Open-source large language models selected for text analysis and intelligence generation. | These models offer a strong balance of capability and size, making them suitable for local execution while providing advanced natural language processing. |
| **Containerization** | Docker Compose | The tool we use for defining and running our multi-container Docker applications. | Docker Compose ensures consistent development environments, simplifies local setup (`docker compose up`), and is fundamental to our local-first approach. |

## 3. Code Quality and Development Tools

To uphold high code quality standards and ensure consistency across the project, we integrate the following tools into our development workflow:

| Tool | Purpose | Description |
| :--- | :--- | :--- |
| **Ruff** | Linter and Formatter | An exceptionally fast Python linter and code formatter, effectively replacing tools like Flake8, Black, and isort. |
| **mypy** | Static Type Checker | An optional static type checker for Python, which helps ensure type safety and significantly reduces potential runtime errors. |
| **pytest** | Testing Framework | A versatile framework for writing small, readable tests, capable of scaling to support complex functional testing needs. |
| **pre-commit** | Git Hooks Manager | A framework designed for managing multi-language pre-commit hooks, ensuring that essential code quality checks are automatically run before each commit. |

## 4. Architecture Alignment

The technology stack we've chosen is in direct alignment with the project's architectural goals and constraints:

*   **Open Source First:** Every tool selected—PostgreSQL, DuckDB, dbt Core, Prefect, FastAPI, Streamlit, Ollama, and the Qwen/Gemma models—is open-source. This choice eliminates licensing costs and avoids vendor lock-in, fostering a collaborative and accessible development environment.
*   **Local-First Development:** The entire stack, encompassing the database, orchestration, backend, frontend, and AI models, is designed to run seamlessly on a developer's local machine. This approach simplifies development and testing workflows.
*   **Docker Compose Integration:** Docker Compose is central to orchestrating all our services. This means new team members can set up a fully functional development environment with a single command: `docker compose up`.
*   **No Paid APIs:** Our platform is built to rely on open-source data sources, judicious web scraping (where permissible), and local AI models (via Ollama). This strategy ensures that the core functionality does not require any paid API subscriptions, keeping the project accessible and cost-effective.
