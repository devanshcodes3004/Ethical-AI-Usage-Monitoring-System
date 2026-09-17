"""
dashboard.py

Dashboard for AI Governance statistics.
"""

import streamlit as st
from datetime import datetime


def format_timestamp(timestamp):

    if not timestamp:
        return "Unknown"

    try:

        if isinstance(timestamp, datetime):

            return timestamp.strftime(
                "%d %b %Y, %I:%M:%S %p"
            )

        return str(timestamp)

    except Exception:

        return str(timestamp)


def display_dashboard(stats: dict):

    st.title("📊 AI Governance Dashboard")

    st.caption("Real-time AI Usage Monitoring")

    st.divider()

    # ======================================================
    # Overview Statistics
    # ======================================================

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

    # ======================================================
    # Model Usage & Risk Statistics
    # ======================================================

    col1, col2 = st.columns(2)

    with col1:

        st.subheader("🤖 Model Usage")

        total_models = (
            stats["gemini_count"] +
            stats["ollama_count"]
        )

        if total_models > 0:

            gemini_percentage = (
                stats["gemini_count"] /
                total_models
            )

            ollama_percentage = (
                stats["ollama_count"] /
                total_models
            )

            st.write(
                f"Gemini: {stats['gemini_count']}"
            )

            st.progress(
                gemini_percentage
            )

            st.write(
                f"Ollama: {stats['ollama_count']}"
            )

            st.progress(
                ollama_percentage
            )

        else:

            st.info(
                "No model usage available."
            )

    with col2:

        st.subheader("⚠️ Risk Statistics")

        st.metric(
            "Average Risk Score",
            stats["average_risk_score"]
        )

        st.metric(
            "Highest Risk Score",
            stats["highest_risk_score"]
        )

    st.divider()

    # ======================================================
    # Top Risk Categories
    # ======================================================

    st.subheader("🏷️ Top Risk Categories")

    if stats["top_categories"]:

        for category in stats["top_categories"]:

            st.write(
                f"• {category['_id']} "
                f"({category['count']})"
            )

    else:

        st.success(
            "No Risk Categories Recorded"
        )

    st.divider()

    # ======================================================
    # Recent Blocked Requests
    # ======================================================

    st.subheader(
        "🚫 Recent Blocked Requests"
    )

    blocked_requests = stats[
        "recent_blocked_requests"
    ]

    if blocked_requests:

        for index, request in enumerate(
            blocked_requests,
            start=1
        ):

            prompt = request.get(
                "prompt",
                "Prompt not available"
            )

            reason = request.get(
                "reason",
                "Reason not available"
            )

            risk_score = request.get(
                "risk_score",
                0
            )

            risk_level = request.get(
                "risk_level",
                "UNKNOWN"
            )

            categories = request.get(
                "categories",
                []
            )

            confidence = request.get(
                "confidence",
                0
            )

            selected_model = request.get(
                "selected_model",
                "Unknown"
            )

            timestamp = format_timestamp(
                request.get("timestamp")
            )

            with st.expander(
                f"🚫 Blocked Request #{index}"
            ):

                # ------------------------------------------
                # Exact User Prompt
                # ------------------------------------------

                st.markdown(
                    "### 💬 User Prompt"
                )

                st.code(
                    prompt,
                    language="text"
                )

                # ------------------------------------------
                # Request Information
                # ------------------------------------------

                st.markdown(
                    "### 📋 Request Details"
                )

                col1, col2, col3 = st.columns(3)

                with col1:

                    st.metric(
                        "Risk Score",
                        risk_score
                    )

                with col2:

                    st.metric(
                        "Risk Level",
                        risk_level
                    )

                with col3:

                    st.metric(
                        "Confidence",
                        f"{confidence:.2%}"
                        if isinstance(
                            confidence,
                            (int, float)
                        )
                        else confidence
                    )

                # ------------------------------------------
                # Governance Information
                # ------------------------------------------

                st.markdown(
                    "### 🛡️ Governance Decision"
                )

                st.write(
                    f"**Decision:** 🚫 {request.get('decision', 'BLOCK')}"
                )

                st.write(
                    f"**Reason:** {reason}"
                )

                if categories:

                    st.write(
                        "**Categories:** "
                        + ", ".join(categories)
                    )

                else:

                    st.write(
                        "**Categories:** None"
                    )

                # ------------------------------------------
                # Model & Timestamp
                # ------------------------------------------

                st.markdown(
                    "### 🤖 Processing Information"
                )

                col1, col2 = st.columns(2)

                with col1:

                    st.write(
                        f"**Selected Model:** "
                        f"{selected_model}"
                    )

                with col2:

                    st.write(
                        f"**Date & Time:** "
                        f"{timestamp}"
                    )

                # ------------------------------------------
                # IDs
                # ------------------------------------------

                with st.expander(
                    "Technical Details"
                ):

                    st.write(
                        f"**Session ID:** "
                        f"{request.get('session_id', 'N/A')}"
                    )

                    st.write(
                        f"**User ID:** "
                        f"{request.get('user_id', 'N/A')}"
                    )

                    st.write(
                        f"**Message ID:** "
                        f"{request.get('message_id', 'N/A')}"
                    )

    else:

        st.success(
            "No blocked requests."
        )