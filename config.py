"""
config.py

Contains all configuration variables used throughout the project.
"""

import os

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# ==========================
# API KEYS
# ==========================

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


# ==========================
# LLM CONFIGURATION
# ==========================

GEMINI_MODEL = "gemini-3-flash-preview"

OLLAMA_MODEL = "llama3.2:latest"

OLLAMA_BASE_URL = "http://localhost:11434"


# ==========================
# GOVERNANCE CONFIGURATION
# ==========================

DEFAULT_TEMPERATURE = 0

MAX_RISK_SCORE = 100

CONFIDENCE_THRESHOLD = 0.75


# ==========================
# LOGGING
# ==========================

LOG_DIRECTORY = "logs"

LOG_FILE = "audit.log"


# ==========================
# DATABASE
# ==========================

# ==========================
# MONGODB
# ==========================

MONGO_URI = "mongodb://127.0.0.1:27017"

DATABASE_NAME = "ethical_ai_monitoring"