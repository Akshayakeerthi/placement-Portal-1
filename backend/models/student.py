from backend.extensions import db
from backend.models.base import TimestampMixin


class StudentProfile(TimestampMixin, db.Model):
    __tablename__ = "student_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)
    branch = db.Column(db.String(100), nullable=False)
    graduation_year = db.Column(db.Integer, nullable=False)
    cgpa = db.Column(db.Float, nullable=False)
    resume_path = db.Column(db.String(255))

    user = db.relationship("User", back_populates="student_profile")
    applications = db.relationship("Application", back_populates="student", cascade="all, delete-orphan")
