# playdo
A chatbot with great ambitions.

# Installation

```bash
uv sync
./install.sh # for now, just loads the database schema
```

# Usage

```bash
uv run -m playdo.app
```

On running, if no conversations have been created yet, you'll drop straight into a new conversation.

If there are existing conversations, you'll be given a list of them from which you can choose one to resume. Previous messages
will be printed out.

# Current phase:

The current phase of this project is to build a chatloop that allows me to speak with Claude, and save the conversation history to a 
sqlite database, from which conversation history can be retrieved and easily reconstructed. Conversations are indexed by a unique
identifier, which is generated when the conversation starts, and which the user may provide later to resume the conversation.

# Architecture

The project is managed with uv. The dependencies are listed in `pyproject.toml` and all project management
is to be done through native uv commands: `uv sync`, `uv run`, `uv add`, etc. All things `pip` are forbidden.

The conversation history is saved to a sqlite database in `data/app.db`. The schema of the database is stored in `schema.sql`.

Models in `playdo.models` are defined using Pydantic, and are pulled to/from the database with a dedicated repository class.
