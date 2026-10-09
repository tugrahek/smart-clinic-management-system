from datetime import date, datetime, timedelta

from clinic.extensions import db
from clinic.models import (
    Appointment,
    Department,
    DoctorAvailability,
    DoctorProfile,
    Notification,
    Patient,
    PatientFlow,
    User,
)


class ClinicRepository:
    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------

    def get_user_by_username(self, username):
        return User.query.filter_by(username=username).first()

    def get_user_by_email(self, email):
        return User.query.filter_by(email=email).first()

    def list_users_by_role(self, role):
        return User.query.filter_by(role=role).order_by(User.full_name).all()

    def get_user(self, user_id):
        return db.session.get(User, user_id)

    # ------------------------------------------------------------------
    # Departments
    # ------------------------------------------------------------------

    def list_departments(self):
        return Department.query.order_by(Department.name).all()

    def get_department(self, department_id):
        return db.session.get(Department, department_id)

    # ------------------------------------------------------------------
    # Doctors
    # ------------------------------------------------------------------

    def list_doctors(self):
        return DoctorProfile.query.join(User).order_by(User.full_name).all()

    def get_doctor(self, doctor_id):
        return db.session.get(DoctorProfile, doctor_id)

    # ------------------------------------------------------------------
    # Patients
    # ------------------------------------------------------------------

    def get_patient(self, patient_id):
        return db.session.get(Patient, patient_id)

    def get_or_create_patient(self, patient_data):
        national_id = patient_data["national_id"].strip()
        patient = Patient.query.filter_by(national_id=national_id).first()
        if patient:
            patient.full_name = patient_data["full_name"].strip()
            patient.phone = patient_data.get("phone")
            patient.email = patient_data.get("email")
            return patient

        patient = Patient(
            national_id=national_id,
            full_name=patient_data["full_name"].strip(),
            birth_date=patient_data.get("birth_date"),
            gender=patient_data.get("gender"),
            phone=patient_data.get("phone"),
            email=patient_data.get("email"),
            address=patient_data.get("address"),
            emergency_contact=patient_data.get("emergency_contact"),
        )
        db.session.add(patient)
        return patient

    def list_patients(self):
        return Patient.query.order_by(Patient.full_name).all()

    # ------------------------------------------------------------------
    # Appointments
    # ------------------------------------------------------------------

    def list_appointments(self, doctor_id=None, patient_email=None, appointment_date=None):
        query = Appointment.query
        if doctor_id:
            query = query.filter_by(doctor_id=doctor_id)
        if patient_email:
            query = query.join(Patient).filter(Patient.email == patient_email)
        if appointment_date:
            query = query.filter_by(appointment_date=appointment_date)
        return query.order_by(Appointment.appointment_date, Appointment.appointment_time).all()

    def list_appointments_in_range(self, start_date, end_date, doctor_id=None):
        """Date-range query used by the reporting module."""
        query = Appointment.query.filter(
            Appointment.appointment_date >= start_date,
            Appointment.appointment_date <= end_date,
        )
        if doctor_id:
            query = query.filter_by(doctor_id=doctor_id)
        return query.order_by(Appointment.appointment_date, Appointment.appointment_time).all()

    def get_appointment(self, appointment_id):
        return db.session.get(Appointment, appointment_id)

    def find_appointment_slot(self, doctor_id, appointment_date, appointment_time):
        return Appointment.query.filter_by(
            doctor_id=doctor_id,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
        ).first()

    def add_appointment(self, appointment):
        db.session.add(appointment)
        return appointment

    # ------------------------------------------------------------------
    # Doctor Availability
    # ------------------------------------------------------------------

    def list_doctor_availability(self, doctor_id=None, available_date=None):
        query = DoctorAvailability.query
        if doctor_id:
            query = query.filter_by(doctor_id=doctor_id)
        if available_date:
            query = query.filter_by(available_date=available_date)
        return query.order_by(
            DoctorAvailability.available_date, DoctorAvailability.start_time
        ).all()

    def get_availability(self, availability_id):
        return db.session.get(DoctorAvailability, availability_id)

    def add_availability(self, availability):
        db.session.add(availability)
        return availability

    def delete_availability(self, availability):
        db.session.delete(availability)

    # ------------------------------------------------------------------
    # Patient Flow
    # ------------------------------------------------------------------

    def add_patient_flow(self, flow_record):
        db.session.add(flow_record)
        return flow_record

    def get_flow_record(self, flow_id):
        return db.session.get(PatientFlow, flow_id)

    def list_patient_flow(self, active_only=False, today_only=False):
        """Return patient flow records ordered by priority (desc) then queue number (asc)."""
        query = PatientFlow.query
        if active_only:
            query = query.filter(
                PatientFlow.current_status.in_(["waiting", "in_consultation", "assessment"])
            )
        if today_only:
            query = query.filter(PatientFlow.checked_in_at >= date.today())
        return (
            query.order_by(
                PatientFlow.priority.desc(),
                PatientFlow.queue_number.asc(),
            )
            .limit(100)
            .all()
        )

    def next_queue_number(self):
        latest = (
            PatientFlow.query.filter(PatientFlow.checked_in_at >= date.today())
            .order_by(PatientFlow.queue_number.desc())
            .first()
        )
        if not latest or latest.queue_number is None:
            return 1
        return latest.queue_number + 1

    def list_flow_in_range(self, start_date, end_date):
        """Date-range query used by the reporting module."""
        end_dt = datetime.combine(end_date, datetime.max.time())
        return (
            PatientFlow.query.filter(
                PatientFlow.checked_in_at >= start_date,
                PatientFlow.checked_in_at <= end_dt,
            )
            .all()
        )

    # ------------------------------------------------------------------
    # Notifications
    # ------------------------------------------------------------------

    def add_notification(self, notification):
        db.session.add(notification)
        return notification

    def count_unread_notifications(self, user_id):
        return Notification.query.filter_by(
            recipient_user_id=user_id, is_read=False
        ).count()

    def list_notifications(self, user_id):
        return (
            Notification.query.filter_by(recipient_user_id=user_id)
            .order_by(Notification.created_at.desc())
            .limit(50)
            .all()
        )

    def mark_notifications_read(self, user_id):
        Notification.query.filter_by(
            recipient_user_id=user_id, is_read=False
        ).update({"is_read": True})

    # ------------------------------------------------------------------
    # Shared writers
    # ------------------------------------------------------------------

    def add_user(self, user):
        db.session.add(user)
        return user

    def add_patient(self, patient):
        db.session.add(patient)
        return patient

    def add_doctor_profile(self, doctor_profile):
        db.session.add(doctor_profile)
        return doctor_profile

    def commit(self):
        db.session.commit()

    def rollback(self):
        db.session.rollback()

    def flush(self):
        db.session.flush()
