from datetime import datetime

from clinic.models import DoctorAvailability
from clinic.repositories import ClinicRepository


class AvailabilityService:
    def __init__(self, repository=None):
        self.repository = repository or ClinicRepository()

    def create_availability(self, form_data, doctor_id):
        errors = self._validate_form(form_data)
        if errors:
            return None, errors

        start_time = datetime.strptime(form_data["start_time"], "%H:%M").time()
        end_time = datetime.strptime(form_data["end_time"], "%H:%M").time()
        if end_time <= start_time:
            return None, ["End time must be later than start time."]

        availability = DoctorAvailability(
            doctor_id=doctor_id,
            available_date=datetime.strptime(form_data["available_date"], "%Y-%m-%d").date(),
            start_time=start_time,
            end_time=end_time,
            slot_minutes=int(form_data.get("slot_minutes", 30)),
            status=form_data.get("status", "available"),
            note=form_data.get("note"),
        )
        self.repository.add_availability(availability)
        self.repository.commit()
        return availability, []

    def delete_availability(self, availability_id, doctor_id):
        availability = self.repository.get_availability(availability_id)
        if not availability:
            return None, ["Availability record not found."]
        if availability.doctor_id != doctor_id:
            return None, ["You can only delete your own availability entries."]

        # Block deletion when booked appointments exist in this window
        appointments = self.repository.list_appointments(
            doctor_id=doctor_id,
            appointment_date=availability.available_date,
        )
        conflicting = [
            a for a in appointments
            if a.status not in ("cancelled",)
            and availability.start_time <= a.appointment_time < availability.end_time
        ]
        if conflicting:
            return None, [
                f"Cannot delete: {len(conflicting)} active appointment(s) fall within this window."
            ]

        self.repository.delete_availability(availability)
        self.repository.commit()
        return availability, []

    def _validate_form(self, form_data):
        required = ["available_date", "start_time", "end_time", "slot_minutes"]
        if any(not form_data.get(f) for f in required):
            return ["Please fill in all required availability fields."]
        return []
