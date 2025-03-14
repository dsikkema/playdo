from collections.abc import Generator
import logging
from pathlib import Path

import pytest
import sqlite3

from playdo.playdo_app import PlaydoApp
from playdo.settings import settings
from playdo.app import create_app
from playdo.svc.user_service import user_service
from flask.testing import FlaskClient


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


@pytest.fixture
def test_user(initialized_test_db_path: Path) -> dict:
    """Create a test user and return their credentials."""
    # Create a test user
    with user_service(initialized_test_db_path) as user_svc:
        username = "testuser"
        email = "test@example.com"
        password = "password12345"
        user = user_svc.create_user(username, email, False, password)

    return {"id": user.id, "username": username, "email": email, "password": password}


@pytest.fixture
def authorized_client(test_app: PlaydoApp, test_user: dict) -> FlaskClient:
    """A test client with JWT authentication."""
    test_client = test_app.test_client()
    login_resp = test_client.post("/api/login", json={"username": test_user["username"], "password": test_user["password"]})
    assert login_resp.status_code == 200
    assert login_resp.is_json
    data = login_resp.get_json()
    assert data
    assert "access_token" in data
    assert data["access_token"] is not None
    test_client.environ_base["HTTP_AUTHORIZATION"] = f"Bearer {data['access_token']}"
    return test_client
