import os

from flask import current_app
from firebase_admin import messaging
from app.firebase.firebase_config import init_firebase


def send_notification(notification) -> bool:
    ok, status = init_firebase()
    if not ok:
        current_app.logger.warning("Firebase not initialized: %s", status)
        return False

    recipient = getattr(notification, "recipient", None)
    token = getattr(recipient, "fb_auth_token", None)

    if not token:
        current_app.logger.info("Missing FCM token for recipient")
        return False

    base_url = (
        os.getenv("PUBLIC_BASE_URL")
        or os.getenv("APP_BASE_URL")
        or os.getenv("CHATFLICK_BASE_URL")
        or ""
    ).rstrip("/")
    notification_url = f"{base_url}/home" if base_url.startswith("https://") else "/home"

    webpush_options = {
        "notification": messaging.WebpushNotification(
            icon="/static/assets/logo.png",
            badge="/static/assets/logo.png",
        )
    }
    if notification_url.startswith("https://"):
        webpush_options["fcm_options"] = messaging.WebpushFCMOptions(
            link=notification_url
        )

    message = messaging.Message(
        notification=messaging.Notification(
            title=notification.title,
            body=notification.message,
        ),
        data={
            "title": str(notification.title or "ChatFlick"),
            "body": str(notification.message or ""),
            "type": str(notification.type),
            "identifier": str(notification.identifier or ""),
            "sender_id": str(notification.sender_id or ""),
            "url": notification_url,
        },
        webpush=messaging.WebpushConfig(**webpush_options),
        token=token,
    )

    try:
        messaging.send(message)
        return True
    except Exception as exc:
        current_app.logger.exception("Push notification failed: %s", exc)
        return False
