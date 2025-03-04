# What?

Check out [product-vision.md](product-vision.md) for what it will be.

Current state: chatbot with CLI and REST API support.
Coming Soon:
 - frontend chatbot
 - context-integrated code editor and python runtime in the frontend (Pyodide for WASM Python runtime in the browser)

## Frontend
Frontend repo: [playdo-frontend](https://github.com/dsikkema/playdo-frontend)

# Who?

?

# How?

## CLI
[cli-readme.md](cli-readme.md)

## Backend API
```bash
export PLAYDO_DATABASE_PATH='data/playdo.db'
export PLAYDO_DEBUG='true'
export PLAYDO_DEBUG='false'
export PLAYDO_ANTHROPIC_MODEL='claude-3-haiku-20240307' # or etc
export ANTHROPIC_API_KEY='hackme'


cd backend
./install.sh # create db schema
uv run -m playdo.app
```

See scripts in `curls/` for examples of how to use the api.
