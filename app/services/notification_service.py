from datetime import datetime

from app.extensions import db
from app.models.notifications import Notification
from app.services.push_service import send_notification


class NotificationService:

    @staticmethod
    def create_notification(sender_id, recipient_id, title, message, type, identifier):

        notification = Notification(
            sender_id=sender_id,
            recipient_id=recipient_id,
            title=title,
            message=message,
            type=type,
            identifier=identifier,
        )

        db.session.add(notification)
        db.session.commit()

        return notification

    @staticmethod
    def update_or_create(type, identifier, message, recipient_id, sender_id=None, title="Notification", commit=True):

        notification = db.session.execute(
            db.select(Notification).where(
                (Notification.type == type)
                & (Notification.identifier == identifier)
                & (Notification.recipient_id == recipient_id)
            )
        ).scalar_one_or_none()

        if notification:
            notification.created_at = datetime.utcnow()
            notification.is_read = False
            notification.message = message
            notification.title = title
        else:
            notification = Notification(
                title=title,
                message=message,
                type=type,
                identifier=identifier,
                recipient_id=recipient_id,
                sender_id=sender_id,
            )
            db.session.add(notification)

        if commit:
            db.session.commit()

        return notification

    @staticmethod
    def send_mention_notifications(post, state):

        mentioned_objects = post.mentions
        notifications = []

        for obj in mentioned_objects:

            user_id = obj.get("user_id")
            if not user_id:
                continue

            if user_id == post.user.id:
                continue

            notif = Notification(
                sender_id=post.user.id,
                recipient_id=user_id,
                title="Mentioned",
                message=f"{post.user.name} mentioned you in a {state}.",
                type=f"mention_{state}",
                identifier=post.id,
            )

            db.session.add(notif)
            notifications.append(notif)

        db.session.commit()

        for notif in notifications:
            try:
                send_notification(notif)
            except Exception as exc:
                print("Notification failed:", exc)