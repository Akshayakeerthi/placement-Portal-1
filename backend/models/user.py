from passlib.hash import pbkdf2_sha256

from backend.extensions import db
from backend.models.base import TimestampMixin


class UserRole:
    ADMIN = "ADMIN"
    COMPANY = "COMPANY"
    STUDENT = "STUDENT"


class User(TimestampMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, index=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_blacklisted = db.Column(db.Boolean, default=False, nullable=False)

    company_profile = db.relationship("CompanyProfile", uselist=False, back_populates="user")
    student_profile = db.relationship("StudentProfile", uselist=False, back_populates="user")

    def set_password(self, password: str):
        self.password_hash = pbkdf2_sha256.hash(password)

    def verify_password(self, password: str) -> bool:
        return pbkdf2_sha256.verify(password, self.password_hash)
