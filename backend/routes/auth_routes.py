from flask import Blueprint, jsonify, request

from backend.services.auth_service import AuthService

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@bp.post("/register")
def register():
    payload = request.get_json() or {}
    try:
        user = AuthService.register(
            name=payload["name"],
            email=payload["email"],
            password=payload["password"],
            confirm_password=payload["confirm_password"],
            role=payload["role"],
        )
        return jsonify({"id": user.id, "email": user.email, "role": user.role}), 201
    except (KeyError, ValueError) as exc:
        return jsonify({"error": str(exc)}), 400


@bp.post("/login")
def login():
    payload = request.get_json() or {}
    try:
        return jsonify(AuthService.login(payload["email"], payload["password"]))
    except (KeyError, ValueError) as exc:
        return jsonify({"error": str(exc)}), 400
