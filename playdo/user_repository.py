"""
This module implements a class for managing users in the database.

The user table is defined in schema.sql.
"""

import logging
import sqlite3
import secrets
from contextlib import contextmanager
from datetime import datetime
from typing import List, Optional, Tuple, Generator, Union
from pathlib import Path

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from playdo.models import User

logger = logging.getLogger("playdo")

# Type alias for parameters to SQLite query
SQLiteParam = Union[str, int, float, None]


class UserAlreadyExistsError(Exception):
    """Exception raised when a user already exists in the database."""

    pass


class UserNotFoundError(Exception):
    """Exception raised when a user is not found in the database."""

    pass


class UserRepository:
    """
    Manages user data in the database.
    """

    def __init__(self, db_path: Path):
        assert db_path.exists(), f"Database file {db_path} does not exist"
        self.db_path = str(db_path)
        self.password_hasher = PasswordHasher()
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

    def _convert_row_to_user(self, row: sqlite3.Row) -> User:
        """Convert a database row to a User model instance."""
        return User(
            id=row["id"],
            username=row["username"],
            email=row["email"],
            password_hash=row["password_hash"],
            password_salt=row["password_salt"],
            # Convert SQLite integer (0/1) to Python boolean
            is_admin=bool(row["is_admin"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def create_user(self, user: User) -> User:
        """
        Create a new user and return the created user with ID and timestamps.

        Return the created user or raise an exception if the user already exists.
        """

        assert user.id is None, "User ID must be None for a new user"
        user.email = user.email.lower()

        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT INTO user (username, email, password_hash, password_salt, is_admin)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user.username, user.email, user.password_hash, user.password_salt, 1 if user.is_admin else 0),
            )
            self.conn.commit()
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed: user.username" in str(e):
                raise UserAlreadyExistsError(f"Username '{user.username}' already exists")
            elif "UNIQUE constraint failed: user.email" in str(e):
                raise UserAlreadyExistsError(f"Email '{user.email}' already exists")
            else:
                raise e

        # Get the created user with all fields
        user_id = cursor.lastrowid
        assert user_id is not None, "Failed to get lastrowid after insert"
        created_user = self.get_user_by_id(user_id)
        if created_user is None:
            raise RuntimeError(f"Failed to retrieve user with ID {user_id} after creating it")
        return created_user

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID, return None if user does not exist."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT id, username, email, password_hash, password_salt, is_admin, created_at, updated_at
            FROM user WHERE id = ?
            """,
            (user_id,),
        )
        row = cursor.fetchone()

        if not row:
            return None

        return self._convert_row_to_user(row)

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username, return None if user does not exist."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT id, username, email, password_hash, password_salt, is_admin, created_at, updated_at
            FROM user WHERE username = ?
            """,
            (username,),
        )
        row = cursor.fetchone()

        if not row:
            return None

        return self._convert_row_to_user(row)

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email (case-insensitive), return None if user does not exist."""
        # Normalize email to lowercase
        email = email.lower()

        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT id, username, email, password_hash, password_salt, is_admin, created_at, updated_at
            FROM user WHERE LOWER(email) = LOWER(?)
            """,
            (email,),
        )
        row = cursor.fetchone()

        if not row:
            return None

        return self._convert_row_to_user(row)

    def list_users(self) -> List[User]:
        """List all users, return empty list if no users exist."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT id, username, email, password_hash, password_salt, is_admin, created_at, updated_at
            FROM user
            """
        )
        rows = cursor.fetchall()

        return [self._convert_row_to_user(row) for row in rows]

    def update_user(
        self,
        user: User,
    ) -> User:
        """
        Update the row, setting all the fields that are set on the user object.

        Calling code should first validate there isn't already a user with the same username or email.
        """
        # First check if user exists
        assert user.id is not None, "User ID must be set to update a user"
        existing_user = self.get_user_by_id(user.id)
        if existing_user is None:
            raise UserNotFoundError(f"User with ID {user.id} not found")

        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                UPDATE user SET
                username = ?,
                email = ?,
                password_hash = ?,
                password_salt = ?,
                is_admin = ?
                WHERE id = ?
                """,
                (user.username, user.email, user.password_hash, user.password_salt, 1 if user.is_admin else 0, user.id),
            )
            self.conn.commit()
        except sqlite3.IntegrityError as e:
            # Handle specific integrity errors
            if "UNIQUE constraint failed: user.username" in str(e):
                raise UserAlreadyExistsError(f"Username '{user.username}' already exists")
            elif "UNIQUE constraint failed: user.email" in str(e):
                raise UserAlreadyExistsError(f"Email '{user.email}' already exists")
            else:
                raise e
        updated_user = self.get_user_by_id(user.id)
        if updated_user is None:
            raise RuntimeError(f"Failed to retrieve user with ID {user.id} after updating it")
        return updated_user

    def delete_user(self, user_id: int) -> None:
        """
        Delete a user by ID, or raise an exception if the user does not exist
        """
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM user WHERE id = ?", (user_id,))
        self.conn.commit()

        if cursor.rowcount == 0:
            raise UserNotFoundError(f"User with ID {user_id} not found")

    def hash_password(self, password: str) -> Tuple[str, str]:
        """
        TOOOD ugh move this out of the user repository
        Hash a password and return the hash and salt.
        """
        # Generate a secure random salt
        salt = secrets.token_hex(16)
        # Combine password with salt and hash
        hash_value = self.password_hasher.hash(password + salt)
        return hash_value, salt

    def verify_password(self, password: str, stored_hash: str, stored_salt: str) -> bool:
        """Verify a password against a stored hash and salt."""
        try:
            self.password_hasher.verify(stored_hash, password + stored_salt)
            return True
        except VerifyMismatchError:
            return False

    def cleanup(self) -> None:
        self.conn.close()


@contextmanager
def user_repository(
    db_path: Path,
) -> Generator[UserRepository, None, None]:
    """Context manager for UserRepository instances."""
    try:
        repo = UserRepository(db_path)
        yield repo
    finally:
        repo.cleanup()
