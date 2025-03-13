import secrets
from typing import Optional, Tuple
from playdo.models import User
from playdo.user_repository import UserRepository
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError


class AuthService:
    def __init__(self, user_repo: UserRepository, password_hasher: PasswordHasher):
        self.user_repo = user_repo
        self.password_hasher = password_hasher

    def login_user(self, username: str, password: str) -> Optional[User]:
        """
        Login a user and return the user if the password is correct.

        Return None if the user doesn't exist or the password is incorrect.
        """
        user = self.user_repo.get_user_by_username(username)
        if not user:
            return None
        if not self.verify_password(password, user.password_hash, user.password_salt):
            return None
        return user

    def hash_password(self, password: str) -> Tuple[str, str]:
        """
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
            # Only returns True, and only if it matches. No match -> Exception
            return self.password_hasher.verify(stored_hash, password + stored_salt)
        except VerifyMismatchError:
            return False
