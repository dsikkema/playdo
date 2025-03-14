"""
Tests for the Flask API endpoints.
"""

import pytest
from typing import Generator, Optional
import json
from unittest.mock import patch, MagicMock
from flask.testing import FlaskClient

from playdo.playdo_app import PlaydoApp
from playdo.models import PlaydoMessage, PlaydoContent


@pytest.fixture
def mock_response_getter() -> Generator[MagicMock, None, None]:
    """Mock the ResponseGetter to avoid calling the Anthropic API during tests."""
    with patch("playdo.response_getter.ResponseGetter._get_next_assistant_resp") as mock_method:
        mock_method.return_value = PlaydoMessage(
            role="assistant",
            content=[PlaydoContent(type="text", text="Hi there! How can I help you today?")],
            editor_code=None,
            stdout=None,
            stderr=None,
        )
        yield mock_method


def test_list_conversations_empty(authorized_client: FlaskClient) -> None:
    """Test listing conversations when there are none."""
    response = authorized_client.get("/api/conversations")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "conversation_ids" in data
    assert len(data["conversation_ids"]) == 0


def test_create_conversation(authorized_client: FlaskClient) -> None:
    """Test creating a new conversation."""
    response = authorized_client.post("/api/conversations")
    assert response.status_code == 201
    data = json.loads(response.data)
    assert "id" in data
    assert "messages" in data
    assert len(data["messages"]) == 0


def test_get_conversation(authorized_client: FlaskClient) -> None:
    """Test retrieving a conversation."""
    # First create a conversation
    create_response = authorized_client.post("/api/conversations")
    assert create_response.status_code == 201
    create_data = json.loads(create_response.data)
    conversation_id = create_data["id"]

    # Then retrieve it
    get_response = authorized_client.get(f"/api/conversations/{conversation_id}")
    assert get_response.status_code == 200
    get_data = json.loads(get_response.data)
    assert get_data["id"] == conversation_id
    assert len(get_data["messages"]) == 0


def test_get_nonexistent_conversation(authorized_client: FlaskClient) -> None:
    """Test retrieving a conversation that doesn't exist."""
    response = authorized_client.get("/api/conversations/999")
    assert response.status_code == 404
    data = json.loads(response.data)
    assert "error" in data


def test_send_message(authorized_client: FlaskClient, mock_response_getter: MagicMock) -> None:
    """Test adding a message to a conversation."""
    # First create a conversation
    create_conv_resp = authorized_client.post("/api/conversations")
    create_conv_data = json.loads(create_conv_resp.data)
    conversation_id = create_conv_data["id"]

    # Then add a message
    conversation_response = authorized_client.post(
        f"/api/conversations/{conversation_id}/send_message", json={"message": "Hello"}, content_type="application/json"
    )
    assert conversation_response.status_code == 200
    conversation_data = json.loads(conversation_response.data)
    assert "messages" in conversation_data
    assert "id" in conversation_data
    assert len(conversation_data["messages"]) == 2
    assert conversation_data["messages"][0]["role"] == "user"
    assert conversation_data["messages"][1]["role"] == "assistant"


def test_add_message_invalid_json(authorized_client: FlaskClient) -> None:
    """Test adding a message with invalid JSON."""
    # First create a conversation
    create_response = authorized_client.post("/api/conversations")
    create_data = json.loads(create_response.data)
    conversation_id = create_data["id"]

    # Then try to add a message with invalid JSON
    message_response = authorized_client.post(
        f"/api/conversations/{conversation_id}/send_message", data="not json", content_type="text/plain"
    )
    assert message_response.status_code == 400
    message_data = json.loads(message_response.data)
    assert "error" in message_data


def test_add_message_missing_field(authorized_client: FlaskClient) -> None:
    """Test adding a message with missing field."""
    # First create a conversation
    create_response = authorized_client.post("/api/conversations")
    create_data = json.loads(create_response.data)
    conversation_id = create_data["id"]

    # Then try to add a message with missing field
    message_response = authorized_client.post(
        f"/api/conversations/{conversation_id}/send_message", json={"not_message": "Hello"}, content_type="application/json"
    )
    assert message_response.status_code == 400
    message_data = json.loads(message_response.data)
    assert "error" in message_data


def test_add_message_nonexistent_conversation(authorized_client: FlaskClient) -> None:
    """Test adding a message to a conversation that doesn't exist."""
    message_response = authorized_client.post(
        "/api/conversations/999/send_message", json={"message": "Hello"}, content_type="application/json"
    )
    assert message_response.status_code == 404
    message_data = json.loads(message_response.data)
    assert "error" in message_data


def test_list_conversations_after_creating(authorized_client: FlaskClient) -> None:
    """Test listing conversations after creating some."""
    # Create a few conversations
    authorized_client.post("/api/conversations")
    authorized_client.post("/api/conversations")
    authorized_client.post("/api/conversations")

    # Then list them
    response = authorized_client.get("/api/conversations")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "conversation_ids" in data
    assert len(data["conversation_ids"]) == 3


