from playdo.cli.historical_conversation import HistoricalConversation
from playdo.models import ConversationHistory, PlaydoMessage
from unittest.mock import Mock, patch


def test_historical_conversation_new_conversation_flow():
    # Mock dependencies
    mock_conversation_history = Mock()
    mock_response_getter = Mock()

    # Set up mock conversation history repository
    mock_conversation_history.get_all_conversation_ids.return_value = []

    # Create a new conversation with ID 1 and empty messages
    new_conversation = ConversationHistory(id=1, messages=[])
    mock_conversation_history.create_new_conversation.return_value = new_conversation

    # Set up mock for adding messages to conversation
    updated_messages = []

    def add_messages_side_effect(conversation_id, new_messages):
        # Simulate adding messages to the conversation
        nonlocal updated_messages
        updated_messages.extend(new_messages)
        updated_conversation = ConversationHistory(id=conversation_id, messages=updated_messages.copy())
        return updated_conversation

    mock_conversation_history.add_messages_to_conversation.side_effect = add_messages_side_effect

    # Set up mock response getter
    def get_next_assistant_resp_side_effect(messages, user_input):
        # Create a user message and an assistant response
        user_message = PlaydoMessage(role="user", content=[{"type": "text", "text": user_input}])
        assistant_message = PlaydoMessage(role="assistant", content=[{"type": "text", "text": f"Response to: {user_input}"}])
        return [user_message, assistant_message]

    mock_response_getter._get_next_assistant_resp.side_effect = get_next_assistant_resp_side_effect

    # Create the HistoricalConversation instance
    historical_conversation = HistoricalConversation(
        conversation_history=mock_conversation_history, response_getter=mock_response_getter
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
    mock_conversation_history.get_all_conversation_ids.assert_called_once()

    # Should have created a new conversation
    mock_conversation_history.create_new_conversation.assert_called_once()

    # Should have called response getter three times with the correct parameters
    assert mock_response_getter._get_next_assistant_resp.call_count == 3

    # Check first call
    args, _ = mock_response_getter._get_next_assistant_resp.call_args_list[0]
    assert args[0] == []  # Empty messages list for a new conversation
    assert args[1] == "Hello, assistant!"  # First user input

    # Check second call
    args, _ = mock_response_getter._get_next_assistant_resp.call_args_list[1]
    assert len(args[0]) == 2  # Two messages from first exchange
    assert args[1] == "Tell me more about Python."  # Second user input

    # Check third call
    args, _ = mock_response_getter._get_next_assistant_resp.call_args_list[2]
    assert len(args[0]) == 4  # Four messages from first two exchanges
    assert args[1] == "How do I use pytest?"  # Third user input

    # Should have saved the new messages three times
    assert mock_conversation_history.add_messages_to_conversation.call_count == 3

    # Check the final state of messages
    assert len(updated_messages) == 6  # Three user messages and three assistant responses
    assert updated_messages[0].role == "user"
    assert updated_messages[1].role == "assistant"
    assert updated_messages[2].role == "user"
    assert updated_messages[3].role == "assistant"
    assert updated_messages[4].role == "user"
    assert updated_messages[5].role == "assistant"


def test_historical_conversation_load_existing_conversation():
    # Mock dependencies
    mock_conversation_history = Mock()
    mock_response_getter = Mock()

    # Set up mock conversation history repository
    mock_conversation_history.get_all_conversation_ids.return_value = [5, 10, 15]

    # Create existing messages for conversation ID 10
    existing_messages = [
        PlaydoMessage(role="user", content=[{"type": "text", "text": "Previous message 1"}]),
        PlaydoMessage(role="assistant", content=[{"type": "text", "text": "Previous response 1"}]),
        PlaydoMessage(role="user", content=[{"type": "text", "text": "Previous message 2"}]),
        PlaydoMessage(role="assistant", content=[{"type": "text", "text": "Previous response 2"}]),
    ]

    # Create an existing conversation with ID 10
    existing_conversation = ConversationHistory(id=10, messages=existing_messages)
    mock_conversation_history.get_conversation.return_value = existing_conversation

    # Set up mock for adding messages to conversation
    updated_messages = existing_messages.copy()

    def add_messages_side_effect(conversation_id, new_messages):
        # Simulate adding messages to the conversation
        nonlocal updated_messages
        updated_messages.extend(new_messages)
        updated_conversation = ConversationHistory(
            id=conversation_id,
            messages=updated_messages.copy(),  # Use a copy to avoid reference issues
        )
        return updated_conversation

    mock_conversation_history.add_messages_to_conversation.side_effect = add_messages_side_effect

    # Set up mock response getter
    def get_next_assistant_resp_side_effect(messages, user_input):
        # Create a user message and an assistant response
        user_message = PlaydoMessage(role="user", content=[{"type": "text", "text": user_input}])
        assistant_message = PlaydoMessage(role="assistant", content=[{"type": "text", "text": f"Response to: {user_input}"}])
        return [user_message, assistant_message]

    mock_response_getter._get_next_assistant_resp.side_effect = get_next_assistant_resp_side_effect

    # Create the HistoricalConversation instance
    historical_conversation = HistoricalConversation(
        conversation_history=mock_conversation_history, response_getter=mock_response_getter
    )

    # Mock stdin and input to simulate user selecting conversation 10 and then sending a message
    with patch("sys.stdin") as mock_stdin, patch("builtins.input") as mock_input:
        mock_input.return_value = "10"  # Select conversation ID 10
        mock_stdin.read.side_effect = ["Continue the conversation!", KeyboardInterrupt()]

        # Run the conversation
        historical_conversation.run_historical_conversation()

    # Verify interactions

    # Should have checked for existing conversations
    mock_conversation_history.get_all_conversation_ids.assert_called_once()

    # Should have loaded conversation 10
    mock_conversation_history.get_conversation.assert_called_once_with(10)

    # Should not have created a new conversation
    mock_conversation_history.create_new_conversation.assert_not_called()

    # Should have called response getter with the existing messages
    mock_response_getter._get_next_assistant_resp.assert_called_once()
    args, _ = mock_response_getter._get_next_assistant_resp.call_args
    assert args[0] == existing_messages  # Should pass existing messages
    assert args[1] == "Continue the conversation!"  # User input

    # Should have saved the new messages
    mock_conversation_history.add_messages_to_conversation.assert_called_once()
    args, _ = mock_conversation_history.add_messages_to_conversation.call_args
    assert args[0] == 10  # Conversation ID
    assert len(args[1]) == 2  # Two new messages (user and assistant)

    # Check the final state of messages
    assert len(updated_messages) == 6  # Four existing messages plus two new ones
    assert updated_messages[4].role == "user"
    assert updated_messages[4].content[0].text == "Continue the conversation!"
    assert updated_messages[5].role == "assistant"
    assert updated_messages[5].content[0].text == "Response to: Continue the conversation!"
