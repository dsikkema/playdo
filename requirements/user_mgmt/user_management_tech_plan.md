# User Management System Technical Specification

## Overview

This specification outlines the implementation of a user management system for the Playdo application, including a new user table in SQLite and a CLI tool for user administration. The system will support basic authentication needs with a focus on simplicity and security, using Argon2 for password hashing and Pydantic for input validation.

## Migration Guide

### Current State

The existing codebase has:
- SQLite database with conversation and message tables
- Flask application structure
- Repository pattern for database operations
- Pydantic models for data validation
- No user authentication system

### Desired State

We need to add:
1. A users table in the SQLite database
2. A CLI tool for user management using Click
3. Password hashing with Argon2
4. Input validation with Pydantic
5. Logging and backup functionality

## Implementation Plan

### Milestone 1: Database Schema Extension

Add the users table to the existing schema:

```sql
-- Add to schema.sql
create table user (
    id integer not null primary key autoincrement, -- explicitly set not null
    username text not null unique,
    email text not null unique,
    password_hash text not null,
    password_salt text not null,
    is_admin integer not null default 0,
    created_at datetime not null default current_timestamp,
    updated_at datetime not null default current_timestamp
);

-- Trigger to update the updated_at timestamp
create trigger update_user_timestamp
after update on user
begin
    update user set updated_at = current_timestamp where id = NEW.id;
end;
```

### Milestone 2: User Model with Validation

Create a Pydantic model for user validation:

```python
# Example model - implement in models.py
from pydantic import BaseModel, EmailStr, validator, Field
import re
from datetime import datetime
from typing import Optional

class User(BaseModel):
    # Primary fields - id may be None during creation but required after
    id: Optional[int] = None
    username: str
    email: EmailStr
    password_hash: str  # Required - stores the Argon2 hash
    password_salt: str  # Required - stores the unique salt
    is_admin: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @validator('username')
    def username_must_be_valid(cls, v):
        # Validate username length
        if len(v) < 4:
            raise ValueError('Username must be at least 4 characters')
        return v

    class Config:
        orm_mode = True

    def to_dict_for_display(self):
        """Return a dictionary suitable for display (excluding sensitive fields)"""
        # Exclude password_hash and password_salt for security when displaying
        data = self.dict(exclude={'password_hash', 'password_salt'})
        return data
```

### Milestone 3: User Repository

Create a repository for user database operations:

```python
# Example repository structure - implement in user_repository.py
from typing import List, Optional, Dict, Any, Tuple
import sqlite3
from contextlib import contextmanager
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import os
import secrets
from datetime import datetime
import re

from .models import User

class UserRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.password_hasher = PasswordHasher()

    @contextmanager
    def get_connection(self):
        # Similar to other repositories
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
        finally:
            connection.close()

    def _check_unique_constraints(self, conn, username: str, email: str, exclude_id: Optional[int] = None) -> Optional[str]:
        """
        Check if username or email already exist in the database.
        Returns an error message if constraints are violated, None otherwise.
        """
        cursor = conn.cursor()
        # Convert email to lowercase for case-insensitive comparison
        email = email.lower() if email else None

        # Check username uniqueness
        query_params = []
        if username:
            query_params.append(username)
        if email:
            query_params.append(email)

        if exclude_id is not None:
            username_query = "SELECT id, username FROM user WHERE username = ? AND id != ?"
            email_query = "SELECT id, email FROM user WHERE LOWER(email) = LOWER(?) AND id != ?"
            username_params = (username, exclude_id)
            email_params = (email, exclude_id)
        else:
            username_query = "SELECT id, username FROM user WHERE username = ?"
            email_query = "SELECT id, email FROM user WHERE LOWER(email) = LOWER(?)"
            username_params = (username,)
            email_params = (email,)

        if username:
            cursor.execute(username_query, username_params)
            existing_user = cursor.fetchone()
            if existing_user:
                return f"Username '{username}' already exists"

        if email:
            cursor.execute(email_query, email_params)
            existing_email = cursor.fetchone()
            if existing_email:
                return f"Email '{email}' already exists"

        return None

    def _convert_row_to_user(self, row) -> User:
        """Convert a database row to a User model instance."""
        return User(
            id=row['id'],
            username=row['username'],
            email=row['email'],
            password_hash=row['password_hash'],
            password_salt=row['password_salt'],
            # Convert SQLite integer (0/1) to Python boolean
            is_admin=bool(row['is_admin']),
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at'])
        )

    def create_user(self, username: str, email: str, password_hash: str, password_salt: str, is_admin: bool = False) -> Tuple[Optional[User], Optional[str]]:
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
                    (username, email, password_hash, password_salt, 1 if is_admin else 0)
                )
                conn.commit()

                # Get the created user with all fields
                user_id = cursor.lastrowid
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
                (user_id,)
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
                (username,)
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
                (email,)
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
        update_fields = []
        params = []

        # For uniqueness checks
        username_to_check = None
        email_to_check = None

        if 'username' in updates and updates['username'] is not None:
            username_to_check = updates['username']
            update_fields.append("username = ?")
            params.append(updates['username'])

        if 'email' in updates and updates['email'] is not None:
            # Normalize email to lowercase
            updates['email'] = updates['email'].lower()
            email_to_check = updates['email']
            update_fields.append("email = ?")
            params.append(updates['email'])

        if 'is_admin' in updates and updates['is_admin'] is not None:
            update_fields.append("is_admin = ?")
            # Convert Python boolean to SQLite integer (0/1)
            params.append(1 if updates['is_admin'] else 0)

        if 'password_hash' in updates and 'password_salt' in updates:
            update_fields.append("password_hash = ?")
            params.append(updates['password_hash'])
            update_fields.append("password_salt = ?")
            params.append(updates['password_salt'])

        if not update_fields:
            return existing_user, None  # No updates to make

        with self.get_connection() as conn:
            # Check uniqueness constraints if updating username or email
            if username_to_check or email_to_check:
                error = self._check_unique_constraints(
                    conn,
                    username_to_check,
                    email_to_check,
                    exclude_id=user_id
                )
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
                    tuple(params)
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

    def hash_password(self, password: str) -> tuple[str, str]:
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
```

