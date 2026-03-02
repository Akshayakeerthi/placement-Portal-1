from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt, get_jwt_identity, verify_jwt_in_request

from backend.models import User


def role_required(*roles):
    def _decorator(fn):
        @wraps(fn)
        def _wrapper(*args, **kwargs):
            verify_jwt_in_request()
            role = get_jwt().get("role")
            if role not in roles:
                return jsonify({"error": "Forbidden"}), 403
            return fn(*args, **kwargs)

        return _wrapper

    return _decorator


def get_current_user() -> User:
    user_id = int(get_jwt_identity())
    return User.query.get_or_404(user_id)
