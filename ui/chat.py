"""
chat.py

Renders the chat conversation.
"""

import streamlit as st


def display_messages(messages):

    for message in messages:

        with st.chat_message(message["role"]):

            st.markdown(message["content"])


def user_input():

    return st.chat_input("Ask anything...")


def display_user_message(prompt: str):

    with st.chat_message("user"):

        st.markdown(prompt)


def display_assistant_message(response: str):

    with st.chat_message("assistant"):

        st.markdown(response)