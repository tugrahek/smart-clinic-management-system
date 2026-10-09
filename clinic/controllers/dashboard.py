from datetime import date

from flask import Blueprint, render_template

from clinic.controllers.helpers import current_user, require_role
from clinic.repositories import ClinicRepository

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
@require_role()
def index():
    user = current_user()
    repository = ClinicRepository()
    today = date.today()

    if user.role == "secretary":
        appointments_today = repository.list_appointments(appointment_date=today)
        flow_items = repository.list_patient_flow(today_only=True)
        active_flow = [
            f for f in flow_items
            if f.current_status in ("waiting", "in_consultation", "assessment")
        ]
        stats = {
            "total": len(appointments_today),
            "scheduled": sum(1 for a in appointments_today if a.status == "scheduled"),
            "in_progress": sum(
                1 for a in appointments_today
                if a.status in ("checked_in", "waiting", "in_consultation", "assessment")
            ),
            "done": sum(1 for a in appointments_today if a.status == "done"),
            "cancelled": sum(1 for a in appointments_today if a.status == "cancelled"),
        }
        return render_template(
            "dashboard/secretary.html",
            user=user,
            appointments_today=appointments_today,
            flow_items=active_flow,
            stats=stats,
            today=today,
        )

    if user.role == "doctor":
        doctor = user.doctor_profile
        appointments_today = repository.list_appointments(
            doctor_id=doctor.id, appointment_date=today
        )
        flow_items = repository.list_patient_flow(today_only=True)
        my_flow = [
            f for f in flow_items
            if f.appointment and f.appointment.doctor_id == doctor.id
        ]
        current_patient = next(
            (f for f in my_flow if f.current_status == "in_consultation"), None
        )
        next_patient = next(
            (f for f in my_flow if f.current_status == "waiting"), None
        )
        stats = {
            "total": len(appointments_today),
            "waiting": sum(1 for f in my_flow if f.current_status == "waiting"),
            "done": sum(1 for a in appointments_today if a.status == "done"),
        }
        return render_template(
            "dashboard/doctor.html",
            user=user,
            appointments_today=appointments_today,
            current_patient=current_patient,
            next_patient=next_patient,
            stats=stats,
            today=today,
        )

    return render_template("dashboard/patient.html", user=user)


@dashboard_bp.route("/not-implemented")
@require_role()
def not_implemented():
    return render_template("shared/not_implemented.html")
