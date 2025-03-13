from unittest.mock import MagicMock
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError
import pytest
from playdo.svc.auth_service import AuthService
from playdo.user_repository import UserRepository


def test_password_verification(initialized_test_db_path):
    """Test password hashing and verification."""
    mock_user_repo = MagicMock(spec=UserRepository)
    auth_service = AuthService(mock_user_repo, PasswordHasher())

    # Hash a password
    test_password = "MySecurePassword123"
    password_hash, password_salt = auth_service.hash_password(test_password)

    # correct password
    assert auth_service.verify_password(test_password, password_hash, password_salt) is True

    # incorrect password
    assert auth_service.verify_password("WrongPassword123", password_hash, password_salt) is False

    # wrong salt
    assert auth_service.verify_password(test_password, password_hash, "wrong_salt") is False

    # wrong hash
    wrong_hash, _ = auth_service.hash_password("no")
    assert auth_service.verify_password(test_password, wrong_hash, password_salt) is False

    # invalid hash
    with pytest.raises(InvalidHashError):
        auth_service.verify_password(
            test_password, "This string, well, it's clearly NOT the right format for a hash.", password_salt
        )
