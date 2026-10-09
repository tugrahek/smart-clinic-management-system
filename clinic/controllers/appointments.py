from datetime import date, datetime

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from clinic.controllers.helpers import current_user, require_role
from clinic.repositories import ClinicRepository
from clinic.services import AppointmentService

appointments_bp = Blueprint("appointments", __name__, url_prefix="/appointments")


@appointments_bp.route("/")
@require_role("secretary", "doctor", "patient")
def index():
    repository = ClinicRepository()
    user = current_user()
    doctor_id = None
    patient_email = None
    if user.role == "doctor" and user.doctor_profile:
        doctor_id = user.doctor_profile.id
    if user.role == "patient":
        patient_email = user.email

    appointments = repository.list_appointments(doctor_id=doctor_id, patient_email=patient_email)
    return render_template("appointments/index.html", appointments=appointments, user=user)


@appointments_bp.route("/new", methods=["GET", "POST"])
@require_role("secretary", "patient")
def new():
    repository = ClinicRepository()
    service = AppointmentService(repository)
    doctors = repository.list_doctors()

    selected_doctor_id = request.values.get("doctor_id", type=int)
    selected_date = request.values.get("appointment_date")
    parsed_date = None
    if selected_date:
        parsed_date = datetime.strptime(selected_date, "%Y-%m-%d").date()

    slots = []
    if selected_doctor_id and parsed_date:
        slots = service.available_slots_for_doctor(selected_doctor_id, parsed_date)

    if request.method == "POST":
        appointment, errors = service.create_appointment(
            request.form,
            created_by_user_id=session.get("user_id"),
        )
        if errors:
            for error in errors:
                flash(error, "error")
        else:
            flash("Appointment created successfully.", "success")
            return redirect(url_for("appointments.index"))

    return render_template(
        "appointments/new.html",
        doctors=doctors,
        slots=slots,
        selected_doctor_id=selected_doctor_id,
        selected_date=selected_date or date.today().isoformat(),
    )


@appointments_bp.route("/<int:appointment_id>/check-in", methods=["POST"])
@require_role("secretary")
def check_in(appointment_id):
    priority = int(request.form.get("priority", 0))
    flow_record, errors = AppointmentService().check_in_appointment(
        appointment_id, priority=priority
    )
    if errors:
        flash(errors[0], "error")
    else:
        flash(
            f"Patient checked in — queue #{flow_record.queue_number} "
            f"({'Emergency' if priority == 2 else 'Urgent' if priority == 1 else 'Normal'}).",
            "success",
        )
    return redirect(url_for("patient_flow.index"))


@appointments_bp.route("/<int:appointment_id>/cancel", methods=["POST"])
@require_role("secretary", "patient")
def cancel(appointment_id):
    user = current_user()
    _, errors = AppointmentService().cancel_appointment(appointment_id, cancelled_by_user=user)
    if errors:
        flash(errors[0], "error")
    else:
        flash("Appointment cancelled successfully.", "success")
    return redirect(url_for("appointments.index"))


@appointments_bp.route("/<int:appointment_id>/reschedule", methods=["GET", "POST"])
@require_role("secretary", "patient")
def reschedule(appointment_id):
    repository = ClinicRepository()
    service = AppointmentService(repository)
    user = current_user()
    appointment = repository.get_appointment(appointment_id)

    if not appointment:
        flash("Appointment not found.", "error")
        return redirect(url_for("appointments.index"))

    selected_date = request.values.get(
        "appointment_date", appointment.appointment_date.isoformat()
    )
    try:
        parsed_date = datetime.strptime(selected_date, "%Y-%m-%d").date()
    except ValueError:
        parsed_date = appointment.appointment_date

    slots = service.available_slots_for_doctor(appointment.doctor_id, parsed_date)

    if request.method == "POST":
        _, errors = service.reschedule_appointment(
            appointment_id,
            request.form["appointment_date"],
            request.form["appointment_time"],
            rescheduled_by_user=user,
        )
        if errors:
            for error in errors:
                flash(error, "error")
        else:
            flash("Appointment rescheduled successfully.", "success")
            return redirect(url_for("appointments.index"))

    return render_template(
        "appointments/reschedule.html",
        appointment=appointment,
        slots=slots,
        selected_date=selected_date,
    )
