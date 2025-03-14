from contextlib import contextmanager
from pathlib import Path
import secrets
from typing import Optional, Tuple, Generator
from playdo.models import User
from playdo.user_repository import UserRepository, user_repository
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from playdo.validators import validate_password_complexity
from playdo.user_repository import UserAlreadyExistsError


class UserService:
    def __init__(self, user_repo: UserRepository, password_hasher: PasswordHasher):
        self.user_repo = user_repo
        self.password_hasher = password_hasher

    def validate_unique_email(self, existing_user_id: Optional[int], email: str) -> None:
        user_with_email = self.get_user_by_email(email)
        # id is None for the case of creating a user: then, there should be NO user with same email
        # otherwise, user with same email must not be a different user_id
        if user_with_email and (existing_user_id is None or user_with_email.id != existing_user_id):
            raise UserAlreadyExistsError(f"Email {email} already exists.")

    def validate_unique_username(self, existing_user_id: Optional[int], username: str) -> None:
        user_with_username = self.get_user_by_username(username)
        if user_with_username and (existing_user_id is None or user_with_username.id != existing_user_id):
            raise UserAlreadyExistsError(f"Username {username} already exists.")

    def create_user(self, username: str, email: str, is_admin: bool, password: str) -> User:
        """Create a new user with a password."""
        if not validate_password_complexity(password):
            raise ValueError("Password does not meet complexity requirements.")
        self.validate_unique_email(None, email)
        self.validate_unique_username(None, username)
        password_hash, password_salt = self._hash_password(password)
        return self.user_repo.create_user(
            User(username=username, email=email, is_admin=is_admin, password_hash=password_hash, password_salt=password_salt)
        )

    def update_user(
        self,
        existing_user: User,
        new_username: Optional[str],
        new_email: Optional[str],
        new_is_admin: Optional[bool],
        new_password: Optional[str],
    ) -> Optional[User]:
        """Update a user."""
        user_id = existing_user.id
        username = existing_user.username
        email = existing_user.email
        is_admin = existing_user.is_admin
        password_hash = existing_user.password_hash
        password_salt = existing_user.password_salt
        if new_password is not None:
            if not validate_password_complexity(new_password):
                raise ValueError("Password does not meet complexity requirements.")
            password_hash, password_salt = self._hash_password(new_password)
        if new_username is not None:
            username = new_username
            self.validate_unique_username(user_id, username)
        if new_email is not None:
            email = new_email
            self.validate_unique_email(user_id, email)
        if new_is_admin is not None:
            is_admin = new_is_admin

        return self.user_repo.update_user(
            User(
                id=user_id,
                username=username,
                email=email,
                is_admin=is_admin,
                password_hash=password_hash,
                password_salt=password_salt,
            )
        )

    def delete_user(self, id: int) -> None:
        """Delete a user."""
        self.user_repo.delete_user(id)

    def login_user(self, username: str, password: str) -> Optional[User]:
        """
        Login a user and return the user if the password is correct.

        Return None if the user doesn't exist or the password is incorrect.
        """
        user = self.user_repo.get_user_by_username(username)
        if not user:
            return None
        if not self._verify_password(password, user.password_hash, user.password_salt):
            return None
        return user

    def list_users(self) -> list[User]:
        """List all users."""
        return self.user_repo.list_users()

    def get_user_by_id(self, id: int) -> Optional[User]:
        """Get a user by id."""
        return self.user_repo.get_user_by_id(id)

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get a user by username."""
        return self.user_repo.get_user_by_username(username)

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by email."""
        return self.user_repo.get_user_by_email(email)

    def _verify_password(self, password: str, stored_hash: str, stored_salt: str) -> bool:
        """Verify a password against a stored hash and salt."""
        try:
            # Only returns True, and only if it matches. No match -> Exception
            return self.password_hasher.verify(stored_hash, password + stored_salt)
        except VerifyMismatchError:
            return False

    def _hash_password(self, password: str) -> Tuple[str, str]:
        """
        Hash a password and return the hash and salt.
        """
        # Generate a secure random salt
        salt = secrets.token_hex(16)
        # Combine password with salt and hash
        hash_value = self.password_hasher.hash(password + salt)
        return hash_value, salt


@contextmanager
def user_service(db_path: Path) -> Generator[UserService, None, None]:
    """
    This is exposed as a context manager so that it can keep UserRepo in the context manager, so the database
    connection can be cleaned up
    """
    with user_repository(db_path) as user_repo:
        yield UserService(user_repo, PasswordHasher())
