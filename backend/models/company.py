from backend.extensions import db
from backend.models.base import TimestampMixin


class CompanyProfile(TimestampMixin, db.Model):
    __tablename__ = "company_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    company_name = db.Column(db.String(150), nullable=False)
    website = db.Column(db.String(255))
    description = db.Column(db.Text)
    approved = db.Column(db.Boolean, default=False, nullable=False)

    user = db.relationship("User", back_populates="company_profile")
    drives = db.relationship("PlacementDrive", back_populates="company", cascade="all, delete-orphan")
