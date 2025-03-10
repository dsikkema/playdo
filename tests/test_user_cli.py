"""
Integration tests for the user management CLI.
"""

import pytest
from pathlib import Path
import shutil
import tempfile
import sqlite3
from click.testing import CliRunner

from playdo.cli.user_cli import cli


@pytest.fixture
def cli_runner():
    """Create a Click CLI runner."""
    return CliRunner()


@pytest.fixture
def temp_db_path():
    """Create a temporary database file."""
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test.db"

    # Initialize the database with schema
    conn = sqlite3.connect(str(db_path))

    # Read schema from file
    schema_path = Path("schema.sql")
    print(f"Schema path exists: {schema_path.exists()}")

    with open(schema_path, "r") as f:
        schema = f.read()
        print(f"Schema content length: {len(schema)}")

    # Execute schema
    conn.executescript(schema)

    # Verify tables were created
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"Created tables: {tables}")

    conn.close()

    yield db_path

    # Cleanup
    shutil.rmtree(temp_dir)


def test_create_and_list_users(cli_runner, temp_db_path, monkeypatch):
    """Test creating and listing users with the CLI."""
    # Mock getpass to return a known password
    import getpass

    monkeypatch.setattr(getpass, "getpass", lambda prompt: "testpassword123")

    # Set environment variables
    db_path_str = str(temp_db_path)
    print(f"Using database path: {db_path_str}")
    monkeypatch.setenv("PLAYDO_DATABASE_PATH", db_path_str)
    monkeypatch.setenv("PLAYDO_DEBUG", "false")
    monkeypatch.setenv("PLAYDO_TESTING", "true")
    monkeypatch.setenv("PLAYDO_ANTHROPIC_MODEL", "claude-3-haiku-20240307")

    # Verify the database has the user table
    conn = sqlite3.connect(db_path_str)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [table[0] for table in cursor.fetchall()]
    print(f"Tables before CLI call: {tables}")
    conn.close()

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


def test_get_user(cli_runner, temp_db_path, monkeypatch):
    """Test retrieving a user with the CLI."""
    # Mock getpass to return a known password
    import getpass

    monkeypatch.setattr(getpass, "getpass", lambda prompt: "testpassword123")

    # Set environment variables
    db_path_str = str(temp_db_path)
    monkeypatch.setenv("PLAYDO_DATABASE_PATH", db_path_str)
    monkeypatch.setenv("PLAYDO_DEBUG", "false")
    monkeypatch.setenv("PLAYDO_TESTING", "true")
    monkeypatch.setenv("PLAYDO_ANTHROPIC_MODEL", "claude-3-haiku-20240307")

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


def test_update_user(cli_runner, temp_db_path, monkeypatch):
    """Test updating a user with the CLI."""
    # Mock getpass to return a known password
    import getpass

    monkeypatch.setattr(getpass, "getpass", lambda prompt: "testpassword123")

    # Set environment variables
    db_path_str = str(temp_db_path)
    monkeypatch.setenv("PLAYDO_DATABASE_PATH", db_path_str)
    monkeypatch.setenv("PLAYDO_DEBUG", "false")
    monkeypatch.setenv("PLAYDO_TESTING", "true")
    monkeypatch.setenv("PLAYDO_ANTHROPIC_MODEL", "claude-3-haiku-20240307")

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


def test_delete_user(cli_runner, temp_db_path, monkeypatch):
    """Test deleting a user with the CLI."""
    # Mock getpass to return a known password
    import getpass

    monkeypatch.setattr(getpass, "getpass", lambda prompt: "testpassword123")

    # Set environment variables
    db_path_str = str(temp_db_path)
    monkeypatch.setenv("PLAYDO_DATABASE_PATH", db_path_str)
    monkeypatch.setenv("PLAYDO_DEBUG", "false")
    monkeypatch.setenv("PLAYDO_TESTING", "true")
    monkeypatch.setenv("PLAYDO_ANTHROPIC_MODEL", "claude-3-haiku-20240307")

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
