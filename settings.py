import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

REQUIRED_KEYS = [
    "ANTHROPIC_API_KEY",
    "GOOGLE_API_KEY",
    "GITHUB_WEBHOOK_SECRET",
    "GITHUB_PAT",
    "OLLAMA_BASE_URL",
    "CHROMADB_PATH",
]

def validate_settings():
    """
    Validates that all required environment variables are present.
    Raises ValueError if any are missing.
    """
    missing_keys = [key for key in REQUIRED_KEYS if not os.getenv(key)]
    if missing_keys:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing_keys)}. "
            f"Please ensure they are set in your .env file or environment."
        )

# Validate at startup
try:
    validate_settings()
except ValueError as e:
    # If being imported, we might want to handle this differently, 
    # but for now we follow the requirement to raise a clear ValueError.
    raise e

# Configuration variables
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET")
GITHUB_PAT = os.getenv("GITHUB_PAT")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL")
CHROMADB_PATH = os.getenv("CHROMADB_PATH")
