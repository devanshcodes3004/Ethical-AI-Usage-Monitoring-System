import streamlit as st

from services.chat_service import ChatService
from services.session_service import SessionService

from ui.sidebar import render_sidebar
from ui.chat import (
    display_messages,
    display_user_message,
    display_assistant_message,
    user_input
)
from ui.governance import display_governance

# ==========================================================
# Page Configuration
# ==========================================================

st.set_page_config(
    page_title="Ethical AI Usage Monitoring System",
    page_icon="🛡️",
    layout="wide"
)

# ==========================================================
# Services
# ==========================================================

chat_service = ChatService()
session_service = SessionService()

# ==========================================================
# Session State
# ==========================================================

if "user_id" not in st.session_state:
    st.session_state.user_id = "user_001"

if "session_id" not in st.session_state:
    st.session_state.session_id = session_service.create_session(
        st.session_state.user_id
    )

if "messages" not in st.session_state:
    st.session_state.messages = chat_service.get_chat_history(
        st.session_state.session_id
    )

# ==========================================================
# Sidebar
# ==========================================================

with st.sidebar:

    selected_session, deleted, new_chat = render_sidebar(
        session_service=session_service,
        user_id=st.session_state.user_id,
        current_session_id=st.session_state.session_id
    )

if deleted or new_chat:

    st.session_state.session_id = selected_session

    st.session_state.messages = chat_service.get_chat_history(
        selected_session
    )

    st.rerun()

if selected_session != st.session_state.session_id:

    st.session_state.session_id = selected_session

    st.session_state.messages = chat_service.get_chat_history(
        selected_session
    )

    st.rerun()

# ==========================================================
# Main Page
# ==========================================================

st.title("🤖 Ethical AI Usage Monitoring System")

st.caption("Enterprise AI Governance Platform")

st.divider()

# ==========================================================
# Display Messages
# ==========================================================

display_messages(
    st.session_state.messages
)

# ==========================================================
# Chat Input
# ==========================================================

prompt = user_input()

if prompt:

    display_user_message(
        prompt
    )

    with st.spinner("Analyzing Prompt..."):

        result = chat_service.chat(
            session_id=st.session_state.session_id,
            user_id=st.session_state.user_id,
            prompt=prompt
        )

    response = result["response"]
    decision = result["decision"]

    display_assistant_message(
        response
    )

    display_governance(
        decision
    )

    st.session_state.messages = chat_service.get_chat_history(
        st.session_state.session_id
    )

    st.rerun()