import csv
from datetime import datetime, timedelta
from pathlib import Path

from flask import current_app

from backend.extensions import celery_app
from backend.models import PlacementDrive, StudentProfile, User, UserRole
from backend.services.admin_service import AdminService
from backend.utils.notifications import send_chat_webhook, send_email


def _build_admin_summary_html(data: dict, heading: str = "Placement Portal Summary Report") -> str:
    return f"""
    <html><body>
      <h2>{heading}</h2>
      <h3>Admin Summary (same as admin dashboard)</h3>
      <ul>
        <li>Total Users: {data['counts']['users']}</li>
        <li>Total Students: {data['counts']['students']}</li>
        <li>Total Companies: {data['counts']['companies']}</li>
        <li>Total Drives: {data['counts']['drives']}</li>
        <li>Total Applications: {data['counts']['applications']}</li>
        <li>Selected Students: {data['counts']['selected']}</li>
        <li>Pending Company Approvals: {data['summary']['pending_companies']}</li>
        <li>Pending Drive Approvals: {data['summary']['pending_drives']}</li>
        <li>Selection Rate: {data['summary']['selection_rate']}%</li>
      </ul>

      <h3>Application Status Breakdown</h3>
      <pre>{data['application_status_summary']}</pre>

      <h3>6-Month Trend</h3>
      <p><strong>Drives created:</strong> {data['trends']['drives']}</p>
      <p><strong>Applications submitted:</strong> {data['trends']['applications']}</p>
    </body></html>
    """


@celery_app.task(name="tasks.daily_reminder")
def daily_reminder_task():
    now = datetime.utcnow()
    in_two_days = now + timedelta(days=2)

    drives = (
        PlacementDrive.query.filter(
            PlacementDrive.approved.is_(True),
            PlacementDrive.closed.is_(False),
            PlacementDrive.deadline >= now,
            PlacementDrive.deadline <= in_two_days,
        )
        .order_by(PlacementDrive.deadline.asc())
        .all()
    )

    if not drives:
        return {"upcoming_drives": 0, "students_notified": 0, "delivery": "skipped"}

    drive_lines = [f"- {d.title} (deadline: {d.deadline.isoformat()} UTC)" for d in drives]
    body = (
        "Hello Student,\n\n"
        "This is your daily reminder for upcoming placement deadlines:\n"
        + "\n".join(drive_lines)
        + "\n\nPlease apply before the deadlines."
    )

    recipients = [
        profile.user.email
        for profile in StudentProfile.query.join(StudentProfile.user).all()
        if profile.user and profile.user.email
    ]
    email_result = send_email(
        subject="Daily Placement Deadline Reminder",
        body=body,
        recipients=recipients,
    )

    webhook_result = send_chat_webhook(
        "Daily reminder: "
        + ", ".join([f"{d.title} ({d.deadline.date().isoformat()})" for d in drives])
    )

    return {
        "upcoming_drives": len(drives),
        "students_notified": len(recipients) if email_result.get("sent") else 0,
        "email_result": email_result,
        "chat_result": webhook_result,
    }


@celery_app.task(name="tasks.monthly_report")
def monthly_report_task():
    data = AdminService.reports()
    report_dir = Path(current_app.config["REPORT_FOLDER"])
    report_dir.mkdir(parents=True, exist_ok=True)

    report_file = report_dir / f"monthly_report_{datetime.utcnow().strftime('%Y_%m')}.html"
    html = _build_admin_summary_html(data, heading="Placement Portal Monthly Report")
    report_file.write_text(html, encoding="utf-8")

    admin = User.query.filter_by(role=UserRole.ADMIN).first()
    recipient = admin.email if admin else current_app.config["ADMIN_EMAIL"]
    email_result = send_email(
        subject="Monthly Placement Activity Report",
        body="Please find the monthly placement activity report attached in HTML format.",
        recipients=[recipient],
        html=html,
    )

    return {
        "report_file": str(report_file),
        "sent_to": recipient,
        "email_result": email_result,
    }


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


@celery_app.task(name="tasks.export_admin_summary")
def export_admin_summary_task():
    data = AdminService.reports()
    html = _build_admin_summary_html(data, heading="Placement Portal Admin Summary Export")

    admin = User.query.filter_by(role=UserRole.ADMIN).first()
    recipient = admin.email if admin else current_app.config["ADMIN_EMAIL"]
    email_result = send_email(
        subject="Placement Portal Admin Summary Export",
        body="Please find the current admin summary report attached in HTML format.",
        recipients=[recipient],
        html=html,
    )

    return {"sent_to": recipient, "email_result": email_result}
