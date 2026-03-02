from datetime import datetime

from backend.extensions import db
from backend.models import Application, ApplicationStatus, CompanyProfile, PlacementDrive


class CompanyService:
    @staticmethod
    def upsert_profile(user_id: int, payload: dict):
        profile = CompanyProfile.query.filter_by(user_id=user_id).first()
        if not profile:
            profile = CompanyProfile(user_id=user_id)
            db.session.add(profile)
        profile.company_name = payload["company_name"]
        profile.website = payload.get("website")
        profile.description = payload.get("description")
        profile.approved = False
        db.session.commit()
        return profile

    @staticmethod
    def create_drive(user_id: int, payload: dict):
        company = CompanyProfile.query.filter_by(user_id=user_id).first_or_404()
        if not company.approved:
            raise ValueError("Company profile is pending approval")
        drive = PlacementDrive(
            company_id=company.id,
            title=payload["title"],
            description=payload["description"],
            eligible_branches=",".join(payload["eligible_branches"]),
            min_cgpa=float(payload["min_cgpa"]),
            graduation_year=int(payload["graduation_year"]),
            deadline=datetime.fromisoformat(payload["deadline"]),
            approved=False,
        )
        db.session.add(drive)
        db.session.commit()
        return drive

    @staticmethod
    def list_applicants(user_id: int, drive_id: int):
        company = CompanyProfile.query.filter_by(user_id=user_id).first_or_404()
        drive = PlacementDrive.query.filter_by(id=drive_id, company_id=company.id).first_or_404()
        return [
            {
                "application_id": app.id,
                "student_name": app.student.user.name,
                "student_email": app.student.user.email,
                "status": app.status,
                "interview_schedule": app.interview_schedule,
            }
            for app in drive.applications
        ]

    @staticmethod
    def update_application_status(user_id: int, app_id: int, status: str, interview_schedule=None):
        company = CompanyProfile.query.filter_by(user_id=user_id).first_or_404()
        app = (
            Application.query.join(PlacementDrive, Application.drive_id == PlacementDrive.id)
            .filter(Application.id == app_id, PlacementDrive.company_id == company.id)
            .first_or_404()
        )
        app.status = status
        if interview_schedule:
            app.interview_schedule = interview_schedule
        db.session.commit()
        return app
