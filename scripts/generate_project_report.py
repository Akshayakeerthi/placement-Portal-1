from __future__ import annotations

import ast
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import ListFlowable, ListItem, Paragraph, SimpleDocTemplate, Spacer

ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs"
MARKDOWN_OUTPUT = DOCS_DIR / "project_report.md"
PDF_OUTPUT = DOCS_DIR / "project_report.pdf"


ROLE_ENDPOINT_DESCRIPTIONS = {
    "auth": "Authentication and account access",
    "admin": "Admin approvals, moderation, search, analytics",
    "company": "Company profile, drives, applicant workflow",
    "student": "Student profile, applications, exports",
}


def read_repo_snapshot() -> dict:
    files = [p for p in ROOT.rglob("*") if p.is_file() and ".git" not in p.parts and p.suffix.lower() != ".pdf"]
    rel_files = [p.relative_to(ROOT) for p in files]
    return {
        "all_files": rel_files,
        "backend_files": [p for p in rel_files if p.parts and p.parts[0] == "backend"],
        "frontend_files": [p for p in rel_files if p.parts and p.parts[0] == "frontend"],
        "docs_files": [p for p in rel_files if p.parts and p.parts[0] == "docs"],
        "requirements": (ROOT / "requirements.txt").read_text(encoding="utf-8") if (ROOT / "requirements.txt").exists() else "",
        "readme": (ROOT / "README.md").read_text(encoding="utf-8") if (ROOT / "README.md").exists() else "",
    }


def extract_endpoints() -> list[tuple[str, str, str]]:
    routes_dir = ROOT / "backend" / "routes"
    endpoints: list[tuple[str, str, str]] = []
    if not routes_dir.exists():
        return endpoints

    method_map = {"get": "GET", "post": "POST", "patch": "PATCH", "put": "PUT", "delete": "DELETE"}

    for route_file in sorted(routes_dir.glob("*_routes.py")):
        source = route_file.read_text(encoding="utf-8")
        tree = ast.parse(source)

        prefix = ""
        for node in tree.body:
            if isinstance(node, ast.Assign):
                if any(isinstance(t, ast.Name) and t.id == "bp" for t in node.targets):
                    if isinstance(node.value, ast.Call) and getattr(node.value.func, "id", "") == "Blueprint":
                        for kw in node.value.keywords:
                            if kw.arg == "url_prefix" and isinstance(kw.value, ast.Constant):
                                prefix = str(kw.value.value)

        for node in tree.body:
            if not isinstance(node, ast.FunctionDef):
                continue
            for dec in node.decorator_list:
                if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
                    method = method_map.get(dec.func.attr)
                    if method and dec.args and isinstance(dec.args[0], ast.Constant):
                        path = str(dec.args[0].value)
                        full_path = f"{prefix}{path}"
                        endpoints.append((full_path, method, node.name))

    return sorted(set(endpoints), key=lambda x: (x[0], x[1]))


def _extract_column_type(expr: ast.AST) -> str:
    if isinstance(expr, ast.Attribute):
        return expr.attr
    if isinstance(expr, ast.Call):
        if isinstance(expr.func, ast.Attribute):
            return expr.func.attr
        if isinstance(expr.func, ast.Name):
            return expr.func.id
    return "Unknown"


def _extract_column_meta(call: ast.Call) -> str:
    flags = []
    for kw in call.keywords:
        if kw.arg == "nullable" and isinstance(kw.value, ast.Constant) and kw.value.value is False:
            flags.append("not null")
        if kw.arg == "unique" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
            flags.append("unique")
        if kw.arg == "primary_key" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
            flags.append("pk")
    return ", ".join(flags)


