import pytest
from unittest.mock import MagicMock, patch
from playdo.svc.conversation_service import ConversationService
from playdo.errors import NotAuthorizedForConversation, ConversationNotFoundError
from playdo.models import ConversationHistory, PlaydoMessage, PlaydoContent


@pytest.fixture
def mock_repo():
    """Create a mock conversation repository."""
    mock = MagicMock()
    return mock


@pytest.fixture
def conversation_service(mock_repo):
    """Create a ConversationService with a mock repository."""
    return ConversationService(mock_repo)


def test_list_conversations(conversation_service, mock_repo):
    """Test that list_conversations passes the user_id to the repository."""
    user_id = 42
    conversation_service.list_conversations(user_id)
    mock_repo.get_all_conversation_ids_for_user.assert_called_once_with(user_id)


def test_create_conversation(conversation_service, mock_repo):
    """Test that create_conversation passes the user_id to the repository."""
    user_id = 42
    conversation_service.create_conversation(user_id)
    mock_repo.create_new_conversation.assert_called_once_with(user_id)


def test_get_conversation_for_user_authorized(conversation_service, mock_repo):
    """Test that a user can access their own conversation."""
    user_id = 42
    conversation_id = 123
    # Create a mock conversation with the same user_id
    mock_conversation = ConversationHistory(id=conversation_id, user_id=user_id, messages=[])
    mock_repo.get_conversation.return_value = mock_conversation

    # This should succeed
    result = conversation_service.get_conversation_for_user(conversation_id, user_id)
    assert result == mock_conversation
    mock_repo.get_conversation.assert_called_once_with(conversation_id)


def test_get_conversation_for_user_unauthorized(conversation_service, mock_repo):
    """Test that a user cannot access another user's conversation."""
    user_id = 42
    other_user_id = 99
    conversation_id = 123
    # Create a mock conversation with a different user_id
    mock_conversation = ConversationHistory(
        id=conversation_id,
        user_id=other_user_id,  # Different user
        messages=[],
    )
    mock_repo.get_conversation.return_value = mock_conversation

    # This should raise NotAuthorizedForConversation
    with pytest.raises(NotAuthorizedForConversation):
        conversation_service.get_conversation_for_user(conversation_id, user_id)
    mock_repo.get_conversation.assert_called_once_with(conversation_id)


def test_send_new_message_authorized(conversation_service, mock_repo):
    """Test that a user can send a message to their own conversation."""
    user_id = 42
    conversation_id = 123
    # Create a mock conversation with the same user_id
    mock_conversation = ConversationHistory(id=conversation_id, user_id=user_id, messages=[])
    # Mock the updated conversation after adding the message
    mock_updated_conversation = ConversationHistory(
        id=conversation_id, user_id=user_id, messages=[PlaydoMessage.user_message("test message")]
    )
    # Mock the final conversation after adding the assistant response
    mock_final_conversation = ConversationHistory(
        id=conversation_id,
        user_id=user_id,
        messages=[
            PlaydoMessage.user_message("test message"),
            PlaydoMessage(role="assistant", content=[PlaydoContent(type="text", text="response")]),
        ],
    )

    # Setup mock returns
    mock_repo.get_conversation.return_value = mock_conversation
    mock_repo.add_messages_to_conversation.side_effect = [mock_updated_conversation, mock_final_conversation]

    # Mock the ResponseGetter
    with patch("playdo.svc.conversation_service.ResponseGetter") as mock_response_getter_class:
        mock_response_getter = MagicMock()
        mock_response_getter_class.return_value = mock_response_getter
        mock_response_getter._get_next_assistant_resp.return_value = PlaydoMessage(
            role="assistant", content=[PlaydoContent(type="text", text="response")]
        )

        # Send a new message
        new_msg = PlaydoMessage.user_message("test message")
        result = conversation_service.send_new_message(conversation_id, user_id, new_msg)

        # Verify the result
        assert result == mock_final_conversation

        # Verify method calls
        mock_repo.get_conversation.assert_called_once_with(conversation_id)
        assert mock_repo.add_messages_to_conversation.call_count == 2
        mock_response_getter._get_next_assistant_resp.assert_called_once()


def test_send_new_message_unauthorized(conversation_service, mock_repo):
    """Test that a user cannot send a message to another user's conversation."""
    user_id = 42
    other_user_id = 99
    conversation_id = 123
    # Create a mock conversation with a different user_id
    mock_conversation = ConversationHistory(
        id=conversation_id,
        user_id=other_user_id,  # Different user
        messages=[],
    )
    mock_repo.get_conversation.return_value = mock_conversation

    # This should raise NotAuthorizedForConversation
    with pytest.raises(NotAuthorizedForConversation):
        new_msg = PlaydoMessage.user_message("test message")
        conversation_service.send_new_message(conversation_id, user_id, new_msg)

    # Verify that get_conversation was called but add_messages_to_conversation was not
    mock_repo.get_conversation.assert_called_once_with(conversation_id)
    mock_repo.add_messages_to_conversation.assert_not_called()


def test_send_new_message_conversation_not_found(conversation_service, mock_repo):
    """Test handling when a conversation is not found."""
    user_id = 42
    conversation_id = 123

    # Mock the repository to raise ConversationNotFoundError
    mock_repo.get_conversation.side_effect = ConversationNotFoundError(conversation_id)

    # This should propagate the ConversationNotFoundError
    with pytest.raises(ConversationNotFoundError):
        new_msg = PlaydoMessage.user_message("test message")
        conversation_service.send_new_message(conversation_id, user_id, new_msg)

    # Verify that get_conversation was called but add_messages_to_conversation was not
    mock_repo.get_conversation.assert_called_once_with(conversation_id)
    mock_repo.add_messages_to_conversation.assert_not_called()
