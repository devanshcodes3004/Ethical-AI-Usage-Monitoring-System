"""
governance_engine.py

Implements the AI Governance Engine responsible for analyzing
user prompts before they are processed by a Large Language Model.

The governance engine uses:
- LangChain
- Ollama
- Pydantic Structured Output
"""

from langchain_ollama import ChatOllama

from config import OLLAMA_MODEL
from governance.prompts import get_governance_prompt
from governance.schemas import GovernanceDecision
from exception import CustomException

import sys

class GovernanceEngine:
    """
    AI Governance Engine.

    This class analyzes every user prompt and returns
    a validated GovernanceDecision object.
    """

    def __init__(self):

        self.model = ChatOllama(
            model=OLLAMA_MODEL,
            temperature=0,
        )

        self.structured_llm = self.model.with_structured_output(
            GovernanceDecision
        )

        self.prompt = get_governance_prompt()

        self.chain = self.prompt | self.structured_llm

    def analyze(self, user_prompt: str) -> GovernanceDecision:
        """
        Analyze a user prompt and return a structured
        governance decision.

        Args:
            user_prompt (str):
                Prompt submitted by the user.

        Returns:
            GovernanceDecision:
                Structured governance analysis.
        """

        try:

            result = self.chain.invoke(
                {
                    "user_prompt": user_prompt
                }
            )

            return result

        except Exception as e:
            raise CustomException(e,sys)