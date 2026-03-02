# Placement Portal Application (Flask + SQLite)

A wireframe-aligned campus placement portal with role-specific dashboards.

## Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

- URL: `http://127.0.0.1:5000`
- Admin login:
  - Username: `admin`
  - Password: `admin123`

## Role Workflows
- **Admin**
  - Search students/organizations
  - Approve company registrations
  - Approve/reject/close drives
  - Blacklist company/student
  - Review recent student applications
- **Company**
  - Register (admin approval required)
  - Create drives
  - View drive details
  - Review each application and update status/remarks
- **Student**
  - Register and edit profile
  - View organizations and current approved drives
  - Open drive details and apply
  - View application history

## Database
Database is created **programmatically** in `init_db()` (`app.py`) using SQLite (`placement_portal.db`).

## Troubleshooting
If you upgraded from an older version and see an error like `no such column: d.drive_name`, just restart the app once with the latest code. The app now auto-migrates the `drives` table and adds missing columns programmatically.
