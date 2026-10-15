"""
governance_service.py

Evaluates sensitive-data restrictions and administrator policies before model-based risk analysis.
"""

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
    def _policy_decision(action, risk_score, reason, policy):
        return GovernanceDecision(
            risk_score=risk_score,
            risk_level=(
                RiskLevel.HIGH if action == "BLOCK"
                else RiskLevel.MEDIUM
            ),
            decision=Decision(action),
            selected_model=ModelProvider.OLLAMA,
            categories=[policy.get("category", "Custom Policy")],
            reason=reason,
            confidence=1.0,
            sanitized_prompt=None,
        )
