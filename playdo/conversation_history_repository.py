"""
This module implements a class for managing the conversation history.

The schema of the database is stored in the following schema initialization file: `schema.sql`.

It interfaces with the following table:
```
CREATE TABLE conversation (
    id integer primary key autoincrement,
    created_at datetime default current_timestamp,
    updated_at datetime default current_timestamp,
    messages text not null -- json array of messages represented as plain string
);
```

When a new conversation is started, a new row is inserted into the table with the current timestamp and an empty messages array.

When the conversation finishes, the messages array is updated with the final state of the conversation.

All messages are read and written as one string represented a json array of messages.

The repository interfaces with a `ConversationHistory` dataclass that represents a conversation, enabling (for instance)
upserting of conversations.
"""
from contextlib import contextmanager
import json
import logging
logger = logging.getLogger('playdo')
import sqlite3
from typing import Generator

from playdo.models import ConversationHistory, PlaydoMessage

class ConversationHistoryRepository:
    """
    Manages the conversation history.
    """
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
    
    def upsert_conversation(self, conversation: ConversationHistory) -> ConversationHistory:
        """
        Upsert a conversation into the database.
        """
        if conversation.id is not None:
            return self.save_conversation_update(conversation)
        else:
            return self.save_new_conversation(conversation)

    def save_new_conversation(self, conversation: ConversationHistory) -> ConversationHistory:
        """
        Save a new conversation to the database.

        @param conversation: the conversation to save
        @return: The new conversation, as loaded from the database
        """
        messages_json = json.dumps(conversation.model_dump()['messages'])
        logger.debug(f"Saving new conversation {messages_json=}")
        self.cursor.execute("INSERT INTO conversation (messages) VALUES (?)", 
                            (messages_json,))
        self.conn.commit()
        # lastrowid is reliable in the scope of a single connection
        return self.get_conversation(self.cursor.lastrowid)

    def save_conversation_update(self, conversation: ConversationHistory) -> ConversationHistory:
        messages_json = json.dumps(conversation.model_dump()['messages'])
        logger.debug(f"Saving conversation update {messages_json=}")
        self.cursor.execute("UPDATE conversation SET messages = ? WHERE id = ?", 
                            (messages_json, conversation.id))
        self.conn.commit()
        return self.get_conversation(conversation.id)

    def get_conversation(self, id: int) -> ConversationHistory:
        self.cursor.execute("SELECT * FROM conversation WHERE id = ?", (id,))
        row = self.cursor.fetchone()
        if row is None:
            raise ValueError(f"Conversation with id {id} not found")

        logger.debug(f"Loaded conversation {row=}")
        return ConversationHistory(
            id=row[0],
            created_at=row[1],
            updated_at=row[2],
            messages=[PlaydoMessage.model_validate(message_json) for message_json in json.loads(row[3])]
        )
    
    def get_all_conversation_ids(self) -> list[int]:
        self.cursor.execute("SELECT id FROM conversation")
        return [row[0] for row in self.cursor.fetchall()]

    def cleanup(self) -> None:
        self.conn.close()


@contextmanager
def conversation_history_manager(db_path: str) -> Generator[ConversationHistoryRepository, None, None]:
    try:
        conversation_history = ConversationHistoryRepository(db_path)
        yield conversation_history
    finally:
        conversation_history.cleanup()
    