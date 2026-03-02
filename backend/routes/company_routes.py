from flask import Blueprint, jsonify, request

from backend.services.company_service import CompanyService
from backend.utils.auth import get_current_user, role_required

bp = Blueprint("company", __name__, url_prefix="/api/company")


@bp.post("/profile")
@role_required("COMPANY")
def upsert_profile():
    user = get_current_user()
    profile = CompanyService.upsert_profile(user.id, request.get_json() or {})
    return jsonify({"id": profile.id, "company_name": profile.company_name, "approved": profile.approved})


@bp.post("/drives")
@role_required("COMPANY")
def create_drive():
    user = get_current_user()
    try:
        drive = CompanyService.create_drive(user.id, request.get_json() or {})
        return jsonify({"id": drive.id, "title": drive.title, "approved": drive.approved}), 201
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@bp.get("/drives/<int:drive_id>/applicants")
@role_required("COMPANY")
def list_applicants(drive_id):
    user = get_current_user()
    return jsonify(CompanyService.list_applicants(user.id, drive_id))


@bp.patch("/applications/<int:application_id>/status")
@role_required("COMPANY")
def update_application(application_id):
    user = get_current_user()
    payload = request.get_json() or {}
    app = CompanyService.update_application_status(
        user.id,
        application_id,
        payload.get("status", "APPLIED"),
        payload.get("interview_schedule"),
    )
    return jsonify({"id": app.id, "status": app.status, "interview_schedule": app.interview_schedule})
