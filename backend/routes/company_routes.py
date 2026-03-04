from flask import Blueprint, jsonify, request

from backend.services.company_service import CompanyService
from backend.utils.auth import get_current_user, role_required
from backend.utils.validators import ValidationError

bp = Blueprint("company", __name__, url_prefix="/api/company")


@bp.post("/profile")
@role_required("COMPANY")
def save_profile():
    user = get_current_user()
    try:
        profile = CompanyService.upsert_profile(user.id, request.get_json() or {})
        return jsonify({"id": profile.id, "company_name": profile.company_name, "approved": profile.approved})
    except (KeyError, ValidationError) as exc:
        return jsonify({"error": str(exc)}), 400


@bp.post("/drives")
@role_required("COMPANY")
def create_drive():
    user = get_current_user()
    try:
        drive = CompanyService.create_drive(user.id, request.get_json() or {})
        return jsonify({"id": drive.id, "title": drive.title, "approved": drive.approved}), 201
    except (KeyError, ValidationError) as exc:
        return jsonify({"error": str(exc)}), 400


@bp.get("/drives")
@role_required("COMPANY")
def list_drives():
    user = get_current_user()
    return jsonify(CompanyService.list_company_drives(user.id))


@bp.patch("/drives/<int:drive_id>/close")
@role_required("COMPANY")
def close_drive(drive_id: int):
    user = get_current_user()
    drive = CompanyService.close_drive(user.id, drive_id)
    return jsonify({"id": drive.id, "closed": drive.closed})


@bp.get("/drives/<int:drive_id>/applicants")
@role_required("COMPANY")
def applicants(drive_id: int):
    user = get_current_user()
    return jsonify(CompanyService.list_applicants(user.id, drive_id))


@bp.patch("/applications/<int:app_id>")
@role_required("COMPANY")
def update_application(app_id: int):
    user = get_current_user()
    payload = request.get_json() or {}
    try:
        app = CompanyService.update_application(
            user.id,
            app_id,
            payload.get("status", "APPLIED"),
            payload.get("interview_schedule"),
        )
        return jsonify({"id": app.id, "status": app.status, "interview_schedule": app.interview_schedule})
    except ValidationError as exc:
        return jsonify({"error": str(exc)}), 400
