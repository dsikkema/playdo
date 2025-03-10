# Playdo Backend Technical Notes

## Purpose

This document is principally used to populate the prompt for LLM tools that will generate code. After substantive changes or additions
to functionality, the LLM should also updated this document.

Dear AI, if you're reading this... thanks for all your help and just have fun out there.

## Overview

Playdo is an integrated learning environment for high school students learning Python. The frontend is a React/TypeScript application that provides a code editor, execution environment via Pyodide (WASM), and an AI assistant chat interface.

The backend is a Flask application that provides a REST API for the frontend to interact with.

## Core Components

The Playdo backend consists of several key components:

1. **PlaydoApp** - A custom Flask application class that extends Flask and provides utility methods for accessing repositories and other services.

2. **ConversationRepository** - Manages database operations for storing and retrieving conversations and messages in SQLite.

3. **UserRepository** - Manages database operations for user authentication and management in SQLite.

4. **ResponseGetter** - Interfaces with the Anthropic Claude API to generate AI responses for user messages.

5. **Models** - Pydantic data models that represent conversations, messages, content blocks, and users, ensuring type safety across the application.

6. **Settings** - Configuration management via environment variables, making the application configurable across different environments.

7. **CLI Interface** - A command-line interface for interacting with the application, useful for testing and development.

## Main Application Structure

Playdo follows a modular architecture

