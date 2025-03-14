"""
Tests for the Pydantic models in playdo/models.py, focusing on validation rules.
"""

import pytest
from pydantic import ValidationError

from playdo.models import PlaydoContent, PlaydoMessage, User


def test_playdo_message_role_validation():
    """Test that PlaydoMessage role must be 'user' or 'assistant'."""
    content = PlaydoContent(type="text", text="Hello")

    with pytest.raises(ValidationError) as exc_info:
        PlaydoMessage(role="invalid", content=[content])

    # Check the specific error message
    error_details = exc_info.value.errors()
    assert any("Input should be 'user' or 'assistant'" in str(err["msg"]) for err in error_details)


def test_playdo_message_content_required():
    """Test that PlaydoMessage content is required and must be a list."""
    with pytest.raises(ValidationError):
        PlaydoMessage(role="user")

    with pytest.raises(ValidationError):
        # Content should be a list, not a single item
        content = PlaydoContent(type="text", text="Hello")
        PlaydoMessage(role="user", content=content)


def test_user_username_length_validation():
    """Test that username must be at least 4 characters."""
    with pytest.raises(ValidationError) as exc_info:
        User(
            username="abc",  # Too short
            email="test@example.com",
            password_hash="hash_value",
            password_salt="salt_value",
        )

    # Verify the error message is about username length
    error_details = exc_info.value.errors()
    assert any("Username must be at least 4 characters" in str(err["msg"]) for err in error_details)


def test_user_username_character_validation():
    """Test that username may only contain alphanumeric characters and underscores."""
    with pytest.raises(ValidationError) as exc_info:
        User(
            username="test-user",  # Contains invalid character '-'
            email="test@example.com",
            password_hash="hash_value",
            password_salt="salt_value",
        )

    # Verify the error message is about username characters
    error_details = exc_info.value.errors()
    assert any("Username may contain only alphanumeric characters and underscores" in str(err["msg"]) for err in error_details)


def test_user_email_validation():
    """Test that user email must be a valid email format."""
    with pytest.raises(ValidationError):
        User(
            username="testuser",
            email="invalid-email",  # Invalid email format
            password_hash="hash_value",
            password_salt="salt_value",
        )


def test_user_required_fields():
    """Test that required User fields cannot be omitted."""
    # Username is required
    with pytest.raises(ValidationError):
        User(email="test@example.com", password_hash="hash", password_salt="salt")

    # Email is required
    with pytest.raises(ValidationError):
        User(username="testuser", password_hash="hash", password_salt="salt")

    # Password hash is required
    with pytest.raises(ValidationError):
        User(username="testuser", email="test@example.com", password_salt="salt")

    # Password salt is required
    with pytest.raises(ValidationError):
        User(username="testuser", email="test@example.com", password_hash="hash")
