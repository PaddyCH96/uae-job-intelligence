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


def display_skill_intelligence():
    """Display skill demand trends and analysis."""
    st.subheader("🎯 Skill Intelligence")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Top In-Demand Skills**")
        try:
            response = requests.get(f"{API_BASE_URL}/aggregations/by-skill", params={"limit": 15})
            if response.status_code == 200:
                skill_data = response.json()
                if skill_data:
                    df = pd.DataFrame(skill_data)
                    fig = px.bar(
                        df,
                        x="count",
                        y="name",
                        orientation="h",
                        title="Most Requested Skills",
                        labels={"count": "Job Count", "name": "Skill"},
                        color="count",
                        color_continuous_scale="Blues"
                    )
                    fig.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No skill data available")
            else:
                st.info("Skill aggregation endpoint not available")
        except Exception as e:
            st.info("Skill data pending enrichment")
    
    with col2:
        st.markdown("**Technology Stack Trends**")
        try:
            response = requests.get(f"{API_BASE_URL}/aggregations/by-technology", params={"limit": 15})
            if response.status_code == 200:
                tech_data = response.json()
                if tech_data:
                    df = pd.DataFrame(tech_data)
                    fig = px.bar(
                        df,
                        x="count",
                        y="name",
                        orientation="h",
                        title="Popular Technologies",
                        labels={"count": "Job Count", "name": "Technology"},
                        color="count",
                        color_continuous_scale="Greens"
                    )
                    fig.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No technology data available")
            else:
                st.info("Technology aggregation endpoint not available")
        except Exception as e:
            st.info("Technology data pending enrichment")


