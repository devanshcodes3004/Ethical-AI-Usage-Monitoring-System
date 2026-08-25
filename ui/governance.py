"""
governance.py

Renders the Governance Analysis panel.
"""

import streamlit as st


def display_governance(decision):

    with st.expander(
        "🛡️ Governance Analysis",
        expanded=False
    ):

        col1, col2 = st.columns(2)

        with col1:

            st.metric(
                "Risk Score",
                decision.risk_score
            )

            st.metric(
                "Risk Level",
                decision.risk_level.value
            )

        with col2:

            st.metric(
                "Decision",
                decision.decision.value
            )

            st.metric(
                "Selected Model",
                decision.selected_model.value
            )

        st.write("### Categories")

        if decision.categories:

            st.write(", ".join(decision.categories))

        else:

            st.success("No Risk Detected")

        st.write("### Reason")

        st.info(decision.reason)