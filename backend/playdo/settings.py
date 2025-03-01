"""
Take settings from environment variables and expose them as a settings object.
"""

import os
from pathlib import Path


class Settings:
    """May be overridden on app creation by passed in arguments"""

    DATABASE_PATH = os.getenv("PLAYDO_DATABASE_PATH")
    BACKEND_BASE_DIR = Path(__file__).parent.parent
    DEBUG = os.getenv("PLAYDO_DEBUG").lower() == "true"
    TESTING = False
    ANTHROPIC_MODEL = os.getenv("PLAYDO_ANTHROPIC_MODEL")


settings = Settings()
