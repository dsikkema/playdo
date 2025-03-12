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
from flask_jwt_extended import jwt_required

from playdo.playdo_app import PlaydoApp
from playdo.response_getter import ResponseGetter
from playdo.models import PlaydoMessage

logger = logging.getLogger(__name__)

conversations_bp = Blueprint("conversations", __name__)


# Type annotation for mypy
def get_app() -> PlaydoApp:
    return cast(PlaydoApp, current_app)


@conversations_bp.route("/conversations", methods=["GET"])
@jwt_required()
def list_conversations() -> ResponseReturnValue:
    """Get a list of all conversation IDs."""
    app = get_app()
    with app.conversation_repository() as conv_repository:
        conversation_ids = conv_repository.get_all_conversation_ids()
    return jsonify({"conversation_ids": conversation_ids})


@conversations_bp.route("/conversations", methods=["POST"])
@jwt_required()
def create_conversation() -> ResponseReturnValue:
    """Create a new conversation."""
    app = get_app()
    with app.conversation_repository() as conv_repository:
        conversation = conv_repository.create_new_conversation()
    return jsonify(conversation.model_dump()), 201


@conversations_bp.route("/conversations/<int:conversation_id>", methods=["GET"])
@jwt_required()
def get_conversation(conversation_id: int) -> ResponseReturnValue:
    """Get a specific conversation with all its messages."""
    app = get_app()
    with app.conversation_repository() as conv_repository:
        try:
            conversation = conv_repository.get_conversation(conversation_id)
        except ValueError:
            return jsonify({"error": f"Conversation with ID {conversation_id} not found"}), 404
    return jsonify(conversation.model_dump())


@conversations_bp.route("/conversations/<int:conversation_id>/send_message", methods=["POST"])
@jwt_required()
def send_new_message(conversation_id: int) -> ResponseReturnValue:
    """
    Send a new message to a conversation.

    The message can include text, code from the editor, and output from running the code.
    """
    if not request.is_json:
        return jsonify({"error": "Missing JSON in request"}), 400

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    text = data.get("message", "")
    editor_code = data.get("editor_code")
    stdout = data.get("stdout")
    stderr = data.get("stderr")

    if not text:
        return jsonify({"error": "Message text is required"}), 400

    # Check that if editor_code is None, both stdout and stderr are also None (no code run)
    if editor_code is None and (stdout is not None or stderr is not None):
        return jsonify({"error": "If editor_code is null, stdout and stderr must also be null"}), 400

    # Both stdout and stderr must be provided together if one is provided
    if (stdout is None) != (stderr is None):
        return jsonify({"error": "Both stdout and stderr must be provided together"}), 400

    user_message = PlaydoMessage.user_message(query=text, editor_code=editor_code, stdout=stdout, stderr=stderr)
    try:
        app = get_app()

        # Save the user message first
        with app.conversation_repository() as repository:
            try:
                # Check if conversation exists
                repository.get_conversation(conversation_id)
            except ValueError:
                return jsonify({"error": f"Conversation with ID {conversation_id} not found"}), 404

            # Save user message
            repository.add_messages_to_conversation(conversation_id, [user_message])

        # Then get complete conversation history with the new user message
        with app.conversation_repository() as repository:
            conversation = repository.get_conversation(conversation_id)

        # Get response from AI
        with app.response_getter() as response_getter:
            assistant_message = response_getter._get_next_assistant_resp(conversation.messages)

        # Save the assistant message
        with app.conversation_repository() as repository:
            repository.add_messages_to_conversation(conversation_id, [assistant_message])

        # Get updated conversation
        with app.conversation_repository() as repository:
            updated_conversation = repository.get_conversation(conversation_id)

        return jsonify(updated_conversation.model_dump())

    except Exception as e:
        logger.exception("Error adding message to conversation")
        return jsonify({"error": f"Error adding message to conversation: {str(e)}"}), 500
