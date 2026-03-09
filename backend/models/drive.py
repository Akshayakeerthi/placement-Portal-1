from datetime import datetime

from backend.extensions import db
from backend.models.base import TimestampMixin


class PlacementDrive(TimestampMixin, db.Model):
    __tablename__ = "placement_drives"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("company_profiles.id"), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    eligible_branches = db.Column(db.String(300), nullable=False)
    min_cgpa = db.Column(db.Float, nullable=False)
    graduation_year = db.Column(db.Integer, nullable=False)
    deadline = db.Column(db.DateTime, nullable=False)
    approved = db.Column(db.Boolean, default=False, nullable=False)
    closed = db.Column(db.Boolean, default=False, nullable=False)

    company = db.relationship("CompanyProfile", back_populates="drives")
    applications = db.relationship("Application", back_populates="drive", cascade="all, delete-orphan")

    def close_if_expired(self):
        if self.deadline < datetime.utcnow() and not self.closed:
            self.closed = True
