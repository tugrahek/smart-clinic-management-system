from datetime import datetime

from clinic.models import Appointment, PatientFlow
from clinic.repositories import ClinicRepository
from clinic.services.time_slots import build_time_slots


class AppointmentService:
    def __init__(self, repository=None):
        self.repository = repository or ClinicRepository()

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def create_appointment(self, form_data, created_by_user_id=None):
        errors = self._validate_create_form(form_data)
        if errors:
            return None, errors

        doctor_id = int(form_data["doctor_id"])
        appointment_date = datetime.strptime(form_data["appointment_date"], "%Y-%m-%d").date()
        appointment_time = datetime.strptime(form_data["appointment_time"], "%H:%M").time()

        if self.repository.find_appointment_slot(doctor_id, appointment_date, appointment_time):
            return None, ["This doctor already has an appointment at the selected time."]

        if not self._slot_is_available(doctor_id, appointment_date, appointment_time):
            return None, ["The selected time is outside the doctor's available schedule."]

        patient = self.repository.get_or_create_patient(
            {
                "national_id": form_data["national_id"],
                "full_name": form_data["patient_name"],
                "phone": form_data.get("phone"),
                "email": form_data.get("email"),
                "birth_date": None,
                "gender": form_data.get("gender"),
                "address": None,
                "emergency_contact": None,
            }
        )
        appointment = Appointment(
            patient=patient,
            doctor_id=doctor_id,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            reason=form_data["reason"].strip(),
            created_by_user_id=created_by_user_id,
        )
        self.repository.add_appointment(appointment)
        self.repository.flush()

        self._notify_patient_appointment_created(patient, appointment)
        self.repository.commit()
        return appointment, []

    # ------------------------------------------------------------------
    # Cancel
    # ------------------------------------------------------------------

    def cancel_appointment(self, appointment_id, cancelled_by_user):
        appointment = self.repository.get_appointment(appointment_id)
        if not appointment:
            return None, ["Appointment not found."]
        if appointment.status in ("done", "cancelled"):
            return None, ["This appointment cannot be cancelled."]
        if cancelled_by_user.role == "patient":
            if appointment.patient.email != cancelled_by_user.email:
                return None, ["You can only cancel your own appointments."]

        appointment.status = "cancelled"
        if (
            appointment.flow_record
            and appointment.flow_record.current_status not in ("done", "cancelled")
        ):
            appointment.flow_record.current_status = "cancelled"

        self._notify_patient_appointment_cancelled(appointment.patient, appointment)
        self.repository.commit()
        return appointment, []

    # ------------------------------------------------------------------
    # Reschedule
    # ------------------------------------------------------------------

    def reschedule_appointment(self, appointment_id, new_date_str, new_time_str, rescheduled_by_user):
        appointment = self.repository.get_appointment(appointment_id)
        if not appointment:
            return None, ["Appointment not found."]
        if appointment.status in ("done", "cancelled", "in_consultation"):
            return None, ["This appointment cannot be rescheduled."]
        if rescheduled_by_user.role == "patient":
            if appointment.patient.email != rescheduled_by_user.email:
                return None, ["You can only reschedule your own appointments."]

        new_date = datetime.strptime(new_date_str, "%Y-%m-%d").date()
        new_time = datetime.strptime(new_time_str, "%H:%M").time()

        existing = self.repository.find_appointment_slot(appointment.doctor_id, new_date, new_time)
        if existing and existing.id != appointment_id:
            return None, ["That time slot is already booked."]

        if not self._slot_is_available(appointment.doctor_id, new_date, new_time):
            return None, ["The selected time is outside the doctor's available schedule."]

        old_date = appointment.appointment_date
        old_time = appointment.appointment_time
        appointment.appointment_date = new_date
        appointment.appointment_time = new_time
        appointment.status = "scheduled"

        self._notify_patient_appointment_rescheduled(
            appointment.patient, appointment, old_date, old_time
        )
        self.repository.commit()
        return appointment, []

    # ------------------------------------------------------------------
    # Check-in
    # ------------------------------------------------------------------

    def check_in_appointment(self, appointment_id, priority=0):
        appointment = self.repository.get_appointment(appointment_id)
        if not appointment:
            return None, ["Appointment could not be found."]
        if appointment.flow_record:
            return appointment.flow_record, []

        flow_record = PatientFlow(
            patient_id=appointment.patient_id,
            appointment_id=appointment.id,
            current_status="waiting",
            priority=priority,
            queue_number=self.repository.next_queue_number(),
        )
        appointment.status = "checked_in"
        self.repository.add_patient_flow(flow_record)
        self.repository.commit()
        return flow_record, []

    # ------------------------------------------------------------------
    # Slot helpers
    # ------------------------------------------------------------------

    def available_slots_for_doctor(self, doctor_id, appointment_date):
        availabilities = self.repository.list_doctor_availability(doctor_id, appointment_date)
        appointments = self.repository.list_appointments(doctor_id, appointment_date=appointment_date)
        booked = {item.appointment_time for item in appointments if item.status != "cancelled"}

        slots = []
        for availability in availabilities:
            for slot in build_time_slots(
                availability.start_time,
                availability.end_time,
                availability.slot_minutes,
            ):
                slots.append(
                    {
                        "time": slot,
                        "is_available": availability.status == "available" and slot not in booked,
                        "is_booked": slot in booked,
                    }
                )
        return slots

    def _slot_is_available(self, doctor_id, appointment_date, appointment_time):
        for availability in self.repository.list_doctor_availability(doctor_id, appointment_date):
            if (
                availability.status == "available"
                and availability.start_time <= appointment_time < availability.end_time
            ):
                return True
        return False

    def _validate_create_form(self, form_data):
        required = [
            "national_id",
            "patient_name",
            "doctor_id",
            "appointment_date",
            "appointment_time",
            "reason",
        ]
        if any(not form_data.get(f) for f in required):
            return ["Please fill in all required appointment fields."]
        return []

    # ------------------------------------------------------------------
    # Notification helpers
    # ------------------------------------------------------------------

    def _notify_patient_appointment_created(self, patient, appointment):
        try:
            from clinic.services.notification_service import NotificationService
            NotificationService(self.repository).notify_patient(
                patient=patient,
                title="Appointment Confirmed",
                body=(
                    f"Your appointment with {appointment.doctor.user.full_name} on "
                    f"{appointment.appointment_date} at "
                    f"{appointment.appointment_time.strftime('%H:%M')} has been confirmed."
                ),
                category="info",
            )
        except Exception:
            pass

    def _notify_patient_appointment_cancelled(self, patient, appointment):
        try:
            from clinic.services.notification_service import NotificationService
            NotificationService(self.repository).notify_patient(
                patient=patient,
                title="Appointment Cancelled",
                body=(
                    f"Your appointment with {appointment.doctor.user.full_name} on "
                    f"{appointment.appointment_date} at "
                    f"{appointment.appointment_time.strftime('%H:%M')} has been cancelled."
                ),
                category="warning",
            )
        except Exception:
            pass

    def _notify_patient_appointment_rescheduled(self, patient, appointment, old_date, old_time):
        try:
            from clinic.services.notification_service import NotificationService
            NotificationService(self.repository).notify_patient(
                patient=patient,
                title="Appointment Rescheduled",
                body=(
                    f"Your appointment with {appointment.doctor.user.full_name} has been moved "
                    f"from {old_date} {old_time.strftime('%H:%M')} to "
                    f"{appointment.appointment_date} at "
                    f"{appointment.appointment_time.strftime('%H:%M')}."
                ),
                category="warning",
            )
        except Exception:
            pass