def display_salary_intelligence():
    """Display salary analysis and insights."""
    st.subheader("💰 Salary Intelligence")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Salary Distribution by Experience Level**")
        jobs = fetch_jobs(limit=200)
        if jobs:
            df = pd.DataFrame(jobs)
            df_filtered = df[df["salary_min"].notna() & df["salary_max"].notna()].copy()
            
            if not df_filtered.empty:
                df_filtered["salary_avg"] = (df_filtered["salary_min"] + df_filtered["salary_max"]) / 2
                
                # Create salary ranges
                bins = [0, 15000, 25000, 35000, 50000, 100000]
                labels = ["<15K", "15-25K", "25-35K", "35-50K", "50K+"]
                df_filtered["salary_range"] = pd.cut(df_filtered["salary_avg"], bins=bins, labels=labels)
                
                salary_dist = df_filtered["salary_range"].value_counts().reset_index()
                salary_dist.columns = ["range", "count"]
                
                fig = px.bar(
                    salary_dist,
                    x="range",
                    y="count",
                    title="Salary Distribution (AED Monthly)",
                    labels={"range": "Salary Range", "count": "Number of Jobs"},
                    color="count",
                    color_continuous_scale="Oranges"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No salary data available")
    
    with col2:
        st.markdown("**Salary by Top Skills**")
        if jobs:
            df = pd.DataFrame(jobs)
            df_salary = df[df["salary_min"].notna() & df["extracted_skills"].notna()].copy()
            
            if not df_salary.empty:
                # Explode skills
                df_salary["salary_avg"] = (df_salary["salary_min"] + df_salary["salary_max"]) / 2
                skills_exploded = df_salary.explode("extracted_skills")
                skill_salary = skills_exploded.groupby("extracted_skills")["salary_avg"].agg(["mean", "count"]).reset_index()
                skill_salary = skill_salary[skill_salary["count"] >= 2].nlargest(10, "count")
                
                if not skill_salary.empty:
                    fig = px.bar(
                        skill_salary,
                        x="extracted_skills",
                        y="mean",
                        title="Average Salary by Skill (AED)",
                        labels={"extracted_skills": "Skill", "mean": "Avg Salary"},
                        color="count",
                        color_continuous_scale="Purples"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Insufficient skill-salary data")
            else:
                st.info("No skill-salary data available")


def display_sentiment_insights():
    """Display job sentiment and market mood analysis."""
    st.subheader("😊 Market Sentiment")
    
    jobs = fetch_jobs(limit=200)
    if not jobs:
        st.info("No data available")
        return
    
    df = pd.DataFrame(jobs)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if "sentiment_score" in df.columns:
            positive = len(df[df["sentiment_score"] > 0.5])
            st.metric("Positive Listings", positive)
        else:
            st.metric("Positive Listings", "N/A")
    
    with col2:
        if "sentiment_score" in df.columns:
            neutral = len(df[(df["sentiment_score"] >= -0.5) & (df["sentiment_score"] <= 0.5)])
            st.metric("Neutral Listings", neutral)
        else:
            st.metric("Neutral Listings", "N/A")
    
    with col3:
        if "sentiment_score" in df.columns:
            negative = len(df[df["sentiment_score"] < -0.5])
            st.metric("Negative Listings", negative)
        else:
            st.metric("Negative Listings", "N/A")
    
    if "sentiment_score" in df.columns and df["sentiment_score"].notna().any():
        fig = px.histogram(
            df,
            x="sentiment_score",
            nbins=20,
            title="Sentiment Distribution",
            labels={"sentiment_score": "Sentiment Score"},
            color_discrete_sequence=["#2ecc71"]
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sentiment analysis pending. Run LLM enrichment to enable.")


def display_market_intelligence():
    """Display market intelligence summary."""
    st.subheader("📊 Market Intelligence Summary")
    
    jobs = fetch_jobs(limit=200)
    if not jobs:
        st.info("No data available")
        return
    
    df = pd.DataFrame(jobs)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Key Insights**")
        
        # Calculate insights
        total_jobs = len(df)
        avg_salary = df["salary_avg"].mean() if "salary_avg" in df.columns else None
        top_skill = df["extracted_skills"].explode().value_counts().index[0] if "extracted_skills" in df.columns else "N/A"
        top_city = df["city"].value_counts().index[0] if "city" in df.columns else "N/A"
        
        salary_text = f"AED {avg_salary:,.0f}/month" if avg_salary else "N/A"
        st.markdown(f"""
        - **Total Active Listings:** {total_jobs}
        - **Average Salary:** {salary_text}
        - **Most In-Demand Skill:** {top_skill}
        - **Top Hiring City:** {top_city}
        - **Remote Work Available:** {df['remote_allowed'].sum() if 'remote_allowed' in df.columns else 0} jobs
        """)
    
    with col2:
        st.markdown("**Hiring Trends**")
        
        # Job growth indicators
        if "posted_date" in df.columns:
            df["posted_date"] = pd.to_datetime(df["posted_date"])
            recent = df[df["posted_date"] >= pd.Timestamp.now() - pd.Timedelta(days=7)]
            older = df[df["posted_date"] < pd.Timestamp.now() - pd.Timedelta(days=7)]
            
            st.markdown(f"""
            - **Last 7 days:** {len(recent)} new listings
            - **Older:** {len(older)} listings
            - **Growth Rate:** {((len(recent) / len(older) * 100) if len(older) > 0 else 0):.1f}%
            """)
        
        # Industry breakdown
        if "industry" in df.columns:
            industry_counts = df["industry"].value_counts().head(5)
            st.markdown("**Top Industries:**")
            for industry, count in industry_counts.items():
                st.markdown(f"  - {industry}: {count} jobs")


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
            "company_name",
            "city",
            "posted_date",
            "salary_range",
            "extracted_skills",
            "remote_allowed",
            "visa_sponsorship"
        ]

        available_cols = [col for col in display_cols if col in df.columns]
        
        # Format skills for display
        if "extracted_skills" in df.columns:
            df["extracted_skills"] = df["extracted_skills"].apply(
                lambda x: ", ".join(x) if isinstance(x, list) else str(x) if x else "N/A"
            )

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
    st.title("📊 UAE Job Intelligence Platform")
    st.markdown("**Real-time market intelligence for UAE data & AI jobs**")

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
    st.header("📈 Platform Metrics")
    display_metrics()

    st.divider()

    st.header("🧠 Market Intelligence")
    display_market_intelligence()

    st.divider()

    st.header("📊 Market Insights")
    display_charts()

    st.divider()

    st.header("🎯 Skill & Technology Intelligence")
    display_skill_intelligence()

    st.divider()

    st.header("💰 Salary Intelligence")
    display_salary_intelligence()

    st.divider()

    st.header("😊 Market Sentiment")
    display_sentiment_insights()

    st.divider()

    st.header("🎯 Job Recommendations")
    from src.dashboard.pages.recommendations import render_recommendations
    render_recommendations()

    st.divider()

    st.header("🔑 ATS Keyword Intelligence")
    from src.dashboard.pages.ats_keywords import render_ats_keywords
    render_ats_keywords()

    st.divider()

    st.header("🏢 Company Contacts")
    from src.dashboard.pages.contacts import render_contacts
    render_contacts()

    st.divider()

    display_job_table()

    # Footer
    st.divider()
    st.caption("UAE Job Intelligence Platform | Powered by LLM-enriched analytics | Data refreshed every 5 minutes")


if __name__ == "__main__":
    main()
