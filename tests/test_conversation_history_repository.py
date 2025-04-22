from time import sleep
from pathlib import Path
from typing import Generator

import pytest
from playdo.conversation_repository import conversation_repository, ConversationRepository
from playdo.errors import ConversationNotFoundError
from playdo.models import PlaydoMessage, PlaydoContent
from unittest.mock import MagicMock, patch


@pytest.fixture
def repository(initialized_test_db_path: Path) -> Generator[ConversationRepository, None, None]:
    """Create a test repository instance."""
    with conversation_repository(initialized_test_db_path) as repo:
        yield repo


def test_save_new_empty_conversation(repository: ConversationRepository) -> None:
    """Test creating a new conversation with no messages."""
    user_id = 1
    conversation = repository.create_new_conversation(user_id)
    assert conversation.id is not None
    assert conversation.messages == []
    assert conversation.user_id == user_id


def test_add_messages_to_new_conversation(repository: ConversationRepository) -> None:
    """
    Test adding messages to a new conversation: first when it's empty, then when it's initialized with messages.
    """
    user_id = 1
    conversation = repository.create_new_conversation(user_id)
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


def test_get_conversation_success(repository: ConversationRepository) -> None:
    """Test retrieving an existing conversation, with messages."""
    user_id = 1
    conversation = repository.create_new_conversation(user_id)
    messages = [
        PlaydoMessage.user_message("Hello, world!"),
        PlaydoMessage(role="assistant", content=[PlaydoContent(type="text", text="Hello, world!")]),
    ]
    repository.add_messages_to_conversation(conversation.id, messages)
    retrieved_conversation = repository.get_conversation(conversation.id)
    assert retrieved_conversation.id == conversation.id
    assert retrieved_conversation.messages == messages
    assert retrieved_conversation.user_id == user_id


def test_get_conversation_empty(repository: ConversationRepository) -> None:
    """Test retrieving an existing conversation, with no messages."""
    user_id = 1
    conversation = repository.create_new_conversation(user_id)
    retrieved_conversation = repository.get_conversation(conversation.id)
    assert retrieved_conversation.id == conversation.id
    assert retrieved_conversation.messages == []
    assert retrieved_conversation.user_id == user_id


def test_get_conversation_not_found(repository: ConversationRepository) -> None:
    """Test attempting to retrieve a non-existent conversation."""
    with pytest.raises(ConversationNotFoundError, match="Conversation with id .* not found"):
        repository.get_conversation(9999)  # Assuming 9999 is a non-existent ID


def test_get_all_conversation_ids_empty(repository: ConversationRepository) -> None:
    """Test getting all conversation IDs when database is empty."""
    user_id = 1
    assert repository.get_all_conversation_ids_for_user(user_id) == []


def test_get_all_conversation_ids_with_data(repository: ConversationRepository) -> None:
    """Test getting all conversation IDs when database has conversations."""
    user_id = 1
    conversation1 = repository.create_new_conversation(user_id)
    conversation2 = repository.create_new_conversation(user_id)
    ids = repository.get_all_conversation_ids_for_user(user_id)
    assert conversation1.id in ids
    assert conversation2.id in ids
    assert len(ids) == 2


def test_get_all_conversation_ids_for_correct_user(repository: ConversationRepository) -> None:
    """Test that getting conversation IDs only returns conversations for the specified user."""
    user1_id = 1
    user2_id = 2

    # Create conversations for two different users
    user1_conv = repository.create_new_conversation(user1_id)
    user2_conv = repository.create_new_conversation(user2_id)

    # Check that user1 only sees their conversations
    user1_ids = repository.get_all_conversation_ids_for_user(user1_id)
    assert user1_conv.id in user1_ids
    assert user2_conv.id not in user1_ids
    assert len(user1_ids) == 1

    # Check that user2 only sees their conversations
    user2_ids = repository.get_all_conversation_ids_for_user(user2_id)
    assert user2_conv.id in user2_ids
    assert user1_conv.id not in user2_ids
    assert len(user2_ids) == 1


def test_conversation_manager_cleanup(initialized_test_db_path: Path) -> None:
    """
    Test that the conversation manager properly cleans up resources. Interogates the stubbed connection object
    to verify it was properly closed.
    """
    with patch("sqlite3.connect") as mock_connect:
        mock_connect.return_value = MagicMock()
        with conversation_repository(initialized_test_db_path):
            pass
        mock_connect.return_value.close.assert_called_once()


def test_message_sequence_ordering(repository: ConversationRepository) -> None:
    """Test that messages are properly ordered by sequence number."""
    user_id = 1
    conversation = repository.create_new_conversation(user_id)
    messages = [
        PlaydoMessage.user_message("First message"),
        PlaydoMessage.user_message("Second message"),
    ]
    repository.add_messages_to_conversation(conversation.id, messages)
    retrieved_conversation = repository.get_conversation(conversation.id)
    assert retrieved_conversation.messages[0].content[0].text == "First message"
    assert retrieved_conversation.messages[1].content[0].text == "Second message"


def test_conversation_timestamps(repository: ConversationRepository) -> None:
    """Test that created_at and updated_at timestamps are properly set."""
    user_id = 1
    conversation = repository.create_new_conversation(user_id)

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
