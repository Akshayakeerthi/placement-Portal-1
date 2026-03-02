# Placement Portal Application (PPA) v2

Production-style Placement Portal built with **Flask + SQLite + Redis + Celery** and **Vue + Bootstrap**.

## 1) Project Structure

```text
backend/
  app.py
  celery_worker.py
  config.py
  extensions.py
  models/
  routes/
  schemas/
  services/
  tasks/
  utils/
frontend/
  index.html
  js/app.js
  components/
  services/api.js
exports/
uploads/
reports/
requirements.txt
```

## 2) Backend Modules

- **Auth**: JWT login/register, password hashing, role claims.
- **RBAC**: role-based decorator on protected routes.
- **Models**: User, CompanyProfile, StudentProfile, PlacementDrive, Application.
- **Constraints**:
  - single admin via init command
  - unique `(student_id, drive_id)` application constraint
  - eligibility + deadline validations
  - automatic drive closure if expired
- **Caching** (Redis): dashboard counts, approved/eligible drives, search results.
- **Service layer**: encapsulates business logic.

## 3) Frontend Vue Components

- `AuthView`: Login + registration
- `AdminDashboard`: counts + student/company search
- `CompanyDashboard`: profile + create drive
- `StudentDashboard`: profile, eligible drives, apply, history, CSV export trigger

> Jinja2 is used only as entry bootstrap (`frontend/index.html`).

## 4) Celery Jobs

- `tasks.daily_deadline_reminder`: notify students for upcoming drive deadlines
- `tasks.monthly_report`: generate HTML report and email-target metadata
- `tasks.export_csv`: async per-student application export

Celery beat schedules are configured in `backend/celery_worker.py`.

## 5) Local Setup

### Prerequisites
- Python 3.11+
- Redis running locally on `localhost:6379`

### Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Initialize DB + admin

```bash
export FLASK_APP=backend.app:create_app
flask init-db
```

Default admin credentials:
- Email: `admin@placement.local`
- Password: `Admin@123`

### Run Flask API + UI

```bash
flask run
```

Open: `http://127.0.0.1:5000/`

### Run Celery worker

```bash
celery -A backend.celery_worker.celery_app worker -B --loglevel=info
```

## 6) Notes

- SQLite DB is created programmatically via SQLAlchemy (`flask init-db`).
- No external DB framework or styling framework beyond Bootstrap is used.