#### Implementation Notes

1. **Boolean Handling in SQLite**:
   - SQLite doesn't have a native boolean type, so we store booleans as integers (0/1)
   - When retrieving data, convert integer values to Python booleans using `bool(row['is_admin'])`
   - When storing data, convert Python booleans to integers using `1 if is_admin else 0`
   - The `_convert_row_to_user` helper method handles this conversion consistently

2. **Case-Insensitive Email Handling**:
   - Always convert emails to lowercase before storing in the database: `email = email.lower()`
   - Use `LOWER()` in SQL queries to ensure case-insensitive matching: `WHERE LOWER(email) = LOWER(?)`
   - Apply this consistently in all methods that deal with email: create, update, and get_by_email

3. **Enhanced Error Handling**:
   - All methods that modify data now return tuples containing a result and an error message
   - Specific error handling for unique constraint violations
   - Separate handling for username and email uniqueness errors
   - The `_check_unique_constraints` helper method centralizes constraint checking logic

4. **Uniqueness Validation During Updates**:
   - Added exclusion of the current user ID when checking uniqueness during updates
   - This allows a user to keep their existing username/email while changing other fields
   - The `exclude_id` parameter in `_check_unique_constraints` handles this logic

5. **Database Error Handling**:
   - Catch and handle specific `sqlite3.IntegrityError` exceptions for uniqueness violations
   - Catch broader `sqlite3.Error` exceptions for other database errors
   - Provide clear, specific error messages for different error scenarios

6. **Code Organization**:
   - Helper methods `_check_unique_constraints` and `_convert_row_to_user` reduce code duplication
   - Consistent return values across methods (Tuple[result, error_message])
   - Clear separation between data validation, database operations, and error handling

These changes ensure that the repository properly handles uniqueness constraints, boolean conversion, case-insensitive email comparison, and provides comprehensive error handling.


### Milestone 4: CLI Tool Implementation

Create a standalone script for user management:

```python
# Example structure - implement in user_cli.py
import click
import os
import getpass
import logging
import json
import datetime
from pathlib import Path
from typing import Optional

from .user_repository import UserRepository
from .models import UserCreate, UserUpdate
from .settings import Settings

# Set up logging
def setup_logging():
    # Implementation

# CLI group
@click.group()
@click.option('--db-path', default=None, help='Path to the SQLite database')
@click.pass_context
def cli(ctx, db_path):
    """User management tool for Playdo."""
    setup_logging()
    settings = Settings()
    db_path = db_path or settings.db_path
    ctx.ensure_object(dict)
    ctx.obj['repo'] = UserRepository(db_path)
    ctx.obj['logger'] = logging.getLogger('user_cli')

# Command implementations
@cli.command()
@click.option('--username', required=True, help='Username')
@click.option('--email', required=True, help='Email address')
@click.option('--admin', is_flag=True, help='Grant admin privileges')
@click.pass_context
def create(ctx, username, email, admin):
    """Create a new user."""
    # Implementation

@cli.command()
@click.pass_context
def list(ctx):
    """List all users."""
    # Implementation

@cli.command()
@click.option('--id', type=int, help='User ID')
@click.option('--username', help='Username')
@click.option('--email', help='Email address')
@click.pass_context
def get(ctx, id, username, email):
    """Get user details."""
    # Implementation

@cli.command()
@click.option('--id', type=int, required=True, help='User ID')
@click.option('--username', help='New username')
@click.option('--email', help='New email address')
@click.option('--password', is_flag=True, help='Update password')
@click.option('--admin', type=bool, help='Update admin status')
@click.pass_context
def update(ctx, id, username, email, password, admin):
    """Update user details."""
    # Implementation

@cli.command()
@click.option('--id', type=int, required=True, help='User ID')
@click.pass_context
def delete(ctx, id):
    """Delete a user."""
    # Implementation

def backup_users_table(repo):
    """Create a backup of the users table."""
    # Implementation

if __name__ == '__main__':
    cli()
```

## Detailed Requirements

### 1. User Table Structure

