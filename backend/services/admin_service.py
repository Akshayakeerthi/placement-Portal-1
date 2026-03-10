from datetime import datetime

from sqlalchemy import func, or_

from backend.extensions import db
from backend.models import Application, CompanyProfile, PlacementDrive, StudentProfile, User, UserRole
from backend.utils.cache import cache_delete_pattern, cache_get, cache_set


class AdminService:
    @staticmethod
    def _month_key(dt: datetime) -> str:
        return dt.strftime("%Y-%m")

    @staticmethod
    def _last_n_month_keys(n: int = 6) -> list[str]:
        now = datetime.utcnow()
        keys = []
        year = now.year
        month = now.month
        for _ in range(n):
            keys.append(f"{year:04d}-{month:02d}")
            month -= 1
            if month == 0:
                month = 12
                year -= 1
        return list(reversed(keys))

    @staticmethod
    def _monthly_trend(rows: list[datetime], months: int = 6):
        keys = AdminService._last_n_month_keys(months)
        bucket = {k: 0 for k in keys}
        for dt in rows:
            if not dt:
                continue
            mk = AdminService._month_key(dt)
            if mk in bucket:
                bucket[mk] += 1
        return [{"month": k, "count": bucket[k]} for k in keys]

    @staticmethod
    def dashboard_counts():
        key = "admin:dashboard:counts"
        cached = cache_get(key)
        if cached:
            return cached

        status_summary = dict(
            db.session.query(Application.status, func.count(Application.id))
            .group_by(Application.status)
            .all()
        )
        selected_count = status_summary.get("SELECTED", 0)
        total_applications = Application.query.count()

        drive_created_rows = [r[0] for r in db.session.query(PlacementDrive.created_at).all()]
        app_created_rows = [r[0] for r in db.session.query(Application.created_at).all()]

        payload = {
            "counts": {
                "users": User.query.count(),
                "students": User.query.filter_by(role=UserRole.STUDENT).count(),
                "companies": User.query.filter_by(role=UserRole.COMPANY).count(),
                "drives": PlacementDrive.query.count(),
                "applications": total_applications,
                "selected": selected_count,
            },
            "summary": {
                "pending_companies": CompanyProfile.query.filter_by(approved=False).count(),
                "pending_drives": PlacementDrive.query.filter_by(approved=False).count(),
                "selection_rate": round((selected_count / total_applications) * 100, 2) if total_applications else 0,
            },
            "application_status_summary": status_summary,
            "trends": {
                "drives": AdminService._monthly_trend(drive_created_rows),
                "applications": AdminService._monthly_trend(app_created_rows),
            },
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
                "description": d.description,
                "eligible_branches": d.eligible_branches,
                "min_cgpa": d.min_cgpa,
                "graduation_year": d.graduation_year,
                "company_name": c.company_name,
                "company_website": c.website,
                "company_description": c.description,
                "approved": d.approved,
                "closed": d.closed or d.deadline < now,
                "deadline": d.deadline.isoformat(),
            }
            for d, c in rows
        ]

    @staticmethod
    def reports():
        payload = AdminService.dashboard_counts()
        counts = payload["counts"]
        return {
            **payload,
            "total_users": counts["users"],
            "total_drives": counts["drives"],
            "total_applications": counts["applications"],
            "students_applied": counts["applications"],
            "students_selected": counts["selected"],
        }
