import csv
import os
from datetime import datetime

from flask import current_app

from backend.extensions import db
from backend.models import Application, ApplicationStatus, PlacementDrive, StudentProfile
from backend.tasks.jobs import export_csv_task
from backend.utils.cache import cache_delete, cache_get, cache_set
from backend.utils.validators import ValidationError, validate_student_profile


class StudentService:
    @staticmethod
    def upsert_profile(user_id: int, payload: dict):
        validate_student_profile(payload["cgpa"], payload["branch"], payload["graduation_year"])
        profile = StudentProfile.query.filter_by(user_id=user_id).first()
        if not profile:
            profile = StudentProfile(user_id=user_id)
            db.session.add(profile)
        profile.branch = payload["branch"]
        profile.cgpa = payload["cgpa"]
        profile.graduation_year = payload["graduation_year"]
        if payload.get("resume_path"):
            profile.resume_path = payload["resume_path"]
        db.session.commit()
        return profile

    @staticmethod
    def get_eligible_drives(user_id: int):
        profile = StudentProfile.query.filter_by(user_id=user_id).first_or_404()
        cache_key = f"drives:approved:eligible:{profile.branch}:{profile.graduation_year}:{profile.cgpa}"
        cached = cache_get(cache_key)
        if cached:
            return cached

        drives = PlacementDrive.query.filter_by(approved=True, closed=False).all()
        now = datetime.utcnow()
        eligible = []
        dirty = False
        for drive in drives:
            drive.close_if_expired()
            if drive.closed:
                dirty = True
                continue
            branches = [x.strip() for x in drive.eligible_branches.split(",")]
            if (
                profile.branch in branches
                and profile.cgpa >= drive.min_cgpa
                and profile.graduation_year == drive.graduation_year
                and drive.deadline >= now
            ):
                eligible.append(
                    {
                        "id": drive.id,
                        "title": drive.title,
                        "company": drive.company.company_name,
                        "deadline": drive.deadline.isoformat(),
                        "min_cgpa": drive.min_cgpa,
                    }
                )
        if dirty:
            db.session.commit()
        cache_set(cache_key, eligible)
        return eligible

    @staticmethod
    def apply_to_drive(user_id: int, drive_id: int):
        profile = StudentProfile.query.filter_by(user_id=user_id).first_or_404()
        drive = PlacementDrive.query.get_or_404(drive_id)
        drive.close_if_expired()
        if drive.closed or drive.deadline < datetime.utcnow():
            db.session.commit()
            raise ValidationError("Drive closed or deadline passed")
        if not drive.approved:
            raise ValidationError("Drive not approved")
        if profile.cgpa < drive.min_cgpa or profile.graduation_year != drive.graduation_year:
            raise ValidationError("Not eligible for this drive")
        if profile.branch not in [b.strip() for b in drive.eligible_branches.split(",")]:
            raise ValidationError("Not eligible branch")

        exists = Application.query.filter_by(student_id=profile.id, drive_id=drive.id).first()
        if exists:
            raise ValidationError("Already applied to this drive")
        app = Application(student_id=profile.id, drive_id=drive.id, status=ApplicationStatus.APPLIED)
        db.session.add(app)
        db.session.commit()
        cache_delete("drives:approved")
        return app

    @staticmethod
    def application_history(user_id: int):
        profile = StudentProfile.query.filter_by(user_id=user_id).first_or_404()
        return [
            {
                "application_id": app.id,
                "drive": app.drive.title,
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
        return {"task_id": task.id, "message": "Export started"}
