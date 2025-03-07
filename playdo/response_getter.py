"""
This module powers the "get next message based on previous messages" functionality of a basic chatloop.
"""

import logging
from typing import List

from anthropic import Anthropic
from anthropic.types import Message, MessageParam

from playdo.settings import settings
from playdo.models import PlaydoMessage

logger = logging.getLogger("playdo")


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

        There's a "bubble" around the Anthropic modelling here: PlaydoMessage objects are more strucutured, with
        fields Anthropic models do not have. We convert into the Anthropic model layer here before calling the API,
        and convert back after receiving the response.

        TOODO: Ideally this function receives a PlaydoMessage input for the user's message, so that the calling code
        can handle already persisting that user message to the database. This way, if the Anthropic API call fails, we
        can retry without user needing to re-type the message - the message they tried to send will already be there.

        @param prev_messages: list of messages to include in the context
        @param user_query: the user's query
        @return: the assistant's response and the updated list of messages
        """
        if user_query.strip() == "":
            raise ValueError("User query is empty")
        user_msg = PlaydoMessage.user_message(user_query)
        logger.debug(f"{prev_messages=}")
        logger.debug(f"User message: {user_msg}")

        assert not settings.TESTING, "Must mock this class during tests to avoid hitting Anthropic API"
        messages = prev_messages + [user_msg]

        # Convert PlaydoMessage objects to MessageParam objects that Anthropic's API expects
        message_params: List[MessageParam] = [msg.to_anthropic_message() for msg in messages]

        resp: Message = self.anthropic_client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=2000,
            messages=message_params,
        )

        latest_msg = PlaydoMessage.from_anthropic_message(resp)
        logger.debug(f"Latest message: {latest_msg}")
        return [user_msg, latest_msg]
