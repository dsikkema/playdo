"""
This module implements a class for managing the conversation history.

The schema of the database is stored in schema.sql, which defines two tables:
- conversation: Stores conversation metadata
- message: Stores individual messages with sequence ordering
"""

import json
import logging
import sqlite3
from contextlib import contextmanager
from typing import Generator, List

from playdo.models import ConversationHistory, PlaydoContent, PlaydoMessage

logger = logging.getLogger("playdo")


class ConversationHistoryRepository:
    """
    Manages the conversation history.
    """

    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()

    def create_new_conversation(self) -> ConversationHistory:
        """
        Create a new conversation. There will be no messages in the conversation initially.
        """
        self.cursor.execute("INSERT INTO conversation DEFAULT VALUES")
        self.conn.commit()
        conversation_id = self.cursor.lastrowid
        return self.get_conversation(conversation_id)

    def add_messages_to_conversation(self, conversation_id: int, new_messages: List[PlaydoMessage]) -> ConversationHistory:
        """Add new messages to an existing conversation."""
        # Get the next sequence number
        self.cursor.execute(
            "SELECT COALESCE(MAX(sequence_number), -1) + 1 FROM message WHERE conversation_id = ?",
            (conversation_id,),
        )
        next_sequence = self.cursor.fetchone()[0]

        # Insert each new message
        for i, message in enumerate(new_messages, start=next_sequence):
            content_json = json.dumps([c.model_dump() for c in message.content])
            self.cursor.execute(
                "INSERT INTO message (conversation_id, sequence_number, role, content) VALUES (?, ?, ?, ?)",
                (conversation_id, i, message.role, content_json),
            )

        # Update conversation timestamp
        self.cursor.execute(
            "UPDATE conversation SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (conversation_id,),
        )
        self.conn.commit()
        return self.get_conversation(conversation_id)

    def get_conversation(self, id: int) -> ConversationHistory:
        """Load a conversation and all its messages."""
        # First verify conversation exists
        self.cursor.execute("SELECT created_at, updated_at FROM conversation WHERE id = ?", (id,))
        conv_row = self.cursor.fetchone()
        if conv_row is None:
            raise ValueError(f"Conversation with id {id} not found")

        # Get all messages in sequence order
        self.cursor.execute(
            "SELECT role, content FROM message WHERE conversation_id = ? ORDER BY sequence_number",
            (id,),
        )
        messages = []
        for role, content_json in self.cursor.fetchall():
            content_list = [PlaydoContent.model_validate(c) for c in json.loads(content_json)]
            messages.append(PlaydoMessage(role=role, content=content_list))

        logger.debug(f"{conv_row=}")
        created_at = conv_row[0]
        updated_at = conv_row[1]
        return ConversationHistory(id=id, created_at=created_at, updated_at=updated_at, messages=messages)

    def get_all_conversation_ids(self) -> list[int]:
        self.cursor.execute("SELECT id FROM conversation")
        return [row[0] for row in self.cursor.fetchall()]

    def cleanup(self) -> None:
        self.conn.close()


@contextmanager
def conversation_history_manager(
    db_path: str,
) -> Generator[ConversationHistoryRepository, None, None]:
    try:
        conversation_history = ConversationHistoryRepository(db_path)
        yield conversation_history
    finally:
        conversation_history.cleanup()
