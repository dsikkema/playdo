"""
Tests for the UserRepository.
"""

import pytest
from playdo.models import User
from playdo.user_repository import UserRepository, UserAlreadyExistsError, UserNotFoundError


def test_create_user(initialized_test_db_path):
    """Test creating a user."""
    # Using initialized_test_db_path fixture from conftest.py
    repo = UserRepository(initialized_test_db_path)

    user = repo.create_user(
        User(
            username="testuser",
            email="test@example.com",
            password_hash="hashbrowns",
            password_salt="salty",
            is_admin=False,
        )
    )

    # Check that user was created successfully
    assert user is not None
    assert user.id is not None
    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert user.is_admin is False
    assert user.password_hash == "hashbrowns"
    assert user.password_salt == "salty"
    assert user.created_at is not None
    assert user.updated_at is not None


def test_create_user_username_unique(initialized_test_db_path):
    """Test that usernames must be unique."""
    repo = UserRepository(initialized_test_db_path)

    # Create first user
    user1 = repo.create_user(
        User(username="uniqueuser", email="unique1@example.com", password_hash="hashbrowns", password_salt="salty")
    )

    assert user1 is not None

    # Try to create second user with same username
    with pytest.raises(UserAlreadyExistsError) as excinfo:
        repo.create_user(
            User(username="uniqueuser", email="unique2@example.com", password_hash="hashbrowns", password_salt="salty")
        )

    assert "already exists" in str(excinfo.value)


def test_create_user_email_unique_case_insensitive(initialized_test_db_path):
    """Test that emails must be unique, case-insensitive."""
    repo = UserRepository(initialized_test_db_path)

    # Create first user with lowercase email
    user1 = repo.create_user(
        User(username="emailuser1", email="same@example.com", password_hash="hashbrowns", password_salt="salty")
    )

    assert user1 is not None

    # Try to create second user with same email but different case
    with pytest.raises(UserAlreadyExistsError) as excinfo:
        repo.create_user(User(username="emailuser2", email="SAME@example.com", password_hash="hashbrowns", password_salt="salty"))

    assert "already exists" in str(excinfo.value)


def test_get_user_by_id(initialized_test_db_path):
    """Test retrieving a user by ID."""
    repo = UserRepository(initialized_test_db_path)

    # Create test user
    user = repo.create_user(
        User(username="getbyiduser", email="getbyid@example.com", password_hash="hashbrowns", password_salt="salty")
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
    user = repo.create_user(
        User(username="getbyusername", email="getbyusername@example.com", password_hash="hashbrowns", password_salt="salty")
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
    user = repo.create_user(
        User(username="getbyemail", email="getbyemail@example.com", password_hash="hashbrowns", password_salt="salty")
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
    repo.create_user(User(username="listuser1", email="listuser1@example.com", password_hash="hashbrowns", password_salt="salty"))

    repo.create_user(User(username="listuser2", email="listuser2@example.com", password_hash="hashbrowns", password_salt="salty"))

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
    user = repo.create_user(
        User(
            username="updateuser",
            email="updateuser@example.com",
            password_hash="hashbrowns",
            password_salt="salty",
            is_admin=False,
        )
    )

    user.username = "updatedusername"
    user.email = "updated@example.com"
    user.is_admin = True

    updated_user = repo.update_user(user)

    assert updated_user is not None
    assert updated_user.username == "updatedusername"
    assert updated_user.email == "updated@example.com"
    assert updated_user.is_admin is True


def test_update_user_unique_constraints(initialized_test_db_path):
    """Test that unique constraints are enforced when updating."""
    repo = UserRepository(initialized_test_db_path)

    # Create two test users
    # Create first user - variable is used to check its username
    user1 = repo.create_user(
        User(username="uniqueupdate1", email="uniqueupdate1@example.com", password_hash="hashbrowns", password_salt="salty")
    )

    user2 = repo.create_user(
        User(username="uniqueupdate2", email="uniqueupdate2@example.com", password_hash="hashbrowns", password_salt="salty")
    )

    # Try to update user2 with user1's username
    with pytest.raises(UserAlreadyExistsError) as excinfo:
        user2.username = user1.username
        repo.update_user(user2)

    assert "already exists" in str(excinfo.value)


def test_delete_user(initialized_test_db_path):
    """Test deleting a user."""
    repo = UserRepository(initialized_test_db_path)

    # Create test user
    user = repo.create_user(
        User(username="deleteuser", email="deleteuser@example.com", password_hash="hashbrowns", password_salt="salty")
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
