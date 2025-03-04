"""
Separate module for PlaydoApp to avoid circular imports.

TOOOD: not doing serverless. Maintain a long-lived repository object and connection pool.
"""

from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from flask import Flask

from playdo.conversation_repository import ConversationRepository, conversation_repository
from playdo.settings import settings


class PlaydoApp(Flask):
    @contextmanager
    def conversation_repository(self) -> Generator[ConversationRepository, None, None]:
        db_path = Path(settings.DATABASE_PATH)
        with conversation_repository(db_path) as repository:
            yield repository
