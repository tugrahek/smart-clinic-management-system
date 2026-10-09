from clinic.repositories import ClinicRepository


class ReportService:
    def __init__(self, repository=None):
        self.repository = repository or ClinicRepository()

    def appointment_volume(self, start_date, end_date):
        """Appointment counts grouped by doctor for the given date range."""
        appointments = self.repository.list_appointments_in_range(start_date, end_date)
        doctors = {}
        for appt in appointments:
            key = appt.doctor_id
            if key not in doctors:
                doctors[key] = {
                    "doctor": appt.doctor,
                    "total": 0,
                    "done": 0,
                    "cancelled": 0,
                    "other": 0,
                }
            doctors[key]["total"] += 1
            if appt.status == "done":
                doctors[key]["done"] += 1
            elif appt.status == "cancelled":
                doctors[key]["cancelled"] += 1
            else:
                doctors[key]["other"] += 1
        return sorted(doctors.values(), key=lambda x: x["total"], reverse=True)

    def workload_by_department(self, start_date, end_date):
        """Appointment counts grouped by department."""
        appointments = self.repository.list_appointments_in_range(start_date, end_date)
        departments = {}
        for appt in appointments:
            dept = appt.doctor.department
            key = dept.id
            if key not in departments:
                departments[key] = {"department": dept, "total": 0}
            departments[key]["total"] += 1
        return sorted(departments.values(), key=lambda x: x["total"], reverse=True)

    def average_wait_time_minutes(self, start_date, end_date):
        """Average time in minutes from check-in to consultation start."""
        records = self.repository.list_flow_in_range(start_date, end_date)
        wait_times = [
            (r.started_at - r.checked_in_at).total_seconds() / 60
            for r in records
            if r.started_at and r.checked_in_at
        ]
        if not wait_times:
            return None
        return round(sum(wait_times) / len(wait_times), 1)

    def no_show_rate(self, start_date, end_date):
        """Percentage of past appointments that were never checked in."""
        from datetime import date
        today = date.today()
        appointments = self.repository.list_appointments_in_range(start_date, end_date)
        total = len(appointments)
        if not total:
            return None
        no_shows = sum(
            1 for a in appointments
            if a.appointment_date < today and a.status == "scheduled"
        )
        return round((no_shows / total) * 100, 1)
