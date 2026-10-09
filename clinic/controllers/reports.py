from datetime import date, datetime, timedelta

from flask import Blueprint, render_template, request

from clinic.controllers.helpers import require_role
from clinic.repositories import ClinicRepository
from clinic.services import ReportService

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")


@reports_bp.route("/")
@require_role("secretary")
def index():
    today = date.today()
    default_start = (today - timedelta(days=30)).isoformat()
    default_end = today.isoformat()

    start_str = request.args.get("start_date", default_start)
    end_str = request.args.get("end_date", default_end)

    try:
        start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_str, "%Y-%m-%d").date()
    except ValueError:
        start_date = today - timedelta(days=30)
        end_date = today
        start_str = start_date.isoformat()
        end_str = end_date.isoformat()

    repository = ClinicRepository()
    service = ReportService(repository)

    volume_by_doctor = service.appointment_volume(start_date, end_date)
    workload = service.workload_by_department(start_date, end_date)
    avg_wait = service.average_wait_time_minutes(start_date, end_date)
    no_show_rate = service.no_show_rate(start_date, end_date)

    return render_template(
        "reports/index.html",
        start_date=start_str,
        end_date=end_str,
        volume_by_doctor=volume_by_doctor,
        workload=workload,
        avg_wait=avg_wait,
        no_show_rate=no_show_rate,
    )
