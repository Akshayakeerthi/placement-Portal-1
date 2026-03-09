from datetime import datetime

from backend.extensions import db
from backend.models import Application, ApplicationStatus, PlacementDrive, StudentProfile
from backend.tasks.jobs import export_csv_task
from backend.utils.cache import cache_delete_pattern, cache_get, cache_set
from backend.utils.validators import ValidationError, validate_student_profile


class StudentService:
    @staticmethod
    def get_profile(user_id: int):
        profile = StudentProfile.query.filter_by(user_id=user_id).first()
        if not profile:
            return {
                "branch": "",
                "graduation_year": datetime.utcnow().year,
                "cgpa": 0,
                "resume_path": "",
            }
        return {
            "id": profile.id,
            "branch": profile.branch,
            "graduation_year": profile.graduation_year,
            "cgpa": profile.cgpa,
            "resume_path": profile.resume_path,
        }

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
    def set_resume(user_id: int, resume_path: str):
        profile = StudentProfile.query.filter_by(user_id=user_id).first_or_404()
        profile.resume_path = resume_path
        db.session.commit()
        return profile

    @staticmethod
    def _is_eligible(profile: StudentProfile, drive: PlacementDrive):
        branches = [b.strip() for b in drive.eligible_branches.split(",")]
        return (
            profile.branch in branches
            and profile.cgpa >= drive.min_cgpa
            and profile.graduation_year <= drive.graduation_year
        )

    @staticmethod
    def list_drives(user_id: int, fit_profile: bool = False, page: int = 1, per_page: int = 5):
        profile = StudentProfile.query.filter_by(user_id=user_id).first()
        if profile is None:
            return {"items": [], "page": 1, "per_page": per_page, "total": 0, "total_pages": 1}

        cache_key = f"drives:list:{user_id}:{fit_profile}:{page}:{per_page}"
        cached = cache_get(cache_key)
        if cached:
            return cached

        now = datetime.utcnow()
        drives = PlacementDrive.query.filter_by(approved=True).order_by(PlacementDrive.deadline.asc()).all()
        dirty = False
        rows = []

        for drive in drives:
            drive.close_if_expired()
            if drive.closed or drive.deadline < now:
                dirty = True
                continue

            eligible = StudentService._is_eligible(profile, drive)
            if fit_profile and not eligible:
                continue

            rows.append(
                {
                    "id": drive.id,
                    "title": drive.title,
                    "description": drive.description,
                    "eligible_branches": drive.eligible_branches,
                    "min_cgpa": drive.min_cgpa,
                    "graduation_year": drive.graduation_year,
                    "deadline": drive.deadline.isoformat(),
                    "eligible": eligible,
                    "company": {
                        "name": drive.company.company_name,
                        "website": drive.company.website,
                        "description": drive.company.description,
                    },
                }
            )

        if dirty:
            db.session.commit()

        total = len(rows)
        total_pages = max(1, (total + per_page - 1) // per_page)
        page = min(max(1, page), total_pages)
        start = (page - 1) * per_page
        paged = rows[start : start + per_page]

        payload = {
            "items": paged,
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
        }
        cache_set(cache_key, payload)
        return payload

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

        if not StudentService._is_eligible(profile, drive):
            raise ValidationError("Not eligible for this drive")

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
