"""
sidebar.py

Renders the Streamlit sidebar.
"""

import streamlit as st


def render_sidebar(
    session_service,
    user_id: str,
    current_session_id: str
):

    st.title("🛡️ AI Governance")

    new_chat = False
    deleted = False
    selected_session = current_session_id

    if st.button(
        "➕ New Chat",
        use_container_width=True
    ):

        selected_session = session_service.create_session(
            user_id=user_id
        )

        new_chat = True

    st.divider()

    st.subheader("Chat History")

    sessions = session_service.get_user_sessions(
        user_id
    )

    if not sessions:

        st.caption("No chats yet.")

        return selected_session, deleted, new_chat

    for session in sessions:

        session_id = session["session_id"]

        title = session["title"]

        if len(title) > 35:
            title = title[:35] + "..."

        col1, col2 = st.columns([8, 1])

        with col1:

            if st.button(
                f"💬 {title}",
                key=f"chat_{session_id}",
                use_container_width=True
            ):

                selected_session = session_id

        with col2:

            if st.button(
                "🗑️",
                key=f"delete_{session_id}"
            ):

                session_service.delete_session(
                    session_id
                )

                deleted = True

                if session_id == current_session_id:

                    selected_session = session_service.create_session(
                        user_id=user_id
                    )

    return selected_session, deleted, new_chat