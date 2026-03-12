from firebase_admin import messaging
from app.firebase.firebase_config import init_firebase


def send_notification(notification) -> bool:
    ok, status = init_firebase()
    if not ok:
        print(f"Firebase not initialized: {status}")
        return False

    recipient = getattr(notification, "recipient", None)
    token = getattr(recipient, "fb_auth_token", None)

    if not token:
        print("Missing FCM token for recipient")
        return False

    message = messaging.Message(
        notification=messaging.Notification(
            title=notification.title,
            body=notification.message,
        ),
        data={
            "type": str(notification.type),
            "identifier": str(notification.identifier or ""),
            "sender_id": str(notification.sender_id or "")
        },
        token=token,
    )

    try:
        messaging.send(message)
        return True
    except Exception as exc:
        print(f"Push notification failed: {exc}")
        return False