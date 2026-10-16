"""
governance_service.py

Evaluates sensitive-data restrictions and administrator policies before model-based risk analysis.
"""

import re

from governance.decision_engine import DecisionEngine
from governance.governance_engine import GovernanceEngine
from governance.schemas import Decision, ModelProvider, RiskLevel, GovernanceDecision
from services.policy_service import PolicyService
from services.csv_data_service import is_sensitive_data_request


class GovernanceService:

    def __init__(self):
        self.governance_engine = GovernanceEngine()
        self.decision_engine = DecisionEngine()
        self.policy_service = PolicyService()

    def analyze_prompt(self, prompt: str):
        # Credential retrieval is denied deterministically before any data lookup
        # or LLM call. This is a safety rule, not a model-generated judgment.
        if is_sensitive_data_request(prompt):
            return self._policy_decision(
                "BLOCK",
                100,
                "Requests to retrieve passwords, credentials, tokens, payment secrets, or similar sensitive information are not permitted.",
                {
                    "name": "Sensitive credential disclosure prevention",
                    "category": "Sensitive Data",
                },
            )

        # Explicit BLOCK and WARN policies take precedence over model-based
        # classification. ALLOW policies never override high-risk BLOCK results.
        matched_policy = self.policy_service.evaluate(prompt)
        if matched_policy and matched_policy.get("action") in {"BLOCK", "WARN"}:
            action = matched_policy["action"]
            risk_score = {"WARN": 45, "BLOCK": 90}[action]
            reason = (
                f"Matched policy: {matched_policy.get('name', 'Unnamed policy')}. "
                f"{matched_policy.get('description', '')}"
            ).strip()[:290]
            if len(reason) < 10:
                reason = f"Matched policy: {matched_policy.get('name', 'Unnamed policy')}."
            return self._policy_decision(action, risk_score, reason, matched_policy)

        # Counts of customers with a specified problem category are likewise
        # a minimized operational query. The explicit BLOCK/WARN policy check
        # above still takes precedence.
        if self._is_customer_problem_count_lookup(prompt):
            return self._policy_decision(
                "ALLOW",
                0,
                "Allowed: aggregate count of customers with matching problem records; personal fields are not returned.",
                {"name": "Minimized customer issue count", "category": "Business Data"},
            )

        # A narrowly scoped request for IDs of customers with issues is an
        # approved operational lookup, not a request to expose contact data.
        # The downstream query returns at most 10 IDs plus issue/status only.
        if self._is_customer_problem_id_lookup(prompt):
            return self._policy_decision(
                "ALLOW",
                0,
                "Allowed: limited customer IDs linked to reported problems; contact data and credentials remain excluded.",
                {
                    "name": "Minimized customer issue lookup",
                    "category": "Business Data",
                },
            )

        analysis = self.governance_engine.analyze(prompt)
        decision = self.decision_engine.evaluate(analysis)

        if (
            matched_policy
            and matched_policy.get("action") == "ALLOW"
            and decision.risk_score < 70
        ):
            decision.decision = Decision.ALLOW
            decision.selected_model = ModelProvider.GEMINI
            policy_name = matched_policy.get("name", "Allow policy")
            decision.reason = (
                f"Allowed by policy '{policy_name}'. "
                f"Classifier assessment: {decision.reason}"
            )[:300]

        return decision

    @staticmethod
    def _is_customer_problem_count_lookup(prompt):
        text = (prompt or "").casefold()
        has_count_intent = bool(
            re.search(r"\b(how many|count|number of|total number of)\b", text)
        )
        has_customer = bool(
            re.search(r"\b(customer|customers|client|clients|clint|clints)\b", text)
        )
        has_problem = bool(
            re.search(
                r"\b(problem|problems|issue|issues|complaint|complaints|del[io]ver(?:y|ies)|delivery|deliveries|shipping|payment|billing|refund|return|login|account|product|damaged|support)\b",
                text,
            )
        )
        return has_count_intent and has_customer and has_problem

    @staticmethod
    def _is_customer_problem_id_lookup(prompt):
        text = (prompt or "").casefold()
        has_customer = bool(re.search(r"\b(customer|customers|client|clients)\b", text))
        has_identifier = bool(re.search(r"\b(ids?|identifiers?)\b", text))
        has_problem = bool(re.search(
            r"\b(problem|problems|issue|issues|complaint|complaints|facing|affected|open|pending)\b",
            text,
        ))
        return has_customer and has_identifier and has_problem

    @staticmethod
    def _policy_decision(action, risk_score, reason, policy):
        return GovernanceDecision(
            risk_score=risk_score,
            risk_level=(
                RiskLevel.LOW if risk_score < 30
                else RiskLevel.MEDIUM if risk_score < 70
                else RiskLevel.HIGH
            ),
            decision=Decision(action),
            selected_model=ModelProvider.OLLAMA,
            categories=[policy.get("category", "Custom Policy")],
            reason=reason,
            confidence=1.0,
            sanitized_prompt=None,
        )
