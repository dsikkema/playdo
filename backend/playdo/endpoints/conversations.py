from flask import Blueprint, jsonify
from flask.typing import ResponseReturnValue

conversations_bp = Blueprint("conversations", __name__)


@conversations_bp.route("/conversations/new", methods=["POST"])
def new_conversation() -> ResponseReturnValue:
    return jsonify({"message": "Hello, World!"})
