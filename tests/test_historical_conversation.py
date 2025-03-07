from typing import List

from playdo.cli.historical_conversation import HistoricalConversation
from playdo.models import ConversationHistory, PlaydoMessage, PlaydoContent
from unittest.mock import Mock, patch


def test_historical_conversation_new_conversation_flow() -> None:
    # Mock dependencies
    mock_conversation_history = Mock()
    mock_response_getter = Mock()

    # Set up mock conversation history repository
    mock_conversation_history.get_all_conversation_ids.return_value = []

    # Create a new conversation with ID 1 and empty messages
    new_conversation = ConversationHistory(id=1, messages=[])
    mock_conversation_history.create_new_conversation.return_value = new_conversation

    # Set up mock for adding messages to conversation
    updated_messages: List[PlaydoMessage] = []

    def add_messages_side_effect(conversation_id: int, new_messages: List[PlaydoMessage]) -> ConversationHistory:
        # Simulate adding messages to the conversation
        nonlocal updated_messages
        updated_messages.extend(new_messages)
        updated_conversation = ConversationHistory(id=conversation_id, messages=updated_messages.copy())
        return updated_conversation

    mock_conversation_history.add_messages_to_conversation.side_effect = add_messages_side_effect

    # Set up mock response getter
    def get_next_assistant_resp_side_effect(messages: List[PlaydoMessage]) -> PlaydoMessage:
        # Create an assistant response based on the last message in the list
        user_input = ""
        if messages and messages[-1].role == "user" and messages[-1].content:
            user_input = messages[-1].content[0].text

        assistant_message = PlaydoMessage(
            role="assistant", content=[PlaydoContent(type="text", text=f"Response to: {user_input}")]
        )
        return assistant_message

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
    assert len(args[0]) == 1  # List containing the user message after it's been added
    assert args[0][0].content[0].text == "Hello, assistant!"  # First user message content

    # Check second call
    args, _ = mock_response_getter._get_next_assistant_resp.call_args_list[1]
    assert len(args[0]) == 3  # Three messages: user and assistant from first exchange, plus new user
    assert args[0][2].content[0].text == "Tell me more about Python."  # Second user message content

    # Check third call
    args, _ = mock_response_getter._get_next_assistant_resp.call_args_list[2]
    assert len(args[0]) == 5  # Five messages from first two exchanges plus new user
    assert args[0][4].content[0].text == "How do I use pytest?"  # Third user message content

    # Should have saved messages six times (two saves per exchange: user message and assistant response)
    assert mock_conversation_history.add_messages_to_conversation.call_count == 6

    # Check the final state of messages
    assert len(updated_messages) == 6  # Three user messages and three assistant responses
    assert updated_messages[0].role == "user"
    assert updated_messages[1].role == "assistant"
    assert updated_messages[2].role == "user"
    assert updated_messages[3].role == "assistant"
    assert updated_messages[4].role == "user"
    assert updated_messages[5].role == "assistant"


def test_historical_conversation_load_existing_conversation() -> None:
    # Mock dependencies
    mock_conversation_history = Mock()
    mock_response_getter = Mock()

    # Set up mock conversation history repository
    mock_conversation_history.get_all_conversation_ids.return_value = [5, 10, 15]

    # Create existing messages for conversation ID 10
    existing_messages = [
        PlaydoMessage(role="user", content=[PlaydoContent(type="text", text="Previous message 1")]),
        PlaydoMessage(role="assistant", content=[PlaydoContent(type="text", text="Previous response 1")]),
        PlaydoMessage(role="user", content=[PlaydoContent(type="text", text="Previous message 2")]),
        PlaydoMessage(role="assistant", content=[PlaydoContent(type="text", text="Previous response 2")]),
    ]

    # Create an existing conversation with ID 10
    existing_conversation = ConversationHistory(id=10, messages=existing_messages)
    mock_conversation_history.get_conversation.return_value = existing_conversation

    # Set up mock for adding messages to conversation
    updated_messages = existing_messages.copy()

    def add_messages_side_effect(conversation_id: int, new_messages: List[PlaydoMessage]) -> ConversationHistory:
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
    def get_next_assistant_resp_side_effect(messages: List[PlaydoMessage]) -> PlaydoMessage:
        # Create an assistant response based on the last message in the list
        user_input = ""
        if messages and messages[-1].role == "user" and messages[-1].content:
            user_input = messages[-1].content[0].text

        assistant_message = PlaydoMessage(
            role="assistant", content=[PlaydoContent(type="text", text=f"Response to: {user_input}")]
        )
        return assistant_message

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
    assert len(args[0]) == 5  # Should pass existing messages plus new user message
    assert args[0][4].content[0].text == "Continue the conversation!"  # Last message is user message

    # Should have saved the new messages twice (once for user message, once for assistant response)
    assert mock_conversation_history.add_messages_to_conversation.call_count == 2

    # First call should save the user message
    args, _ = mock_conversation_history.add_messages_to_conversation.call_args_list[0]
    assert args[0] == 10  # Conversation ID
    assert len(args[1]) == 1  # One new message (user)
    assert args[1][0].role == "user"
    assert args[1][0].content[0].text == "Continue the conversation!"

    # Second call should save the assistant response
    args, _ = mock_conversation_history.add_messages_to_conversation.call_args_list[1]
    assert args[0] == 10  # Conversation ID
    assert len(args[1]) == 1  # One new message (assistant)
    assert args[1][0].role == "assistant"

    # Check the final state of messages
    assert len(updated_messages) == 6  # Four existing messages plus two new ones
    assert updated_messages[4].role == "user"
    assert updated_messages[4].content[0].text == "Continue the conversation!"
    assert updated_messages[5].role == "assistant"
    assert updated_messages[5].content[0].text == "Response to: Continue the conversation!"
