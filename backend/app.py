import os

from flask import Flask, jsonify, render_template
from flask_cors import CORS

from backend.config import Config
from backend.extensions import db, init_extensions
from backend.models import User, UserRole
from backend.routes.admin_routes import bp as admin_bp
from backend.routes.auth_routes import bp as auth_bp
from backend.routes.company_routes import bp as company_bp
from backend.routes.student_routes import bp as student_bp
from backend.tasks import jobs as _jobs  # noqa: F401


def create_app():
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), "..", "frontend"),
        static_folder=os.path.join(os.path.dirname(__file__), "..", "frontend"),
        static_url_path="/frontend",
    )
    app.config.from_object(Config)
    CORS(app)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["EXPORT_FOLDER"], exist_ok=True)
    os.makedirs(app.config["REPORT_FOLDER"], exist_ok=True)

    init_extensions(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(company_bp)
    app.register_blueprint(student_bp)

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.cli.command("init-db")
    def init_db():
        db.create_all()
        admin = User.query.filter_by(role=UserRole.ADMIN).first()
        if admin is None:
            admin = User(
                name=app.config["ADMIN_NAME"],
                email=app.config["ADMIN_EMAIL"].lower(),
                role=UserRole.ADMIN,
            )
            admin.set_password(app.config["ADMIN_PASSWORD"])
            db.session.add(admin)
            db.session.commit()
            print("Admin created")
        else:
            print("Admin already exists")

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
