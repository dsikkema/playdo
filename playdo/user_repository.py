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

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Get a database connection with row factory set to sqlite3.Row."""
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
        finally:
            connection.close()

    def username_already_exists(self, username: str) -> bool:
        """Check if a username already exists in the database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM user WHERE username = ?", (username,))
            return cursor.fetchone() is not None

    def email_already_exists(self, conn: sqlite3.Connection, email: str) -> bool:
        """
        Check if email already exists in the database.
        """
        cursor = conn.cursor()
        # Convert email to lowercase for case-insensitive comparison
        email_lower = email.lower() if email else None

        # Check email uniqueness
        cursor.execute("SELECT id, email FROM user WHERE LOWER(email) = LOWER(?)", (email_lower,))
        return cursor.fetchone() is not None

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

    def create_user(self, username: str, email: str, password_hash: str, password_salt: str, is_admin: bool = False) -> User:
        """
        Create a new user and return the created user with ID and timestamps.

        Return the created user or raise an exception if the user already exists.
        """
        # Normalize email to lowercase
        email = email.lower()
        if self.username_already_exists(username):
            raise UserAlreadyExistsError(f"Username '{username}' already exists")

        with self.get_connection() as conn:
            if self.email_already_exists(conn, email):
                raise UserAlreadyExistsError(f"Email '{email}' already exists")

            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO user (username, email, password_hash, password_salt, is_admin)
                VALUES (?, ?, ?, ?, ?)
                """,
                (username, email, password_hash, password_salt, 1 if is_admin else 0),
            )
            conn.commit()

            # Get the created user with all fields
            user_id = cursor.lastrowid
            assert user_id is not None, "Failed to get lastrowid after insert"
            created_user = self.get_user_by_id(user_id)
            if created_user is None:
                raise RuntimeError(f"Failed to retrieve user with ID {user_id} after creating it")
            return created_user

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID, return None if user does not exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
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
        with self.get_connection() as conn:
            cursor = conn.cursor()
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

        with self.get_connection() as conn:
            cursor = conn.cursor()
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
        with self.get_connection() as conn:
            cursor = conn.cursor()
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
        *,
        user_id: int,
        username: Optional[str] = None,
        email: Optional[str] = None,
        is_admin: Optional[bool] = None,
        password: Optional[str] = None,
    ) -> User:
        """
        Update user fields and return the updated user, or raise an exception if the user does not exist.

        Password salt is set automatically, and password is taken directly and transformed into a salted hash.
        """
        # First check if user exists
        existing_user = self.get_user_by_id(user_id)
        if not existing_user:
            raise UserNotFoundError(f"User with ID {user_id} not found")

        # Build UPDATE statement dynamically based on provided fields
        update_fields: List[str] = []
        params: List[SQLiteParam] = []

        with self.get_connection() as conn:
            if username is not None and username != existing_user.username:
                if self.username_already_exists(username):
                    raise UserAlreadyExistsError(f"Username '{username}' already exists")
                update_fields.append("username = ?")
                params.append(username)

            if email is not None:
                # Normalize email to lowercase
                email_lower = str(email).lower()
                if email_lower != existing_user.email:
                    if self.email_already_exists(conn, email_lower):
                        raise UserAlreadyExistsError(f"Email '{email}' already exists")
                    update_fields.append("email = ?")
                    params.append(email_lower)

            if is_admin is not None and is_admin != existing_user.is_admin:
                update_fields.append("is_admin = ?")
                # Convert Python boolean to SQLite integer (0/1)
                params.append(1 if is_admin else 0)

            if password is not None:
                password_hash, password_salt = self.hash_password(password)
                update_fields.append("password_hash = ?")
                params.append(password_hash)
                update_fields.append("password_salt = ?")
                params.append(password_salt)

            if not update_fields:
                return existing_user  # No updates to make, return existing user

            try:
                # Add updated_at timestamp
                update_fields.append("updated_at = ?")
                params.append(datetime.now().isoformat())

                # Add user_id to params for the WHERE clause
                params.append(user_id)

                # Build and execute query
                query = f"UPDATE user SET {', '.join(update_fields)} WHERE id = ?"
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()

                # Get and return the updated user
                updated_user = self.get_user_by_id(user_id)
                if updated_user is None:
                    # This should never happen since we verified the user exists
                    raise UserNotFoundError(f"User with ID {user_id} not found after update")
                return updated_user

            except sqlite3.IntegrityError as e:
                # Handle specific integrity errors
                if "UNIQUE constraint failed: user.username" in str(e):
                    raise UserAlreadyExistsError(f"Username '{username}' already exists")
                elif "UNIQUE constraint failed: user.email" in str(e):
                    raise UserAlreadyExistsError(f"Email '{email}' already exists")
                else:
                    raise e

    def delete_user(self, user_id: int) -> None:
        """
        Delete a user by ID, or raise an exception if the user does not exist
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM user WHERE id = ?", (user_id,))
            conn.commit()

            if cursor.rowcount == 0:
                raise UserNotFoundError(f"User with ID {user_id} not found")

    def hash_password(self, password: str) -> Tuple[str, str]:
        """Hash a password and return the hash and salt."""
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


@contextmanager
def user_repository(
    db_path: Path,
) -> Generator[UserRepository, None, None]:
    """Context manager for UserRepository instances."""
    repo = UserRepository(db_path)
    try:
        yield repo
    finally:
        pass  # No cleanup needed, connections are handled per operation
