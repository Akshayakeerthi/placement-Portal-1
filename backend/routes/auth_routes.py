from flask import Blueprint, jsonify, request

from backend.models import UserRole
from backend.services.auth_service import AuthService

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@bp.post("/register")
def register():
    data = request.get_json() or {}
    try:
        user = AuthService.register_user(
            name=data["name"],
            email=data["email"],
            password=data["password"],
            role=data["role"],
        )
        return jsonify({"id": user.id, "email": user.email, "role": user.role}), 201
    except (KeyError, ValueError) as exc:
        return jsonify({"error": str(exc)}), 400


@bp.post("/login")
def login():
    data = request.get_json() or {}
    try:
        response = AuthService.login(data["email"], data["password"])
        return jsonify(response)
    except (KeyError, ValueError) as exc:
        return jsonify({"error": str(exc)}), 400
