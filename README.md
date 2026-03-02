# Placement Portal Application (Flask + SQLite)

## Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

- URL: `http://127.0.0.1:5000`
- Default admin login:
  - Username: `admin`
  - Password: `admin123`

## Features
- **Admin**: approve/reject companies and drives, search users, blacklist student/company.
- **Company**: register (approval required), create drives, review applications, update status.
- **Student**: register, edit profile, apply to approved drives, track application history.

## Database
SQLite database file (`placement_portal.db`) is created automatically via `init_db()` in `app.py`.
No manual DB creation is required.
