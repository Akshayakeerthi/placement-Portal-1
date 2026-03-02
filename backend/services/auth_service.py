from flask_jwt_extended import create_access_token

from backend.extensions import db
from backend.models import User, UserRole


class AuthService:
    @staticmethod
    def register_user(name: str, email: str, password: str, role: str):
        if role not in [UserRole.COMPANY, UserRole.STUDENT]:
            raise ValueError("Invalid registration role")
        if User.query.filter_by(email=email).first():
            raise ValueError("Email already exists")
        user = User(name=name, email=email.lower(), role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def login(email: str, password: str):
        user = User.query.filter_by(email=email.lower()).first()
        if not user or not user.verify_password(password):
            raise ValueError("Invalid credentials")
        if not user.is_active or user.is_blacklisted:
            raise ValueError("User is inactive or blacklisted")
        token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
        return {"token": token, "role": user.role, "name": user.name}
