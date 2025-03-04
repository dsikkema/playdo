"""
Take settings from environment variables and expose them as a settings object.
"""

import os
from pathlib import Path


_PLAYDO_DATABASE_PATH_KEY = "PLAYDO_DATABASE_PATH"
_PLAYDO_DEBUG_KEY = "PLAYDO_DEBUG"
_PLAYDO_TESTING_KEY = "PLAYDO_TESTING"
_PLAYDO_ANTHROPIC_MODEL_KEY = "PLAYDO_ANTHROPIC_MODEL"


def _get_required_envvar(key: str) -> str:
    env_var = os.getenv(key)
    assert env_var is not None, f"{key} is not set"
    return env_var


class Settings:
    """May be overridden on app creation by passed in arguments"""

    DATABASE_PATH = _get_required_envvar(_PLAYDO_DATABASE_PATH_KEY)
    assert Path(DATABASE_PATH).exists(), f"Database file {DATABASE_PATH} does not exist"

    BACKEND_BASE_DIR = Path(__file__).parent.parent
    DEBUG = _get_required_envvar(_PLAYDO_DEBUG_KEY).lower() == "true"
    TESTING = _get_required_envvar(_PLAYDO_TESTING_KEY).lower() == "true"
    ANTHROPIC_MODEL = _get_required_envvar(_PLAYDO_ANTHROPIC_MODEL_KEY)


settings = Settings()
