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
from playdo.svc.conversation_service import ConversationService
from playdo.models import ConversationHistory, PlaydoMessage, User
import logging

from playdo.svc.user_service import UserService

logger = logging.getLogger("playdo")


class HistoricalConversation:
    def __init__(self, conversation_service: ConversationService, response_getter: ResponseGetter, user_service: UserService):
        self.conversation_service = conversation_service
        self.response_getter = response_getter
        self.user_service = user_service

    def _prompt_for_conversation_id(self, user_id: int) -> int | None:
        """
        Display available conversation IDs and prompt the user to select one.
        """
        conversation_ids = self.conversation_service.list_conversations_for_user(user_id)

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

    def _prompt_for_user_id(self) -> int:
        existing_users: list[User] = self.user_service.list_users()
        valid_user_ids = []
        user_id = None

        if len(existing_users) == 0:
            raise ValueError("No users found")

        print("Available users:")
        for user in existing_users:
            assert user.id is not None
            valid_user_ids.append(user.id)
            print(f"{user.id}: {user.username}")

        while user_id is None:
            user_id = input("Enter the ID of the user to load: ")
            if not user_id.isdigit() or int(user_id) not in valid_user_ids:
                print("Invalid input. Please enter a valid user ID.")
                continue

        return int(user_id)

    def run_historical_conversation(self) -> None:
        # get conversation ID from user
        user_id = self._prompt_for_user_id()
        conversation_id = self._prompt_for_conversation_id(user_id)
        conversation: Optional[ConversationHistory]

        # load conversation from database if one is chosen
        if conversation_id is not None:
            conversation = self.conversation_service.get_conversation_for_user(conversation_id, user_id)
            logger.debug(f"Loaded conversation {conversation=}")
        else:
            logger.debug("No conversation ID provided, starting new conversation")
            conversation = self.conversation_service.create_conversation(user_id)
            print(f"You're in a brand new conversation: ID={conversation.id}")
            logger.debug(f"Created new conversation {conversation=}")

        # run the chatloop, passing in the messages
        self._chatloop(conversation, user_id)

    def _chatloop(self, conversation: ConversationHistory, user_id: int) -> None:
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
                # Create user message
                user_msg = PlaydoMessage.user_message(query=user_message_str)

                # Send message using the conversation service
                updated_conversation = self.conversation_service.send_new_message(conversation.id, user_id, user_msg)

                # Print the assistant's response (last message)
                response = updated_conversation.messages[-1]
                print(f"\nAssistant: {response.content[0].text}\n")

            except anthropic.InternalServerError as e:
                print(f"Error: {e}")
                continue
