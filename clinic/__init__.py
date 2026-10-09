from pathlib import Path

from flask import Flask

from clinic.config import Config
from clinic.extensions import db
from clinic.controllers.appointments import appointments_bp
from clinic.controllers.auth import auth_bp
from clinic.controllers.availability import availability_bp
from clinic.controllers.dashboard import dashboard_bp
from clinic.controllers.notifications import notifications_bp
from clinic.controllers.patient_flow import patient_flow_bp
from clinic.controllers.reports import reports_bp
from clinic.cli import register_commands


def create_app(config_object=Config):
    project_root = Path(__file__).resolve().parent.parent
    app = Flask(
        __name__,
        template_folder=str(project_root / "templates"),
        static_folder=str(project_root / "static"),
    )
    app.config.from_object(config_object)

    db.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(appointments_bp)
    app.register_blueprint(availability_bp)
    app.register_blueprint(patient_flow_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(notifications_bp)
    register_commands(app)

    @app.context_processor
    def inject_unread_notifications():
        """Make unread notification count available in every template."""
        from clinic.controllers.helpers import current_user
        from clinic.services.notification_service import NotificationService
        user = current_user()
        if user:
            count = NotificationService().get_unread_count(user.id)
            return {"unread_notifications": count}
        return {"unread_notifications": 0}

    return app
