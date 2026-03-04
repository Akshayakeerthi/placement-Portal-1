# Placement Portal Application (PPA) v2

A complete full-stack placement portal built with:

- **Backend**: Flask API, SQLAlchemy, SQLite, Redis cache, Celery workers
- **Frontend**: Vue 3 (CDN), Bootstrap, Axios
- **Template usage**: Jinja2 only for Vue bootstrapping (`frontend/index.html`)

## Project structure

```text
backend/
  app.py
  config.py
  extensions.py
  celery_worker.py
  models/
  routes/
  services/
  tasks/
  utils/
  schemas/
frontend/
  index.html
  js/
  components/
  services/
exports/
uploads/
reports/
requirements.txt
```

## Backend features

- JWT authentication and role-based access
- Unified `User` model (`ADMIN`, `COMPANY`, `STUDENT`)
- Programmatic DB init with single pre-created admin (`flask init-db`)
- Core domain models:
  - `User`
  - `CompanyProfile`
  - `StudentProfile`
  - `PlacementDrive`
  - `Application`
- Business rules:
  - no duplicate student application per drive (DB unique constraint)
  - eligibility checks (branch/cgpa/year)
  - no applications after deadline
  - drives auto-close after deadline
- Redis caching:
  - admin dashboard counts
  - approved/eligible drives queries
  - search queries
- Celery async jobs:
  - daily reminders
  - monthly report generation (HTML)
  - CSV export for student history

## API modules

- `/api/auth/*` - login/register
- `/api/admin/*` - dashboard, approvals, search, blacklist, reports
- `/api/company/*` - profile, drives, applicants, application updates
- `/api/student/*` - profile, resume upload, eligible drives, apply, history, csv export

## Local setup

### 1) Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Start Redis

```bash
redis-server
```

### 3) Initialize DB and admin

```bash
export FLASK_APP=backend.app:create_app
flask init-db
```

Default admin credentials:
- email: `admin@ppa.local`
- password: `Admin@123`

### 4) Run Flask app

```bash
flask run
```

Open: `http://127.0.0.1:5000`

### 5) Run Celery worker + beat

```bash
celery -A backend.celery_worker.celery_app worker -B --loglevel=info
```

## Notes

- SQLite is generated via SQLAlchemy programmatically.
- No frameworks beyond Flask, SQLite, Redis, Celery, Vue, Bootstrap are used.


## Basic automated tests

```bash
. .venv/bin/activate
python -m unittest tests/test_api_smoke.py -v
```
