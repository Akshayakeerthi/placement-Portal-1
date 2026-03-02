from flask import Blueprint, jsonify, request

from backend.services.student_service import StudentService
from backend.utils.auth import get_current_user, role_required
from backend.utils.validators import ValidationError

bp = Blueprint("student", __name__, url_prefix="/api/student")


@bp.post("/profile")
@role_required("STUDENT")
def upsert_profile():
    user = get_current_user()
    try:
        profile = StudentService.upsert_profile(user.id, request.get_json() or {})
        return jsonify(
            {
                "id": profile.id,
                "branch": profile.branch,
                "cgpa": profile.cgpa,
                "graduation_year": profile.graduation_year,
                "resume_path": profile.resume_path,
            }
        )
    except (ValidationError, KeyError) as exc:
        return jsonify({"error": str(exc)}), 400


@bp.get("/drives")
@role_required("STUDENT")
def eligible_drives():
    user = get_current_user()
    return jsonify(StudentService.get_eligible_drives(user.id))


@bp.post("/drives/<int:drive_id>/apply")
@role_required("STUDENT")
def apply(drive_id):
    user = get_current_user()
    try:
        app = StudentService.apply_to_drive(user.id, drive_id)
        return jsonify({"id": app.id, "status": app.status}), 201
    except ValidationError as exc:
        return jsonify({"error": str(exc)}), 400


@bp.get("/applications")
@role_required("STUDENT")
def history():
    user = get_current_user()
    return jsonify(StudentService.application_history(user.id))


@bp.post("/applications/export")
@role_required("STUDENT")
def export_csv():
    user = get_current_user()
    return jsonify(StudentService.trigger_export(user.id)), 202
