"""
TOODO:
 - proper response types
 - autogenerate OpenAPI schema
"""

from typing import cast
import logging
from flask import Blueprint, jsonify, request, current_app
from flask.typing import ResponseReturnValue
import sqlite3

from playdo.playdo_app import PlaydoApp
from playdo.response_getter import ResponseGetter
from playdo.models import PlaydoMessage

logger = logging.getLogger(__name__)

conversations_bp = Blueprint("conversations", __name__)


# Type annotation for mypy
def get_app() -> PlaydoApp:
    return cast(PlaydoApp, current_app)


@conversations_bp.route("/conversations", methods=["GET"])
def list_conversations() -> ResponseReturnValue:
    """Get a list of all conversation IDs."""
    app = get_app()
    with app.conversation_repository() as conv_repository:
        conversation_ids = conv_repository.get_all_conversation_ids()
    return jsonify({"conversation_ids": conversation_ids})


@conversations_bp.route("/conversations", methods=["POST"])
def create_conversation() -> ResponseReturnValue:
    """Create a new conversation."""
    app = get_app()
    with app.conversation_repository() as conv_repository:
        conversation = conv_repository.create_new_conversation()
    return jsonify(conversation.model_dump()), 201


@conversations_bp.route("/conversations/<int:conversation_id>", methods=["GET"])
def get_conversation(conversation_id: int) -> ResponseReturnValue:
    """Get a specific conversation with all its messages."""
    app = get_app()
    with app.conversation_repository() as conv_repository:
        try:
            conversation = conv_repository.get_conversation(conversation_id)
            return jsonify(conversation.model_dump())
        except ValueError:
            return jsonify({"error": f"Conversation with id {conversation_id} not found"}), 404


@conversations_bp.route("/conversations/<int:conversation_id>/send_message", methods=["POST"])
def send_new_message(conversation_id: int) -> ResponseReturnValue:
    """
    Add a user message to a conversation and get the assistant's response.

    The request JSON should contain:
    - message: The user's message text (required)
    - editor_code: The code in the editor (optional)
    - stdout: Standard output from running the code (optional)
    - stderr: Standard error from running the code (optional)
    """
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()
    if not data or "message" not in data:
        return jsonify({"error": "Missing 'message' field"}), 400

    user_message = data["message"]
    editor_code = data.get("editor_code")  # Optional
    stdout = data.get("stdout")  # Optional
    stderr = data.get("stderr")  # Optional

    logger.debug(f"User message: {user_message}")
    if editor_code is not None:
        logger.debug(f"Editor code included (length: {len(editor_code)})")
    if stdout is not None:
        logger.debug(f"Stdout included (length: {len(stdout)})")
    if stderr is not None:
        logger.debug(f"Stderr included (length: {len(stderr)})")

    app = get_app()
    with app.conversation_repository() as conv_repository:
        response_getter = ResponseGetter()
        try:
            # Get the existing conversation
            conversation = conv_repository.get_conversation(conversation_id)
            logger.debug(f"Conversation: {conversation.model_dump()}")

            # Create user message with code context
            user_msg = PlaydoMessage.user_message(query=user_message, editor_code=editor_code, stdout=stdout, stderr=stderr)

            # Get the assistant's response (using the existing conversation messages plus our new user message)
            new_messages = response_getter._get_next_assistant_resp(conversation.messages, user_message)

            # Replace the auto-generated user message with our version that includes code context
            new_messages[0] = user_msg

            logger.debug(f"New messages: {new_messages}")
            # Save the new messages
            updated_conversation = conv_repository.add_messages_to_conversation(conversation_id, new_messages)
            logger.debug(f"Updated conversation: {updated_conversation.model_dump()}")
            # Return the updated conversation with the new messages
            return jsonify(updated_conversation.model_dump())
        except ValueError as e:
            logger.exception(e)
            return jsonify({"error": f"Conversation with id {conversation_id} not found"}), 404
        except sqlite3.Error as e:
            logger.exception(e)
            return jsonify({"error": "sorry"}), 500
