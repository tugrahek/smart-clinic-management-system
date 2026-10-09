from datetime import datetime

from clinic.repositories import ClinicRepository


class PatientFlowService:
    ALLOWED_TRANSITIONS = {
        "waiting": {"in_consultation", "cancelled"},
        "in_consultation": {"assessment", "done", "cancelled"},
        "assessment": {"done", "cancelled"},
        "done": set(),
        "cancelled": set(),
    }

    def __init__(self, repository=None):
        self.repository = repository or ClinicRepository()

    def update_status(self, flow_id, next_status):
        flow_record = self.repository.get_flow_record(flow_id)
        if not flow_record:
            return None, ["Patient flow record could not be found."]

        allowed = self.ALLOWED_TRANSITIONS.get(flow_record.current_status, set())
        if next_status not in allowed:
            return None, [
                f"Cannot transition from '{flow_record.current_status}' to '{next_status}'."
            ]

        was_delayed = flow_record.is_delayed
        flow_record.current_status = next_status

        if next_status == "in_consultation":
            flow_record.started_at = datetime.utcnow()
            if flow_record.appointment:
                flow_record.appointment.status = "in_consultation"
            if was_delayed:
                self._alert_delay(flow_record)
        elif next_status == "assessment":
            if flow_record.appointment:
                flow_record.appointment.status = "assessment"
        elif next_status == "done":
            flow_record.completed_at = datetime.utcnow()
            if flow_record.appointment:
                flow_record.appointment.status = "done"
        elif next_status == "cancelled":
            if flow_record.appointment:
                flow_record.appointment.status = "cancelled"

        self.repository.commit()
        return flow_record, []

    def _alert_delay(self, flow_record):
        """Create a staff notification when a delayed patient starts consultation."""
        try:
            from clinic.services.notification_service import NotificationService
            NotificationService(self.repository).notify_staff(
                title="Patient Delay Alert",
                body=(
                    f"{flow_record.patient.full_name} started consultation with a significant delay. "
                    f"Queue #{flow_record.queue_number}."
                ),
                category="alert",
            )
        except Exception:
            pass
