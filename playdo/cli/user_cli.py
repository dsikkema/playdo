"""
Command-line interface for user management.
"""

from argon2 import PasswordHasher
import click
import getpass
import logging
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from playdo.svc.auth_service import AuthService
from playdo.user_repository import UserRepository, UserAlreadyExistsError, UserNotFoundError, user_repository
from playdo.models import User
from playdo.settings import settings

logger = logging.getLogger(__name__)


# Set up logging
def setup_logging() -> None:
    """
    Set up logging for the user management CLI.
    Logs are stored in logs/user_management.log.
    """
    # Create logs directory if it doesn't exist
    logs_dir = settings.LOGS_DIR

    log_file = logs_dir / "user_management.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(log_file), logging.StreamHandler(sys.stdout)],
    )


def backup_users_table(repo: UserRepository) -> Optional[str]:
    """
    Create a backup of the users table.
    Returns the path to the backup file or None if backup failed.
    """
    # Create backup directory if it doesn't exist
    backup_dir = settings.BACKUPS_DIR

    # Generate a timestamp for the filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    backup_file = backup_dir / f"users_backup_{timestamp}.json"

    try:
        # Get all users
        users = repo.list_users()

        # Convert to dict for JSON serialization
        users_dict = [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "password_hash": user.password_hash,
                "password_salt": user.password_salt,
                "is_admin": user.is_admin,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "updated_at": user.updated_at.isoformat() if user.updated_at else None,
            }
            for user in users
        ]

        # Write to backup file
        with open(backup_file, "w") as f:
            json.dump(users_dict, f, indent=2)

        return str(backup_file)
    except Exception as e:
        logging.exception("Backup failed")
        raise e


def validate_password(password: str) -> bool:
    """
    Validate password complexity requirements.
    Password must be at least 12 characters and contain both letters and numbers.
    """
    if len(password) < 12:
        return False
    if not re.search(r"[A-Za-z]", password) or not re.search(r"[0-9]", password):
        return False
    return True


def get_password() -> str:
    """
    Prompt for password with confirmation.
    """
    while True:
        password = getpass.getpass("Enter password: ")

        if not validate_password(password):
            click.echo("Password must be at least 12 characters and contain both letters and numbers.")
            continue

        confirm_password = getpass.getpass("Confirm password: ")
        if password != confirm_password:
            click.echo("Passwords do not match. Please try again.")
            continue

        return password


def format_user_for_display(user: User) -> str:
    """
    Format a user object for display, excluding sensitive fields.
    """
    user_dict = user.to_dict_for_display()
    return "\n".join(sorted([f"{key}: {value}" for key, value in user_dict.items()]))


# CLI group
@click.group()
@click.option("--db-path", default=None, type=click.Path(exists=True, path_type=Path), help="Path to the SQLite database")
def cli(db_path: Optional[Path] = None):
    """
    User management tool for Playdo.

    Allows creation, listing, updating, and deletion of users.
    """
    setup_logging()

    # Get settings
    if db_path is not None:
        settings.DATABASE_PATH = str(db_path)

    # Log CLI invocation (excluding password data)
    server_user = os.environ.get("USER", "unknown")
    command = " ".join(sys.argv)
    logging.info(f"CLI invoked by {server_user}: {command}")


@cli.command()
@click.option("--username", required=True, help="Username (min 4 characters, alphanumeric and underscores only)")
@click.option("--email", required=True, help="Email address")
@click.option("--admin", is_flag=True, help="Grant admin privileges")
@click.option("--force", is_flag=True, help="Skip confirmation prompt")
def create(username: str, email: str, admin: bool, force: bool):
    """
    Create a new user.
    """
    with user_repository(Path(settings.DATABASE_PATH)) as repo:
        # Get password
        password = get_password()

        # Confirm admin creation
        if admin and not force and not click.confirm("Are you sure you want to create an admin user?"):
            click.echo("Operation cancelled.")
            return

        # Create backup before making changes
        backup_file = backup_users_table(repo)
        if backup_file:
            logger.info(f"Backup created at {backup_file}")

        # Hash password
        password_hash, password_salt = AuthService(repo, PasswordHasher()).hash_password(password)

        # Create user
        try:
            user = repo.create_user(
                User(username=username, email=email, password_hash=password_hash, password_salt=password_salt, is_admin=admin)
            )

            # Log activity
            log_fields = f"username={username}, email={email}, is_admin={admin}"
            logger.info(f"User created: id={user.id}, {log_fields}")

            # Display created user
            click.echo("User created successfully:")
            click.echo(format_user_for_display(user))
        except Exception as e:
            click.echo(f"Error: {str(e)}")
            logger.error(f"User creation failed: {str(e)}, fields: username={username}, email={email}, is_admin={admin}")
            return


@cli.command()
def list():
    """
    List all users.
    """
    with user_repository(Path(settings.DATABASE_PATH)) as repo:
        users = repo.list_users()

    if not users:
        click.echo("No users found.")
        return

    click.echo(f"Found {len(users)} users:")
    for user in users:
        click.echo("\n" + format_user_for_display(user))
        click.echo("-" * 40)


@cli.command()
@click.option("--id", type=int, help="User ID")
@click.option("--username", help="Username")
@click.option("--email", help="Email address")
def get(id: Optional[int], username: Optional[str], email: Optional[str]):
    """
    Get user details by ID, username, or email.
    """
    with user_repository(Path(settings.DATABASE_PATH)) as user_repo:
        # Check that exactly one identifier is provided
        identifiers = [i for i in [id, username, email] if i is not None]
        if len(identifiers) != 1:
            click.echo("Error: Please provide exactly one of: --id, --username, or --email")
            return

        # Get user by the provided identifier
        user = None
        if id is not None:
            user = user_repo.get_user_by_id(id)
        elif username is not None:
            user = user_repo.get_user_by_username(username)
        elif email is not None:
            user = user_repo.get_user_by_email(email)

    if not user:
        click.echo("User not found.")
        return

    click.echo("User details:")
    click.echo(format_user_for_display(user))


