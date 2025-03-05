"""
Tests for the Flask API endpoints.
"""

import pytest
from typing import Generator
import json
from unittest.mock import patch, MagicMock
from flask.testing import FlaskClient

from playdo.playdo_app import PlaydoApp
from playdo.models import PlaydoMessage, PlaydoContent


@pytest.fixture
def client(test_app: PlaydoApp) -> FlaskClient:
    """A test client for the app."""
    return test_app.test_client()


@pytest.fixture
def mock_response_getter() -> Generator[MagicMock, None, None]:
    """Mock the ResponseGetter to avoid calling the Anthropic API during tests."""
    with patch("playdo.response_getter.ResponseGetter._get_next_assistant_resp") as mock_method:
        mock_method.return_value = [
            PlaydoMessage(role="user", content=[PlaydoContent(type="text", text="Hello")]),
            PlaydoMessage(role="assistant", content=[PlaydoContent(type="text", text="Hi there! How can I help you today?")]),
        ]
        yield mock_method


def test_list_conversations_empty(client: FlaskClient) -> None:
    """Test listing conversations when there are none."""
    response = client.get("/api/conversations")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "conversation_ids" in data
    assert len(data["conversation_ids"]) == 0


def test_create_conversation(client: FlaskClient) -> None:
    """Test creating a new conversation."""
    response = client.post("/api/conversations")
    assert response.status_code == 201
    data = json.loads(response.data)
    assert "id" in data
    assert "messages" in data
    assert len(data["messages"]) == 0


def test_get_conversation(client: FlaskClient) -> None:
    """Test retrieving a conversation."""
    # First create a conversation
    create_response = client.post("/api/conversations")
    create_data = json.loads(create_response.data)
    conversation_id = create_data["id"]

    # Then retrieve it
    get_response = client.get(f"/api/conversations/{conversation_id}")
    assert get_response.status_code == 200
    get_data = json.loads(get_response.data)
    assert get_data["id"] == conversation_id
    assert len(get_data["messages"]) == 0


def test_get_nonexistent_conversation(client: FlaskClient) -> None:
    """Test retrieving a conversation that doesn't exist."""
    response = client.get("/api/conversations/999")
    assert response.status_code == 404
    data = json.loads(response.data)
    assert "error" in data


def test_send_message(client: FlaskClient, mock_response_getter: MagicMock) -> None:
    """Test adding a message to a conversation."""
    # First create a conversation
    create_conv_resp = client.post("/api/conversations")
    create_conv_data = json.loads(create_conv_resp.data)
    conversation_id = create_conv_data["id"]

    # Then add a message
    conversation_response = client.post(
        f"/api/conversations/{conversation_id}/send_message", json={"message": "Hello"}, content_type="application/json"
    )
    assert conversation_response.status_code == 200
    conversation_data = json.loads(conversation_response.data)
    assert "messages" in conversation_data
    assert "id" in conversation_data
    assert len(conversation_data["messages"]) == 2
    assert conversation_data["messages"][0]["role"] == "user"
    assert conversation_data["messages"][1]["role"] == "assistant"


def test_add_message_invalid_json(client: FlaskClient) -> None:
    """Test adding a message with invalid JSON."""
    # First create a conversation
    create_response = client.post("/api/conversations")
    create_data = json.loads(create_response.data)
    conversation_id = create_data["id"]

    # Then try to add a message with invalid JSON
    message_response = client.post(
        f"/api/conversations/{conversation_id}/send_message", data="not json", content_type="text/plain"
    )
    assert message_response.status_code == 400
    message_data = json.loads(message_response.data)
    assert "error" in message_data


def test_add_message_missing_field(client: FlaskClient) -> None:
    """Test adding a message with missing field."""
    # First create a conversation
    create_response = client.post("/api/conversations")
    create_data = json.loads(create_response.data)
    conversation_id = create_data["id"]

    # Then try to add a message with missing field
    message_response = client.post(
        f"/api/conversations/{conversation_id}/send_message", json={"not_message": "Hello"}, content_type="application/json"
    )
    assert message_response.status_code == 400
    message_data = json.loads(message_response.data)
    assert "error" in message_data


def test_add_message_nonexistent_conversation(client: FlaskClient) -> None:
    """Test adding a message to a conversation that doesn't exist."""
    message_response = client.post(
        "/api/conversations/999/send_message", json={"message": "Hello"}, content_type="application/json"
    )
    assert message_response.status_code == 404
    message_data = json.loads(message_response.data)
    assert "error" in message_data


def test_list_conversations_after_creating(client: FlaskClient) -> None:
    """Test listing conversations after creating some."""
    # Create a few conversations
    client.post("/api/conversations")
    client.post("/api/conversations")
    client.post("/api/conversations")

    # Then list them
    response = client.get("/api/conversations")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "conversation_ids" in data
    assert len(data["conversation_ids"]) == 3
