from collections.abc import Generator
import logging
from pathlib import Path

import pytest
import sqlite3

from playdo.playdo_app import PlaydoApp
from playdo.settings import settings
from playdo.app import create_app
from playdo.user_repository import UserRepository
from flask.testing import FlaskClient
from flask_jwt_extended import create_access_token


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
    repo = UserRepository(initialized_test_db_path)
    username = "testuser"
    email = "test@example.com"
    password = "password12345"
    password_hash, password_salt = repo.hash_password(password)
    
    user = repo.create_user(
        username=username,
        email=email,
        password_hash=password_hash,
        password_salt=password_salt,
        is_admin=False
    )
    
    return {
        "id": user.id,
        "username": username,
        "email": email,
        "password": password
    }


@pytest.fixture
def auth_client(test_app: PlaydoApp, test_user: dict) -> FlaskClient:
    """A test client with JWT authentication."""
    with test_app.app_context():
        # Create an access token for the test user
        access_token = create_access_token(
            identity=test_user["id"],
            additional_claims={
                "username": test_user["username"],
                "email": test_user["email"],
                "is_admin": False
            }
        )
    
    client = test_app.test_client()
    # Set the Authorization header for all requests
    client.environ_base = {
        "HTTP_AUTHORIZATION": f"Bearer {access_token}"
    }
    return client
