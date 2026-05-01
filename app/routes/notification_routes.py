from flask import Blueprint, jsonify, render_template, request
from flask_login import login_required, current_user

from app.extensions import db
from app.models.notifications import Notification
from app.services.notification_service import NotificationService
from app.services.push_service import send_notification
from app.decorators import verified_user


notification_bp = Blueprint("notifications", __name__)


@notification_bp.route("/save-token", methods=["POST"])
@login_required
def save_token():

    data = request.get_json(silent=True) or {}
    token = data.get("token", "").strip()

    if not token:
        return jsonify({"status": "error", "message": "token is required"}), 400

    current_user.fb_auth_token = token
    db.session.commit()

    return jsonify({"status": "saved"})


@notification_bp.route("/notifications")
@login_required
def notifications():

    notifications = (
        db.session.execute(
            db.select(Notification)
            .where(Notification.recipient_id == current_user.id)
            .order_by(Notification.created_at.desc())
            .limit(15)
        )
        .scalars()
        .all()
    )

    return render_template(
        "notifications.html",
        notifications=notifications,
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

            notifications.append(notif)

        db.session.commit()

        if send_push:
            for notif in notifications:
                try:
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

        if send_push:
            try:
                send_notification(notif)
            except Exception as exc:
                print("Notification failed:", exc)

        return jsonify({"status": "success"})

    return jsonify({"status": "error", "message": "Invalid state"}), 400
