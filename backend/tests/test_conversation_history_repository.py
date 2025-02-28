import sqlite3
from time import sleep
from pathlib import Path
from typing import Generator

import pytest
from playdo.conversation_history_repository import conversation_history_manager, ConversationHistoryRepository
from playdo.models import PlaydoMessage, PlaydoContent
from unittest.mock import MagicMock, patch


@pytest.fixture
def initialized_db(tmp_path: Path) -> str:
    """Create a temporary database file for testing."""
    db_path = str(tmp_path / "test.db")
    with open("schema.sql", "r") as f:
        schema = f.read()
    with sqlite3.connect(db_path) as conn:
        conn.executescript(schema)
    return db_path


@pytest.fixture
def repository(initialized_db: str) -> Generator[ConversationHistoryRepository, None, None]:
    """Create a test repository instance."""
    with conversation_history_manager(initialized_db) as repo:
        yield repo


def test_save_new_empty_conversation(repository: ConversationHistoryRepository) -> None:
    """Test creating a new conversation with no messages."""
    conversation = repository.create_new_conversation()
    assert conversation.id is not None
    assert conversation.messages == []


def test_add_messages_to_new_conversation(repository: ConversationHistoryRepository) -> None:
    """
    Test adding messages to a new conversation: first when it's empty, then when it's initialized with messages.
    """
    conversation = repository.create_new_conversation()
    first_new_messages = [
        PlaydoMessage.user_message("Hello, world!"),
        PlaydoMessage(role="assistant", content=[PlaydoContent(type="text", text="Hello, world!")]),
    ]
    conversation = repository.add_messages_to_conversation(conversation.id, first_new_messages)
    assert conversation.messages == first_new_messages

    # now add a second message
    second_new_messages = [
        PlaydoMessage.user_message("Hello, world!"),
        PlaydoMessage(role="assistant", content=[PlaydoContent(type="text", text="Hello, world!")]),
    ]
    conversation = repository.add_messages_to_conversation(conversation.id, second_new_messages)
    assert len(conversation.messages) == 4
    assert conversation.messages[:2] == first_new_messages  # first two messages are the ones we added earlier
    assert conversation.messages[-2:] == second_new_messages  # last two messages are the ones we added


def test_get_conversation_success(repository: ConversationHistoryRepository) -> None:
    """Test retrieving an existing conversation, with messages."""
    conversation = repository.create_new_conversation()
    messages = [
        PlaydoMessage.user_message("Hello, world!"),
        PlaydoMessage(role="assistant", content=[PlaydoContent(type="text", text="Hello, world!")]),
    ]
    repository.add_messages_to_conversation(conversation.id, messages)
    retrieved_conversation = repository.get_conversation(conversation.id)
    assert retrieved_conversation.id == conversation.id
    assert retrieved_conversation.messages == messages


def test_get_conversation_empty(repository: ConversationHistoryRepository) -> None:
    """Test retrieving an existing conversation, with no messages."""
    conversation = repository.create_new_conversation()
    retrieved_conversation = repository.get_conversation(conversation.id)
    assert retrieved_conversation.id == conversation.id
    assert retrieved_conversation.messages == []


def test_get_conversation_not_found(repository: ConversationHistoryRepository) -> None:
    """Test attempting to retrieve a non-existent conversation."""
    with pytest.raises(ValueError, match="Conversation with id .* not found"):
        repository.get_conversation(9999)  # Assuming 9999 is a non-existent ID


def test_get_all_conversation_ids_empty(repository: ConversationHistoryRepository) -> None:
    """Test getting all conversation IDs when database is empty."""
    assert repository.get_all_conversation_ids() == []


def test_get_all_conversation_ids_with_data(repository: ConversationHistoryRepository) -> None:
    """Test getting all conversation IDs when database has conversations."""
    conversation1 = repository.create_new_conversation()
    conversation2 = repository.create_new_conversation()
    ids = repository.get_all_conversation_ids()
    assert conversation1.id in ids
    assert conversation2.id in ids
    assert len(ids) == 2


def test_conversation_manager_cleanup(initialized_db: str) -> None:
    """
    Test that the conversation manager properly cleans up resources. Interogates the stubbed connection object
    to verify it was properly closed.
    """
    with patch("sqlite3.connect") as mock_connect:
        mock_connect.return_value = MagicMock()
        with conversation_history_manager(initialized_db):
            pass
        mock_connect.return_value.close.assert_called_once()


def test_message_sequence_ordering(repository: ConversationHistoryRepository) -> None:
    """Test that messages are properly ordered by sequence number."""
    conversation = repository.create_new_conversation()
    messages = [
        PlaydoMessage.user_message("First message"),
        PlaydoMessage.user_message("Second message"),
    ]
    repository.add_messages_to_conversation(conversation.id, messages)
    retrieved_conversation = repository.get_conversation(conversation.id)
    assert retrieved_conversation.messages[0].content[0].text == "First message"
    assert retrieved_conversation.messages[1].content[0].text == "Second message"


def test_conversation_timestamps(repository: ConversationHistoryRepository) -> None:
    """Test that created_at and updated_at timestamps are properly set."""
    conversation = repository.create_new_conversation()

    assert conversation.created_at is not None
    assert conversation.updated_at is not None

    # Add a message and check if updated_at changes
    sleep(1.25)
    repository.add_messages_to_conversation(conversation.id, [PlaydoMessage.user_message("New message")])
    updated_conversation = repository.get_conversation(conversation.id)

    # Ensure both timestamps are not None before comparing
    assert updated_conversation.updated_at is not None
    assert conversation.updated_at is not None

    # Now we can safely compare the timestamps
    assert updated_conversation.updated_at > conversation.updated_at
