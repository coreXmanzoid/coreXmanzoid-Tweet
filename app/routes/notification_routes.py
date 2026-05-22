import os
from datetime import timedelta
from types import SimpleNamespace

from flask import Blueprint, jsonify, render_template, request
from flask_login import login_required, current_user

from app.extensions import db
from app.firebase.firebase_config import get_firebase_web_config, init_firebase
from app.models.notifications import Notification
from app.models.users import UserData
from app.services.notification_service import NotificationService
from app.services.push_service import send_notification
from app.decorators import verified_user
from app.utils.subscription_manager import get_limit, has_feature, is_unlimited
from app.utils.time_utils import utc_iso_from, utc_now


notification_bp = Blueprint("notifications", __name__)


@notification_bp.route("/save-token", methods=["POST"])
@login_required
def save_token():

    data = request.get_json(silent=True) or {}
    token = data.get("token", "").strip()

    if not token:
        return jsonify({"status": "error", "message": "token is required"}), 400
    if not has_feature(current_user, "notifications", "push_notifications"):
        return jsonify({"status": "error", "message": "Push notifications require a higher plan."}), 403

    duplicate_owner = db.session.execute(
        db.select(db.func.count())
        .select_from(UserData)
        .where(
            UserData.fb_auth_token == token,
            UserData.id != current_user.id,
        )
    ).scalar()

    if duplicate_owner:
        db.session.execute(
            db.update(UserData)
            .where(
                UserData.fb_auth_token == token,
                UserData.id != current_user.id,
            )
            .values(fb_auth_token=None)
        )

    current_user.fb_auth_token = token
    db.session.commit()

    return jsonify(
        {
            "status": "saved",
            "token_length": len(token),
            "duplicates_removed": int(duplicate_owner or 0),
        }
    )


@notification_bp.route("/delete-token", methods=["POST"])
@login_required
def delete_token():
    data = request.get_json(silent=True) or {}
    token = (data.get("token") or "").strip()

    if token and current_user.fb_auth_token != token:
        return jsonify({"status": "ignored"})

    current_user.fb_auth_token = None
    db.session.commit()
    return jsonify({"status": "deleted"})


@notification_bp.route("/notification-health")
@login_required
def notification_health():
    firebase_ok, firebase_status = init_firebase()
    firebase_config = get_firebase_web_config()

    return jsonify(
        {
            "firebase_admin_ready": firebase_ok,
            "firebase_admin_status": firebase_status,
            "fcm_vapid_key_configured": bool(os.getenv("FCM_VAPID_KEY")),
            "firebase_web_configured": all(
                bool(firebase_config.get(key))
                for key in (
                    "apiKey",
                    "authDomain",
                    "projectId",
                    "messagingSenderId",
                    "appId",
                )
            ),
            "current_user_has_token": bool(current_user.fb_auth_token),
            "current_user_token_length": len(current_user.fb_auth_token or ""),
            "request_is_secure": request.is_secure,
            "request_host": request.host,
            "public_base_url": (
                os.getenv("PUBLIC_BASE_URL")
                or os.getenv("APP_BASE_URL")
                or os.getenv("CHATFLICK_BASE_URL")
                or ""
            ),
        }
    )


@notification_bp.route("/notification-test-push", methods=["POST"])
@login_required
def notification_test_push():
    if not current_user.fb_auth_token:
        return jsonify(
            {
                "status": "error",
                "message": "No FCM token is saved for the current user. Enable notifications first.",
            }
        ), 400
    if not has_feature(current_user, "notifications", "push_notifications"):
        return jsonify({"status": "error", "message": "Push notifications require a higher plan."}), 403

    test_notification = SimpleNamespace(
        title="ChatFlick test",
        message="Push notifications are connected for this device.",
        type="test",
        identifier=current_user.id,
        sender_id=current_user.id,
        recipient=current_user,
    )

    if not send_notification(test_notification):
        return jsonify(
            {
                "status": "error",
                "message": "Firebase accepted no send. Check PythonAnywhere error logs for the exact Firebase error.",
            }
        ), 502

    return jsonify({"status": "sent"})


