from datetime import datetime

from backend.extensions import db
from backend.models import Application, ApplicationStatus, CompanyProfile, PlacementDrive
from backend.utils.validators import ValidationError, validate_drive


class CompanyService:
    @staticmethod
    def upsert_profile(user_id: int, payload: dict):
        profile = CompanyProfile.query.filter_by(user_id=user_id).first()
        if profile is None:
            profile = CompanyProfile(user_id=user_id)
            db.session.add(profile)

        profile.company_name = payload["company_name"].strip()
        profile.website = payload.get("website")
        profile.description = payload.get("description")
        profile.approved = False
        db.session.commit()
        return profile

    @staticmethod
    def create_drive(user_id: int, payload: dict):
        company = CompanyProfile.query.filter_by(user_id=user_id).first_or_404()
        if not company.approved:
            raise ValidationError("Company profile not approved yet")

        deadline = validate_drive(payload["deadline"], float(payload["min_cgpa"]), int(payload["graduation_year"]))

        drive = PlacementDrive(
            company_id=company.id,
            title=payload["title"].strip(),
            description=payload["description"].strip(),
            eligible_branches=",".join([b.strip() for b in payload["eligible_branches"] if b.strip()]),
            min_cgpa=float(payload["min_cgpa"]),
            graduation_year=int(payload["graduation_year"]),
            deadline=deadline,
            approved=False,
        )
        db.session.add(drive)
        db.session.commit()
        return drive

    @staticmethod
    def list_company_drives(user_id: int):
        company = CompanyProfile.query.filter_by(user_id=user_id).first()
        if company is None:
            return []

        now = datetime.utcnow()
        drives = []
        dirty = False
        for drive in company.drives:
            drive.close_if_expired()
            if drive.closed and drive.deadline >= now:
                drive.closed = True
            if drive.deadline < now and not drive.closed:
                dirty = True
            drives.append(
                {
                    "id": drive.id,
                    "title": drive.title,
                    "approved": drive.approved,
                    "closed": drive.closed,
                    "deadline": drive.deadline.isoformat(),
                }
            )
        if dirty:
            db.session.commit()
        return drives

    @staticmethod
    def close_drive(user_id: int, drive_id: int):
        company = CompanyProfile.query.filter_by(user_id=user_id).first_or_404()
        drive = PlacementDrive.query.filter_by(company_id=company.id, id=drive_id).first_or_404()
        drive.closed = True
        db.session.commit()
        return drive

    @staticmethod
    def list_applicants(user_id: int, drive_id: int):
        company = CompanyProfile.query.filter_by(user_id=user_id).first_or_404()
        drive = PlacementDrive.query.filter_by(company_id=company.id, id=drive_id).first_or_404()

        return [
            {
                "application_id": app.id,
                "student_name": app.student.user.name,
                "student_email": app.student.user.email,
                "branch": app.student.branch,
                "cgpa": app.student.cgpa,
                "graduation_year": app.student.graduation_year,
                "resume_path": app.student.resume_path,
                "status": app.status,
                "interview_schedule": app.interview_schedule,
            }
            for app in drive.applications
        ]

    @staticmethod
    def update_application(user_id: int, app_id: int, status: str, interview_schedule: str | None = None):
        company = CompanyProfile.query.filter_by(user_id=user_id).first_or_404()
        app = (
            Application.query.join(PlacementDrive, Application.drive_id == PlacementDrive.id)
            .filter(Application.id == app_id, PlacementDrive.company_id == company.id)
            .first_or_404()
        )

        valid_status = {
            ApplicationStatus.APPLIED,
            ApplicationStatus.SHORTLISTED,
            ApplicationStatus.INTERVIEW_SCHEDULED,
            ApplicationStatus.SELECTED,
            ApplicationStatus.REJECTED,
        }
        if status not in valid_status:
            raise ValidationError("Invalid application status")

        app.status = status
        if interview_schedule:
            app.interview_schedule = interview_schedule
        db.session.commit()
        return app
