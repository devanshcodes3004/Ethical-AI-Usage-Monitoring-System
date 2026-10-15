"""Streamlit UI for creating and managing governance policies."""

import streamlit as st
from services.policy_service import PolicyService


def render_policy_manager():
    st.title("🧭 Governance Policies")
    st.caption("Define which prompt categories should be allowed, flagged for review, or blocked before they reach an AI model.")

    service = PolicyService()
    policies = service.list_policies()

    with st.expander("➕ Create a policy", expanded=False):
        with st.form("policy_form", clear_on_submit=True):
            name = st.text_input("Policy name", placeholder="e.g. Block credential theft")
            category = st.selectbox(
                "Category",
                [
                    "Prompt Injection", "Sensitive Data", "Cybersecurity",
                    "Violence or Self-harm", "Harassment or Hate", "Medical Advice",
                    "Financial Advice", "Academic Integrity", "Custom"
                ],
            )
            custom_category = ""
            if category == "Custom":
                custom_category = st.text_input("Custom category", placeholder="e.g. Internal company topics")
            action = st.selectbox(
                "When matched, the policy should",
                ["BLOCK", "WARN", "ALLOW"],
                help="BLOCK stops the request; WARN marks it for review; ALLOW permits a matching request unless a stronger BLOCK/WARN policy also matches."
            )
            description = st.text_area("Description", placeholder="Explain what this policy enforces.")
            keywords_text = st.text_area(
                "Match terms (one per line)",
                placeholder="ignore previous instructions\nreveal system prompt",
                help="Case-insensitive phrase matching. Use specific phrases to reduce false positives."
            )
            enabled = st.checkbox("Enable this policy", value=True)
            submitted = st.form_submit_button("Save policy", use_container_width=True)
            if submitted:
                chosen_category = custom_category.strip() if category == "Custom" else category
                keywords = [line.strip() for line in keywords_text.splitlines() if line.strip()]
                try:
                    service.save_policy(name, chosen_category, action, description, keywords, enabled)
                    st.success("Policy saved.")
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))

    st.subheader("Configured policies")
    policies = service.list_policies()
    if not policies:
        st.info("No policies configured.")
        return

    for index, policy in enumerate(policies):
        status = "Enabled" if policy.get("enabled", True) else "Disabled"
        with st.container(border=True):
            left, middle, right = st.columns([5, 2, 1])
            with left:
                st.markdown(f"**{policy.get('name', 'Unnamed policy')}**")
                st.caption(f"{policy.get('category', 'Custom')} · {status}")
                if policy.get("description"):
                    st.write(policy["description"])
            with middle:
                st.metric("Action", policy.get("action", "WARN"))
            with right:
                if st.button("🗑️", key=f"delete_policy_{index}", help="Delete this policy"):
                    service.delete_policy(policy["name"])
                    st.rerun()
            terms = policy.get("keywords") or []
            st.caption("Match terms: " + (", ".join(terms) if terms else "No keyword terms configured"))
    st.info("Policy matching uses case-insensitive keyword phrases. It is a transparent first layer, not a replacement for semantic classifiers or security testing.")
