# playdo
A chatbot with great ambitions.

# Installation

required environment variables:
```bash
export ANTHROPIC_API_KEY=nicetryhackers
```

```bash
uv sync
./install.sh # for now, just loads the database schema
```

# CLI Usage

```bash
uv run -m playdo.cli.cli_app
```

```
 $ uv run -m playdo.app
Available conversations:
1
2
3
4
Enter the number of the conversation to load (or press Enter for new):
You're in a brand new conversation: ID=5
Enter your message (Ctrl-D to finish):
Hello, world.
^D
Assistant: Hi! How can I help you today?

Enter your message (Ctrl-D to finish):
^C
Input interrupted
. . . .

 $ uv run -m playdo.app
Available conversations:
1
2
3
4
5
Enter the number of the conversation to load (or press Enter for new): 5
Conversation history:
user: Hello, world.

assistant: Hi! How can I help you today?
Enter your message (Ctrl-D to finish):
Sorry, the line got dropped. Anyway, please list two or three flowers that go nicely with white roses in a bouquet.
^D
Assistant: Pink carnations, baby's breath (gypsophila), and purple statice all complement white roses well in bouquets. Baby's breath in particular is a classic pairing with white roses, adding a delicate, airy quality to the arrangement. Pink carnations provide a nice color contrast while maintaining an elegant look, and purple statice adds both color and interesting texture.
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
