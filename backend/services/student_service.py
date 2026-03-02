from datetime import datetime

from backend.extensions import db
from backend.models import Application, ApplicationStatus, PlacementDrive, StudentProfile
from backend.tasks.jobs import export_csv_task
from backend.utils.cache import cache_delete_pattern, cache_get, cache_set
from backend.utils.validators import ValidationError, validate_student_profile


class StudentService:
    @staticmethod
    def upsert_profile(user_id: int, payload: dict):
        validate_student_profile(float(payload["cgpa"]), payload["branch"], int(payload["graduation_year"]))

        profile = StudentProfile.query.filter_by(user_id=user_id).first()
        if profile is None:
            profile = StudentProfile(user_id=user_id)
            db.session.add(profile)

        profile.branch = payload["branch"].strip()
        profile.cgpa = float(payload["cgpa"])
        profile.graduation_year = int(payload["graduation_year"])
        profile.resume_path = payload.get("resume_path", profile.resume_path)

        db.session.commit()
        cache_delete_pattern("drives:approved:*")
        return profile

    @staticmethod
    def approved_eligible_drives(user_id: int):
        profile = StudentProfile.query.filter_by(user_id=user_id).first_or_404()
        key = f"drives:approved:{profile.branch}:{profile.graduation_year}:{profile.cgpa}"
        cached = cache_get(key)
        if cached:
            return cached

        drives = PlacementDrive.query.filter_by(approved=True).all()
        now = datetime.utcnow()
        dirty = False
        out = []

        for drive in drives:
            drive.close_if_expired()
            if drive.closed:
                dirty = True
                continue
            branches = [b.strip() for b in drive.eligible_branches.split(",")]
            if (
                profile.branch in branches
                and profile.cgpa >= drive.min_cgpa
                and profile.graduation_year == drive.graduation_year
                and drive.deadline >= now
            ):
                out.append(
                    {
                        "id": drive.id,
                        "title": drive.title,
                        "company": drive.company.company_name,
                        "deadline": drive.deadline.isoformat(),
                    }
                )

        if dirty:
            db.session.commit()

        cache_set(key, out)
        return out

    @staticmethod
    def apply(user_id: int, drive_id: int):
        profile = StudentProfile.query.filter_by(user_id=user_id).first_or_404()
        drive = PlacementDrive.query.get_or_404(drive_id)

        drive.close_if_expired()
        if drive.closed or drive.deadline < datetime.utcnow():
            db.session.commit()
            raise ValidationError("Drive is closed")
        if not drive.approved:
            raise ValidationError("Drive not approved")

        branches = [b.strip() for b in drive.eligible_branches.split(",")]
        if profile.branch not in branches:
            raise ValidationError("Not eligible: branch")
        if profile.cgpa < drive.min_cgpa:
            raise ValidationError("Not eligible: CGPA")
        if profile.graduation_year != drive.graduation_year:
            raise ValidationError("Not eligible: graduation year")

        if Application.query.filter_by(student_id=profile.id, drive_id=drive.id).first():
            raise ValidationError("Already applied")

        app = Application(student_id=profile.id, drive_id=drive.id, status=ApplicationStatus.APPLIED)
        db.session.add(app)
        db.session.commit()
        return app

    @staticmethod
    def history(user_id: int):
        profile = StudentProfile.query.filter_by(user_id=user_id).first_or_404()
        return [
            {
                "application_id": app.id,
                "drive_title": app.drive.title,
                "company": app.drive.company.company_name,
                "status": app.status,
                "interview_schedule": app.interview_schedule,
                "applied_at": app.created_at.isoformat(),
            }
            for app in profile.applications
        ]

    @staticmethod
    def trigger_export(user_id: int):
        task = export_csv_task.delay(user_id)
        return {"task_id": task.id, "status": "queued"}