- `id`: Integer, primary key, auto-incrementing
- `username`: Text, unique, minimum 4 characters
- `email`: Text, unique, valid email format
- `password_hash`: Text, containing Argon2 hash
- `password_salt`: Text, containing unique salt for each user
- `is_admin`: Boolean, default false
- `created_at`: Datetime, auto-populated on creation
- `updated_at`: Datetime, auto-updated on changes

### 2. Password Security

- Use `argon2-cffi` for password hashing
- Generate a unique salt for each user
- Store salt and hash separately
- Never store or log plain text passwords
- Hide password input in CLI
- Require confirmation when setting a password

### 3. User Model and Validation

- Use Pydantic for model definitions and validation
- Validate email format
- Validate username (minimum 4 characters)
- Validate password (minimum 12 characters, mix of letters and numbers)
- Different models for creation vs. updates

#### Detailed email/username validation notes

When implementing the User model and repository, pay special attention to these validation requirements:

1. **Username validation**:
   - Username must be at least 4 characters long
   - Username may contain only alphanumeric characters (a-z, A-Z, 0-9) and underscores (_)
   - No spaces or other special characters are allowed
   - The validator in the User model should enforce these rules
   - The repository should check for uniqueness before creating or updating users

2. **Email validation**:
   - Emails must be unique in a case-insensitive manner
   - To enforce this, convert all email addresses to lowercase before saving them to the database
   - When checking for existing emails (for uniqueness validation), also convert the email being checked to lowercase
   - Use Pydantic's EmailStr type for basic email format validation
   - The repository should implement the case-insensitive uniqueness check before creating or updating users
   - Example implementation pattern: `email = email.lower()` before any database operations
   - When querying by email, also convert the search parameter to lowercase: `get_user_by_email(email.lower())`

3. **Additional database constraints**:
   - enforce email uniqueness in the database schema
   - additional to database level, ensure the application logic always converts emails to lowercase before any database operations

The validation must occur both at the Pydantic model level (for format validation) and at the repository level (for uniqueness validation) to ensure data integrity.

### 4. CLI Tool Requirements

- Commands: create, list, get, update, delete
- Confirm destructive operations (admin creation, admin status change, deletion)
- Allow lookup by ID, username, or email (mutually exclusive)
- Update fields individually without requiring all fields
- Hide password and salt in output
- Format output consistently
- Print full user details after creation or update

### 5. Logging

- Log the activities of the CLI tool that create/update/delete users
- Log to `logs/user_management.log`
- Create the logs directory if it doesn't exist
- Log format: timestamp, system username, command, fields affected
- Log create, update, and delete operations: not get

### 6. Backup

- Before destructive operations, back up the users table data
- Store in a dedicated backup directory
- Use millisecond timestamps in filenames
- Only backup data, not schema

### 7. Error Handling

- Display clear error messages for common issues
- Handle database errors gracefully
- Display validation errors from Pydantic

### 8. Testing

- conftest.py already has fixtures for setting up an initialized sqlite3 database. Use that to create integration tests for the CLI tool.

### 9. Password Handling

- Password input and validation occurs in the CLI tool, not in the model
- Passwords should never be stored in the User model
- The CLI tool should:
  - Collect passwords securely via hidden input (stdin)
  - Validate password complexity (12+ chars, mix of letters and numbers)
  - Require confirmation when setting a password (confirm via entering the password twice)
  - Use a dedicated validation function before processing:
    ```python
    def validate_password(password: str) -> bool:
        """Validate password complexity requirements."""
        if len(password) < 12:
            return False
        if not re.search(r'[A-Za-z]', password) or not re.search(r'[0-9]', password):
            return False
        return True
    ```
  - After validation, pass the password to the repository's hash_password method
  - The repository will:
    - Generate a secure salt
    - Hash the password with the salt using argon2-cffi
    - Return both the hash and salt to be stored separately in the database
  - The CLI tool should never log or display the password
  - Passwords should be removed from memory as soon as possible after use
## Guidelines for Integration

When implementing this specification, follow these guidelines:

1. **Repository Pattern**: Follow the existing pattern for database operations.
2. **Context Managers**: Use context managers for resource management.
3. **Type Safety**: Use type hints and Pydantic for runtime type checking.
4. **Consistent API**: Maintain consistency with the existing codebase style.
5. **Separation of Concerns**: Keep model, repository, and CLI logic separate.
6. **Testing**: Write tests for all new functionality.

## Important Considerations

- The CLI tool is for server administrators only, not end users
- The CLI doesn't require authentication itself (security is access to the server)
- No database migrations will be handled by the tool
- The user model will eventually be used with JWT authentication via Flask-JWT-Extended (Note: we are NOT implementing the actual JWT authentication here, just the user management)

## Note to AI Developer

Critically evaluate these suggestions as you implement them. The real codebase might have slightly different names, conventions, or structures than what is proposed here. Intelligently adapt these suggestions to fit the existing codebase rather than blindly following them to the letter.

Remember to follow the existing code standards for linting, typechecking, and tests. The existing rules in the codebase for these aspects should take precedence over any conflicting guidance provided here.
