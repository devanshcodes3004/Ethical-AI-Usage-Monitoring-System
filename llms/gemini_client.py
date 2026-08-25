"""
gemini_client.py

Provides a wrapper around Google's Gemini model.
"""

import sys

from langchain_google_genai import ChatGoogleGenerativeAI

from config import GOOGLE_API_KEY
from exception import CustomException


class GeminiClient:

    def __init__(self):

        self.model = "gemini-3-flash-preview"

        self.llm = ChatGoogleGenerativeAI(
            model=self.model,
            google_api_key=GOOGLE_API_KEY,
            temperature=0.7
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
                "provider": "Gemini",
                "model": self.model,
                "response": text.strip()
            }

        except Exception as e:

            raise CustomException(e, sys)