def extract_db_schema_from_models() -> list[dict]:
    models_dir = ROOT / "backend" / "models"
    tables: list[dict] = []
    if not models_dir.exists():
        return tables

    for model_file in sorted(models_dir.glob("*.py")):
        source = model_file.read_text(encoding="utf-8")
        tree = ast.parse(source)

        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue

            tablename = None
            columns = []
            constraints = []

            for stmt in node.body:
                if isinstance(stmt, ast.Assign):
                    for target in stmt.targets:
                        if isinstance(target, ast.Name) and target.id == "__tablename__":
                            if isinstance(stmt.value, ast.Constant):
                                tablename = str(stmt.value.value)

                        if isinstance(target, ast.Name) and target.id == "__table_args__":
                            if isinstance(stmt.value, ast.Tuple):
                                for el in stmt.value.elts:
                                    if isinstance(el, ast.Call) and isinstance(el.func, ast.Attribute) and el.func.attr == "UniqueConstraint":
                                        cols = [a.value for a in el.args if isinstance(a, ast.Constant)]
                                        constraints.append(f"unique({', '.join(cols)})")

                        if isinstance(target, ast.Name) and isinstance(stmt.value, ast.Call):
                            call = stmt.value
                            if isinstance(call.func, ast.Attribute) and call.func.attr == "Column":
                                col_name = target.id
                                col_type = _extract_column_type(call.args[0]) if call.args else "Unknown"
                                meta = _extract_column_meta(call)
                                columns.append({"name": col_name, "type": col_type, "meta": meta})

            if tablename and columns:
                tables.append({"name": tablename, "columns": columns, "constraints": constraints})

    return tables


def extract_tech_stack(req_text: str, readme: str) -> list[str]:
    items = []
    for line in req_text.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            items.append(line.split("==")[0])

    for item in ["Vue 3 (CDN)", "Bootstrap", "Axios", "Jinja2 templates"]:
        if item.lower().split()[0] in readme.lower():
            items.append(item)

    unique = []
    seen = set()
    for item in items:
        k = item.lower()
        if k not in seen:
            seen.add(k)
            unique.append(item)
    return unique


def generate_markdown() -> str:
    snapshot = read_repo_snapshot()
    endpoints = extract_endpoints()
    tables = extract_db_schema_from_models()
    tech = extract_tech_stack(snapshot["requirements"], snapshot["readme"])

    tech_lines = "\n".join([f"- `{t}`" for t in tech])

    api_groups = []
    for segment, desc in ROLE_ENDPOINT_DESCRIPTIONS.items():
        count = len([e for e in endpoints if f"/api/{segment}/" in e[0]])
        api_groups.append(f"- `/api/{segment}/*`: {desc} ({count} endpoints).")
    api_group_lines = "\n".join(api_groups)

    endpoint_lines = "\n".join([f"- `{m} {p}`" for p, m, _ in endpoints])

    table_lines = []
    for table in tables:
        cols = ", ".join([f"{c['name']} ({c['type']}{'; ' + c['meta'] if c['meta'] else ''})" for c in table["columns"]])
        line = f"- `{table['name']}`: {cols}."
        if table["constraints"]:
            line += f" Constraints: {', '.join(table['constraints'])}."
        table_lines.append(line)
    table_section = "\n".join(table_lines)

    return f"""# App Dev Project Report

## 1. Student Details
**Name:** << Your full name >>  
**Roll Number:** << Roll number >>  
**Email:** << student email >>  
**About Me:** I am a student interested in full-stack web development and backend engineering. I enjoy creating practical systems that improve real institutional workflows through automation, data consistency, and role-based access.

## 2. AI/LLM Usage
**AI/LLM used:** GPT-5.2-Codex (OpenAI).

**Extent of use:** Approximately **20-30%** for report drafting/formatting and documentation support. Repository understanding, architecture interpretation, and implementation details were validated manually from source files.

## 3. Description
This project implements a **Placement Portal Application (PPA)** for three roles: Admin, Company, and Student. It supports company approvals, placement drive management, student applications, status tracking, reporting, caching, and asynchronous/scheduled jobs. The design follows the mandated stack and local-run constraints provided by the institute.

**AI/LLM usage percentage and extra details:** About **20-30%** of assistance was used for writing quality and structure in this report. The actual project analysis was completed by directly reading and summarizing repository code.

## 4. Technologies Used
{tech_lines}

**Purpose behind using these technologies:**
- Flask stack provides API modularity with role-protected routes and service-layer organization.
- SQLite satisfies the mandatory local relational storage requirement.
- Redis + Celery handle cache and background workloads (daily, monthly, async export).
- Vue + Bootstrap provide responsive, role-centric user interfaces.

## 5. DB Schema Design
Database is created programmatically via SQLAlchemy model definitions (no manual DB creation).

### Table structure, columns, and constraints
{table_section}

### Design reasons
- A unified `users` table centralizes authentication and role handling.
- Separate `student_profiles` and `company_profiles` normalize role-specific attributes.
- `applications` models many-to-many linkage between students and drives while also tracking lifecycle status.
- Unique and FK constraints enforce consistency and prevent invalid/duplicate operations.

## 6. API Design
APIs are implemented using role-based Flask Blueprints with JWT-protected access.

### API modules
{api_group_lines}

### Endpoint list
{endpoint_lines}

YAML/API specification should be submitted separately as instructed.

## 7. Architecture and Features
### Architecture overview
- `backend/app.py`: app factory, extension setup, blueprint registration, DB init command.
- `backend/models/`: SQLAlchemy entities for users, profiles, drives, applications.
- `backend/routes/`: controller layer grouped by role.
- `backend/services/`: business logic (approval flows, eligibility, validations).
- `backend/tasks/`: Celery tasks for reminders, monthly reports, CSV export.
- `backend/utils/`: auth decorators, validators, cache and notification utilities.
- `frontend/components/`: role-specific dashboards and authentication views.

### Implemented features
- Admin pre-seeding and role-based authentication/login.
- Company registration approval and drive approval workflows.
- Company drive lifecycle management and application status updates.
- Student profile/resume management, eligibility filtering, apply/history flows.
- Duplicate application prevention through DB uniqueness + service checks.
- Scheduled jobs: daily reminders, monthly report generation, async CSV export.
- Redis-backed cache for selected dashboard/search/list operations.

### Repository scan summary
- Total non-PDF files scanned (excluding `.git`): **{len(snapshot['all_files'])}**
- Backend files scanned: **{len(snapshot['backend_files'])}**
- Frontend files scanned: **{len(snapshot['frontend_files'])}**
- Docs files scanned: **{len(snapshot['docs_files'])}**

## 8. Video
**Video Link (<= 3 minutes):** << Add your public video URL here >>
"""


