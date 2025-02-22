# playdo, the chatbot
A chatbot with great ambitions.

# Current phase:

The current phase of this project is to build a chatloop that allows me to speak with Claude, and save the conversation history to a 
sqlite database, from which conversation history can be retrieved and easily reconstructed. Conversations are indexed by a unique
identifier, which is generated when the conversation starts, and which the user may provide later to resume the conversation.

# Architecture

The project is managed with uv. The dependencies are listed in `pyproject.toml` and all project management
is to be done through native uv commands: `uv sync`, `uv run`, `uv add`, etc. All things `pip` are forbidden.

The chatloop is implemented in `chatloop.py`. It uses the `anthropic` library to interact with Claude.

The conversation history is saved to a sqlite database, which is implemented in `conversation_history.py`.

The schema of the database is stored in the following schema initialization file: `schema.sql`.

# Usage

To start a new conversation, run `python chatloop.py`. To resume a conversation, run `python chatloop.py --resume <conversation_id>`.

