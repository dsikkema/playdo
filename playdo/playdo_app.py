"""
Separate module for PlaydoApp to avoid circular imports.

TOOOD: not doing serverless. Maintain a long-lived repository object and connection pool.
"""

from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from argon2 import PasswordHasher
from flask import Flask

from playdo.conversation_repository import ConversationRepository, conversation_repository
from playdo.svc.user_service import UserService
from playdo.user_repository import user_repository
from playdo.settings import settings


class PlaydoApp(Flask):
    @contextmanager
    def conversation_repository(self) -> Generator[ConversationRepository, None, None]:
        db_path = Path(settings.DATABASE_PATH)
        with conversation_repository(db_path) as repository:
            yield repository

    @contextmanager
    def user_service(self) -> Generator[UserService, None, None]:
        with user_repository(Path(settings.DATABASE_PATH)) as user_repo:
            yield UserService(user_repo, PasswordHasher())
