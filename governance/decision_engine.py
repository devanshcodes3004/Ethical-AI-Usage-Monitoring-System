"""
decision_engine.py

Applies deterministic governance rules to the analysis produced
by the AI Governance Engine.
"""

from governance.schemas import (
    GovernanceDecision,
    RiskLevel,
    Decision,
    ModelProvider,
)


class DecisionEngine:
    """
    Applies deterministic governance rules.
    """

    def evaluate(self, analysis: GovernanceDecision) -> GovernanceDecision:
        """
        Applies business rules to the governance analysis.
        """

        score = analysis.risk_score

        if score < 30:
            analysis.risk_level = RiskLevel.LOW
            analysis.decision = Decision.ALLOW

        elif score < 70:
            analysis.risk_level = RiskLevel.MEDIUM
            analysis.decision = Decision.WARN

        else:
            analysis.risk_level = RiskLevel.HIGH
            analysis.decision = Decision.BLOCK

        if score >= 70:
            analysis.selected_model = ModelProvider.OLLAMA
        else:
            analysis.selected_model = ModelProvider.GEMINI

        return analysis