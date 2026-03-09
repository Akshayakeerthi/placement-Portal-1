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
  - daily reminders (email + optional chat webhook)
  - monthly report generation (HTML + admin email)
  - CSV export for student history

## API modules

- `/api/auth/*` - login/register
- `/api/admin/*` - dashboard, approvals, search, blacklist, reports
- `/api/company/*` - profile, drives, applicants, application updates
- `/api/student/*` - profile, resume upload, eligible drives, apply, history, csv export

---

## Quick run paths

- **Path A (Manual run):** Use steps 1-5 below (venv + redis + flask + celery).
- **Path B (Docker Compose run):** Use step 6 directly; `docker compose up --build` handles startup for the full stack.

## Complete setup and run steps

> Run all commands from project root: `placement-Portal-1/`

### 1) Create and activate virtual environment

#### Linux / macOS / WSL

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

#### Windows Command Prompt

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2) Start Redis

Choose **one** option.

#### Option A: Local Redis command (Linux/WSL)

```bash
redis-server
```

#### Option B: Docker Redis (Windows/macOS/Linux)

```bash
docker run -d --name ppa-redis -p 6379:6379 redis:7
```

Verify Redis:

```bash
redis-cli -h 127.0.0.1 -p 6379 ping
```

Should return `PONG`.

> If Redis is not on localhost, set `REDIS_URL` before running Flask/Celery.


### Notification environment variables (for reminders/reports)

Set these before running Flask/Celery if you want real email/chat delivery:

- `SMTP_HOST` (required for real email delivery)
- `SMTP_PORT` (default: `25`)
- `SMTP_USE_TLS` (`1` to enable TLS)
- `SMTP_USERNAME`, `SMTP_PASSWORD` (optional auth)
- `MAIL_FROM` (default: `noreply@ppa.local`)
- `MAIL_SUPPRESS_SEND=1` (testing mode, captures emails in-memory)
- `CHAT_WEBHOOK_URL` (optional Google Chat webhook URL for daily summary ping)

### 3) Configure Flask app and initialize DB

#### Linux / macOS / WSL

```bash
export FLASK_APP=backend.app:create_app
flask init-db
```

#### Windows Command Prompt

```bat
set FLASK_APP=backend.app:create_app
flask init-db
```

Default admin credentials:
- email: `admin@ppa.local`
- password: `Admin@123`

### 4) Run Flask API + frontend entry page

```bash
flask run
```

Open: `http://127.0.0.1:5000`

### 5) Run Celery worker + beat scheduler (new terminal)

```bash
celery -A backend.celery_worker.celery_app worker -B --loglevel=info
```


### 6) Run with Docker Compose (optional)

Build and start all services (Flask, Redis, Celery worker, Celery beat):

```bash
docker compose up --build
```

Yes — this is enough to start the application stack for local development.
After containers are up, open: `http://127.0.0.1:5000`

Run in background:

```bash
docker compose up --build -d
```

Stop all services:

```bash
docker compose down
```

The Docker setup includes:
- `Dockerfile` for the Flask/Celery runtime image
- `docker-compose.yml` with services: `redis`, `flask`, `celery`, `celery_beat`
- Flask service auto-runs `flask init-db` before starting the server

Admin login credentials (same for Docker and non-Docker runs):
- email: `admin@ppa.local`
- password: `Admin@123`

### 7) (Optional) Run automated smoke tests

#### Linux / macOS / WSL

```bash
. .venv/bin/activate
python -m unittest tests/test_api_smoke.py -v
```

#### Windows Command Prompt

```bat
.venv\Scripts\activate
python -m unittest tests\test_api_smoke.py -v
```

---

## Notes

- SQLite is generated via SQLAlchemy programmatically.
- No frameworks beyond Flask, SQLite, Redis, Celery, Vue, Bootstrap are used.
- Keep Redis, Flask, and Celery in the same runtime environment (all WSL or all Windows) for easiest connectivity.


### Registration payload

`POST /api/auth/register` now expects: `name`, `email`, `password`, `confirm_password`, `role`.
