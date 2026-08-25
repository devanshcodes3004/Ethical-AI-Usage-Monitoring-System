from llms.gemini_client import GeminiClient
from llms.ollama_client import OllamaClient

import sys

from exception import CustomException


class Router:
    """
    Responsible for selecting the appropriate LLM.
    """

    def __init__(self):

        self.models = {
            "gemini": GeminiClient(),
            "ollama": OllamaClient(),
        }

    def get_model(self, provider: str):

        provider = provider.lower()

        if provider not in self.models:
            raise CustomException(
                f"'{provider}' is not a supported provider.",
                sys
            )

        return self.models[provider]