from celery import Celery
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from redis import Redis


db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
celery_app = Celery("placement_portal")
redis_client: Redis | None = None


def init_extensions(app):
    global redis_client

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    redis_client = Redis.from_url(app.config["REDIS_URL"], decode_responses=True)

    celery_app.conf.update(
        broker_url=app.config["CELERY_BROKER_URL"],
        result_backend=app.config["CELERY_RESULT_BACKEND"],
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
    )

    class FlaskContextTask(celery_app.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app.Task = FlaskContextTask
