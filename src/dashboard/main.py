"""Streamlit dashboard for UAE Job Intelligence Platform."""

import os
import requests
from typing import Dict, List
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Page config
st.set_page_config(
    page_title="UAE Job Intelligence Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


@st.cache_data(ttl=300)
def fetch_stats() -> Dict:
    """Fetch platform statistics from API."""
    try:
        response = requests.get(f"{API_BASE_URL}/stats")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Failed to fetch stats: {str(e)}")
        return {}


@st.cache_data(ttl=300)
def fetch_jobs(skip: int = 0, limit: int = 100, **filters) -> List[Dict]:
    """Fetch job postings from API."""
    try:
        params = {"skip": skip, "limit": limit, **filters}
        response = requests.get(f"{API_BASE_URL}/jobs", params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Failed to fetch jobs: {str(e)}")
        return []


@st.cache_data(ttl=300)
def fetch_aggregation(endpoint: str, limit: int = 20) -> List[Dict]:
    """Fetch aggregation data from API."""
    try:
        response = requests.get(f"{API_BASE_URL}/{endpoint}", params={"limit": limit})
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Failed to fetch aggregation: {str(e)}")
        return []


def display_metrics():
    """Display key platform metrics."""
    stats = fetch_stats()

    if not stats:
        return

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Active Jobs", f"{stats.get('active_jobs', 0):,}")

    with col2:
        st.metric("Total Companies", f"{stats.get('total_companies', 0):,}")

    with col3:
        st.metric("Remote Jobs", f"{stats.get('remote_jobs', 0):,}")

    with col4:
        st.metric("Visa Sponsorship", f"{stats.get('visa_sponsorship_jobs', 0):,}")

    # Second row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Jobs Processed", f"{stats.get('total_jobs', 0):,}")

    with col2:
        st.metric("Duplicates Removed", f"{stats.get('duplicate_jobs', 0):,}")

    with col3:
        st.metric("Deduplication Rate", f"{stats.get('deduplication_rate', 0)}%")

    with col4:
        st.metric("Jobs with Salary", f"{stats.get('jobs_with_salary_info', 0):,}")


def display_charts():
    """Display visualization charts."""
    col1, col2 = st.columns(2)

    # Top Companies Chart
    with col1:
        st.subheader("Top Hiring Companies")
        company_data = fetch_aggregation("aggregations/by-company", limit=10)

        if company_data:
            df = pd.DataFrame(company_data)
            fig = px.bar(
                df,
                x="count",
                y="name",
                orientation="h",
                title="Top 10 Companies by Job Count",
                labels={"count": "Number of Jobs", "name": "Company"}
            )
            fig.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, use_container_width=True)

    # Top Cities Chart
    with col2:
        st.subheader("Top Cities")
        city_data = fetch_aggregation("aggregations/by-city", limit=10)

        if city_data:
            df = pd.DataFrame(city_data)
            fig = px.pie(
                df,
                values="count",
                names="name",
                title="Job Distribution by City"
            )
            st.plotly_chart(fig, use_container_width=True)


def display_job_table():
    """Display job listings table with filters."""
    st.subheader("Job Listings")

    # Filters in sidebar
    with st.sidebar:
        st.header("Filters")

        company_filter = st.text_input("Company Name")
        city_filter = st.text_input("City")
        min_salary = st.number_input("Minimum Salary (AED)", min_value=0, value=0, step=1000)
        remote_only = st.checkbox("Remote Only")
        visa_sponsorship = st.checkbox("Visa Sponsorship")

        apply_filters = st.button("Apply Filters")

    # Build filter dict
    filters = {}
    if company_filter:
        filters["company_name"] = company_filter
    if city_filter:
        filters["city"] = city_filter
    if min_salary > 0:
        filters["min_salary"] = min_salary
    if remote_only:
        filters["remote_only"] = True
    if visa_sponsorship:
        filters["visa_sponsorship"] = True

    # Fetch and display jobs
    jobs = fetch_jobs(skip=0, limit=100, **filters)

    if jobs:
        # Convert to DataFrame
        df = pd.DataFrame(jobs)

        # Format salary columns
        if "salary_min" in df.columns and "salary_max" in df.columns:
            df["salary_range"] = df.apply(
                lambda row: f"AED {row['salary_min']:,.0f} - {row['salary_max']:,.0f}"
                if pd.notna(row['salary_min']) and pd.notna(row['salary_max'])
                else "Not specified",
                axis=1
            )

        # Select columns to display
        display_cols = [
            "job_title",
            "posted_date",
            "salary_range",
            "remote_allowed",
            "visa_sponsorship"
        ]

        available_cols = [col for col in display_cols if col in df.columns]

        st.dataframe(
            df[available_cols],
            use_container_width=True,
            hide_index=True
        )

        st.caption(f"Showing {len(jobs)} jobs")
    else:
        st.info("No jobs found matching the filters.")


def main():
    """Main dashboard application."""
    # Header
    st.title("📊 UAE Job Intelligence Dashboard")
    st.markdown("Real-time insights into the UAE data & AI job market")

    # Health check
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            st.error("⚠️ API is not responding. Please check if services are running.")
            return
    except Exception:
        st.error("⚠️ Cannot connect to API. Please ensure the backend is running.")
        st.code("docker compose up")
        return

    # Display sections
    st.header("Platform Metrics")
    display_metrics()

    st.divider()

    st.header("Market Insights")
    display_charts()

    st.divider()

    display_job_table()

    # Footer
    st.divider()
    st.caption("UAE Job Intelligence Platform - Phase 1 MVP | Data refreshed every 5 minutes")


if __name__ == "__main__":
    main()
