import csv
from datetime import datetime, timedelta
from pathlib import Path

from flask import current_app

from backend.extensions import celery_app, db
from backend.models import PlacementDrive, StudentProfile, User, UserRole
from backend.services.admin_service import AdminService


def _write_report_html(data: dict, output_file: Path):
    rows = "".join(
        [f"<li>{key}: {value}</li>" for key, value in data["application_status_breakdown"].items()]
    )
    html = f"""
    <html><body>
      <h1>Monthly Placement Report</h1>
      <p>Total Users: {data['total_users']}</p>
      <p>Total Drives: {data['total_drives']}</p>
      <p>Total Applications: {data['total_applications']}</p>
      <ul>{rows}</ul>
    </body></html>
    """
    output_file.write_text(html, encoding="utf-8")


@celery_app.task(name="tasks.daily_deadline_reminder")
def daily_deadline_reminder_task():
    now = datetime.utcnow()
    upcoming = now + timedelta(days=2)
    drives = PlacementDrive.query.filter(
        PlacementDrive.approved.is_(True),
        PlacementDrive.closed.is_(False),
        PlacementDrive.deadline <= upcoming,
        PlacementDrive.deadline >= now,
    ).all()
    # Simulated notification dispatch
    return {"notified_students": StudentProfile.query.count(), "upcoming_drives": len(drives)}


@celery_app.task(name="tasks.monthly_report")
def monthly_report_task():
    report_data = AdminService.reports_summary()
    out_dir = Path(current_app.config["REPORT_FOLDER"])
    out_dir.mkdir(parents=True, exist_ok=True)
    file_path = out_dir / f"monthly_report_{datetime.utcnow().strftime('%Y_%m')}.html"
    _write_report_html(report_data, file_path)
    admin = User.query.filter_by(role=UserRole.ADMIN).first()
    return {
        "report_file": str(file_path),
        "email_to": admin.email if admin else current_app.config["ADMIN_EMAIL"],
    }


@celery_app.task(name="tasks.export_csv")
def export_csv_task(user_id: int):
    profile = StudentProfile.query.filter_by(user_id=user_id).first()
    if not profile:
        return {"error": "Student profile not found"}
    out_dir = Path(current_app.config["EXPORT_FOLDER"])
    out_dir.mkdir(parents=True, exist_ok=True)
    file_path = out_dir / f"applications_{user_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.csv"
    with file_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Drive", "Company", "Status", "Interview", "Applied At"])
        for app in profile.applications:
            writer.writerow(
                [
                    app.drive.title,
                    app.drive.company.company_name,
                    app.status,
                    app.interview_schedule or "",
                    app.created_at.isoformat(),
                ]
            )
    return {"file": str(file_path), "message": "Student notified"}
