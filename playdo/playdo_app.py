"""
Separate module for PlaydoApp to avoid circular imports.

TOOOD: not doing serverless. Maintain a long-lived repository object and connection pool.
"""

from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from flask import Flask

from playdo.conversation_repository import ConversationRepository, conversation_repository
from playdo.user_repository import UserRepository, user_repository
from playdo.response_getter import ResponseGetter
from playdo.settings import settings


class PlaydoApp(Flask):
    @contextmanager
    def conversation_repository(self) -> Generator[ConversationRepository, None, None]:
        db_path = Path(settings.DATABASE_PATH)
        with conversation_repository(db_path) as repository:
            yield repository

    @contextmanager
    def user_repository(self) -> Generator[UserRepository, None, None]:
        db_path = Path(settings.DATABASE_PATH)
        with user_repository(db_path) as repository:
            yield repository

    @contextmanager
    def response_getter(self) -> Generator[ResponseGetter, None, None]:
        response_getter = ResponseGetter()
        try:
            yield response_getter
        finally:
            pass  # No cleanup needed
