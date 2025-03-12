"""
Tests for the UserRepository.
"""

import pytest
from playdo.user_repository import UserRepository, UserAlreadyExistsError, UserNotFoundError


def test_create_user(initialized_test_db_path):
    """Test creating a user."""
    # Using initialized_test_db_path fixture from conftest.py
    repo = UserRepository(initialized_test_db_path)

    # Hash a simple password for testing
    password_hash, password_salt = repo.hash_password("testpassword123")

    # Create test user
    user = repo.create_user(
        username="testuser", email="test@example.com", password_hash=password_hash, password_salt=password_salt, is_admin=False
    )

    # Check that user was created successfully
    assert user is not None
    assert user.id is not None
    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert user.is_admin is False
    assert user.password_hash is not None
    assert user.password_salt is not None
    assert user.created_at is not None
    assert user.updated_at is not None


def test_create_user_username_unique(initialized_test_db_path):
    """Test that usernames must be unique."""
    repo = UserRepository(initialized_test_db_path)

    # Hash a simple password for testing
    password_hash, password_salt = repo.hash_password("testpassword123")

    # Create first user
    user1 = repo.create_user(
        username="uniqueuser", email="unique1@example.com", password_hash=password_hash, password_salt=password_salt
    )

    assert user1 is not None

    # Try to create second user with same username
    with pytest.raises(UserAlreadyExistsError) as excinfo:
        repo.create_user(
            username="uniqueuser", email="unique2@example.com", password_hash=password_hash, password_salt=password_salt
        )

    assert "already exists" in str(excinfo.value)


def test_create_user_email_unique_case_insensitive(initialized_test_db_path):
    """Test that emails must be unique, case-insensitive."""
    repo = UserRepository(initialized_test_db_path)

    # Hash a simple password for testing
    password_hash, password_salt = repo.hash_password("testpassword123")

    # Create first user with lowercase email
    user1 = repo.create_user(
        username="emailuser1", email="same@example.com", password_hash=password_hash, password_salt=password_salt
    )

    assert user1 is not None

    # Try to create second user with same email but different case
    with pytest.raises(UserAlreadyExistsError) as excinfo:
        repo.create_user(
            username="emailuser2", email="SAME@example.com", password_hash=password_hash, password_salt=password_salt
        )

    assert "already exists" in str(excinfo.value)


def test_get_user_by_id(initialized_test_db_path):
    """Test retrieving a user by ID."""
    repo = UserRepository(initialized_test_db_path)

    # Create test user
    password_hash, password_salt = repo.hash_password("testpassword123")
    user = repo.create_user(
        username="getbyiduser", email="getbyid@example.com", password_hash=password_hash, password_salt=password_salt
    )

    # Get user by ID
    retrieved_user = repo.get_user_by_id(user.id)

    assert retrieved_user is not None
    assert retrieved_user.id == user.id
    assert retrieved_user.username == "getbyiduser"
    assert retrieved_user.email == "getbyid@example.com"


def test_get_user_by_username(initialized_test_db_path):
    """Test retrieving a user by username."""
    repo = UserRepository(initialized_test_db_path)

    # Create test user
    password_hash, password_salt = repo.hash_password("testpassword123")
    user = repo.create_user(
        username="getbyusername", email="getbyusername@example.com", password_hash=password_hash, password_salt=password_salt
    )

    # Get user by username
    retrieved_user = repo.get_user_by_username("getbyusername")

    assert retrieved_user is not None
    assert retrieved_user.id == user.id
    assert retrieved_user.username == "getbyusername"
    assert retrieved_user.email == "getbyusername@example.com"


