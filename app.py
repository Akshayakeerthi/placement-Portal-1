from __future__ import annotations

import os
import sqlite3
from datetime import datetime
from functools import wraps
from pathlib import Path

from flask import Flask, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "placement_portal.db"

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "placement-portal-dev-secret")


def now_iso() -> str:
    return datetime.utcnow().isoformat()


# ---------- DB ----------
def get_db() -> sqlite3.Connection:
    if "db" not in g:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        g.db = conn
    return g.db


@app.teardown_appcontext
def close_db(_ex: Exception | None) -> None:
    db = g.pop("db", None)
    if db:
        db.close()


def init_db() -> None:
    db = sqlite3.connect(DATABASE)
    db.execute("PRAGMA foreign_keys = ON")
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL CHECK(role IN ('admin','company','student')),
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            is_approved INTEGER NOT NULL DEFAULT 1,
            is_blacklisted INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS company_profiles (
            user_id INTEGER PRIMARY KEY,
            company_name TEXT NOT NULL,
            hr_contact TEXT,
            website TEXT,
            description TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS student_profiles (
            user_id INTEGER PRIMARY KEY,
            full_name TEXT NOT NULL,
            email TEXT,
            department TEXT,
            cgpa REAL,
            graduation_year INTEGER,
            skills TEXT,
            placement_status TEXT NOT NULL DEFAULT 'seeking',
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS drives (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER NOT NULL,
            drive_name TEXT,
            job_title TEXT NOT NULL,
            job_description TEXT NOT NULL,
            eligibility_criteria TEXT NOT NULL,
            location TEXT,
            salary_package TEXT,
            application_deadline TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','approved','closed','rejected')),
            created_at TEXT NOT NULL,
            FOREIGN KEY (company_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            drive_id INTEGER NOT NULL,
            application_date TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'applied' CHECK(status IN ('applied','shortlisted','selected','rejected')),
            remarks TEXT,
            UNIQUE(student_id, drive_id),
            FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (drive_id) REFERENCES drives(id) ON DELETE CASCADE
        );
        """
    )

    # Lightweight migrations for older DB files created before new columns existed.
    drive_columns = {row[1] for row in db.execute("PRAGMA table_info(drives)").fetchall()}
    if "drive_name" not in drive_columns:
        db.execute("ALTER TABLE drives ADD COLUMN drive_name TEXT")

    admin = db.execute("SELECT id FROM users WHERE role='admin' LIMIT 1").fetchone()
    if not admin:
        db.execute(
            "INSERT INTO users (role, username, password_hash, is_approved, created_at) VALUES (?,?,?,?,?)",
            ("admin", "admin", generate_password_hash("admin123"), 1, now_iso()),
        )

    db.commit()
    db.close()


# ---------- Auth ----------
def login_required(role: str | None = None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user = session.get("user")
            if not user:
                flash("Please login first.", "warning")
                return redirect(url_for("login"))
            if role and user["role"] != role:
                flash("Unauthorized action.", "danger")
                return redirect(url_for("dashboard"))
            return func(*args, **kwargs)

        return wrapper

    return decorator


@app.context_processor
def inject_globals():
    return {"session_user": session.get("user")}


# ---------- Public ----------
@app.route("/")
def home():
    return render_template("home.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip().lower()
        password = request.form["password"]
        user = get_db().execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()

        if not user or not check_password_hash(user["password_hash"], password):
            flash("Invalid credentials.", "danger")
            return redirect(url_for("login"))

        if user["is_blacklisted"]:
            flash("Account is blacklisted.", "danger")
            return redirect(url_for("login"))

        if user["role"] == "company" and not user["is_approved"]:
            flash("Company account pending admin approval.", "warning")
            return redirect(url_for("login"))

        session["user"] = {"id": user["id"], "username": user["username"], "role": user["role"]}
        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.route("/register/student", methods=["GET", "POST"])
def register_student():
    if request.method == "POST":
        db = get_db()
        try:
            cur = db.execute(
                "INSERT INTO users (role, username, password_hash, is_approved, created_at) VALUES (?,?,?,?,?)",
                (
                    "student",
                    request.form["username"].strip().lower(),
                    generate_password_hash(request.form["password"]),
                    1,
                    now_iso(),
                ),
            )
            db.execute(
                """
                INSERT INTO student_profiles (user_id, full_name, email, department, cgpa, graduation_year, skills)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cur.lastrowid,
                    request.form["full_name"].strip(),
                    request.form.get("email", "").strip(),
                    request.form.get("department", "").strip(),
                    float(request.form["cgpa"]) if request.form.get("cgpa") else None,
                    int(request.form["graduation_year"]) if request.form.get("graduation_year") else None,
                    request.form.get("skills", "").strip(),
                ),
            )
            db.commit()
            flash("Student registration successful.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Username already exists.", "danger")

    return render_template("register_student.html")


@app.route("/register/company", methods=["GET", "POST"])
def register_company():
    if request.method == "POST":
        db = get_db()
        try:
            cur = db.execute(
                "INSERT INTO users (role, username, password_hash, is_approved, created_at) VALUES (?,?,?,?,?)",
                (
                    "company",
                    request.form["username"].strip().lower(),
                    generate_password_hash(request.form["password"]),
                    0,
                    now_iso(),
                ),
            )
            db.execute(
                "INSERT INTO company_profiles (user_id, company_name, hr_contact, website, description) VALUES (?,?,?,?,?)",
                (
                    cur.lastrowid,
                    request.form["company_name"].strip(),
                    request.form.get("hr_contact", "").strip(),
                    request.form.get("website", "").strip(),
                    request.form.get("description", "").strip(),
                ),
            )
            db.commit()
            flash("Company registration submitted for approval.", "info")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Username already exists.", "danger")

    return render_template("register_company.html")


@app.route("/dashboard")
@login_required()
def dashboard():
    role = session["user"]["role"]
    if role == "admin":
        return redirect(url_for("admin_dashboard"))
    if role == "company":
        return redirect(url_for("company_dashboard"))
    return redirect(url_for("student_dashboard"))


# ---------- Admin ----------
@app.route("/admin")
@login_required("admin")
def admin_dashboard():
    db = get_db()
    q = request.args.get("search", "").strip()
    like = f"%{q}%"

    companies = db.execute(
        """
        SELECT u.id, u.username, u.is_approved, u.is_blacklisted, c.company_name
        FROM users u JOIN company_profiles c ON c.user_id=u.id
        WHERE u.role='company' AND (?='' OR c.company_name LIKE ? OR u.username LIKE ? OR CAST(u.id AS TEXT) LIKE ?)
        ORDER BY u.created_at DESC
        """,
        (q, like, like, like),
    ).fetchall()

    students = db.execute(
        """
        SELECT u.id, u.username, u.is_blacklisted, s.full_name, s.department
        FROM users u JOIN student_profiles s ON s.user_id=u.id
        WHERE u.role='student' AND (?='' OR s.full_name LIKE ? OR u.username LIKE ? OR CAST(u.id AS TEXT) LIKE ?)
        ORDER BY u.created_at DESC
        """,
        (q, like, like, like),
    ).fetchall()

    pending_companies = [c for c in companies if not c["is_approved"]]

    drives = db.execute(
        """
        SELECT d.id, d.drive_name, d.job_title, d.status, d.application_deadline, c.company_name
        FROM drives d JOIN company_profiles c ON c.user_id=d.company_id
        ORDER BY d.created_at DESC
        """
    ).fetchall()

    student_applications = db.execute(
        """
        SELECT a.id, a.application_date, a.status, s.full_name, d.job_title, c.company_name
        FROM applications a
        JOIN student_profiles s ON s.user_id=a.student_id
        JOIN drives d ON d.id=a.drive_id
        JOIN company_profiles c ON c.user_id=d.company_id
        ORDER BY a.application_date DESC
        LIMIT 20
        """
    ).fetchall()

    return render_template(
        "admin_dashboard.html",
        search=q,
        companies=companies,
        students=students,
        pending_companies=pending_companies,
        drives=drives,
        student_applications=student_applications,
    )


@app.post("/admin/company/<int:user_id>/approve")
@login_required("admin")
def admin_approve_company(user_id: int):
    db = get_db()
    db.execute("UPDATE users SET is_approved=1 WHERE id=? AND role='company'", (user_id,))
    db.commit()
    flash("Company approved.", "success")
    return redirect(url_for("admin_dashboard"))


@app.post("/admin/company/<int:user_id>/blacklist")
@login_required("admin")
def admin_blacklist_company(user_id: int):
    db = get_db()
    db.execute("UPDATE users SET is_blacklisted=1 WHERE id=? AND role='company'", (user_id,))
    db.execute("UPDATE drives SET status='closed' WHERE company_id=?", (user_id,))
    db.commit()
    flash("Company blacklisted. All drives closed.", "warning")
    return redirect(url_for("admin_dashboard"))


@app.post("/admin/student/<int:user_id>/blacklist")
@login_required("admin")
def admin_blacklist_student(user_id: int):
    db = get_db()
    db.execute("UPDATE users SET is_blacklisted=1 WHERE id=? AND role='student'", (user_id,))
    db.commit()
    flash("Student blacklisted.", "warning")
    return redirect(url_for("admin_dashboard"))


@app.post("/admin/drive/<int:drive_id>/status")
@login_required("admin")
def admin_update_drive_status(drive_id: int):
    status = request.form.get("status", "")
    if status not in {"approved", "rejected", "closed"}:
        flash("Invalid drive status.", "danger")
        return redirect(url_for("admin_dashboard"))

    db = get_db()
    db.execute("UPDATE drives SET status=? WHERE id=?", (status, drive_id))
    db.commit()
    flash("Drive updated.", "success")
    return redirect(url_for("admin_dashboard"))


@app.get("/admin/drive/<int:drive_id>")
@login_required("admin")
def admin_drive_details(drive_id: int):
    drive = get_db().execute(
        """
        SELECT d.*, c.company_name
        FROM drives d JOIN company_profiles c ON c.user_id=d.company_id
        WHERE d.id=?
        """,
        (drive_id,),
    ).fetchone()
    if not drive:
        flash("Drive not found.", "danger")
        return redirect(url_for("admin_dashboard"))
    return render_template("drive_details.html", drive=drive, show_apply=False)


# ---------- Company ----------
@app.route("/company")
@login_required("company")
def company_dashboard():
    db = get_db()
    cid = session["user"]["id"]
    company = db.execute("SELECT * FROM company_profiles WHERE user_id=?", (cid,)).fetchone()

    upcoming_drives = db.execute(
        "SELECT * FROM drives WHERE company_id=? AND status IN ('pending','approved') ORDER BY created_at DESC",
        (cid,),
    ).fetchall()
    closed_drives = db.execute(
        "SELECT * FROM drives WHERE company_id=? AND status='closed' ORDER BY created_at DESC",
        (cid,),
    ).fetchall()

    return render_template(
        "company_dashboard.html",
        company=company,
        upcoming_drives=upcoming_drives,
        closed_drives=closed_drives,
    )


@app.route("/company/drive/create", methods=["GET", "POST"])
@login_required("company")
def create_drive():
    if request.method == "POST":
        db = get_db()
        db.execute(
            """
            INSERT INTO drives
            (company_id, drive_name, job_title, job_description, eligibility_criteria, location, salary_package, application_deadline, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)
            """,
            (
                session["user"]["id"],
                request.form.get("drive_name", "").strip(),
                request.form["job_title"].strip(),
                request.form["job_description"].strip(),
                request.form["eligibility_criteria"].strip(),
                request.form.get("location", "").strip(),
                request.form.get("salary_package", "").strip(),
                request.form["application_deadline"],
                now_iso(),
            ),
        )
        db.commit()
        flash("Drive created and sent to admin for approval.", "success")
        return redirect(url_for("company_dashboard"))
    return render_template("create_drive.html")


@app.get("/company/drive/<int:drive_id>")
@login_required("company")
def company_drive_details(drive_id: int):
    drive = get_db().execute(
        "SELECT * FROM drives WHERE id=? AND company_id=?", (drive_id, session["user"]["id"])
    ).fetchone()
    if not drive:
        flash("Drive not found.", "danger")
        return redirect(url_for("company_dashboard"))
    return render_template("drive_details.html", drive=drive, show_apply=False)


@app.post("/company/drive/<int:drive_id>/close")
@login_required("company")
def company_close_drive(drive_id: int):
    db = get_db()
    db.execute("UPDATE drives SET status='closed' WHERE id=? AND company_id=?", (drive_id, session["user"]["id"]))
    db.commit()
    flash("Drive marked as closed.", "warning")
    return redirect(url_for("company_dashboard"))


@app.get("/company/drive/<int:drive_id>/applications")
@login_required("company")
def company_drive_applications(drive_id: int):
    db = get_db()
    drive = db.execute("SELECT * FROM drives WHERE id=? AND company_id=?", (drive_id, session["user"]["id"])).fetchone()
    if not drive:
        flash("Drive not found.", "danger")
        return redirect(url_for("company_dashboard"))

    applications = db.execute(
        """
        SELECT a.id, a.status, a.application_date, s.full_name, s.department
        FROM applications a JOIN student_profiles s ON s.user_id=a.student_id
        WHERE a.drive_id=? ORDER BY a.application_date DESC
        """,
        (drive_id,),
    ).fetchall()
    return render_template("company_drive_applications.html", drive=drive, applications=applications)


@app.get("/company/application/<int:application_id>")
@login_required("company")
def company_application_detail(application_id: int):
    app_row = get_db().execute(
        """
        SELECT a.*, s.full_name, s.department, s.skills, d.job_title, d.id AS drive_id
        FROM applications a
        JOIN student_profiles s ON s.user_id=a.student_id
        JOIN drives d ON d.id=a.drive_id
        WHERE a.id=? AND d.company_id=?
        """,
        (application_id, session["user"]["id"]),
    ).fetchone()
    if not app_row:
        flash("Application not found.", "danger")
        return redirect(url_for("company_dashboard"))
    return render_template("application_review.html", app_row=app_row, mode="company")


@app.post("/company/application/<int:application_id>/status")
@login_required("company")
def company_update_application(application_id: int):
    status = request.form.get("status", "")
    if status not in {"applied", "shortlisted", "selected", "rejected"}:
        flash("Invalid status.", "danger")
        return redirect(request.referrer or url_for("company_dashboard"))

    db = get_db()
    db.execute(
        """
        UPDATE applications SET status=?, remarks=?
        WHERE id=? AND drive_id IN (SELECT id FROM drives WHERE company_id=?)
        """,
        (status, request.form.get("remarks", "").strip(), application_id, session["user"]["id"]),
    )
    db.commit()
    flash("Application updated.", "success")
    return redirect(url_for("company_drive_applications", drive_id=request.form["drive_id"]))


# ---------- Student ----------
@app.route("/student")
@login_required("student")
def student_dashboard():
    db = get_db()
    sid = session["user"]["id"]

    profile = db.execute("SELECT * FROM student_profiles WHERE user_id=?", (sid,)).fetchone()
    organizations = db.execute(
        """
        SELECT c.company_name, c.website
        FROM users u JOIN company_profiles c ON c.user_id=u.id
        WHERE u.role='company' AND u.is_approved=1 AND u.is_blacklisted=0
        ORDER BY c.company_name
        """
    ).fetchall()
    current_drives = db.execute(
        """
        SELECT d.*, c.company_name
        FROM drives d JOIN company_profiles c ON c.user_id=d.company_id
        WHERE d.status='approved' ORDER BY d.application_deadline
        """
    ).fetchall()
    applied_drives = db.execute(
        """
        SELECT a.id, a.status, a.application_date, d.id AS drive_id, d.job_title, c.company_name
        FROM applications a
        JOIN drives d ON d.id=a.drive_id
        JOIN company_profiles c ON c.user_id=d.company_id
        WHERE a.student_id=? ORDER BY a.application_date DESC
        """,
        (sid,),
    ).fetchall()

    return render_template(
        "student_dashboard.html",
        profile=profile,
        organizations=organizations,
        current_drives=current_drives,
        applied_drives=applied_drives,
    )


@app.route("/student/profile", methods=["GET", "POST"])
@login_required("student")
def student_profile():
    db = get_db()
    sid = session["user"]["id"]
    if request.method == "POST":
        db.execute(
            """
            UPDATE student_profiles
            SET full_name=?, email=?, department=?, cgpa=?, graduation_year=?, skills=?, placement_status=?
            WHERE user_id=?
            """,
            (
                request.form["full_name"].strip(),
                request.form.get("email", "").strip(),
                request.form.get("department", "").strip(),
                float(request.form["cgpa"]) if request.form.get("cgpa") else None,
                int(request.form["graduation_year"]) if request.form.get("graduation_year") else None,
                request.form.get("skills", "").strip(),
                request.form.get("placement_status", "seeking"),
                sid,
            ),
        )
        db.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("student_dashboard"))

    profile = db.execute("SELECT * FROM student_profiles WHERE user_id=?", (sid,)).fetchone()
    return render_template("student_profile.html", profile=profile)


