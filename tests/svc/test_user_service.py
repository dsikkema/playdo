from unittest.mock import MagicMock
from argon2 import PasswordHasher
import pytest
from playdo.svc.user_service import UserService
from playdo.user_repository import UserRepository, UserAlreadyExistsError
from playdo.models import User


def test_create_user():
    """Test user creation with password hashing."""
    # Setup
    mock_user_repo = MagicMock(spec=UserRepository)
    mock_user_repo.create_user.return_value = User(
        id=1,
        username="testuser",
        email="test@example.com",
        is_admin=False,
        password_hash="hashed_password",
        password_salt="salt_value",
    )
    # Mock the get_user methods to return None (no existing users with same username/email)
    mock_user_repo.get_user_by_email.return_value = None
    mock_user_repo.get_user_by_username.return_value = None

    user_service = UserService(mock_user_repo, PasswordHasher())

    # Execute
    test_password = "MySecurePassword123"
    user = user_service.create_user(username="testuser", email="test@example.com", is_admin=False, password=test_password)

    # Verify
    assert user is not None
    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert user.is_admin is False
    # Verify the repository was called with a User object that has hashed password
    mock_user_repo.create_user.assert_called_once()
    created_user = mock_user_repo.create_user.call_args[0][0]
    assert created_user.username == "testuser"
    assert created_user.email == "test@example.com"
    assert created_user.password_hash != test_password  # Password should be hashed
    assert created_user.password_salt is not None
    # Verify the validation methods were called
    mock_user_repo.get_user_by_email.assert_called_once_with("test@example.com")
    mock_user_repo.get_user_by_username.assert_called_once_with("testuser")


def test_create_user_with_existing_email():
    """Test user creation fails when email already exists."""
    # Setup
    mock_user_repo = MagicMock(spec=UserRepository)
    # Mock the get_user_by_email to return an existing user
    mock_user_repo.get_user_by_email.return_value = User(
        id=1,
        username="existinguser",
        email="test@example.com",
        is_admin=False,
        password_hash="existing_hash",
        password_salt="existing_salt",
    )
    mock_user_repo.get_user_by_username.return_value = None

    user_service = UserService(mock_user_repo, PasswordHasher())

    # Execute & Verify
    with pytest.raises(UserAlreadyExistsError, match="Email test@example.com already exists"):
        user_service.create_user(username="newuser", email="test@example.com", is_admin=False, password="MySecurePassword123")

    # Verify repository was not called for creation
    mock_user_repo.create_user.assert_not_called()


def test_create_user_with_existing_username():
    """Test user creation fails when username already exists."""
    # Setup
    mock_user_repo = MagicMock(spec=UserRepository)
    # Mock the get_user_by_username to return an existing user
    mock_user_repo.get_user_by_email.return_value = None
    mock_user_repo.get_user_by_username.return_value = User(
        id=1,
        username="testuser",
        email="existing@example.com",
        is_admin=False,
        password_hash="existing_hash",
        password_salt="existing_salt",
    )

    user_service = UserService(mock_user_repo, PasswordHasher())

    # Execute & Verify
    with pytest.raises(UserAlreadyExistsError, match="Username testuser already exists"):
        user_service.create_user(username="testuser", email="new@example.com", is_admin=False, password="MySecurePassword123")

    # Verify repository was not called for creation
    mock_user_repo.create_user.assert_not_called()


def test_create_user_with_weak_password():
    """Test user creation with a weak password that should be rejected."""
    mock_user_repo = MagicMock(spec=UserRepository)
    mock_user_repo.get_user_by_email.return_value = None
    mock_user_repo.get_user_by_username.return_value = None

    user_service = UserService(mock_user_repo, PasswordHasher())

    # Weak password
    with pytest.raises(ValueError, match="Password does not meet complexity requirements"):
        user_service.create_user(username="testuser", email="test@example.com", is_admin=False, password="weak")

    # Verify repository was not called
    mock_user_repo.create_user.assert_not_called()


def test_update_user():
    """Test updating a user's details."""
    # Setup
    mock_user_repo = MagicMock(spec=UserRepository)

    # Return None for email/username checks (no conflicts)
    mock_user_repo.get_user_by_email.return_value = None
    mock_user_repo.get_user_by_username.return_value = None

    # Mock the update_user method to return a successfully updated user
    mock_user_repo.update_user.return_value = User(
        id=1,
        username="newusername",
        email="new@example.com",
        is_admin=True,
        password_hash="updated_hash",
        password_salt="updated_salt",
    )

    user_service = UserService(mock_user_repo, PasswordHasher())

    # Existing user to update
    existing_user = User(
        id=1,
        username="oldusername",
        email="old@example.com",
        is_admin=False,
        password_hash="old_hash",
        password_salt="old_salt",
    )

    # Execute
    updated_user = user_service.update_user(
        existing_user=existing_user,
        new_username="newusername",
        new_email="new@example.com",
        new_is_admin=True,
        new_password="MyNewSecurePassword123",
    )

    # Verify
    assert updated_user is not None
    assert updated_user.id == 1
    assert updated_user.username == "newusername"
    assert updated_user.email == "new@example.com"
    assert updated_user.is_admin is True

    # Verify update_user was called with correct user object
    mock_user_repo.update_user.assert_called_once()
    user_obj = mock_user_repo.update_user.call_args[0][0]
    assert user_obj.id == 1
    assert user_obj.username == "newusername"
    assert user_obj.email == "new@example.com"
    assert user_obj.is_admin is True
    assert user_obj.password_hash != "old_hash"  # Password should be updated
    assert user_obj.password_salt != "old_salt"  # Salt should be updated

    # Verify validation methods were called
    mock_user_repo.get_user_by_email.assert_called_once_with("new@example.com")
    mock_user_repo.get_user_by_username.assert_called_once_with("newusername")