@cli.command()
@click.option("--id", type=int, required=True, help="ID of the user to update")
@click.option("--username", help="New username")
@click.option("--email", help="New email address")
@click.option("--password", is_flag=True, help="Update password")
@click.option("--admin", type=bool, help="Update admin status (True/False)")
@click.option("--force", is_flag=True, help="Skip confirmation prompt")
def update(id: int, username: Optional[str], email: Optional[str], password: bool, admin: Optional[bool], force: bool):
    """
    Update user details.
    """

    with user_repository(Path(settings.DATABASE_PATH)) as user_repo:
        # Check if at least one field is being updated
        if username is None and email is None and not password and admin is None:
            click.echo("Error: Please provide at least one field to update.")
            return

        # Get existing user
        user = user_repo.get_user_by_id(id)
        if not user:
            click.echo(f"Error: User with ID {id} not found.")
            return

        if email:
            user_with_email = user_repo.get_user_by_email(email)
            if user_with_email:
                if user_with_email.id != id:
                    click.echo(f"Error: another user with email {email} already exists.")
                    return
                else:
                    click.error("Email is the same as existing value.")
                    return

        if username:
            user_with_username = user_repo.get_user_by_username(username)
            if user_with_username:
                if user_with_username.id != id:
                    click.echo(f"Error: another user with username {username} already exists.")
                    return
                else:
                    click.error("Username is the same as existing value.")
                    return

        # Confirm admin status change
        if admin is not None and admin != user.is_admin:
            action = "grant" if admin else "revoke"
            if not force and not click.confirm(f"Are you sure you want to {action} admin privileges for this user?"):
                click.echo("Operation cancelled.")
                return

        # Handle password update
        new_password = None
        if password:
            new_password = get_password()

        # Create backup before making changes
        backup_file = backup_users_table(user_repo)
        if backup_file:
            logger.info(f"Backup created at {backup_file}")

        # Update the user object before saving it
        log_fields = []
        if username is not None:
            user.username = username
            log_fields.append(f"username={username}")
        if email is not None:
            user.email = email
            log_fields.append(f"email={email}")
        if admin is not None:
            user.is_admin = admin
            log_fields.append(f"is_admin={admin}")
        if new_password:
            password_hash, password_salt = AuthService(user_repo, PasswordHasher()).hash_password(new_password)
            user.password_hash = password_hash
            user.password_salt = password_salt
            log_fields.append("password_updated=True")

        log_fields_str = ", ".join(log_fields)

        # Update user
        try:
            updated_user = user_repo.update_user(user)
            logger.info(f"User updated: id={id}, {log_fields_str}")

            # Display updated user
            click.echo("User updated successfully:")
            click.echo(format_user_for_display(updated_user))
        except UserAlreadyExistsError as e:
            click.echo(f"Error: {str(e)}")
            logger.error(f"User update failed: {str(e)}, user_id={id}, fields: {log_fields_str}")
            return
        except UserNotFoundError as e:
            click.echo(f"Error: {str(e)}")
            logger.error(f"User update failed: {str(e)}, user_id={id}, fields: {log_fields_str}")
            return
        except Exception as e:
            click.echo(f"Error: {str(e)}")
            logger.error(f"User update failed: {str(e)}, user_id={id}, fields: {log_fields_str}")
            return


@cli.command()
@click.option("--id", type=int, required=True, help="User ID")
def dummy_login(id: int):
    """
    Dummy command for manually testing password verification.
    """
    password = getpass.getpass("Enter password: ")
    with user_repository(Path(settings.DATABASE_PATH)) as repo:
        user = repo.get_user_by_id(id)
        if not user:
            click.echo(f"Error: User with ID {id} not found.")
            return
        is_valid = AuthService(repo, PasswordHasher()).verify_password(password, user.password_hash, user.password_salt)
    click.echo(f"Password verification result: {is_valid}")


@cli.command()
@click.option("--id", type=int, required=True, help="User ID")
@click.option("--force", is_flag=True, help="Skip confirmation prompt")
def delete(id: int, force: bool):
    """
    Delete a user.
    """
    with user_repository(Path(settings.DATABASE_PATH)) as repo:
        # Get user to display details before deletion
        user = repo.get_user_by_id(id)
        if not user:
            click.echo(f"Error: User with ID {id} not found.")
            return

        # Display user details
        click.echo("User to delete:")
        click.echo(format_user_for_display(user))

        # Confirm deletion
        if not force and not click.confirm("Are you sure you want to delete this user?"):
            click.echo("Operation cancelled.")
            return

        # Create backup before making changes
        backup_file = backup_users_table(repo)
        if backup_file:
            logger.info(f"Backup created at {backup_file}")

        # Delete user
        try:
            repo.delete_user(id)
            logger.info(f"User deleted: id={id}, username={user.username}, email={user.email}")
            click.echo("User deleted successfully.")
        except UserNotFoundError as e:
            click.echo(f"Error: {str(e)}")
            logger.error(f"User deletion failed: {str(e)}, user_id={id}")
        except Exception as e:
            click.echo(f"Error: {str(e)}")
            logger.error(f"User deletion failed: {str(e)}, user_id={id}")


if __name__ == "__main__":
    cli()
