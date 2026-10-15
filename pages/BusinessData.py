"""CSV business-data import page."""

import streamlit as st

from ui.business_data import render_business_data_page


st.set_page_config(
    page_title="Business Data (CSV)",
    page_icon="📂",
    layout="wide",
)

render_business_data_page()
