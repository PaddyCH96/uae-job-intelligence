"""Recommendations Dashboard Page - Display top 10 job recommendations."""

import streamlit as st
import pandas as pd
from datetime import datetime
from src.api.main import fetch_jobs, fetch_aggregation


def render_recommendations():
    """Render top 10 job recommendations."""
    st.header("🎯 Today's Top 10 Jobs")
    
    st.markdown("""
    AI-powered job recommendations based on skills match, salary, location, and experience level.
    Updated daily at 10 AM UAE time.
    """)
    
    # Get recommendations
    # For now, use the job ranking engine directly
    from src.intelligence.recommendations.engine import RecommendationEngine
    
    engine = RecommendationEngine()
    jobs = fetch_jobs(limit=100)
    
    if not jobs:
        st.info("No jobs available. Run the daily scrape to populate data.")
        return
    
    # Default user profile (can be customized)
    user_profile = {
        "skills": ["Python", "SQL", "Data Analysis", "Machine Learning"],
        "experience_years": 3,
        "expected_salary_min": 15000,
        "expected_salary_max": 30000,
        "preferred_cities": ["Dubai", "Abu Dhabi", "UAE"],
        "preferred_industries": ["Technology", "Finance"]
    }
    
    # Get recommendations
    recommendations = engine.rank_jobs(jobs, user_profile)
    
    if not recommendations:
        st.info("No recommendations available.")
        return
    
    # Display recommendations
    for i, rec in enumerate(recommendations, 1):
        score = rec.get("score", 0)
        score_color = "green" if score > 0.7 else "orange" if score > 0.5 else "red"
        
        with st.expander(f"#{i} - {rec.get('title', 'Unknown')} at {rec.get('company_name', 'Unknown')}", expanded=True):
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.markdown(f"**Score:** :{score_color}[{score:.1%}]")
                st.markdown(f"**Salary:** {rec.get('salary_range', 'Not specified')}")
                st.markdown(f"**Location:** {rec.get('city', 'Not specified')}")
            
            with col2:
                st.markdown(f"**Experience:** {rec.get('experience_level', 'Not specified')}")
                st.markdown(f"**Remote:** {'Yes' if rec.get('remote_allowed') else 'No'}")
            
            with col3:
                st.markdown(f"**Posted:** {rec.get('posted_date', 'Unknown')}")
                st.markdown(f"**Source:** {rec.get('source', 'Unknown')}")
            
            # ATS Keywords
            ats_keywords = rec.get("ats_keywords", {})
            if ats_keywords:
                st.subheader("📝 ATS Keywords to Use")
                
                col_a, col_b = st.columns(2)
                
                with col_a:
                    hard_skills = ats_keywords.get("hard_skills", [])
                    if hard_skills:
                        st.markdown("**Technical Skills:**")
                        st.markdown(", ".join(hard_skills[:5]))
                    
                    action_verbs = ats_keywords.get("action_verbs", [])
                    if action_verbs:
                        st.markdown("**Action Verbs:**")
                        st.markdown(", ".join(action_verbs[:5]))
                
                with col_b:
                    soft_skills = ats_keywords.get("soft_skills", [])
                    if soft_skills:
                        st.markdown("**Soft Skills:**")
                        st.markdown(", ".join(soft_skills[:3]))
            
            # Company Info
            st.subheader("🏢 Company Information")
            st.markdown(f"**Company:** {rec.get('company_name', 'Unknown')}")
            st.markdown(f"**Description:** {rec.get('description', 'No description available')[:200]}...")
            
            # Apply link
            if rec.get("url"):
                st.markdown(f"[Apply Now]({rec['url']})")
    
    # Refresh info
    st.divider()
    st.caption("Last updated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    st.caption("Recommendations refresh daily at 10 AM UAE time")
