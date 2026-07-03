# Data Model: UAE AI & Data Job Intelligence Platform

## 1. Introduction

This document lays out the conceptual data model for the UAE AI & Data Job Intelligence Platform. Our model is meticulously designed to support the efficient collection, transformation, and analysis of job market data, ultimately enabling us to generate actionable intelligence. We differentiate between **fact tables**, which capture specific events or measurements, and **dimension tables**, which provide the descriptive attributes that give context to those facts.

## 2. Fact Tables

Fact tables are where we store the quantitative data about events, such as individual job postings. These tables typically include foreign keys that link them to our dimension tables, along with measurable attributes that can be aggregated for analysis.

### 2.1 `fact_job_posting`

This table serves as the core record for each job posting, capturing its essential attributes.

| Column Name           | Data Type    | Description                                       | Relationships                               |
| :-------------------- | :----------- | :------------------------------------------------ | :------------------------------------------ |
| `job_posting_id`      | UUID         | Unique identifier for each job posting            | Primary Key                                 |
| `job_title`           | VARCHAR      | Title of the job                                  |                                             |
| `job_description`     | TEXT         | Full description of the job                       |                                             |
| `posted_date`         | DATE         | Date the job was posted                           |                                             |
| `salary_min`          | DECIMAL      | Minimum reported salary (if available)            |                                             |
| `salary_max`          | DECIMAL      | Maximum reported salary (if available)            |                                             |
| `currency`            | VARCHAR(3)   | Currency of the salary                            | FK to `dim_currency`                        |
| `experience_level`    | VARCHAR      | Required experience level (e.g., Junior, Senior)  | FK to `dim_experience_level`                |
| `employment_type`     | VARCHAR      | Type of employment (e.g., Full-time, Contract)    | FK to `dim_employment_type`                 |
| `company_id`          | UUID         | Foreign key to the `dim_company` table            | FK to `dim_company`                         |
| `location_id`         | UUID         | Foreign key to the `dim_location` table           | FK to `dim_location`                        |
| `source_id`           | UUID         | Foreign key to the `dim_source` table             | FK to `dim_source`                          |
| `extracted_skills`    | JSONB        | JSON array of skills extracted from description   |                                             |
| `extracted_technologies`| JSONB        | JSON array of technologies extracted              |                                             |

## 3. Dimension Tables

Dimension tables enrich our factual data by providing descriptive context. They contain attributes that help us categorize and describe the data found in our fact tables.

### 3.1 `dim_company`

This table holds comprehensive information about the companies that post jobs.

| Column Name      | Data Type | Description                               |
| :--------------- | :-------- | :---------------------------------------- |
| `company_id`     | UUID      | Unique identifier for each company        |
| `company_name`   | VARCHAR   | Name of the company                       |
| `industry`       | VARCHAR   | Industry sector of the company            |
| `company_size`   | VARCHAR   | Size of the company (e.g., Small, Large)  |
| `company_url`    | VARCHAR   | Official website URL of the company       |

### 3.2 `dim_location`

This table stores geographical details pertinent to job postings.

| Column Name      | Data Type | Description                               |
| :--------------- | :-------- | :---------------------------------------- |
| `location_id`    | UUID      | Unique identifier for each location       |
| `city`           | VARCHAR   | City where the job is located             |
| `state_province` | VARCHAR   | State or province (if applicable)         |
| `country`        | VARCHAR   | Country (always UAE for this project)     |
| `latitude`       | DECIMAL   | Latitude coordinate of the location       |
| `longitude`      | DECIMAL   | Longitude coordinate of the location      |

### 3.3 `dim_skill`

This table maintains a standardized list of skills identified within the job market.

| Column Name  | Data Type | Description                               |
| :----------- | :-------- | :---------------------------------------- |
| `skill_id`   | UUID      | Unique identifier for each skill          |
| `skill_name` | VARCHAR   | Name of the skill (e.g., Python, SQL)     |
| `skill_category`| VARCHAR   | Category of the skill (e.g., Programming) |

### 3.4 `dim_technology`

This table contains a standardized list of technologies prevalent in the job market.

| Column Name       | Data Type | Description                               |
| :---------------- | :-------- | :---------------------------------------- |
| `technology_id`   | UUID      | Unique identifier for each technology     |
| `technology_name` | VARCHAR   | Name of the technology (e.g., Spark, AWS) |
| `technology_category`| VARCHAR   | Category (e.g., Cloud, Database)          |

### 3.5 `dim_source`

This table records information about the various data sources from which job postings are gathered.

| Column Name  | Data Type | Description                               |
| :----------- | :-------- | :---------------------------------------- |
| `source_id`  | UUID      | Unique identifier for each data source    |
| `source_name`| VARCHAR   | Name of the data source (e.g., LinkedIn)  |
| `source_type`| VARCHAR   | Type of source (e.g., API, Scraped)       |
| `source_url` | VARCHAR   | Base URL of the data source               |

### 3.6 `dim_currency`

This table stores details about the currencies used for salary reporting.

| Column Name  | Data Type | Description                               |
| :----------- | :-------- | :---------------------------------------- |
| `currency_id`| UUID      | Unique identifier for each currency       |
| `currency_code`| VARCHAR(3)| ISO 4217 currency code (e.g., AED, USD)   |
| `currency_name`| VARCHAR   | Full name of the currency                 |

### 3.7 `dim_experience_level`

This table standardizes the various experience levels encountered in job postings.

| Column Name        | Data Type | Description                               |
| :----------------- | :-------- | :---------------------------------------- |
| `experience_level_id`| UUID      | Unique identifier for experience level    |
| `level_name`       | VARCHAR   | Name of the experience level              |
| `level_description`| TEXT      | Description of the experience level       |

### 3.8 `dim_employment_type`

This table standardizes the different types of employment offered.

| Column Name        | Data Type | Description                               |
| :----------------- | :-------- | :---------------------------------------- |
| `employment_type_id`| UUID      | Unique identifier for employment type     |
| `type_name`        | VARCHAR   | Name of the employment type               |
| `type_description` | TEXT      | Description of the employment type        |

## 4. Relationships

The `fact_job_posting` table forms the central hub of our data model, linking to various dimension tables through foreign keys. This design establishes a classic star schema, which is highly effective for facilitating efficient querying and in-depth analysis of job market data. Specifically, `fact_job_posting.company_id` references `dim_company.company_id`, `fact_job_posting.location_id` references `dim_location.location_id`, and `fact_job_posting.source_id` references `dim_source.source_id`. Similarly, `fact_job_posting.currency` links to `dim_currency.currency_code`, `fact_job_posting.experience_level` to `dim_experience_level.level_name`, and `fact_job_posting.employment_type` to `dim_employment_type.type_name`.

Skills and technologies, which are extracted from job descriptions, are stored as JSONB arrays within the `extracted_skills` and `extracted_technologies` columns of the `fact_job_posting` table. For more granular analysis and tracking of trends related to individual skills and technologies, these JSONB fields can be unnested or joined with the `dim_skill` and `dim_technology` tables, respectively. This process typically occurs within the transformation layer (dbt Core) to create aggregated fact tables or specialized analytical views.