def test_update_user_email_conflict():
    """Test updating a user fails when the new email conflicts with another user."""
    # Setup
    mock_user_repo = MagicMock(spec=UserRepository)

    # Mock email conflict
    mock_user_repo.get_user_by_email.return_value = User(
        id=2,  # Different ID than our existing user (important!)
        username="otheruser",
        email="new@example.com",
        is_admin=False,
        password_hash="other_hash",
        password_salt="other_salt",
    )

    user_service = UserService(mock_user_repo, PasswordHasher())

    # Existing user to update
    existing_user = User(
        id=1,
        username="testuser",
        email="old@example.com",
        is_admin=False,
        password_hash="old_hash",
        password_salt="old_salt",
    )

    # Execute & Verify
    with pytest.raises(UserAlreadyExistsError, match="Email new@example.com already exists"):
        user_service.update_user(
            existing_user=existing_user, new_username=None, new_email="new@example.com", new_is_admin=None, new_password=None
        )

    # Verify update_user was not called
    mock_user_repo.update_user.assert_not_called()


def test_login_user_success():
    """Test successful user login."""
    # Setup
    mock_user_repo = MagicMock(spec=UserRepository)
    password_hasher = PasswordHasher()
    user_service = UserService(mock_user_repo, password_hasher)

    # Create a password/salt/hash combination that will verify correctly
    test_password = "MySecurePassword123"
    password_salt = "test_salt"
    password_hash = password_hasher.hash(test_password + password_salt)

    # Configure mock to return a user with the hashed password
    mock_user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        is_admin=False,
        password_hash=password_hash,
        password_salt=password_salt,
    )
    mock_user_repo.get_user_by_username.return_value = mock_user

    # Execute
    logged_in_user = user_service.login_user("testuser", test_password)

    # Verify
    assert logged_in_user is not None
    assert logged_in_user.id == 1
    assert logged_in_user.username == "testuser"
    mock_user_repo.get_user_by_username.assert_called_once_with("testuser")


def test_login_user_wrong_password():
    """Test login with wrong password."""
    # Setup
    mock_user_repo = MagicMock(spec=UserRepository)
    password_hasher = PasswordHasher()
    user_service = UserService(mock_user_repo, password_hasher)

    # Create a password/salt/hash combination
    test_password = "MySecurePassword123"
    password_salt = "test_salt"
    password_hash = password_hasher.hash(test_password + password_salt)

    # Configure mock to return a user with the hashed password
    mock_user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        is_admin=False,
        password_hash=password_hash,
        password_salt=password_salt,
    )
    mock_user_repo.get_user_by_username.return_value = mock_user

    # Execute with wrong password
    logged_in_user = user_service.login_user("testuser", "WrongPassword123")

    # Verify
    assert logged_in_user is None
    mock_user_repo.get_user_by_username.assert_called_once_with("testuser")


def test_login_user_nonexistent_user():
    """Test login with a username that doesn't exist."""
    # Setup
    mock_user_repo = MagicMock(spec=UserRepository)
    mock_user_repo.get_user_by_username.return_value = None

    user_service = UserService(mock_user_repo, PasswordHasher())

    # Execute
    logged_in_user = user_service.login_user("nonexistent", "AnyPassword123")

    # Verify
    assert logged_in_user is None
    mock_user_repo.get_user_by_username.assert_called_once_with("nonexistent")


def test_delete_user():
    """Test deleting a user."""
    # Setup
    mock_user_repo = MagicMock(spec=UserRepository)
    user_service = UserService(mock_user_repo, PasswordHasher())

    # Execute
    user_service.delete_user(1)

    # Verify
    mock_user_repo.delete_user.assert_called_once_with(1)


def test_get_user_methods():
    """Test the get_user convenience methods."""
    # Setup
    mock_user_repo = MagicMock(spec=UserRepository)
    mock_user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        is_admin=False,
        password_hash="hash",
        password_salt="salt",
    )

    # Configure mocks to return our test user
    mock_user_repo.get_user_by_id.return_value = mock_user
    mock_user_repo.get_user_by_username.return_value = mock_user
    mock_user_repo.get_user_by_email.return_value = mock_user
    mock_user_repo.list_users.return_value = [mock_user]

    user_service = UserService(mock_user_repo, PasswordHasher())

    # Execute and verify each method
    assert user_service.get_user_by_id(1) == mock_user
    mock_user_repo.get_user_by_id.assert_called_once_with(1)

    assert user_service.get_user_by_username("testuser") == mock_user
    mock_user_repo.get_user_by_username.assert_called_once_with("testuser")

    assert user_service.get_user_by_email("test@example.com") == mock_user
    mock_user_repo.get_user_by_email.assert_called_once_with("test@example.com")

    assert user_service.list_users() == [mock_user]
    mock_user_repo.list_users.assert_called_once()


def test_update_user_with_weak_password():
    """Test updating a user with a weak password that should be rejected."""
    # Setup
    mock_user_repo = MagicMock(spec=UserRepository)
    user_service = UserService(mock_user_repo, PasswordHasher())

    existing_user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        is_admin=False,
        password_hash="old_hash",
        password_salt="old_salt",
    )

    # Execute & Verify
    with pytest.raises(ValueError, match="Password does not meet complexity requirements"):
        user_service.update_user(
            existing_user=existing_user, new_username=None, new_email=None, new_is_admin=None, new_password="weak"
        )

    # Verify update_user was not called
    mock_user_repo.update_user.assert_not_called()
