"""
Authentication endpoints for the Playdo API.

Provides login functionality using flask-jwt-extended for JWT authentication.
"""

import logging
from typing import cast
from flask import Blueprint, jsonify, request, current_app
from flask.typing import ResponseReturnValue
from flask_jwt_extended import create_access_token

from playdo.playdo_app import PlaydoApp

logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth", __name__)


# Type annotation for mypy
def get_app() -> PlaydoApp:
    return cast(PlaydoApp, current_app)


@auth_bp.route("/login", methods=["POST"])
def login() -> ResponseReturnValue:
    """
    Login endpoint to authenticate users and generate JWT tokens.

    Expected request body:
    {
        "username": "string",
        "password": "string"
    }

    Returns:
    {
        "access_token": "string"
    }
    """
    if not request.is_json:
        return jsonify({"error": "Missing JSON in request"}), 400

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    username = data.get("username", None)
    password = data.get("password", None)

    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400

    app = get_app()
    with app.user_repository() as repo:
        # Get user by username
        user = repo.get_user_by_username(username)

        if not user:
            # For security reasons, don't disclose whether username exists
            return jsonify({"error": "Invalid credentials"}), 401

        # Verify password
        is_valid = repo.verify_password(password, user.password_hash, user.password_salt)

        if not is_valid:
            return jsonify({"error": "Invalid credentials"}), 401

        # Create access token
        # Add user ID and admin status to JWT claims
        access_token = create_access_token(
            # relies on app having @jwt.user_identity_loader set, which translates the User object into a subject
            identity=user,
            additional_claims={
                "username": user.username,
                "email": user.email,
                "is_admin": user.is_admin,
            },
        )

        return jsonify({"access_token": access_token}), 200
