import csv
from datetime import datetime, timedelta
from pathlib import Path

from flask import current_app

from backend.extensions import celery_app
from backend.models import PlacementDrive, StudentProfile, User, UserRole
from backend.services.admin_service import AdminService


@celery_app.task(name="tasks.daily_reminder")
def daily_reminder_task():
    now = datetime.utcnow()
    in_two_days = now + timedelta(days=2)

    drives = PlacementDrive.query.filter(
        PlacementDrive.approved.is_(True),
        PlacementDrive.closed.is_(False),
        PlacementDrive.deadline >= now,
        PlacementDrive.deadline <= in_two_days,
    ).all()

    return {
        "upcoming_drives": len(drives),
        "students_notified": StudentProfile.query.count(),
    }


@celery_app.task(name="tasks.monthly_report")
def monthly_report_task():
    data = AdminService.reports()
    report_dir = Path(current_app.config["REPORT_FOLDER"])
    report_dir.mkdir(parents=True, exist_ok=True)

    report_file = report_dir / f"monthly_report_{datetime.utcnow().strftime('%Y_%m')}.html"
    html = f"""
    <html><body>
      <h2>Placement Portal Monthly Report</h2>
      <p>Total Users: {data['total_users']}</p>
      <p>Total Drives: {data['total_drives']}</p>
      <p>Total Applications: {data['total_applications']}</p>
      <pre>{data['application_status_summary']}</pre>
    </body></html>
    """
    report_file.write_text(html, encoding="utf-8")

    admin = User.query.filter_by(role=UserRole.ADMIN).first()
    return {"report_file": str(report_file), "sent_to": admin.email if admin else current_app.config["ADMIN_EMAIL"]}


@celery_app.task(name="tasks.export_csv")
def export_csv_task(user_id: int):
    profile = StudentProfile.query.filter_by(user_id=user_id).first()
    if not profile:
        return {"error": "Student profile missing"}

    export_dir = Path(current_app.config["EXPORT_FOLDER"])
    export_dir.mkdir(parents=True, exist_ok=True)

    file_path = export_dir / f"applications_{user_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.csv"
    with file_path.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.writer(fp)
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

    return {"csv_file": str(file_path), "notified": True}
