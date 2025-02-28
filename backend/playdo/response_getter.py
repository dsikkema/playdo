"""
This module powers the "get next message based on previous messages" functionality of a basic chatloop.
"""

import logging
from typing import List

from anthropic import Anthropic
from anthropic.types import Message, MessageParam

from playdo.models import PlaydoMessage

logger = logging.getLogger("playdo")
MODEL_NAME = "claude-3-5-sonnet-latest"
# MODEL_NAME = "claude-3-5-haiku-latest"


class ResponseGetter:
    def __init__(self) -> None:
        self.anthropic_client = Anthropic()

    def _get_next_assistant_resp(self, prev_messages: list[PlaydoMessage], user_query: str) -> list[PlaydoMessage]:
        """
        Get the next assistant response. Return the message and the updated list of messages.

        The response_getter object just gets the latest message from Claude. It takes a list of previous messages and
        returns an updated message list - really the new message list will contain _two new message objects_, one
        representing the last message from the user (this is the second to last in returned messages), and the last
        message being the last message from the assistant.

        @param prev_messages: list of messages to include in the context
        @param user_query: the user's query
        @return: the assistant's response and the updated list of messages
        """
        if user_query.strip() == "":
            raise ValueError("User query is empty")
        user_msg = PlaydoMessage.user_message(user_query)
        logger.debug(f"{prev_messages=}")
        logger.debug(f"User message: {user_msg}")

        messages = prev_messages + [user_msg]

        # Convert PlaydoMessage objects to MessageParam objects that Anthropic's API expects
        message_params: List[MessageParam] = [
            {"role": msg.role, "content": [{"type": "text", "text": content.text} for content in msg.content]} for msg in messages
        ]

        resp: Message = self.anthropic_client.messages.create(
            model=MODEL_NAME,
            max_tokens=2000,
            messages=message_params,
        )

        latest_msg = PlaydoMessage.anthropic_message(resp)
        logger.debug(f"Latest message: {latest_msg}")
        return [user_msg, latest_msg]
