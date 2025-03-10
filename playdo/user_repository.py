"""
This module implements a class for managing users in the database.

The user table is defined in schema.sql.
"""

import logging
import sqlite3
import secrets
from contextlib import contextmanager
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple, Generator, Union
from pathlib import Path

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from playdo.models import User

logger = logging.getLogger("playdo")

# Type alias for parameters to SQLite query
SQLiteParam = Union[str, int, float, None]


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

    def _check_unique_constraints(
        self, conn: sqlite3.Connection, username: Optional[str], email: Optional[str], exclude_id: Optional[int] = None
    ) -> Optional[str]:
        """
        Check if username or email already exist in the database.
        Returns an error message if constraints are violated, None otherwise.
        """
        cursor = conn.cursor()
        # Convert email to lowercase for case-insensitive comparison
        email_lower = email.lower() if email else None

        # Check username uniqueness
        if username:
            if exclude_id is not None:
                cursor.execute("SELECT id, username FROM user WHERE username = ? AND id != ?", (username, exclude_id))
            else:
                cursor.execute("SELECT id, username FROM user WHERE username = ?", (username,))

            existing_user = cursor.fetchone()
            if existing_user:
                return f"Username '{username}' already exists"

        # Check email uniqueness
        if email_lower:
            if exclude_id is not None:
                cursor.execute("SELECT id, email FROM user WHERE LOWER(email) = LOWER(?) AND id != ?", (email_lower, exclude_id))
            else:
                cursor.execute("SELECT id, email FROM user WHERE LOWER(email) = LOWER(?)", (email_lower,))

            existing_email = cursor.fetchone()
            if existing_email:
                return f"Email '{email}' already exists"

        return None

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

    def create_user(
        self, username: str, email: str, password_hash: str, password_salt: str, is_admin: bool = False
    ) -> Tuple[Optional[User], Optional[str]]:
        """
        Create a new user and return the created user with ID and timestamps.
        Returns a tuple of (user, error_message) where:
        - If successful: (User, None)
        - If failed: (None, error_message)
        """
        # Normalize email to lowercase
        email = email.lower()

        with self.get_connection() as conn:
            # Check uniqueness constraints
            error = self._check_unique_constraints(conn, username, email)
            if error:
                return None, error

            try:
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
                user = self.get_user_by_id(user_id)
                return user, None
            except sqlite3.IntegrityError as e:
                # Handle specific integrity errors
                if "UNIQUE constraint failed: user.username" in str(e):
                    return None, f"Username '{username}' already exists"
                elif "UNIQUE constraint failed: user.email" in str(e):
                    return None, f"Email '{email}' already exists"
                else:
                    return None, f"Database integrity error: {str(e)}"
            except sqlite3.Error as e:
                return None, f"Database error: {str(e)}"

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
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
        """Get user by username."""
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
        """Get user by email (case-insensitive)."""
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
        """List all users."""
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

    def update_user(self, user_id: int, updates: Dict[str, Any]) -> Tuple[Optional[User], Optional[str]]:
        """
        Update user fields and return the updated user.
        Returns a tuple of (user, error_message) where:
        - If successful: (User, None)
        - If failed: (None, error_message)
        """
        # First check if user exists
        existing_user = self.get_user_by_id(user_id)
        if not existing_user:
            return None, "User not found"

        # Build UPDATE statement dynamically based on provided fields
        update_fields: List[str] = []
        params: List[SQLiteParam] = []

        # For uniqueness checks
        username_to_check: Optional[str] = None
        email_to_check: Optional[str] = None

        if "username" in updates and updates["username"] is not None:
            username_to_check = str(updates["username"])
            update_fields.append("username = ?")
            params.append(username_to_check)

        if "email" in updates and updates["email"] is not None:
            # Normalize email to lowercase
            email_value = str(updates["email"]).lower()
            email_to_check = email_value
            update_fields.append("email = ?")
            params.append(email_value)

        if "is_admin" in updates and updates["is_admin"] is not None:
            update_fields.append("is_admin = ?")
            # Convert Python boolean to SQLite integer (0/1)
            params.append(1 if updates["is_admin"] else 0)

        if "password_hash" in updates and "password_salt" in updates:
            update_fields.append("password_hash = ?")
            params.append(str(updates["password_hash"]))
            update_fields.append("password_salt = ?")
            params.append(str(updates["password_salt"]))

        if not update_fields:
            return existing_user, None  # No updates to make

        with self.get_connection() as conn:
            # Check uniqueness constraints if updating username or email
            if username_to_check or email_to_check:
                error = self._check_unique_constraints(conn, username_to_check, email_to_check, exclude_id=user_id)
                if error:
                    return None, error

            try:
                # Add user_id to params
                params.append(user_id)

                cursor = conn.cursor()
                cursor.execute(
                    f"""
                    UPDATE user
                    SET {", ".join(update_fields)}, updated_at = current_timestamp
                    WHERE id = ?
                    """,
                    tuple(params),
                )
                conn.commit()

                if cursor.rowcount == 0:
                    return None, "Update failed: no rows affected"

                # Return the updated user
                updated_user = self.get_user_by_id(user_id)
                return updated_user, None
            except sqlite3.IntegrityError as e:
                # Handle specific integrity errors
                if "UNIQUE constraint failed: user.username" in str(e):
                    return None, f"Username '{username_to_check}' already exists"
                elif "UNIQUE constraint failed: user.email" in str(e):
                    return None, f"Email '{email_to_check}' already exists"
                else:
                    return None, f"Database integrity error: {str(e)}"
            except sqlite3.Error as e:
                return None, f"Database error: {str(e)}"

    def delete_user(self, user_id: int) -> Tuple[bool, Optional[str]]:
        """
        Delete a user by ID.
        Returns (success, error_message)
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM user WHERE id = ?", (user_id,))
                conn.commit()

                if cursor.rowcount == 0:
                    return False, "User not found"
                return True, None
        except sqlite3.Error as e:
            return False, f"Database error: {str(e)}"

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
