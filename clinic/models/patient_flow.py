from datetime import datetime, timedelta

from clinic.extensions import db


class PatientFlow(db.Model):
    __tablename__ = "patient_flow"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    appointment_id = db.Column(db.Integer, db.ForeignKey("appointments.id"), nullable=True)
    current_status = db.Column(db.String(30), nullable=False, default="waiting")
    # 0 = normal, 1 = urgent, 2 = emergency
    priority = db.Column(db.Integer, nullable=False, default=0)
    queue_number = db.Column(db.Integer, nullable=True)
    checked_in_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, nullable=True)

    patient = db.relationship("Patient", back_populates="flow_records")
    appointment = db.relationship("Appointment", back_populates="flow_record")

    PRIORITY_LABELS = {0: "Normal", 1: "Urgent", 2: "Emergency"}

    @property
    def priority_label(self):
        return self.PRIORITY_LABELS.get(self.priority, "Normal")

    @property
    def is_delayed(self):
        """True when a waiting/in-consultation patient is more than 15 min past their slot."""
        if self.current_status not in ("waiting", "in_consultation"):
            return False
        if not self.appointment:
            return False
        slot_dt = datetime.combine(
            self.appointment.appointment_date,
            self.appointment.appointment_time,
        )
        return datetime.utcnow() > slot_dt + timedelta(minutes=15)
