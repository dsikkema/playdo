#!/bin/bash

# Wrapper script for user management CLI
# This script ensures the proper environment for running the user_cli tool

# Check if UV exists
if ! command -v uv &> /dev/null; then
    echo "Error: UV is not installed or not in PATH."
    echo "Please install UV before running this script."
    exit 1
fi

# Run the CLI with proper Python module path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
uv run python -m playdo.cli.user_cli "$@"
