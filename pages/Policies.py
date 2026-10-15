"""Policy management page for the Ethical AI Usage Monitoring System."""

import streamlit as st
from ui.policies import render_policy_manager

st.set_page_config(
    page_title="Governance Policies",
    page_icon="🧭",
    layout="wide",
)

render_policy_manager()