@notification_bp.route("/notifications")
@login_required
def notifications():

    history_days = get_limit(current_user, "notifications", "notification_history_days", 7)
    query = db.select(Notification).where(Notification.recipient_id == current_user.id)
    if not is_unlimited(history_days):
        query = query.where(Notification.created_at >= utc_now() - timedelta(days=int(history_days)))
    notifications = (
        db.session.execute(query.order_by(Notification.created_at.desc()).limit(15))
        .scalars()
        .all()
    )

    return render_template(
        "notifications.html",
        notifications=notifications,
        utc_iso_from=utc_iso_from,
    )


@notification_bp.route("/notifications/mark_read/<int:user_id>")
@login_required
# @verified_user
def mark_as_read(user_id):

    if user_id != current_user.id:
        return jsonify({"status": "error", "message": "Unauthorized"}), 403

    db.session.execute(
        db.update(Notification)
        .where(Notification.recipient_id == user_id)
        .values(is_read=True)
    )

    db.session.commit()

    return jsonify({"status": "success"})


@notification_bp.route("/check-notifications/<int:user_id>")
@login_required
def check_notifications(user_id):
    if user_id != current_user.id:
        return jsonify({"status": "error", "message": "Unauthorized"}), 403

    unread_count = db.session.execute(
        db.select(db.func.count())
        .select_from(Notification)
        .where(
            Notification.recipient_id == user_id,
            Notification.is_read == False
        )
    ).scalar()

    return jsonify({"unread_count": unread_count})


@notification_bp.route("/send-notification-route/<int:state>/<string:push>", methods=["POST"])
@login_required
def send_notification_route(state, push):

    data = request.get_json(silent=True) or {}

    try:
        sender_id = int(data.get("sender_id") or current_user.id)
    except (TypeError, ValueError):
        return jsonify({"status": "error", "message": "Invalid sender_id"}), 400

    if sender_id != current_user.id:
        return jsonify({"status": "error", "message": "Unauthorized sender"}), 403

    title = (data.get("title") or "").strip()
    message = (data.get("message") or "").strip()
    ntype = (data.get("type") or "general").strip()
    identifier = data.get("identifier")

    if not title or not message:
        return jsonify({"status": "error", "message": "title and message are required"}), 400

    send_push = str(push).lower() == "true"
    if send_push and not has_feature(current_user, "notifications", "push_notifications"):
        send_push = False

    if state == 2:

        notifications = []

        for follow in current_user.followers:

            recipient_id = follow.follower_id

            if recipient_id == sender_id:
                continue

            notif = NotificationService.update_or_create(
                ntype,
                identifier,
                message,
                recipient_id=recipient_id,
                sender_id=sender_id,
                title=title,
                commit=False,
            )

            if notif:
                notifications.append(notif)

        db.session.commit()

        if send_push:
            for notif in notifications:
                try:
                    if has_feature(notif.recipient, "notifications", "push_notifications"):
                        send_notification(notif)
                except Exception as exc:
                    print("Notification failed:", exc)

        return jsonify({"status": "success", "count": len(notifications)})

    if state == 3:

        recipient_id = data.get("recipient_id")

        if not recipient_id:
            return jsonify({"status": "error", "message": "recipient_id required"}), 400

        try:
            recipient_id = int(recipient_id)
        except (TypeError, ValueError):
            return jsonify({"status": "error", "message": "Invalid recipient_id"}), 400

        if recipient_id == sender_id:
            return jsonify({"status": "skipped", "message": "No self notifications"})

        notif = NotificationService.update_or_create(
            ntype,
            identifier,
            message,
            recipient_id=recipient_id,
            sender_id=sender_id,
            title=title,
            commit=True,
        )

        if send_push and notif:
            try:
                if has_feature(notif.recipient, "notifications", "push_notifications"):
                    send_notification(notif)
            except Exception as exc:
                print("Notification failed:", exc)

        return jsonify({"status": "success"})

    return jsonify({"status": "error", "message": "Invalid state"}), 400
