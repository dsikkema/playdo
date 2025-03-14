"""
This module implements a "historical conversation" - it contains a chatloop,
but features the API surrounding saving the conversation history after it finishes,
and (optionally) loading up a previous conversation by ID before it starts.

First, it interacts with the user, asking for an ID of a conversation to load,
defaulting to None. If a conversation is chosen, it loads the conversation from the database
and prints it out.

Then it enters the chatloop, initialized if needed with previous messages. After each
message exchange, it saves only the new messages to the database.

"""

import sys
from typing import Optional

import anthropic
from playdo.response_getter import ResponseGetter
from playdo.conversation_repository import ConversationRepository
from playdo.models import ConversationHistory, PlaydoMessage
import logging

logger = logging.getLogger("playdo")


class HistoricalConversation:
    def __init__(self, conversation_history: ConversationRepository, response_getter: ResponseGetter):
        self.conversation_history = conversation_history
        self.response_getter = response_getter

    def _prompt_for_conversation_id(self) -> int | None:
        """
        Display available conversation IDs and prompt the user to select one.
        """
        conversation_ids = self.conversation_history.get_all_conversation_ids()

        if not conversation_ids:
            return None

        valid_input_received = False
        while not valid_input_received:
            print("Available conversations:")
            for id in conversation_ids:
                print(f"{id}")
            user_input = input("Enter the number of the conversation to load (or press Enter for new): ")
            if not user_input:
                valid_input_received = True
                choice = None
                continue
            if not user_input.isdigit():
                print("Invalid input. Please enter a valid integer.")
                continue
            choice = int(user_input)
            if choice not in conversation_ids:
                print("Invalid input. Please enter a valid conversation ID.")
                continue
            valid_input_received = True
        return choice

    def run_historical_conversation(self) -> None:
        # get conversation ID from user
        conversation_id = self._prompt_for_conversation_id()
        conversation: Optional[ConversationHistory]

        # load conversation from database if one is chosen
        if conversation_id is not None:
            conversation = self.conversation_history.get_conversation(conversation_id)
            logger.debug(f"Loaded conversation {conversation=}")
        else:
            logger.debug("No conversation ID provided, starting new conversation")
            conversation = self.conversation_history.create_new_conversation()
            print(f"You're in a brand new conversation: ID={conversation.id}")
            logger.debug(f"Created new conversation {conversation=}")

        # run the chatloop, passing in the messages
        self._chatloop(conversation)

    def _chatloop(self, conversation: ConversationHistory) -> None:
        """
        Functions by taking all messages from conversation history (which is an empty list if it's a new
        conversation), and passing them into the response_getter, which returns a new message list
        with new messages added to the end.

        After each response, it saves only the new messages to the database.
        """

        if conversation.messages:
            print("Conversation history:\n")
            for message in conversation.messages:
                # if it's a user message AND if code or output is present, then print the xml representation for debugging help
                print(f"{message.role}: {message.content[0].text}")
                if message.role == "user" and (message.editor_code or message.stdout or message.stderr):
                    print(f"XML:\n{message.to_anthropic_xml()}")
        while True:
            print("\nEnter your message (Ctrl-D to send): ")
            try:
                user_message_str = sys.stdin.read()
                if user_message_str.strip() == "":
                    print("\nInput cannot be empty!")
                    continue
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break

            try:
                # Get updated messages from response getter
                user_msg = PlaydoMessage.user_message(query=user_message_str)
                conversation = self.conversation_history.add_messages_to_conversation(conversation.id, [user_msg])
                response: PlaydoMessage = self.response_getter._get_next_assistant_resp(conversation.messages)

                # Save only the new messages
                conversation = self.conversation_history.add_messages_to_conversation(conversation.id, [response])

                # Print the assistant's response (last message)
                print(f"\nAssistant: {response.content[0].text}\n")

            except anthropic.InternalServerError as e:
                print(f"Error: {e}")
                continue