def test_get_user_by_email_case_insensitive(initialized_test_db_path):
    """Test retrieving a user by email, case-insensitive."""
    repo = UserRepository(initialized_test_db_path)

    # Create test user
    password_hash, password_salt = repo.hash_password("testpassword123")
    user = repo.create_user(
        username="getbyemail", email="getbyemail@example.com", password_hash=password_hash, password_salt=password_salt
    )

    # Get user by email, different case
    retrieved_user = repo.get_user_by_email("GETBYEMAIL@example.com")

    assert retrieved_user is not None
    assert retrieved_user.id == user.id
    assert retrieved_user.username == "getbyemail"
    assert retrieved_user.email == "getbyemail@example.com"


def test_list_users(initialized_test_db_path):
    """Test listing all users."""
    repo = UserRepository(initialized_test_db_path)

    # Create two test users
    password_hash, password_salt = repo.hash_password("testpassword123")
    repo.create_user(
        username="listuser1", email="listuser1@example.com", password_hash=password_hash, password_salt=password_salt
    )

    repo.create_user(
        username="listuser2", email="listuser2@example.com", password_hash=password_hash, password_salt=password_salt
    )

    # List all users
    users = repo.list_users()

    # Should have at least 2 users (there might be others from previous tests)
    assert len(users) >= 2

    # Verify our test users are in the list
    usernames = [user.username for user in users]
    assert "listuser1" in usernames
    assert "listuser2" in usernames


def test_update_user(initialized_test_db_path):
    """Test updating user details."""
    repo = UserRepository(initialized_test_db_path)

    # Create test user
    password_hash, password_salt = repo.hash_password("testpassword123")
    user = repo.create_user(
        username="updateuser",
        email="updateuser@example.com",
        password_hash=password_hash,
        password_salt=password_salt,
        is_admin=False,
    )

    # Update user with named parameters
    updated_user = repo.update_user(user_id=user.id, username="updateduserid", email="updated@example.com", is_admin=True)

    assert updated_user is not None
    assert updated_user.username == "updateduserid"
    assert updated_user.email == "updated@example.com"
    assert updated_user.is_admin is True


def test_update_user_unique_constraints(initialized_test_db_path):
    """Test that unique constraints are enforced when updating."""
    repo = UserRepository(initialized_test_db_path)

    # Create two test users
    password_hash, password_salt = repo.hash_password("testpassword123")
    # Create first user - variable is used to check its username
    user1 = repo.create_user(
        username="uniqueupdate1", email="uniqueupdate1@example.com", password_hash=password_hash, password_salt=password_salt
    )

    user2 = repo.create_user(
        username="uniqueupdate2", email="uniqueupdate2@example.com", password_hash=password_hash, password_salt=password_salt
    )

    # Try to update user2 with user1's username
    with pytest.raises(UserAlreadyExistsError) as excinfo:
        repo.update_user(user_id=user2.id, username=user1.username)

    assert "already exists" in str(excinfo.value)


def test_delete_user(initialized_test_db_path):
    """Test deleting a user."""
    repo = UserRepository(initialized_test_db_path)

    # Create test user
    password_hash, password_salt = repo.hash_password("testpassword123")
    user = repo.create_user(
        username="deleteuser", email="deleteuser@example.com", password_hash=password_hash, password_salt=password_salt
    )

    # Delete user
    repo.delete_user(user.id)

    # Verify user no longer exists
    deleted_user = repo.get_user_by_id(user.id)
    assert deleted_user is None


def test_delete_user_not_found(initialized_test_db_path):
    """Test deleting a non-existent user."""
    repo = UserRepository(initialized_test_db_path)

    # Try to delete a user that doesn't exist
    with pytest.raises(UserNotFoundError) as excinfo:
        repo.delete_user(999999)

    assert "not found" in str(excinfo.value)


def test_password_verification(initialized_test_db_path):
    """Test password hashing and verification."""
    repo = UserRepository(initialized_test_db_path)

    # Hash a password
    test_password = "MySecurePassword123"
    password_hash, password_salt = repo.hash_password(test_password)

    # Verify correct password
    assert repo.verify_password(test_password, password_hash, password_salt) is True

    # Verify incorrect password
    assert repo.verify_password("WrongPassword123", password_hash, password_salt) is False
