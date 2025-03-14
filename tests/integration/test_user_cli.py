"""
Integration tests for the user management CLI.
"""

import pytest
from click.testing import CliRunner

from playdo.cli.user_cli import cli


@pytest.fixture
def cli_runner():
    """Create a Click CLI runner."""
    return CliRunner()


def test_create_and_list_users(cli_runner, initialized_test_db_path, monkeypatch):
    """Test creating and listing users with the CLI."""
    # Mock getpass to return a known password
    import getpass

    monkeypatch.setattr(getpass, "getpass", lambda prompt: "testpassword123")

    # Set environment variables
    db_path_str = str(initialized_test_db_path)
    print(f"Using database path: {db_path_str}")

    # Create a user with explicit db_path
    result = cli_runner.invoke(
        cli,
        ["--db-path", db_path_str, "create", "--username", "cliuser", "--email", "cli@example.com"],
        input="y\n",  # Confirm password
    )

    # Print the full output for debugging
    print(f"CLI output: {result.output}")
    print(f"CLI exit code: {result.exit_code}")
    print(f"CLI exception: {result.exception}")

    # Check command succeeded
    assert result.exit_code == 0, f"Command failed with output: {result.output}"
    assert "User created successfully" in result.output

    # List users with explicit db_path
    result = cli_runner.invoke(cli, ["--db-path", db_path_str, "list"])

    # Check command succeeded and shows our user
    assert result.exit_code == 0
    assert "cliuser" in result.output
    assert "cli@example.com" in result.output


def test_get_user(cli_runner, initialized_test_db_path, monkeypatch):
    """Test retrieving a user with the CLI."""
    # Mock getpass to return a known password
    import getpass

    monkeypatch.setattr(getpass, "getpass", lambda prompt: "testpassword123")

    # Set environment variables
    db_path_str = str(initialized_test_db_path)

    # Create a user first with explicit db_path
    result = cli_runner.invoke(
        cli,
        ["--db-path", db_path_str, "create", "--username", "getuser", "--email", "get@example.com"],
        input="y\n",  # Confirm password
    )

    assert result.exit_code == 0, f"User creation failed with output: {result.output}"

    # Get user by username with explicit db_path
    result = cli_runner.invoke(cli, ["--db-path", db_path_str, "get", "--username", "getuser"])

    # Check command succeeded and shows our user
    assert result.exit_code == 0
    assert "getuser" in result.output
    assert "get@example.com" in result.output


def test_update_user(cli_runner, initialized_test_db_path, monkeypatch):
    """Test updating a user with the CLI."""
    # Mock getpass to return a known password
    import getpass

    monkeypatch.setattr(getpass, "getpass", lambda prompt: "testpassword123")

    # Set environment variables
    db_path_str = str(initialized_test_db_path)

    # Create a user first with explicit db_path
    result = cli_runner.invoke(
        cli,
        ["--db-path", db_path_str, "create", "--username", "updateme", "--email", "update@example.com"],
        input="y\n",  # Confirm password
    )

    assert result.exit_code == 0, f"User creation failed with output: {result.output}"

    # Get user ID from output
    output_lines = result.output.split("\n")
    id_line = next(line for line in output_lines if "id:" in line)
    user_id = int(id_line.split(":")[1].strip())

    # Update user with explicit db_path
    result = cli_runner.invoke(
        cli,
        ["--db-path", db_path_str, "update", "--id", str(user_id), "--username", "updated", "--email", "updated@example.com"],
    )

    # Check command succeeded
    assert result.exit_code == 0
    assert "User updated successfully" in result.output
    assert "updated" in result.output
    assert "updated@example.com" in result.output


def test_delete_user(cli_runner, initialized_test_db_path, monkeypatch):
    """Test deleting a user with the CLI."""
    # Mock getpass to return a known password
    import getpass

    monkeypatch.setattr(getpass, "getpass", lambda prompt: "testpassword123")

    # Set environment variables
    db_path_str = str(initialized_test_db_path)

    # Create a user first with explicit db_path
    result = cli_runner.invoke(
        cli,
        ["--db-path", db_path_str, "create", "--username", "deleteme", "--email", "delete@example.com"],
        input="y\n",  # Confirm password
    )

    assert result.exit_code == 0, f"User creation failed with output: {result.output}"

    # Get user ID from output
    output_lines = result.output.split("\n")
    id_line = next(line for line in output_lines if "id:" in line)
    user_id = int(id_line.split(":")[1].strip())

    # Delete user with explicit db_path
    result = cli_runner.invoke(
        cli,
        ["--db-path", db_path_str, "delete", "--id", str(user_id), "--force"],
    )

    # Check command succeeded
    assert result.exit_code == 0
    assert "User deleted successfully" in result.output

    # Verify user no longer exists with explicit db_path
    result = cli_runner.invoke(cli, ["--db-path", db_path_str, "get", "--id", str(user_id)])
    assert "User not found" in result.output
