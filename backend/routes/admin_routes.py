from flask import Blueprint, jsonify, request

from backend.services.admin_service import AdminService
from backend.tasks.jobs import export_admin_summary_task
from backend.utils.auth import role_required

bp = Blueprint("admin", __name__, url_prefix="/api/admin")


@bp.get("/dashboard")
@role_required("ADMIN")
def dashboard():
    return jsonify(AdminService.dashboard_counts())


@bp.patch("/companies/<int:company_id>/approval")
@role_required("ADMIN")
def company_approval(company_id: int):
    payload = request.get_json() or {}
    company = AdminService.set_company_status(company_id, bool(payload.get("approved", False)))
    return jsonify({"company_id": company.id, "approved": company.approved})


@bp.patch("/drives/<int:drive_id>/approval")
@role_required("ADMIN")
def drive_approval(drive_id: int):
    payload = request.get_json() or {}
    drive = AdminService.set_drive_status(drive_id, bool(payload.get("approved", False)))
    return jsonify({"drive_id": drive.id, "approved": drive.approved})


@bp.patch("/drives/<int:drive_id>/close")
@role_required("ADMIN")
def close_drive(drive_id: int):
    drive = AdminService.close_drive(drive_id)
    return jsonify({"drive_id": drive.id, "closed": drive.closed})


@bp.patch("/users/<int:user_id>/blacklist")
@role_required("ADMIN")
def blacklist(user_id: int):
    payload = request.get_json() or {}
    try:
        user = AdminService.blacklist_user(user_id, bool(payload.get("is_blacklisted", True)))
        return jsonify({"user_id": user.id, "is_blacklisted": user.is_blacklisted})
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@bp.get("/students")
@role_required("ADMIN")
def students():
    q = request.args.get("q", "")
    return jsonify(AdminService.search_students(q))


@bp.get("/companies")
@role_required("ADMIN")
def companies():
    q = request.args.get("q", "")
    return jsonify(AdminService.search_companies(q))


@bp.get("/drives")
@role_required("ADMIN")
def drives():
    q = request.args.get("q", "")
    return jsonify(AdminService.list_drives(q))


@bp.get("/reports")
@role_required("ADMIN")
def reports():
    return jsonify(AdminService.reports())


@bp.post("/summary/export")
@role_required("ADMIN")
def export_summary():
    result = export_admin_summary_task.apply().get()
    return jsonify({"message": "Summary exported and emailed to admin.", "result": result})
