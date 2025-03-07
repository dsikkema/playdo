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

3. **ResponseGetter** - Interfaces with the Anthropic Claude API to generate AI responses for user messages.

4. **Models** - Pydantic data models that represent conversations, messages, and content blocks, ensuring type safety across the application.

5. **Settings** - Configuration management via environment variables, making the application configurable across different environments.

6. **CLI Interface** - A command-line interface for interacting with the application, useful for testing and development.

## Main Application Structure

Playdo follows a modular architecture

- **app.py** - Entry point for the web application, creates and configures the Flask app.
- **playdo_app.py** - Custom Flask application class with utility methods.
- **endpoints/** - Contains API route definitions organized by domain (conversations).
- **models.py** - Data models for the application using Pydantic.
- **conversation_repository.py** - Database operations for conversations.
- **response_getter.py** - Anthropic Claude API integration.
- **settings.py** - Application configuration via environment variables.
- **db.py** - Database connection management.
- **cli/** - Command-line interface for the application.

## File Structure

```
# python directory structure
playdo
├── __init__.py
├── app.py                         # Main application entry point
├── cli
│   ├── __init__.py
│   ├── cli_app.py                 # CLI application entry point
│   └── historical_conversation.py # Interactive CLI conversation
├── conversation_repository.py     # Database operations for conversations
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
uv.lock                            # Dependency lock file
```

## Data Flow

The typical data flow in Playdo involves:

1. **User Interaction** - The frontend sends user messages to the backend API.

2. **API Processing** - The Flask endpoints receive requests and delegate to appropriate services:
   - Requests for conversation history go to the ConversationRepository
   - Requests for AI responses go first to ConversationRepository to get history, then to ResponseGetter

3. **Database Operations** - ConversationRepository handles storing and retrieving conversations and messages from SQLite.

4. **AI Integration** - ResponseGetter sends conversation history to the Anthropic Claude API and receives AI responses.

5. **Response Delivery** - The API sends responses back to the frontend for display to the user.

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
     <stderr status="not_run" />
   </message>
   ```

3. **Automatic Context Inclusion** - When a student sends a message, their current code and output are automatically included with the message, ensuring the AI tutor has the necessary context without manual sharing.

4. **API Endpoint** - The `/conversations/{id}/send_message` endpoint now accepts:
   ```json
   {
     "message": "User's message text",
     "editor_code": "print('Hello, world!')",
     "stdout": "Hello, world!",
     "stderr": null
   }
   ```

5. **Efficiency** - The XML representation is designed to be token-efficient, using status attributes to indicate when code hasn't been run rather than including redundant explanations.

## Key Design Principles

Playdo follows several key design principles:

1. **Clean Separation of Concerns** - Components have specific responsibilities with minimal overlap.

2. **Repository Pattern** - Database operations are encapsulated in repository classes.

3. **Context Managers** - Resources like database connections are managed with context managers for proper cleanup.

4. **Type Safety** - Extensive use of type hints and Pydantic models for runtime type checking.

5. **Environment-based Configuration** - All configuration is managed via environment variables.

6. **REST API Design** - The backend exposes a RESTful API for the frontend to consume.

7. **Seamless Context Sharing** - The system automatically ensures the AI tutor has the context it needs without the student having to think about it.

## Technical Dependencies

The Playdo backend relies on several key technologies:

1. **Flask** - Web framework for the API.

2. **SQLite** - Lightweight database for storing conversations.

3. **Pydantic** - Data validation and settings management.

4. **Anthropic Claude API** - AI model for generating responses.

5. **UV** - Modern Python package manager used instead of pip.

6. **Ruff** - Fast Python linter used for code quality.

7. **Mypy** - Static type checker for Python.

8. **Pytest** - Testing framework for Python.

## Cursor Rules Reminders:
There are rules in the context window. They contain instructions for the AI writing code about how to properly design tests and verify functionality with
running tests, linters, typecheckers, etc. ALWAYS think about how to properly implement these rules when writing code.
