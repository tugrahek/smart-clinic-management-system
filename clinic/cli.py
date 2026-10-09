from datetime import date, time, timedelta

from clinic.extensions import db
from clinic.models import (
    Appointment,
    Department,
    DoctorAvailability,
    DoctorProfile,
    Patient,
    User,
)


def register_commands(app):
    @app.cli.command("init-db")
    def init_db():
        """Drop and recreate all tables with demo data."""
        db.drop_all()
        db.create_all()

        # ------------------------------------------------------------------
        # Departments
        # ------------------------------------------------------------------
        cardiology   = Department(name="Cardiology",    floor="2nd Floor", description="Heart and cardiovascular system.")
        dermatology  = Department(name="Dermatology",   floor="3rd Floor", description="Skin, hair and nail conditions.")
        neurology    = Department(name="Neurology",     floor="4th Floor", description="Brain and nervous system disorders.")
        orthopedics  = Department(name="Orthopedics",   floor="1st Floor", description="Bones, joints and musculoskeletal system.")
        pediatrics   = Department(name="Pediatrics",    floor="2nd Floor", description="Medical care for children.")
        db.session.add_all([cardiology, dermatology, neurology, orthopedics, pediatrics])

        # ------------------------------------------------------------------
        # Secretaries
        # ------------------------------------------------------------------
        sec1 = User(full_name="Aylin Demir",   username="aylin.demir",   email="aylin@clinic.local",   phone="+90 555 100 2025", employee_code="SEC-201", role="secretary")
        sec1.set_password("clinic123")
        sec2 = User(full_name="Burak Şahin",   username="burak.sahin",   email="burak@clinic.local",   phone="+90 555 100 2030", employee_code="SEC-202", role="secretary")
        sec2.set_password("clinic123")
        db.session.add_all([sec1, sec2])

        # ------------------------------------------------------------------
        # Doctors
        # ------------------------------------------------------------------
        doc_users = [
            User(full_name="Dr. Deniz Arslan",  username="deniz.arslan",  email="deniz@clinic.local",  phone="+90 555 100 2027", employee_code="DOC-101", role="doctor"),
            User(full_name="Dr. Selin Yıldız",  username="selin.yildiz",  email="selin@clinic.local",  phone="+90 555 100 2028", employee_code="DOC-102", role="doctor"),
            User(full_name="Dr. Emre Çelik",    username="emre.celik",    email="emre@clinic.local",   phone="+90 555 100 2031", employee_code="DOC-103", role="doctor"),
            User(full_name="Dr. Fatma Kara",    username="fatma.kara",    email="fatma@clinic.local",  phone="+90 555 100 2032", employee_code="DOC-104", role="doctor"),
            User(full_name="Dr. Ahmet Doğan",   username="ahmet.dogan",   email="ahmet@clinic.local",  phone="+90 555 100 2033", employee_code="DOC-105", role="doctor"),
        ]
        for u in doc_users:
            u.set_password("clinic123")
        db.session.add_all(doc_users)

        # ------------------------------------------------------------------
        # Patients (user accounts)
        # ------------------------------------------------------------------
        pat_users = [
            User(full_name="Mert Kaya",       username="mert.kaya",      email="mert@clinic.local",    phone="+90 555 200 1001", role="patient"),
            User(full_name="Zeynep Aydın",    username="zeynep.aydin",   email="zeynep@clinic.local",  phone="+90 555 200 1002", role="patient"),
            User(full_name="Can Öztürk",      username="can.ozturk",     email="can@clinic.local",     phone="+90 555 200 1003", role="patient"),
            User(full_name="Elif Yılmaz",     username="elif.yilmaz",    email="elif@clinic.local",    phone="+90 555 200 1004", role="patient"),
            User(full_name="Hasan Çetin",     username="hasan.cetin",    email="hasan@clinic.local",   phone="+90 555 200 1005", role="patient"),
            User(full_name="Merve Koç",       username="merve.koc",      email="merve@clinic.local",   phone="+90 555 200 1006", role="patient"),
        ]
        for u in pat_users:
            u.set_password("clinic123")
        db.session.add_all(pat_users)

        db.session.flush()

        # ------------------------------------------------------------------
        # Doctor profiles
        # ------------------------------------------------------------------
        profiles = [
            DoctorProfile(user_id=doc_users[0].id, department=cardiology,  title="Cardiologist",       room_number="204"),
            DoctorProfile(user_id=doc_users[1].id, department=dermatology, title="Dermatologist",      room_number="312"),
            DoctorProfile(user_id=doc_users[2].id, department=neurology,   title="Neurologist",        room_number="401"),
            DoctorProfile(user_id=doc_users[3].id, department=orthopedics, title="Orthopedic Surgeon", room_number="105"),
            DoctorProfile(user_id=doc_users[4].id, department=pediatrics,  title="Pediatrician",       room_number="210"),
        ]
        db.session.add_all(profiles)
        db.session.flush()

        # ------------------------------------------------------------------
        # Patient records
        # ------------------------------------------------------------------
        patients = [
            Patient(national_id="11111111111", full_name="Mert Kaya",    phone="+90 555 200 1001", email="mert@clinic.local",   gender="Male"),
            Patient(national_id="22222222222", full_name="Zeynep Aydın", phone="+90 555 200 1002", email="zeynep@clinic.local", gender="Female"),
            Patient(national_id="33333333333", full_name="Can Öztürk",   phone="+90 555 200 1003", email="can@clinic.local",    gender="Male"),
            Patient(national_id="44444444444", full_name="Elif Yılmaz",  phone="+90 555 200 1004", email="elif@clinic.local",   gender="Female"),
            Patient(national_id="55555555555", full_name="Hasan Çetin",  phone="+90 555 200 1005", email="hasan@clinic.local",  gender="Male"),
            Patient(national_id="66666666666", full_name="Merve Koç",    phone="+90 555 200 1006", email="merve@clinic.local",  gender="Female"),
        ]
        db.session.add_all(patients)
        db.session.flush()

        # ------------------------------------------------------------------
        # Doctor availability — next 7 days, all doctors
        # ------------------------------------------------------------------
        today = date.today()
        for profile in profiles:
            for offset in range(7):
                db.session.add(DoctorAvailability(
                    doctor_id=profile.id,
                    available_date=today + timedelta(days=offset),
                    start_time=time(9, 0),
                    end_time=time(17, 0),
                    slot_minutes=30,
                    status="available",
                ))

        # ------------------------------------------------------------------
        # Sample appointments (today)
        # ------------------------------------------------------------------
        sample_appts = [
            Appointment(patient=patients[0], doctor_id=profiles[0].id, appointment_date=today, appointment_time=time(9, 0),  reason="Chest pain follow-up",      status="scheduled"),
            Appointment(patient=patients[1], doctor_id=profiles[0].id, appointment_date=today, appointment_time=time(9, 30), reason="Annual cardiac checkup",     status="scheduled"),
            Appointment(patient=patients[2], doctor_id=profiles[1].id, appointment_date=today, appointment_time=time(10, 0), reason="Skin rash examination",      status="scheduled"),
            Appointment(patient=patients[3], doctor_id=profiles[2].id, appointment_date=today, appointment_time=time(10, 30),reason="Migraine consultation",      status="scheduled"),
            Appointment(patient=patients[4], doctor_id=profiles[3].id, appointment_date=today, appointment_time=time(11, 0), reason="Knee pain assessment",       status="scheduled"),
            Appointment(patient=patients[5], doctor_id=profiles[4].id, appointment_date=today, appointment_time=time(11, 30),reason="Child vaccination visit",    status="scheduled"),
        ]
        db.session.add_all(sample_appts)

        db.session.commit()

        print("\n=== Database initialized ===")
        print("\nSecretaries:")
        print("  aylin.demir / clinic123")
        print("  burak.sahin / clinic123")
        print("\nDoctors:")
        print("  deniz.arslan  (Cardiology)  / clinic123")
        print("  selin.yildiz  (Dermatology) / clinic123")
        print("  emre.celik    (Neurology)   / clinic123")
        print("  fatma.kara    (Orthopedics) / clinic123")
        print("  ahmet.dogan   (Pediatrics)  / clinic123")
        print("\nPatients:")
        print("  mert.kaya / zeynep.aydin / can.ozturk")
        print("  elif.yilmaz / hasan.cetin / merve.koc")
        print("  (all passwords: clinic123)")
        print("\n6 sample appointments created for today.")
