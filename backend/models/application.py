from backend.extensions import db
from backend.models.base import TimestampMixin


class ApplicationStatus:
    APPLIED = "APPLIED"
    SHORTLISTED = "SHORTLISTED"
    INTERVIEW_SCHEDULED = "INTERVIEW_SCHEDULED"
    SELECTED = "SELECTED"
    REJECTED = "REJECTED"


class Application(TimestampMixin, db.Model):
    __tablename__ = "applications"
    __table_args__ = (
        db.UniqueConstraint("student_id", "drive_id", name="uq_student_drive_application"),
    )

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student_profiles.id"), nullable=False)
    drive_id = db.Column(db.Integer, db.ForeignKey("placement_drives.id"), nullable=False)
    status = db.Column(db.String(50), nullable=False, default=ApplicationStatus.APPLIED)
    interview_schedule = db.Column(db.String(255))

    student = db.relationship("StudentProfile", back_populates="applications")
    drive = db.relationship("PlacementDrive", back_populates="applications")
