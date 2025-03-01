"""
Separate module for PlaydoApp to avoid circular imports.

TOOOD: not doing serverless. Maintain a long-lived repository object and connection pool.
"""

from collections.abc import Generator
from contextlib import contextmanager

from flask import Flask

from playdo.conversation_repository import ConversationRepository, conversation_repository
from playdo.settings import settings


class PlaydoApp(Flask):
    @contextmanager
    def conversation_repository(self) -> Generator[ConversationRepository, None, None]:
        with conversation_repository(settings.DATABASE_PATH) as repository:
            yield repository
