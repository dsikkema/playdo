"""
Tests for the Pydantic models in playdo/models.py, focusing on validation rules.
"""

import datetime
import pytest
from pydantic import ValidationError

from playdo.models import PlaydoContent, PlaydoMessage, ConversationHistory, User


#
# Tests for valid model creation
#


def test_valid_playdo_content_creation():
    """Test creating a valid PlaydoContent with no exceptions."""
    # Test successful creation without raising exceptions
    _ = PlaydoContent(type="text", text="Hello, world!")
    # No assertions needed - we're verifying it doesn't throw an exception


def test_valid_playdo_message_creation():
    """Test creating a valid PlaydoMessage with no exceptions."""
    content = PlaydoContent(type="text", text="Hello, world!")
    _ = PlaydoMessage(role="user", content=[content])
    # No assertions needed - we're verifying it doesn't throw an exception


def test_playdo_message_with_code_context():
    """Test creating a PlaydoMessage with editor code and outputs."""
    content = PlaydoContent(type="text", text="Check my code")
    _ = PlaydoMessage(role="user", content=[content], editor_code="print('Hello, world!')", stdout="Hello, world!\n", stderr="")
    # No assertions needed - we're verifying it doesn't throw an exception


def test_valid_conversation_history_creation():
    """Test creating a valid ConversationHistory with no exceptions."""
    content = PlaydoContent(type="text", text="Hello")
    message = PlaydoMessage(role="user", content=[content])
    _ = ConversationHistory(messages=[message], id=1, created_at=datetime.datetime.now(), updated_at=datetime.datetime.now())
    # No assertions needed - we're verifying it doesn't throw an exception


def test_valid_user_creation():
    """Test creating a valid User with no exceptions."""
    _ = User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="hash_value",
        password_salt="salt_value",
        is_admin=False,
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
    )
    # No assertions needed - we're verifying it doesn't throw an exception


#
# Tests for PlaydoContent validation
#


def test_playdo_content_type_validation():
    """Test that PlaydoContent type must be 'text'."""
    with pytest.raises(ValidationError) as exc_info:
        PlaydoContent(type="invalid", text="Hello")

    # Check the specific error message
    error_details = exc_info.value.errors()
    assert any("Input should be 'text'" in str(err["msg"]) for err in error_details)


def test_playdo_content_text_required():
    """Test that PlaydoContent text field is required."""
    with pytest.raises(ValidationError):
        PlaydoContent(type="text")


#
# Tests for PlaydoMessage validation
#


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


#
# Tests for ConversationHistory validation
#


def test_conversation_history_id_required():
    """Test that ConversationHistory id is required."""
    content = PlaydoContent(type="text", text="Hello")
    message = PlaydoMessage(role="user", content=[content])

    with pytest.raises(ValidationError):
        ConversationHistory(messages=[message])


def test_conversation_history_messages_required():
    """Test that ConversationHistory messages are required."""
    with pytest.raises(ValidationError):
        ConversationHistory(id=1)


#
# Tests for User validation
#


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
