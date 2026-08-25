import logging
import os
from datetime import datetime


class AuditLogger:
    """
    Handles logging for the AI Governance System.
    """

    def __init__(
        self,
        log_dir: str = "logs",
        log_file: str = "audit.log"
    ):

        os.makedirs(log_dir, exist_ok=True)

        self.log_path = os.path.join(log_dir, log_file)

        self.logger = logging.getLogger("AuditLogger")
        self.logger.setLevel(logging.INFO)

        # Prevent duplicate handlers
        if not self.logger.handlers:

            file_handler = logging.FileHandler(self.log_path)

            formatter = logging.Formatter(
                "%(asctime)s | %(levelname)s | %(message)s"
            )

            file_handler.setFormatter(formatter)

            self.logger.addHandler(file_handler)

    def log_interaction(
        self,
        provider: str,
        model: str,
        prompt: str,
        response: str,
        status: str,
        latency: float = None
    ):

        message = (
            f"Provider={provider} | "
            f"Model={model} | "
            f"Status={status} | "
            f"Latency={latency}s | "
            f"Prompt={prompt} | "
            f"Response={response}"
        )

        self.logger.info(message)

    def log_error(
        self,
        provider: str,
        model: str,
        error: str
    ):

        message = (
            f"Provider={provider} | "
            f"Model={model} | "
            f"ERROR={error}"
        )

        self.logger.error(message) 