def test_send_message_with_code_context(authorized_client: FlaskClient, mock_response_getter: MagicMock) -> None:
    """Test adding a message with code context to a conversation."""
    # First create a conversation
    create_conv_resp = authorized_client.post("/api/conversations")
    create_conv_data = json.loads(create_conv_resp.data)
    conversation_id = create_conv_data["id"]

    # Then add a message with code context
    message_data = {
        "message": "Can you explain this code?",
        "editor_code": "print('Hello, world!')",
        "stdout": "Hello, world!",
        "stderr": "",
    }

    conversation_response = authorized_client.post(
        f"/api/conversations/{conversation_id}/send_message", json=message_data, content_type="application/json"
    )

    assert conversation_response.status_code == 200
    conversation_data = json.loads(conversation_response.data)

    assert "messages" in conversation_data
    assert "id" in conversation_data
    assert len(conversation_data["messages"]) == 2

    # Check user message has code context
    user_message = conversation_data["messages"][0]
    assert user_message["role"] == "user"
    assert user_message["editor_code"] == "print('Hello, world!')"
    assert user_message["stdout"] == "Hello, world!"
    assert user_message["stderr"] == ""

    # Check assistant message
    assert conversation_data["messages"][1]["role"] == "assistant"


def test_send_message_with_code_no_output(authorized_client: FlaskClient, mock_response_getter: MagicMock) -> None:
    """
    This case is valid
    """
    # Create a conversation first
    response = authorized_client.post("/api/conversations", json={"name": "Test conversation"})
    assert response.status_code == 201
    conversation_id = response.get_json()["id"]

    # Set up the mock response
    mock_response = {"message": "I'm the assistant response"}
    mock_response_getter.get_response.return_value = mock_response

    # Send message with code but no output (valid case)
    message_data = {"message": "Help me with this code", "editor_code": "print('Hello world')", "stdout": None, "stderr": None}

    response = authorized_client.post(f"/api/conversations/{conversation_id}/send_message", json=message_data)
    assert response.status_code == 200

    # Verify the response contains the expected data
    conversation_data = response.get_json()
    assert "id" in conversation_data
    assert "messages" in conversation_data
    assert len(conversation_data["messages"]) == 2

    # Check user message
    user_message = conversation_data["messages"][0]
    assert user_message["role"] == "user"
    assert user_message["editor_code"] == "print('Hello world')"
    assert user_message["stdout"] is None
    assert user_message["stderr"] is None

    # Check assistant message
    assert conversation_data["messages"][1]["role"] == "assistant"


@pytest.mark.parametrize(
    "stdout, stderr",
    [
        (None, "errors!"),
        ("outputs!", None),
    ],
)
def test_send_message_bothneither_outerr(
    authorized_client: FlaskClient, mock_response_getter: MagicMock, stdout: Optional[str], stderr: Optional[str]
) -> None:
    """
    Even when code is provided, both or neither of stdout and stderr must be provided. If one and not the other, expect an error.
    """
    # Create a conversation first
    response = authorized_client.post("/api/conversations", json={"name": "Test conversation"})
    assert response.status_code == 201
    conversation_id = response.get_json()["id"]

    # Send message with mismatched stdout/stderr (should fail)
    message_data = {
        "message": "Help me with this code",
        "editor_code": "print('Hello world')",
        "stdout": stdout,
        "stderr": stderr,
    }

    response = authorized_client.post(f"/api/conversations/{conversation_id}/send_message", json=message_data)
    assert response.status_code == 400

    # Verify the error message
    error_data = response.get_json()
    assert "error" in error_data
    assert error_data["error"] == "Must provide both stdout and stderr if code has been run, or neither if code has not been run"


def test_send_message_output_with_no_code(authorized_client: FlaskClient, mock_response_getter: MagicMock) -> None:
    """
    If code has not been run (editor_code is null), stdout and stderr must both be null.
    """
    # Create a conversation first
    response = authorized_client.post("/api/conversations", json={"name": "Test conversation"})
    assert response.status_code == 201
    conversation_id = response.get_json()["id"]

    # Send message with no code but with output (should fail)
    message_data = {"message": "Help me with this code", "editor_code": None, "stdout": "Some output", "stderr": ""}

    response = authorized_client.post(f"/api/conversations/{conversation_id}/send_message", json=message_data)
    assert response.status_code == 400

    # Verify the error message
    error_data = response.get_json()
    assert "error" in error_data
    assert error_data["error"] == "Cannot provide stdout or stderr if editor_code is null"


def test_login_successful(authorized_client: FlaskClient, test_user: dict) -> None:
    """Test successful login."""
    response = authorized_client.post(
        "/api/login", json={"username": test_user["username"], "password": test_user["password"]}, content_type="application/json"
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "access_token" in data
    assert isinstance(data["access_token"], str)
    assert len(data["access_token"]) > 0


def test_login_invalid_credentials(authorized_client: FlaskClient, test_user: dict) -> None:
    """Test login with invalid credentials."""
    response = authorized_client.post(
        "/api/login", json={"username": test_user["username"], "password": "wrongpassword"}, content_type="application/json"
    )
    assert response.status_code == 401
    data = json.loads(response.data)
    assert "error" in data
    assert data["error"] == "Invalid credentials"


def test_login_missing_fields(authorized_client: FlaskClient, test_user: dict) -> None:
    """Test login with missing fields."""
    response = authorized_client.post("/api/login", json={"username": "someuser"}, content_type="application/json")
    assert response.status_code == 400
    data = json.loads(response.data)
    assert "error" in data
    assert data["error"] == "Missing username or password"


def test_unauthorized_access(test_app: PlaydoApp) -> None:
    """
    Test accessing a protected endpoint without authentication.
    """

    # request should 401 because it's not the authorized_client fixture making it, but a client which hasn't been wired up with an auth header
    response = test_app.test_client().get("/api/conversations")
    assert response.status_code == 401


def test_access_invalid_authorization(test_app: PlaydoApp) -> None:
    """Test accessing a protected endpoint with an invalid authorization header."""
    response = test_app.test_client().get("/api/conversations", headers={"Authorization": "Bearer invalidtoken"})
    assert response.status_code == 422
