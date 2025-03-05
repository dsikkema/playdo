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

logger = logging.getLogger(__name__)

conversations_bp = Blueprint("conversations", __name__)

current_app = cast(PlaydoApp, current_app)  # typing enables jump-to-definition


@conversations_bp.route("/conversations", methods=["GET"])
def list_conversations() -> ResponseReturnValue:
    """Get a list of all conversation IDs."""
    with current_app.conversation_repository() as conv_repository:
        conversation_ids = conv_repository.get_all_conversation_ids()
    return jsonify({"conversation_ids": conversation_ids})


@conversations_bp.route("/conversations", methods=["POST"])
def create_conversation() -> ResponseReturnValue:
    """Create a new conversation."""
    with current_app.conversation_repository() as conv_repository:
        conversation = conv_repository.create_new_conversation()
    return jsonify(conversation.model_dump()), 201


@conversations_bp.route("/conversations/<int:conversation_id>", methods=["GET"])
def get_conversation(conversation_id: int) -> ResponseReturnValue:
    """Get a specific conversation with all its messages."""
    with current_app.conversation_repository() as conv_repository:
        try:
            conversation = conv_repository.get_conversation(conversation_id)
            return jsonify(conversation.model_dump())
        except ValueError:
            return jsonify({"error": f"Conversation with id {conversation_id} not found"}), 404


@conversations_bp.route("/conversations/<int:conversation_id>/send_message", methods=["POST"])
def send_new_message(conversation_id: int) -> ResponseReturnValue:
    """Add a user message to a conversation and get the assistant's response."""
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()
    if not data or "message" not in data:
        return jsonify({"error": "Missing 'message' field"}), 400

    user_message = data["message"]
    logger.debug(f"User message: {user_message}")

    with current_app.conversation_repository() as conv_repository:
        response_getter = ResponseGetter()
        try:
            # Get the existing conversation
            conversation = conv_repository.get_conversation(conversation_id)
            logger.debug(f"Conversation: {conversation.model_dump()}")

            # Get the assistant's response
            new_messages = response_getter._get_next_assistant_resp(conversation.messages, user_message)
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
