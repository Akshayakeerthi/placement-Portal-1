from datetime import datetime

from sqlalchemy import func, or_

from backend.extensions import db
from backend.models import Application, CompanyProfile, PlacementDrive, StudentProfile, User, UserRole
from backend.utils.cache import cache_delete_pattern, cache_get, cache_set


class AdminService:
    @staticmethod
    def dashboard_counts():
        key = "admin:dashboard:counts"
        cached = cache_get(key)
        if cached:
            return cached

        payload = {
            "users": User.query.count(),
            "students": User.query.filter_by(role=UserRole.STUDENT).count(),
            "companies": User.query.filter_by(role=UserRole.COMPANY).count(),
            "pending_companies": CompanyProfile.query.filter_by(approved=False).count(),
            "drives": PlacementDrive.query.count(),
            "pending_drives": PlacementDrive.query.filter_by(approved=False).count(),
            "applications": Application.query.count(),
        }
        cache_set(key, payload)
        return payload

    @staticmethod
    def set_company_status(company_id: int, approved: bool):
        company = CompanyProfile.query.get_or_404(company_id)
        company.approved = approved
        db.session.commit()
        cache_delete_pattern("admin:*")
        return company

    @staticmethod
    def set_drive_status(drive_id: int, approved: bool):
        drive = PlacementDrive.query.get_or_404(drive_id)
        drive.approved = approved
        db.session.commit()
        cache_delete_pattern("admin:*")
        cache_delete_pattern("drives:approved:*")
        return drive

    @staticmethod
    def close_drive(drive_id: int):
        drive = PlacementDrive.query.get_or_404(drive_id)
        drive.closed = True
        db.session.commit()
        cache_delete_pattern("admin:*")
        cache_delete_pattern("drives:approved:*")
        return drive

    @staticmethod
    def blacklist_user(user_id: int, value: bool):
        user = User.query.get_or_404(user_id)
        if user.role == UserRole.ADMIN:
            raise ValueError("Cannot blacklist ADMIN")
        user.is_blacklisted = value
        db.session.commit()
        return user

    @staticmethod
    def search_students(query: str):
        key = f"search:students:{query}"
        cached = cache_get(key)
        if cached:
            return cached

        rows = (
            db.session.query(StudentProfile, User)
            .join(User, StudentProfile.user_id == User.id)
            .filter(or_(User.name.ilike(f"%{query}%"), User.email.ilike(f"%{query}%"), StudentProfile.branch.ilike(f"%{query}%")))
            .all()
        )

        result = [
            {
                "user_id": user.id,
                "name": user.name,
                "email": user.email,
                "branch": profile.branch,
                "cgpa": profile.cgpa,
                "graduation_year": profile.graduation_year,
                "blacklisted": user.is_blacklisted,
            }
            for profile, user in rows
        ]
        cache_set(key, result)
        return result

    @staticmethod
    def search_companies(query: str):
        key = f"search:companies:{query}"
        cached = cache_get(key)
        if cached:
            return cached

        rows = (
            db.session.query(CompanyProfile, User)
            .join(User, CompanyProfile.user_id == User.id)
            .filter(or_(CompanyProfile.company_name.ilike(f"%{query}%"), User.email.ilike(f"%{query}%")))
            .all()
        )

        result = [
            {
                "company_id": company.id,
                "user_id": user.id,
                "company_name": company.company_name,
                "email": user.email,
                "approved": company.approved,
                "blacklisted": user.is_blacklisted,
            }
            for company, user in rows
        ]
        cache_set(key, result)
        return result

    @staticmethod
    def list_drives(query: str = ""):
        rows = (
            db.session.query(PlacementDrive, CompanyProfile)
            .join(CompanyProfile, PlacementDrive.company_id == CompanyProfile.id)
            .filter(
                or_(
                    PlacementDrive.title.ilike(f"%{query}%"),
                    CompanyProfile.company_name.ilike(f"%{query}%"),
                )
            )
            .order_by(PlacementDrive.created_at.desc())
            .all()
        )
        now = datetime.utcnow()
        return [
            {
                "drive_id": d.id,
                "title": d.title,
                "company_name": c.company_name,
                "approved": d.approved,
                "closed": d.closed or d.deadline < now,
                "deadline": d.deadline.isoformat(),
            }
            for d, c in rows
        ]

    @staticmethod
    def reports():
        status_summary = dict(
            db.session.query(Application.status, func.count(Application.id))
            .group_by(Application.status)
            .all()
        )
        return {
            "total_users": User.query.count(),
            "total_drives": PlacementDrive.query.count(),
            "total_applications": Application.query.count(),
            "application_status_summary": status_summary,
        }
