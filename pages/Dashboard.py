"""
Dashboard.py

Dashboard page for the Ethical AI Usage Monitoring System.
"""

import streamlit as st

from services.dashboard_service import DashboardService
from ui.dashboard import display_dashboard

# ==========================================================
# Page Configuration
# ==========================================================

st.set_page_config(
    page_title="AI Governance Dashboard",
    page_icon="📊",
    layout="wide"
)

# ==========================================================
# Initialize Service
# ==========================================================

dashboard_service = DashboardService()

# ==========================================================
# Load Statistics
# ==========================================================

with st.spinner("Loading Dashboard..."):

    stats = dashboard_service.get_dashboard_statistics()

# ==========================================================
# Display Dashboard
# ==========================================================

display_dashboard(stats)