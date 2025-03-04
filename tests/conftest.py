from collections.abc import Generator
import logging
from pathlib import Path

import pytest
import sqlite3

from playdo.playdo_app import PlaydoApp
from playdo.settings import settings
from playdo.app import create_app


def pytest_configure() -> None:
    logger = logging.getLogger("playdo")
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    logger.debug("pytest configured")


@pytest.fixture
def test_app(initialized_test_db_path: Path) -> Generator[PlaydoApp, None, None]:
    """
    Create and configure a Flask app for testing using built-in fixture for temp files.
    """
    app = create_app(database_path=str(initialized_test_db_path), testing=True)

    yield app


@pytest.fixture
def initialized_test_db_path(tmp_path: Path) -> Path:
    """Create a temporary database file for testing."""
    db_path = tmp_path / "test.db"
    with open(settings.BACKEND_BASE_DIR / "schema.sql", "r") as f:
        schema = f.read()
    with sqlite3.connect(str(db_path)) as conn:
        conn.executescript(schema)
    return db_path
