"""ATS Keywords Dashboard Page - Display ATS keyword intelligence."""

import os
import sys
import streamlit as st
import plotly.express as px
import pandas as pd

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

try:
    from src.api.main import fetch_jobs
except ImportError:
    def fetch_jobs(limit=100):
        return []


def render_ats_keywords():
    """Render ATS keyword analysis."""
    st.header("🔑 ATS Keyword Intelligence")
    
    # Description
    st.markdown("""
    Extract ATS-optimization keywords from job descriptions to help you tailor your resume.
    These keywords are extracted using AI analysis of job postings.
    """)
    
    # Get jobs with ATS keywords
    jobs = fetch_jobs(limit=100)
    
    if not jobs:
        st.info("No jobs available. Run the daily scrape to populate data.")
        return
    
    # Collect all keywords
    all_hard_skills = []
    all_soft_skills = []
    all_action_verbs = []
    all_certifications = []
    
    for job in jobs:
        keywords = job.get("ats_keywords", {})
        if keywords:
            all_hard_skills.extend(keywords.get("hard_skills", []))
            all_soft_skills.extend(keywords.get("soft_skills", []))
            all_action_verbs.extend(keywords.get("action_verbs", []))
            all_certifications.extend(keywords.get("certifications", []))
    
    if not all_hard_skills:
        st.info("No ATS keywords extracted yet. Run the daily intelligence pipeline.")
        return
    
    # Top Skills
    st.subheader("Most In-Demand Skills")
    
    skill_counts = pd.Series(all_hard_skills).value_counts().head(15)
    fig = px.bar(
        x=skill_counts.values,
        y=skill_counts.index,
        orientation='h',
        title="Top 15 Technical Skills",
        labels={'x': 'Frequency', 'y': 'Skill'}
    )
    fig.update_layout(yaxis={'categoryorder': 'total ascending'})
    st.plotly_chart(fig, use_container_width=True)
    
    # Soft Skills
    st.subheader("Soft Skills")
    
    soft_skill_counts = pd.Series(all_soft_skills).value_counts().head(10)
    fig = px.bar(
        x=soft_skill_counts.values,
        y=soft_skill_counts.index,
        orientation='h',
        title="Top 10 Soft Skills",
        labels={'x': 'Frequency', 'y': 'Skill'},
        color_discrete_sequence=['#2ecc71']
    )
    fig.update_layout(yaxis={'categoryorder': 'total ascending'})
    st.plotly_chart(fig, use_container_width=True)
    
    # Action Verbs
    st.subheader("Action Verbs")
    
    verb_counts = pd.Series(all_action_verbs).value_counts().head(10)
    fig = px.bar(
        x=verb_counts.values,
        y=verb_counts.index,
        orientation='h',
        title="Top 10 Action Verbs",
        labels={'x': 'Frequency', 'y': 'Verb'},
        color_discrete_sequence=['#3498db']
    )
    fig.update_layout(yaxis={'categoryorder': 'total ascending'})
    st.plotly_chart(fig, use_container_width=True)
    
    # Certifications
    if all_certifications:
        st.subheader("Certifications")
        
        cert_counts = pd.Series(all_certifications).value_counts().head(10)
        st.dataframe(cert_counts.reset_index().rename(columns={0: 'Count', 'index': 'Certification'}))
    
    # ATS Tips
    st.subheader("💡 ATS Optimization Tips")
    
    st.markdown("""
    1. **Use exact keywords** from the job description
    2. **Include both acronyms and full terms** (e.g., "SQL" and "Structured Query Language")
    3. **Use standard job titles** that ATS systems recognize
    4. **Avoid special characters** and unusual formatting
    5. **Include relevant certifications** mentioned in the posting
    """)
