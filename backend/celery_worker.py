from celery.schedules import crontab

from backend.app import create_app
from backend.extensions import celery_app

app = create_app()

celery_app.conf.beat_schedule = {
    "daily-reminder": {
        "task": "tasks.daily_reminder",
        "schedule": crontab(hour=8, minute=0),
    },
    "monthly-report": {
        "task": "tasks.monthly_report",
        "schedule": crontab(day_of_month=1, hour=7, minute=30),
    },
}

if __name__ == "__main__":
    celery_app.start()
