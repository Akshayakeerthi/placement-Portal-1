from sqlalchemy import func, or_

from backend.extensions import db
from backend.models import Application, CompanyProfile, PlacementDrive, StudentProfile, User, UserRole
from backend.utils.cache import cache_delete, cache_get, cache_set


class AdminService:
    @staticmethod
    def dashboard_counts():
        cache_key = "admin:dashboard:counts"
        cached = cache_get(cache_key)
        if cached:
            return cached
        result = {
            "students": User.query.filter_by(role=UserRole.STUDENT).count(),
            "companies": User.query.filter_by(role=UserRole.COMPANY).count(),
            "drives": PlacementDrive.query.count(),
            "applications": Application.query.count(),
            "pending_companies": CompanyProfile.query.filter_by(approved=False).count(),
            "pending_drives": PlacementDrive.query.filter_by(approved=False).count(),
        }
        cache_set(cache_key, result)
        return result

    @staticmethod
    def set_company_approval(company_id: int, approved: bool):
        profile = CompanyProfile.query.get_or_404(company_id)
        profile.approved = approved
        db.session.commit()
        cache_delete("admin:dashboard")
        return profile

    @staticmethod
    def set_drive_approval(drive_id: int, approved: bool):
        drive = PlacementDrive.query.get_or_404(drive_id)
        drive.approved = approved
        db.session.commit()
        cache_delete("drives:approved")
        return drive

    @staticmethod
    def blacklist_user(user_id: int, status: bool):
        user = User.query.get_or_404(user_id)
        if user.role == UserRole.ADMIN:
            raise ValueError("Admin cannot be blacklisted")
        user.is_blacklisted = status
        db.session.commit()
        return user

    @staticmethod
    def search_students(query: str):
        cache_key = f"search:students:{query}"
        cached = cache_get(cache_key)
        if cached:
            return cached
        rows = (
            db.session.query(StudentProfile, User)
            .join(User, StudentProfile.user_id == User.id)
            .filter(or_(User.name.ilike(f"%{query}%"), User.email.ilike(f"%{query}%")))
            .all()
        )
        result = [
            {
                "id": u.id,
                "name": u.name,
                "email": u.email,
                "branch": s.branch,
                "cgpa": s.cgpa,
                "graduation_year": s.graduation_year,
            }
            for s, u in rows
        ]
        cache_set(cache_key, result)
        return result

    @staticmethod
    def search_companies(query: str):
        cache_key = f"search:companies:{query}"
        cached = cache_get(cache_key)
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
                "id": c.id,
                "name": c.company_name,
                "email": u.email,
                "approved": c.approved,
            }
            for c, u in rows
        ]
        cache_set(cache_key, result)
        return result

    @staticmethod
    def reports_summary():
        by_status = dict(
            db.session.query(Application.status, func.count(Application.id))
            .group_by(Application.status)
            .all()
        )
        return {
            "total_users": User.query.count(),
            "total_drives": PlacementDrive.query.count(),
            "total_applications": Application.query.count(),
            "application_status_breakdown": by_status,
        }
