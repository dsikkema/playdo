"""
TOODO: blanket error handlers to prevent exception leakage
"""

import logging
import os
from typing import Optional
from datetime import timedelta

from flask_jwt_extended import JWTManager

from playdo.playdo_app import PlaydoApp
from playdo.settings import settings
from playdo.endpoints.conversations import conversations_bp
from playdo.endpoints.auth import auth_bp


def create_app(database_path: Optional[str] = None, testing: bool = False) -> PlaydoApp:
    """Create and configure the Flask application."""
    app = PlaydoApp(__name__)

    if database_path is not None:
        settings.DATABASE_PATH = database_path

    if testing:
        settings.TESTING = True

    # Configure JWT authentication
    app.config["JWT_SECRET_KEY"] = settings.JWT_SECRET_KEY
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=24)  # Token expiry time
    jwt = JWTManager(app)

    # do not allow API calls during automated tests
    anthropic_api_key_key = "ANTHROPIC_API_KEY"
    if not settings.TESTING:
        assert os.getenv(anthropic_api_key_key) is not None, f"{anthropic_api_key_key} is not set"
    else:
        os.environ[anthropic_api_key_key] = "test-api-key"

    # Register blueprints
    app.register_blueprint(conversations_bp, url_prefix="/api")
    app.register_blueprint(auth_bp, url_prefix="/api")

    return app


app = create_app()


def _configure_logging():
    logger = logging.getLogger("playdo")
    level = logging.DEBUG if settings.DEBUG else logging.INFO
    logger.setLevel(level)
    handler = logging.StreamHandler()
    handler.setLevel(level)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def main():
    _configure_logging()
    app.run(debug=settings.DEBUG, host="0.0.0.0")


if __name__ == "__main__":
    main()
