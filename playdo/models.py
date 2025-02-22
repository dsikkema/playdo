"""
Models for messages and content blocks, meant to be json-serializable (unlike Anthropic's models)
and also well-typed (unlike dictionaries).
"""
from typing import Optional, Literal
from anthropic.types import Message, ContentBlock


import datetime

from pydantic import BaseModel

class PlaydoContent(BaseModel):
    type: Literal["text"]
    text: str

    @staticmethod
    def from_anthropic_content(content: ContentBlock) -> "PlaydoContent":
        assert content.type == "text"
        return PlaydoContent(type="text", text=content.text)


class PlaydoMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: list[PlaydoContent]

    @staticmethod
    def anthropic_message(message: Message) -> "PlaydoMessage":
        """
        Create a PlaydoMessage from an Anthropic Message.
        """
        return PlaydoMessage(
            role=message.role,
            content=[
                PlaydoContent.from_anthropic_content(content)
                for content in message.content
            ],
        )

    @staticmethod
    def user_message(query: str) -> "PlaydoMessage":
        """
        Create a user message from a query string.
        """
        return PlaydoMessage(role="user", content=[PlaydoContent(type="text", text=query)])

class ConversationHistory(BaseModel):
    messages: list[PlaydoMessage]
    id: Optional[int] = None
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None