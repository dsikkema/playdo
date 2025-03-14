"""
Take settings from environment variables and expose them as a settings object.
"""

import os
from pathlib import Path


_PLAYDO_DATABASE_PATH_KEY = "PLAYDO_DATABASE_PATH"
_PLAYDO_DEBUG_KEY = "PLAYDO_DEBUG"
_PLAYDO_TESTING_KEY = "PLAYDO_TESTING"
_PLAYDO_ANTHROPIC_MODEL_KEY = "PLAYDO_ANTHROPIC_MODEL"
_PLAYDO_JWT_SECRET_KEY = "PLAYDO_JWT_SECRET_KEY"


def _get_required_envvar(key: str) -> str:
    env_var = os.getenv(key)
    assert env_var is not None, f"{key} is not set"
    return env_var


class Settings:
    """
    Settings object.

    Note: it's tricky to be too clever about conditionally required settings. E.g. env vars
    being "required, except for tests". It's also tricky to try to set env vars in tests
    before the settings object is created (the test imports the settings module before running code to
    set vars that are needed to initialize the settings module).

    Our approach is therefore pretty heavy-handed: just require all env vars all the time.

    Some MAY be reset based on custom settings passed into the create_app function for testing
    purposes, but you still have to provide all env vars all the time even in tests, even if
    they're going to be overridden.

    Just embrace, accept, export PLAYDO_ANTHROPIC_MODEL=whatever, and that's the end of it.
    """

    # May be overridden on app creation by passed in arguments
    DATABASE_PATH = _get_required_envvar(_PLAYDO_DATABASE_PATH_KEY)
    assert Path(DATABASE_PATH).exists(), f"Database file {DATABASE_PATH} does not exist"

    DEBUG = _get_required_envvar(_PLAYDO_DEBUG_KEY).lower() == "true"
    TESTING = _get_required_envvar(_PLAYDO_TESTING_KEY).lower() == "true"
    ANTHROPIC_MODEL = _get_required_envvar(_PLAYDO_ANTHROPIC_MODEL_KEY)

    # JWT settings - use a default in development, but should be overridden in production
    JWT_SECRET_KEY = _get_required_envvar(_PLAYDO_JWT_SECRET_KEY)

    BACKEND_BASE_DIR = Path(__file__).parent.parent
    LOGS_DIR = BACKEND_BASE_DIR / "logs"
    LOGS_DIR.mkdir(exist_ok=True)

    BACKUPS_DIR = BACKEND_BASE_DIR / "backups"
    BACKUPS_DIR.mkdir(exist_ok=True)

    # this will be needed later so might as well just assert it now (just set it to "whatever" for tests
    # if needed)
    assert os.getenv("ANTHROPIC_API_KEY") is not None, "ANTHROPIC_API_KEY is not set"


settings = Settings()
