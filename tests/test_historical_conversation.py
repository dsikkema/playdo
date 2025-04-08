from typing import List

from playdo.cli.historical_conversation import HistoricalConversation
from playdo.models import ConversationHistory, PlaydoMessage, PlaydoContent
from unittest.mock import Mock, patch


def test_historical_conversation_new_conversation_flow() -> None:
    # Mock dependencies
    mock_conversation_service = Mock()
    mock_response_getter = Mock()
    user_id = 1

    # Set up mock conversation service
    mock_conversation_service.list_conversations.return_value = []

    # Create a new conversation with ID 1 and empty messages
    new_conversation = ConversationHistory(id=1, messages=[], user_id=user_id)
    mock_conversation_service.create_conversation.return_value = new_conversation

    # Set up mock for sending messages
    updated_messages: List[PlaydoMessage] = []

    def send_new_message_side_effect(conversation_id: int, user_id: int, new_msg: PlaydoMessage) -> ConversationHistory:
        # Simulate adding user message and getting assistant response
        nonlocal updated_messages
        # Add user message
        updated_messages.append(new_msg)
        # Add simulated assistant message
        assistant_msg = PlaydoMessage(
            role="assistant", content=[PlaydoContent(type="text", text=f"Response to: {new_msg.content[0].text}")]
        )
        updated_messages.append(assistant_msg)
        # Return updated conversation
        return ConversationHistory(id=conversation_id, messages=updated_messages.copy(), user_id=user_id)

    mock_conversation_service.send_new_message.side_effect = send_new_message_side_effect

    # Create the HistoricalConversation instance
    historical_conversation = HistoricalConversation(
        conversation_service=mock_conversation_service, response_getter=mock_response_getter, user_id=user_id
    )

    # Mock stdin.read() to simulate user input and then KeyboardInterrupt
    with patch("sys.stdin") as mock_stdin:
        # First three calls return user messages, fourth call raises KeyboardInterrupt
        mock_stdin.read.side_effect = [
            "Hello, assistant!",
            "Tell me more about Python.",
            "How do I use pytest?",
            KeyboardInterrupt(),
        ]

        # Run the conversation
        historical_conversation.run_historical_conversation()

    # Verify interactions

    # Should have checked for existing conversations
    mock_conversation_service.list_conversations.assert_called_once_with(user_id)

    # Should have created a new conversation
    mock_conversation_service.create_conversation.assert_called_once_with(user_id)

    # Should have called send_new_message three times
    assert mock_conversation_service.send_new_message.call_count == 3

    # Check first call
    args, _ = mock_conversation_service.send_new_message.call_args_list[0]
    assert args[0] == 1  # Conversation ID
    assert args[1] == user_id  # User ID
    assert args[2].content[0].text == "Hello, assistant!"  # First user message content

    # Check second call
    args, _ = mock_conversation_service.send_new_message.call_args_list[1]
    assert args[0] == 1  # Conversation ID
    assert args[1] == user_id  # User ID
    assert args[2].content[0].text == "Tell me more about Python."  # Second user message content

    # Check third call
    args, _ = mock_conversation_service.send_new_message.call_args_list[2]
    assert args[0] == 1  # Conversation ID
    assert args[1] == user_id  # User ID
    assert args[2].content[0].text == "How do I use pytest?"  # Third user message content

    # Check the final state of messages (6 messages total: 3 pairs of user & assistant)
    assert len(updated_messages) == 6
    assert updated_messages[0].role == "user"
    assert updated_messages[1].role == "assistant"
    assert updated_messages[2].role == "user"
    assert updated_messages[3].role == "assistant"
    assert updated_messages[4].role == "user"
    assert updated_messages[5].role == "assistant"


def test_historical_conversation_load_existing_conversation() -> None:
    # Mock dependencies
    mock_conversation_service = Mock()
    mock_response_getter = Mock()
    user_id = 1

    # Set up mock conversation service
    mock_conversation_service.list_conversations.return_value = [5, 10, 15]

    # Create existing messages for conversation ID 10
    existing_messages = [
        PlaydoMessage(role="user", content=[PlaydoContent(type="text", text="Previous message 1")]),
        PlaydoMessage(role="assistant", content=[PlaydoContent(type="text", text="Previous response 1")]),
        PlaydoMessage(role="user", content=[PlaydoContent(type="text", text="Previous message 2")]),
        PlaydoMessage(role="assistant", content=[PlaydoContent(type="text", text="Previous response 2")]),
    ]

    # Create an existing conversation with ID 10
    existing_conversation = ConversationHistory(id=10, messages=existing_messages, user_id=user_id)
    mock_conversation_service.get_conversation_for_user.return_value = existing_conversation

    # Set up mock for sending messages
    updated_messages = existing_messages.copy()

    def send_new_message_side_effect(conversation_id: int, user_id: int, new_msg: PlaydoMessage) -> ConversationHistory:
        # Simulate adding user message and getting assistant response
        nonlocal updated_messages
        # Add user message
        updated_messages.append(new_msg)
        # Add simulated assistant message
        assistant_msg = PlaydoMessage(
            role="assistant", content=[PlaydoContent(type="text", text=f"Response to: {new_msg.content[0].text}")]
        )
        updated_messages.append(assistant_msg)
        # Return updated conversation
        return ConversationHistory(id=conversation_id, messages=updated_messages.copy(), user_id=user_id)

    mock_conversation_service.send_new_message.side_effect = send_new_message_side_effect

    # Create the HistoricalConversation instance
    historical_conversation = HistoricalConversation(
        conversation_service=mock_conversation_service, response_getter=mock_response_getter, user_id=user_id
    )

    # Mock stdin and input to simulate user selecting conversation 10 and then sending a message
    with patch("sys.stdin") as mock_stdin, patch("builtins.input") as mock_input:
        mock_input.return_value = "10"  # Select conversation ID 10
        mock_stdin.read.side_effect = ["Continue the conversation!", KeyboardInterrupt()]

        # Run the conversation
        historical_conversation.run_historical_conversation()

    # Verify interactions

    # Should have checked for existing conversations
    mock_conversation_service.list_conversations.assert_called_once_with(user_id)

    # Should have loaded conversation 10
    mock_conversation_service.get_conversation_for_user.assert_called_once_with(10, user_id)

    # Should not have created a new conversation
    mock_conversation_service.create_conversation.assert_not_called()

    # Should have called send_new_message once
    mock_conversation_service.send_new_message.assert_called_once()
    args, _ = mock_conversation_service.send_new_message.call_args
    assert args[0] == 10  # Conversation ID
    assert args[1] == user_id  # User ID
    assert args[2].content[0].text == "Continue the conversation!"  # User message content

    # Check the final state of messages
    assert len(updated_messages) == 6  # Four existing messages plus two new ones
    assert updated_messages[4].role == "user"
    assert updated_messages[4].content[0].text == "Continue the conversation!"
    assert updated_messages[5].role == "assistant"
    assert updated_messages[5].content[0].text == "Response to: Continue the conversation!"
