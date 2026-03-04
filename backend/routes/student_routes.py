import os
from datetime import datetime

from flask import Blueprint, current_app, jsonify, request
from werkzeug.utils import secure_filename

from backend.services.student_service import StudentService
from backend.utils.auth import get_current_user, role_required
from backend.utils.validators import ValidationError

bp = Blueprint("student", __name__, url_prefix="/api/student")


@bp.post("/profile")
@role_required("STUDENT")
def save_profile():
    user = get_current_user()
    try:
        profile = StudentService.upsert_profile(user.id, request.get_json() or {})
        return jsonify(
            {
                "id": profile.id,
                "branch": profile.branch,
                "graduation_year": profile.graduation_year,
                "cgpa": profile.cgpa,
                "resume_path": profile.resume_path,
            }
        )
    except (KeyError, ValidationError) as exc:
        return jsonify({"error": str(exc)}), 400


@bp.post("/resume")
@role_required("STUDENT")
def upload_resume():
    user = get_current_user()
    file = request.files.get("resume")
    if not file:
        return jsonify({"error": "resume file is required"}), 400

    filename = secure_filename(file.filename)
    if not filename:
        return jsonify({"error": "invalid filename"}), 400

    suffix = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    final_name = f"{user.id}_{suffix}_{filename}"
    abs_path = os.path.join(current_app.config["UPLOAD_FOLDER"], final_name)
    file.save(abs_path)

    rel_path = f"uploads/{final_name}"
    profile = StudentService.set_resume(user.id, rel_path)
    return jsonify({"resume_path": profile.resume_path})


@bp.get("/drives")
@role_required("STUDENT")
def drives():
    user = get_current_user()
    return jsonify(StudentService.approved_eligible_drives(user.id))


@bp.post("/drives/<int:drive_id>/apply")
@role_required("STUDENT")
def apply(drive_id: int):
    user = get_current_user()
    try:
        app = StudentService.apply(user.id, drive_id)
        return jsonify({"id": app.id, "status": app.status}), 201
    except ValidationError as exc:
        return jsonify({"error": str(exc)}), 400


@bp.get("/applications")
@role_required("STUDENT")
def applications():
    user = get_current_user()
    return jsonify(StudentService.history(user.id))


@bp.post("/applications/export")
@role_required("STUDENT")
def export_csv():
    user = get_current_user()
    return jsonify(StudentService.trigger_export(user.id)), 202
