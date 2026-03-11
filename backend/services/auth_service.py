import re
from flask import current_app
from flask_jwt_extended import create_access_token

from backend.extensions import db
from backend.models import User, UserRole
from backend.utils.notifications import send_email


class AuthService:
    @staticmethod
    def register(name: str, email: str, password: str, confirm_password: str, role: str):
        if role not in (UserRole.COMPANY, UserRole.STUDENT):
            raise ValueError("Only COMPANY/STUDENT can self-register")

        if password != confirm_password:
            raise ValueError("Password and confirm password must match")

        email = email.strip().lower()
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
            raise ValueError("Incorrect email id")

        if User.query.filter_by(email=email).first():
            raise ValueError("Email already registered")

        user = User(name=name.strip(), email=email, role=role)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        subject = "Registration successful - Placement Portal"
        body = (
            f"Hello {user.name},\n\n"
            "You have successfully registered on Placement Portal. "
            "You can now log in and complete your profile.\n\n"
            f"Role: {user.role}\n"
            f"Support: {current_app.config['ADMIN_EMAIL']}\n"
        )
        send_email(subject=subject, body=body, recipients=[user.email])

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
