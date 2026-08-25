"""
ollama_client.py

Provides a wrapper around Ollama models.
"""

import sys

from langchain_ollama import ChatOllama

from exception import CustomException


class OllamaClient:

    def __init__(
        self,
        model: str = "llama3.2:latest",
        temperature: float = 0.7
    ):

        self.model = model
        self.temperature = temperature

        self.llm = ChatOllama(
            model=self.model,
            temperature=self.temperature
        )

    def invoke(self, messages) -> dict:

        try:

            response = self.llm.invoke(messages)

            content = response.content

            if isinstance(content, list):

                text = ""

                for item in content:

                    if isinstance(item, dict):

                        text += item.get("text", "")

                    else:

                        text += str(item)

            else:

                text = str(content)

            return {
                "success": True,
                "provider": "Ollama",
                "model": self.model,
                "response": text.strip()
            }

        except Exception as e:

            raise CustomException(e, sys)