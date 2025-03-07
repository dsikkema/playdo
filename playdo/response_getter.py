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

    def _get_next_assistant_resp(self, prev_messages: list[PlaydoMessage]) -> PlaydoMessage:
        """
        Get the next assistant response. Return the message and the updated list of messages.

        The response_getter object just gets the latest message from Claude. It takes a list of previous messages and
        returns the reponse from the assistant.
        
        The most recent user's message is expected to be the last item in the list of previous messages, added there by
        the calling code.

        There's a "bubble" around the Anthropic modeling here: PlaydoMessage objects are more strucutured, with
        fields Anthropic models do not have. We convert into the Anthropic model layer here before calling the API,
        and convert back after receiving the response.

        TOODO: something possible for future token-optimization (but stopping short of conversation summarization), just
        omit the code/output from being rendered into the conversation context sent to Claude IFF there are N or more
        _more recent_ code updates that have been sent afterwards. In other words, keep the user's text messages no 
        matter how old, but drop code/output that's "outdated" by newer code updates.

        @param prev_messages: list of messages to include in the context (includes the user's most recent message)
        @return: the assistant's response
        """
        logger.debug(f"{prev_messages=}")

        assert not settings.TESTING, "Must mock this class during tests to avoid hitting Anthropic API"

        # 'bubble begin': Convert PlaydoMessage objects to MessageParam objects that Anthropic's API expects
        message_params: List[MessageParam] = [msg.to_anthropic_message() for msg in prev_messages]

        resp: Message = self.anthropic_client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=2000,
            messages=message_params,
        )

        latest_msg = PlaydoMessage.from_anthropic_message(resp)
        # 'bubble end' (line above): Convert Anthropic Message objects back to PlaydoMessage objects

        logger.debug(f"Latest message: {latest_msg}")
        return latest_msg
