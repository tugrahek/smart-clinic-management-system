from clinic.models import Notification
from clinic.repositories import ClinicRepository


class NotificationService:
    def __init__(self, repository=None):
        self.repository = repository or ClinicRepository()

    def notify_patient(self, patient, title, body, category="info"):
        """Create an in-app notification for the patient's linked user account."""
        user = None
        if patient.email:
            user = self.repository.get_user_by_email(patient.email)
        notification = Notification(
            recipient_user_id=user.id if user else None,
            patient_id=patient.id,
            title=title,
            body=body,
            category=category,
        )
        self.repository.add_notification(notification)

    def notify_staff(self, title, body, category="warning"):
        """Create a notification for every secretary user."""
        for user in self.repository.list_users_by_role("secretary"):
            self.repository.add_notification(
                Notification(
                    recipient_user_id=user.id,
                    title=title,
                    body=body,
                    category=category,
                )
            )

    def notify_user(self, user_id, title, body, category="info"):
        self.repository.add_notification(
            Notification(
                recipient_user_id=user_id,
                title=title,
                body=body,
                category=category,
            )
        )

    def get_unread_count(self, user_id):
        return self.repository.count_unread_notifications(user_id)

    def get_notifications_for_user(self, user_id):
        return self.repository.list_notifications(user_id)

    def mark_all_read(self, user_id):
        self.repository.mark_notifications_read(user_id)
        self.repository.commit()
