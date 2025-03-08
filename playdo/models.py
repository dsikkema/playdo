"""
Models for messages and content blocks, meant to be json-serializable (unlike Anthropic's models)
and also well-typed (unlike dictionaries).
"""

from typing import Optional, Literal
from anthropic.types import Message, ContentBlock, MessageParam
import xml.etree.ElementTree as ET
import xml.dom.minidom
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
    editor_code: Optional[str] = None  # Code from the editor (null if not applicable)
    stdout: Optional[str] = None  # Standard output (null if not run or not applicable)
    stderr: Optional[str] = None  # Standard error (null if not run or not applicable)

    @staticmethod
    def from_anthropic_message(message: Message) -> "PlaydoMessage":
        """
        Create a PlaydoMessage from an Anthropic Message.
        """
        return PlaydoMessage(
            role=message.role,
            content=[PlaydoContent.from_anthropic_content(content) for content in message.content],
        )

    @staticmethod
    def user_message(
        query: str, editor_code: Optional[str] = None, stdout: Optional[str] = None, stderr: Optional[str] = None
    ) -> "PlaydoMessage":
        """
        Create a user message from a query string, optionally including code editor context.

        Args:
            query: The user's message text
            editor_code: The code in the editor (None if not applicable)
            stdout: The standard output from running the code (None if not run)
            stderr: The standard error from running the code (None if not run)
        """
        return PlaydoMessage(
            role="user", content=[PlaydoContent(type="text", text=query)], editor_code=editor_code, stdout=stdout, stderr=stderr
        )

    def to_anthropic_xml(self) -> str:
        """
        Convert the message to an XML representation for Anthropic API.
        This is a token-efficient way to include code context in messages.

        Uses whitespace in rendered xml to make it easier to read (both by humans and AI)
        """
        root = ET.Element("message")

        # Add text content
        text_elem = ET.SubElement(root, "text")
        text_elem.text = " ".join(content.text for content in self.content)

        # Add code if present
        if self.editor_code is not None:
            code_elem = ET.SubElement(root, "code")
            code_elem.text = self.editor_code

        # Add stdout if present, otherwise add empty element with status
        if self.stdout is not None:
            stdout_elem = ET.SubElement(root, "stdout")
            stdout_elem.text = self.stdout
        else:
            stdout_elem = ET.SubElement(root, "stdout")
            stdout_elem.set("status", "stale_or_not_run")

        # Add stderr if present, otherwise add empty element with status
        if self.stderr is not None:
            stderr_elem = ET.SubElement(root, "stderr")
            stderr_elem.text = self.stderr
        else:
            stderr_elem = ET.SubElement(root, "stderr")
            stderr_elem.set("status", "stale_or_not_run")

        # Convert to string
        raw_xml_str = ET.tostring(root, encoding="unicode")
        dom = xml.dom.minidom.parseString(raw_xml_str)
        return dom.toprettyxml(indent="  ")

    def to_anthropic_message(self) -> MessageParam:
        """
        Convert to Anthropic MessageParam format with all context embedded.

        For user messages with code context, we convert to an XML representation.
        For assistant messages or user messages without code, we use the standard format.
        """
        if self.role == "user" and (self.editor_code is not None or self.stdout is not None or self.stderr is not None):
            # If we have code context, use XML format
            return {"role": self.role, "content": self.to_anthropic_xml()}
        else:
            # Otherwise use standard format
            return {"role": self.role, "content": [{"type": "text", "text": content.text} for content in self.content]}


class ConversationHistory(BaseModel):
    messages: list[PlaydoMessage]
    id: int
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None
