# What?

Check out [product-vision.md](product-vision.md) for what it will be.

Current state: chatbot with CLI and REST API support.
Coming Soon:
 - frontend chatbot
 - context-integrated code editor and python runtime in the frontend (Pyodide for WASM Python runtime in the browser)

# Who?

?

# How?

## CLI
[backend/README.md](backend/README.md)

## Backend API
toodo write dedicated readme
```bash
export PLAYDO_DATABASE_PATH='data/playdo.db'
export PLAYDO_DEBUG='true'
export PLAYDO_ANTHROPIC_MODEL='claude-3-haiku-20240307' # or etc
export ANTHROPIC_API_KEY='hackme'


cd backend
./install.sh # create db schema
uv run -m playdo.app
```

See scripts in `backend/curls` for examples of how to use the api.

## Frontend

[frontend/README.md](frontend/README.md)