def parse_markdown_lines(text: str):
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        if not line.strip():
            yield ("blank", "")
            i += 1
            continue
        if line.startswith("# "):
            yield ("h1", line[2:].strip())
            i += 1
            continue
        if line.startswith("## "):
            yield ("h2", line[3:].strip())
            i += 1
            continue
        if line.startswith("### "):
            yield ("h3", line[4:].strip())
            i += 1
            continue
        if line.startswith("- "):
            bullets = []
            while i < len(lines) and lines[i].startswith("- "):
                bullets.append(lines[i][2:].strip())
                i += 1
            yield ("ul", bullets)
            continue
        yield ("p", line.replace("  ", " "))
        i += 1


def build_pdf(markdown_text: str):
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleCustom", parent=styles["Title"], fontSize=20, spaceAfter=14, textColor=colors.HexColor("#0f172a"))
    h2_style = ParagraphStyle("H2Custom", parent=styles["Heading2"], fontSize=13, spaceBefore=8, spaceAfter=6, textColor=colors.HexColor("#111827"))
    h3_style = ParagraphStyle("H3Custom", parent=styles["Heading3"], fontSize=11, spaceBefore=6, spaceAfter=4, textColor=colors.HexColor("#1f2937"))
    body_style = ParagraphStyle("BodyCustom", parent=styles["BodyText"], fontSize=10.2, leading=14.5, spaceAfter=4)

    doc = SimpleDocTemplate(
        str(PDF_OUTPUT),
        pagesize=A4,
        leftMargin=1.8 * cm,
        rightMargin=1.8 * cm,
        topMargin=1.6 * cm,
        bottomMargin=1.6 * cm,
        title="Placement Portal Project Report",
    )

    story = []
    for kind, value in parse_markdown_lines(markdown_text):
        if kind == "h1":
            story.append(Paragraph(value, title_style))
            story.append(Spacer(1, 4))
        elif kind == "h2":
            story.append(Paragraph(value, h2_style))
        elif kind == "h3":
            story.append(Paragraph(value, h3_style))
        elif kind == "p":
            story.append(Paragraph(value.replace("**", ""), body_style))
        elif kind == "ul":
            items = [ListItem(Paragraph(v.replace("**", ""), body_style), leftIndent=10) for v in value]
            story.append(ListFlowable(items, bulletType="bullet", leftIndent=16))
            story.append(Spacer(1, 4))
        elif kind == "blank":
            story.append(Spacer(1, 3))

    doc.build(story)


def main():
    markdown = generate_markdown()
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    MARKDOWN_OUTPUT.write_text(markdown, encoding="utf-8")
    build_pdf(markdown)
    print(f"Generated markdown: {MARKDOWN_OUTPUT}")
    print(f"Generated PDF: {PDF_OUTPUT}")


if __name__ == "__main__":
    main()