- **app.py** - Entry point for the web application, creates and configures the Flask app.
- **playdo_app.py** - Custom Flask application class with utility methods.
- **endpoints/** - Contains API route definitions organized by domain (conversations).
- **models.py** - Data models for the application using Pydantic.
- **conversation_repository.py** - Database operations for conversations.
- **user_repository.py** - Database operations for user management.
- **response_getter.py** - Anthropic Claude API integration.
- **settings.py** - Application configuration via environment variables.
- **db.py** - Database connection management.
- **cli/** - Command-line interface for the application.
  - **user_cli.py** - CLI tool for user management.

## File Structure

```
# python directory structure
playdo
├── __init__.py
├── app.py                         # Main application entry point
├── cli
│   ├── __init__.py
│   ├── cli_app.py                 # CLI application entry point
│   ├── historical_conversation.py # Interactive CLI conversation
│   └── user_cli.py                # User management CLI
├── conversation_repository.py     # Database operations for conversations
├── user_repository.py             # Database operations for users
├── db.py                          # Database utilities
├── endpoints
│   └── conversations.py           # API endpoints for conversations
├── models.py                      # Pydantic data models
├── playdo_app.py                  # Custom Flask application class
├── response_getter.py             # Anthropic Claude API integration
└── settings.py                    # Application configuration

# project root:
 $ ls -1p
ARCHITECTURE.md                    # High-level architecture documentation
DETAILED_TECHNICAL_NOTES.md        # This file
README.md                          # Project overview
bin/                               # Scripts and executables
cli-readme.md                      # CLI documentation
cli_run.sh                         # Script to run the CLI
curls/                             # Example curl commands
data/                              # Data storage directory
install.sh                         # Database installation script
playdo/                            # Main application code
product-vision.md                  # Product vision document
pyproject.toml                     # Python project dependencies
run.sh                             # Script to run the web application
sanity_test.py                     # Basic smoke tests
schema.sql                         # Database schema
tests/                             # Test suite
user_cli.sh                        # Script to run the user management CLI
uv.lock                            # Dependency lock file
```

## Data Flow

The typical data flow in Playdo involves:

1. **User Interaction** - The frontend sends user messages to the backend API.

2. **API Processing** - The Flask endpoints receive requests and delegate to appropriate services:
   - Requests for conversation history go to the ConversationRepository
   - Requests for AI responses go first to ConversationRepository to get history, then to ResponseGetter

3. **Database Operations** - ConversationRepository handles storing and retrieving conversations and messages from SQLite.

4. **Conversation Saving Loop** - The application follows a clear pattern for saving conversations:
   - User message is first saved to the database
   - The complete conversation history (including the newly saved user message) is sent to the ResponseGetter
   - ResponseGetter returns only the assistant's response message
   - Assistant message is then saved to the database
   - This ensures that even if the AI response generation fails, the user's message is still preserved

5. **AI Integration** - ResponseGetter sends conversation history to the Anthropic Claude API and receives AI responses.

6. **Response Delivery** - The API sends responses back to the frontend for display to the user.

## Code Editor Integration

Playdo integrates the code editor with the chat interface, allowing the AI tutor to have context about the student's code and its output:

1. **Message Structure** - Messages now include optional fields for:
   - `editor_code`: The code currently in the editor
   - `stdout`: Standard output from running the code
   - `stderr`: Standard error from running the code

2. **XML Transformation** - User messages with code context are transformed into an XML format when sent to the Claude API:
   ```xml
   <message>
     <text>User's message text</text>
     <code>Python code from editor</code>
     <stdout>Output from running the code</stdout>
     <stderr></stderr>
   </message>
   ```

   Alternately:
   ```xml
   <message>
     <text>User's message text</text>
     <code>Python code from editor (has not been run, therefore no stdout or stderr)</code>
     <stdout status="stale_or_not_run"/>
     <stderr status="stale_or_not_run"/>
   </message>
   ```

3. **Field Validation Rules** - The API enforces specific validation rules for code-related fields:
   - If `editor_code` is null, then `stdout` and `stderr` must also be null (indicating no code change since the last run)
   - If `editor_code` is not null, then `stdout` and `stderr` may still be null (if the user hasn't run the code yet)
   - Empty string values for `editor_code`, `stdout`, or `stderr` are valid and distinct from null values - they represent actual empty strings in these fields
   - A null value indicates absence of data (code not run yet), while an empty string represents an intentional empty value
   - stdout and stderr are "both or neither" - if one is provided, the other must also be provided

4. **Automatic Context Inclusion** - When a student sends a message, their current code and output are automatically included with the message (but only if code content has changed since the last time it was sent), ensuring the AI tutor has the necessary context without manual sharing.

5. **API Endpoint** - The `/conversations/{id}/send_message` endpoint now accepts:
   ```json
   {
     "message": "User's message text",
     "editor_code": "print('Hello, world!')",
     "stdout": "Hello, world!",
     "stderr": ""
   }
   ```

6. **Efficiency** - The XML representation is designed to be token-efficient, using status attributes to indicate when code hasn't been run rather than including redundant explanations.

## User Management System

The Playdo application includes a user management system for authentication and authorization:

1. **User Model** - The User model includes:
   - `id`: Unique identifier for the user
   - `username`: Unique username (alphanumeric and underscores only)
   - `email`: Unique email address (case-insensitive)
   - `password_hash`: Argon2 hash of the user's password
   - `password_salt`: Unique salt for password hashing
   - `is_admin`: Boolean flag for admin privileges
   - `created_at` and `updated_at`: Timestamps for user creation and updates

2. **UserRepository** - This component manages database operations for users:
   - Create, read, update, and delete operations for users
   - Password hashing and verification using Argon2
   - Case-insensitive email uniqueness validation
   - Username uniqueness validation

3. **CLI Tool** - A command-line interface for user management:
   - Create users with secure password handling
   - List all users
   - Get user details by ID, username, or email
   - Update user details (username, email, password, admin status)
   - Delete users
   - Automatic backup of user data before destructive operations
   - Logging of all user management operations

4. **Security Features**:
   - Passwords are never stored in plain text
   - Each user has a unique salt for password hashing
   - Argon2 is used for secure password hashing
   - Password validation ensures strong passwords (12+ characters, mix of letters and numbers)
   - Confirmation required for destructive operations (admin creation, admin status change, deletion)

5. **Usage**:
   - The CLI tool is accessible via the `user_cli.sh` script
   - Commands: create, list, get, update, delete
   - Example: `./user_cli.sh create --username johndoe --email john@example.com`
   - Example: `./user_cli.sh update --id 1 --username newname --email new@example.com --password --admin true`

## Key Design Principles

Playdo follows several key design principles:

1. **Repository Pattern** - Database operations are encapsulated in repository classes.

2. **Context Managers** - Resources like database connections are managed with context managers for proper cleanup.

3. **Type Safety** - Extensive use of type hints and Pydantic models for runtime type checking.

4. **Environment-based Configuration** - All configuration is managed via environment variables.

5. **REST API Design** - The backend exposes a RESTful API for the frontend to consume.

6. **Seamless Context Sharing** - The system automatically ensures the AI tutor has the context it needs without the student having to think about it.

7. **Secure Authentication** - User authentication is handled securely with proper password hashing and validation.

## Technical Dependencies

The Playdo backend relies on several key technologies:

1. **Flask** - Web framework for the API.

2. **SQLite** - Lightweight database for storing conversations and user data.

3. **Pydantic** - Data validation and settings management.

4. **Anthropic Claude API** - AI model for generating responses.

5. **UV** - Modern Python package manager used instead of pip.

6. **Ruff** - Fast Python linter used for code quality.

7. **Mypy** - Static type checker for Python.

8. **Pytest** - Testing framework for Python.

9. **Argon2** - Secure password hashing algorithm.

10. **Click** - Command-line interface toolkit.

## Cursor Rules Reminders:
There are rules in the context window. They contain instructions for the AI writing code about how to properly design tests and verify functionality with
running tests, linters, typecheckers, etc. ALWAYS think about how to properly implement these rules when writing code.

## AI Integration

The Playdo application integrates with the Anthropic Claude API to generate AI responses:

1. **ResponseGetter** - This component is responsible for generating AI responses by sending conversation history to the Claude API:
   - The `_get_next_assistant_resp` method takes a list of conversation messages (including the most recent user message)
   - It converts Playdo's internal message format to Anthropic's format
   - The Claude API returns an assistant response that is converted back to Playdo's format
   - The method returns only the assistant's response message, not a list including both the user's and assistant's messages

2. **Model Conversion Bubble** - The ResponseGetter implements a "bubble" pattern to handle model conversion:
   - PlaydoMessage objects (with editor_code, stdout, stderr fields) enter the bubble
   - Inside the bubble, they are converted to Anthropic's MessageParam objects
   - After receiving the response from Anthropic API, Anthropic Message objects are converted back to PlaydoMessage objects
   - This encapsulation creates a clear boundary around the external API integration, isolating model differences

3. **Conversation Handling** - The new design improves error handling and message management:
   - User messages are saved to the database before calling the AI API, ensuring they're preserved even if the API call fails
   - The complete conversation history (including the newly saved user message) is sent to the ResponseGetter
   - ResponseGetter returns only the assistant's response message
   - The assistant message is then saved to the database separately

4. **Model Conversion** - The code manages conversion between Playdo's internal models and Anthropic's API models:
   - PlaydoMessage objects include additional metadata like editor code and outputs
   - These are converted to Anthropic's MessageParam objects for API requests
   - Anthropic Message objects are converted back to PlaydoMessage objects for internal use
