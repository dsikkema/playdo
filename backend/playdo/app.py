from pathlib import Path
from typing import Optional

from playdo.playdo_app import PlaydoApp
from playdo.settings import settings
from playdo.endpoints.conversations import conversations_bp


def create_app(database_path: Optional[Path] = None, testing: bool = False) -> PlaydoApp:
    """Create and configure the Flask application."""
    app = PlaydoApp(__name__)

    if database_path is not None:
        settings.DATABASE_PATH = database_path

    if testing:
        settings.TESTING = True

    # Register blueprints
    app.register_blueprint(conversations_bp, url_prefix="/api")

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=settings.DEBUG)
