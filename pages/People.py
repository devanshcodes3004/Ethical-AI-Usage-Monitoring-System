"""Employee and customer records page."""

import streamlit as st

from ui.people import render_people_manager


st.set_page_config(
    page_title="Employee & Customer Records",
    page_icon="👥",
    layout="wide",
)

render_people_manager()
