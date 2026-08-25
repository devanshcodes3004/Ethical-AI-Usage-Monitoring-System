"""
governance_service.py

Handles the governance pipeline.
"""

from governance.decision_engine import DecisionEngine
from governance.governance_engine import GovernanceEngine


class GovernanceService:

    def __init__(self):

        self.governance_engine = GovernanceEngine()
        self.decision_engine = DecisionEngine()

    def analyze_prompt(self, prompt: str):

        analysis = self.governance_engine.analyze(prompt)

        decision = self.decision_engine.evaluate(analysis)

        return decision