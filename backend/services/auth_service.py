from flask_jwt_extended import create_access_token

from backend.extensions import db
from backend.models import User, UserRole


class AuthService:
    @staticmethod
    def register(name: str, email: str, password: str, role: str):
        if role not in (UserRole.COMPANY, UserRole.STUDENT):
            raise ValueError("Only COMPANY/STUDENT can self-register")

        email = email.strip().lower()
        if User.query.filter_by(email=email).first():
            raise ValueError("Email already registered")

        user = User(name=name.strip(), email=email, role=role)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def login(email: str, password: str):
        user = User.query.filter_by(email=email.strip().lower()).first()
        if not user or not user.verify_password(password):
            raise ValueError("Invalid credentials")
        if user.is_blacklisted or not user.is_active:
            raise ValueError("User inactive or blacklisted")

        token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
        return {"token": token, "name": user.name, "role": user.role}
