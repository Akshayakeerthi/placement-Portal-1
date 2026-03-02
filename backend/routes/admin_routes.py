from flask import Blueprint, jsonify, request

from backend.services.admin_service import AdminService
from backend.utils.auth import role_required

bp = Blueprint("admin", __name__, url_prefix="/api/admin")


@bp.get("/dashboard")
@role_required("ADMIN")
def dashboard():
    return jsonify(AdminService.dashboard_counts())


@bp.patch("/companies/<int:company_id>/approval")
@role_required("ADMIN")
def approve_company(company_id):
    payload = request.get_json() or {}
    profile = AdminService.set_company_approval(company_id, bool(payload.get("approved", False)))
    return jsonify({"company_id": profile.id, "approved": profile.approved})


@bp.patch("/drives/<int:drive_id>/approval")
@role_required("ADMIN")
def approve_drive(drive_id):
    payload = request.get_json() or {}
    drive = AdminService.set_drive_approval(drive_id, bool(payload.get("approved", False)))
    return jsonify({"drive_id": drive.id, "approved": drive.approved})


@bp.get("/students")
@role_required("ADMIN")
def search_students():
    q = request.args.get("q", "")
    return jsonify(AdminService.search_students(q))


@bp.get("/companies")
@role_required("ADMIN")
def search_companies():
    q = request.args.get("q", "")
    return jsonify(AdminService.search_companies(q))


@bp.patch("/users/<int:user_id>/blacklist")
@role_required("ADMIN")
def blacklist_user(user_id):
    payload = request.get_json() or {}
    try:
        user = AdminService.blacklist_user(user_id, bool(payload.get("is_blacklisted", True)))
        return jsonify({"id": user.id, "is_blacklisted": user.is_blacklisted})
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@bp.get("/reports")
@role_required("ADMIN")
def reports():
    return jsonify(AdminService.reports_summary())
