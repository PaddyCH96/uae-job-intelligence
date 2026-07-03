# Tasks: UAE AI & Data Job Intelligence Platform

## 1. Introduction

This document serves as a dynamic repository for atomic implementation tasks within the UAE AI & Data Job Intelligence Platform. Our aim is to break down larger features or components into granular, actionable items suitable for assignment to both human developers and AI coding agents. The goal is to provide clear, unambiguous instructions that can be directly translated into code or configuration changes, thereby facilitating efficient and collaborative development.

## 2. Audience

This document is a critical resource for several stakeholders. **Human developers** will consult it to pick up specific implementation tasks, understand their scope, and track their progress. Similarly, **AI coding agents** will use it to receive precise instructions for code generation, refactoring, or configuration updates, ensuring their output aligns perfectly with project requirements. Ultimately, it functions as a central task management system for all granular development efforts.

## 3. Task Structure and Examples

### 3.1 Task Structure

Each task should adhere to a consistent structure to ensure clarity and completeness:

*   **Task ID:** A unique identifier (e.g., `FEAT-001`, `BUG-005`, `INFRA-010`).
*   **Title:** A concise description of the task.
*   **Description:** A detailed explanation of what needs to be done, including context, requirements, and expected outcomes.
*   **Acceptance Criteria:** Clear, verifiable conditions that must be met for the task to be considered complete.
*   **Dependencies:** Any other tasks that must be completed before this task can begin.
*   **Assigned To:** The human developer or AI agent responsible for the task.
*   **Status:** The current state of the task (e.g., `To Do`, `In Progress`, `Review`, `Done`, `Blocked`).
*   **Priority:** The urgency of the task (e.g., `High`, `Medium`, `Low`).
*   **Estimated Effort:** An estimate of the time required (e.g., `1 day`, `4 hours`).

### 3.2 Example Tasks (Illustrative)

These examples demonstrate the level of granularity and detail we expect for our tasks. Actual tasks will be generated as part of our regular sprint planning.

#### Task: `INFRA-001` - Initialize Docker Compose for PostgreSQL and Python Service

*   **Title:** Initialize Docker Compose for PostgreSQL and Python Service
*   **Description:** Create a `docker-compose.yml` file that defines two essential services: `db` (PostgreSQL) and `app` (a Python-based service). The `db` service should utilize the official PostgreSQL image, ensure data persistence using a named volume, and expose port 5432. The `app` service will build from a `Dockerfile` located in the project root, mount the current directory as a volume, and declare `db` as a dependency. Crucially, environment variables for PostgreSQL connection must be correctly set for the `app` service.
*   **Acceptance Criteria:**
    *   A `docker-compose.yml` file exists in the project root.
    *   The `db` service is correctly defined, using the `postgres:latest` image.
    *   A named volume `pg_data` is defined and successfully mounted to `/var/lib/postgresql/data` within the `db` service.
    *   `POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD` environment variables are properly set for the `db` service.
    *   The `app` service is defined, building from `./Dockerfile`.
    *   The current directory is mounted to `/app` in the `app` service.
    *   The `app` service correctly depends on the `db` service.
    *   The `DATABASE_URL` environment variable is set in the `app` service, pointing to the `db` service.
    *   Running `docker compose up` successfully starts both services without any errors.
*   **Dependencies:** None.
*   **Assigned To:** AI Agent
*   **Status:** To Do
*   **Priority:** High
*   **Estimated Effort:** 4 hours

#### Task: `DATA-001` - Implement LinkedIn Jobs API Ingestion Script

*   **Title:** Implement LinkedIn Jobs API Ingestion Script
*   **Description:** Develop a Python script (`src/ingestion/linkedin_jobs.py`) that connects to the LinkedIn Jobs API (or a suitable public equivalent/mock API for initial development) to fetch job postings relevant to the UAE. The script must handle API authentication (if applicable), pagination, and rate limiting. It should extract key data points such as `job_title`, `job_description`, `company_name`, `location`, `posted_date`, and `salary_range` (if available). The extracted data should be structured into a Python dictionary or object for subsequent loading.
*   **Acceptance Criteria:**
    *   The `src/ingestion/linkedin_jobs.py` file exists.
    *   The script successfully fetches at least 10 job postings from the target API.
    *   All specified fields are included in the extracted data.
    *   The script effectively handles basic error cases (e.g., API limits, network issues).
    *   The output of the script is a list of dictionaries, each representing a job posting.
*   **Dependencies:** `INFRA-001` (Python service running).
*   **Assigned To:** Human Developer
*   **Status:** To Do
*   **Priority:** High
*   **Estimated Effort:** 1 day

#### Task: `DB-001` - Create `raw_job_postings` Table in PostgreSQL

*   **Title:** Create `raw_job_postings` Table in PostgreSQL
*   **Description:** Write a SQL script (`sql/init/create_raw_job_postings.sql`) to create the `raw_job_postings` table within the `raw_data` schema in the PostgreSQL database. The table should include columns for `job_posting_id` (UUID, primary key), `job_title` (VARCHAR), `job_description` (TEXT), `company_name` (VARCHAR), `location` (VARCHAR), `posted_date` (DATE), `salary_min` (DECIMAL), `salary_max` (DECIMAL), `currency` (VARCHAR(3)), and `raw_json` (JSONB) to store the original API response. Ensure appropriate data types and constraints are applied.
*   **Acceptance Criteria:**
    *   The `sql/init/create_raw_job_postings.sql` file exists.
    *   Executing the script successfully creates the `raw_job_postings` table with the specified schema.
    *   The table has a primary key defined on `job_posting_id`.
    *   All columns possess appropriate data types.
*   **Dependencies:** `INFRA-001` (PostgreSQL service running).
*   **Assigned To:** AI Agent
*   **Status:** To Do
*   **Priority:** Medium
*   **Estimated Effort:** 2 hours

### 3.3 Task Management Workflow

Our task management workflow is structured to ensure efficient progress:

*   **Creation:** Tasks are typically created during sprint planning sessions or as bugs and enhancements are identified.
*   **Assignment:** Tasks are assigned to either human developers or AI coding agents, based on their complexity and type.
*   **Execution:** Assigned parties implement the task, diligently updating its status as they progress.
*   **Review:** Completed tasks undergo a thorough review process, which includes code reviews for human developers and automated validation for AI agents.
*   **Closure:** Once all acceptance criteria are met and the task has been reviewed, it is marked as `Done`.
