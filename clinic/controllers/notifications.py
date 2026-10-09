from flask import Blueprint, render_template

from clinic.controllers.helpers import current_user, require_role
from clinic.services import NotificationService

notifications_bp = Blueprint("notifications", __name__, url_prefix="/notifications")


@notifications_bp.route("/")
@require_role()
def index():
    user = current_user()
    service = NotificationService()
    notifications = service.get_notifications_for_user(user.id)
    service.mark_all_read(user.id)
    return render_template("notifications/index.html", notifications=notifications, user=user)
