"""
dashboard.py

Dashboard for AI Governance statistics.
"""

import streamlit as st


def display_dashboard(stats: dict):

    st.title("📊 AI Governance Dashboard")
    st.caption("Real-time AI Usage Monitoring")
    st.divider()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Chats",
            stats["total_sessions"]
        )

    with col2:
        st.metric(
            "Total Messages",
            stats["total_messages"]
        )

    with col3:
        st.metric(
            "Blocked Requests",
            stats["blocked_requests"]
        )

    with col4:
        st.metric(
            "Allowed Requests",
            stats["allowed_requests"]
        )

    st.divider()

    col1, col2 = st.columns(2)

    with col1:

        st.subheader("Model Usage")

        total_models = (
            stats["gemini_count"] +
            stats["ollama_count"]
        )

        if total_models > 0:

            st.progress(stats["gemini_count"] / total_models)
            st.write(
                f"Gemini : {stats['gemini_count']}"
            )

            st.progress(stats["ollama_count"] / total_models)
            st.write(
                f"Ollama : {stats['ollama_count']}"
            )

        else:

            st.info("No model usage available.")

    with col2:

        st.subheader("Risk Statistics")

        st.metric(
            "Average Risk Score",
            stats["average_risk_score"]
        )

        st.metric(
            "Highest Risk Score",
            stats["highest_risk_score"]
        )

    st.divider()

    st.subheader("Top Risk Categories")

    if stats["top_categories"]:

        for category in stats["top_categories"]:

            st.write(
                f"• {category['_id']} ({category['count']})"
            )

    else:

        st.success("No Risk Categories Recorded")

    st.divider()

    st.subheader("Recent Blocked Requests")

    if stats["recent_blocked_requests"]:

        for request in stats["recent_blocked_requests"]:

            st.error(
                request["reason"]
            )

    else:

        st.success("No blocked requests.")