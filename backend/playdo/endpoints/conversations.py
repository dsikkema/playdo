from flask import Blueprint, request, jsonify

conversations_bp = Blueprint('conversations', __name__)

@conversations_bp.route('/conversations/new', methods=['POST'])
def new_conversation():
    return jsonify({'message': 'Hello, World!'})