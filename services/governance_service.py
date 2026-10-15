"""
governance_service.py

Evaluates administrator-configured policies before model-based risk analysis.
"""

from governance.decision_engine import DecisionEngine
from governance.governance_engine import GovernanceEngine
from governance.schemas import Decision, ModelProvider, RiskLevel, GovernanceDecision
from services.policy_service import PolicyService


class GovernanceService:

    def __init__(self):
        self.governance_engine = GovernanceEngine()
        self.decision_engine = DecisionEngine()
        self.policy_service = PolicyService()

    def analyze_prompt(self, prompt: str):
        # Explicit policy rules are checked before the model-based detector.
        # A matched BLOCK/WARN/ALLOW policy is converted into the same schema
        # consumed by the existing chat pipeline.
        matched_policy = self.policy_service.evaluate(prompt)
        if matched_policy:
            action = matched_policy.get("action", "WARN")
            if action in {"BLOCK", "WARN", "ALLOW"}:
                risk_score = {"ALLOW": 5, "WARN": 45, "BLOCK": 90}[action]
                reason = (
                    f"Matched policy: {matched_policy.get('name', 'Unnamed policy')}. "
                    f"{matched_policy.get('description', '')}"
                ).strip()[:290]
                if len(reason) < 10:
                    reason = f"Matched policy: {matched_policy.get('name', 'Unnamed policy')}."
                return GovernanceDecision(
                    risk_score=risk_score,
                    risk_level=(
                        RiskLevel.HIGH if action == "BLOCK"
                        else RiskLevel.MEDIUM if action == "WARN"
                        else RiskLevel.LOW
                    ),
                    decision=Decision(action),
                    selected_model=(
                        ModelProvider.OLLAMA if action in {"BLOCK", "WARN"}
                        else ModelProvider.GEMINI
                    ),
                    categories=[matched_policy.get("category", "Custom Policy")],
                    reason=reason,
                    confidence=1.0,
                    sanitized_prompt=None,
                )

        analysis = self.governance_engine.analyze(prompt)
        return self.decision_engine.evaluate(analysis)