@app.get("/student/drive/<int:drive_id>")
@login_required("student")
def student_drive_details(drive_id: int):
    drive = get_db().execute(
        """
        SELECT d.*, c.company_name
        FROM drives d JOIN company_profiles c ON c.user_id=d.company_id
        WHERE d.id=? AND d.status='approved'
        """,
        (drive_id,),
    ).fetchone()
    if not drive:
        flash("Drive not available.", "danger")
        return redirect(url_for("student_dashboard"))
    return render_template("drive_details.html", drive=drive, show_apply=True)


@app.post("/student/drive/<int:drive_id>/apply")
@login_required("student")
def apply_drive(drive_id: int):
    db = get_db()
    drive = db.execute("SELECT id FROM drives WHERE id=? AND status='approved'", (drive_id,)).fetchone()
    if not drive:
        flash("Drive unavailable.", "danger")
        return redirect(url_for("student_dashboard"))

    try:
        db.execute(
            "INSERT INTO applications (student_id, drive_id, application_date, status) VALUES (?, ?, ?, 'applied')",
            (session["user"]["id"], drive_id, now_iso()),
        )
        db.commit()
        flash("Application submitted.", "success")
    except sqlite3.IntegrityError:
        flash("You already applied to this drive.", "warning")
    return redirect(url_for("student_dashboard"))


@app.get("/student/history")
@login_required("student")
def student_history():
    sid = session["user"]["id"]
    db = get_db()
    student = db.execute("SELECT * FROM student_profiles WHERE user_id=?", (sid,)).fetchone()
    history = db.execute(
        """
        SELECT a.application_date, a.status, a.remarks, d.job_title, c.company_name
        FROM applications a
        JOIN drives d ON d.id=a.drive_id
        JOIN company_profiles c ON c.user_id=d.company_id
        WHERE a.student_id=? ORDER BY a.application_date DESC
        """,
        (sid,),
    ).fetchall()
    return render_template("student_history.html", student=student, history=history)


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)


with app.app_context():
    init_db()
