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
from playdo.svc.auth_service import AuthService
from playdo.user_repository import UserRepository, user_repository
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
    def auth_service(self) -> Generator[AuthService, None, None]:
        with self.user_repository() as user_repo:
            auth_service = AuthService(user_repo, PasswordHasher())
            yield auth_service
