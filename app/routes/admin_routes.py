from flask import Blueprint, jsonify, render_template, request
from flask_login import login_required
from app.decorators import verified_user, only_admin

from app.services.admin_service import AdminService
from app.services.ai_service import AIService

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/admin")
@login_required
@verified_user
@only_admin
def admin_dashboard():
    return render_template("admin.html")


@admin_bp.route("/admin/api/dashboard")
@login_required
@verified_user
@only_admin
def admin_dashboard_data():
    return jsonify({"status": "success", "data": AdminService.dashboard_data()})


@admin_bp.route("/admin/api/support/<int:request_id>/reply", methods=["POST"])
@login_required
@verified_user
@only_admin
def save_support_reply(request_id):
    data = request.get_json(silent=True) or {}
    reply = (data.get("reply") or "").strip()
    if not reply:
        return jsonify({"status": "error", "message": "Reply is required"}), 400

    try:
        support_request = AdminService.save_support_reply(request_id, reply)
    except ValueError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 404

    return jsonify({"status": "success", "item": support_request})


@admin_bp.route("/admin/api/support/<int:request_id>/answer", methods=["POST"])
@login_required
@verified_user
@only_admin
def mark_support_answered(request_id):
    data = request.get_json(silent=True) or {}
    reply = data.get("reply")
    if isinstance(reply, str):
        reply = reply.strip() or None

    try:
        support_request = AdminService.mark_support_answered(request_id, reply)
    except ValueError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 404

    return jsonify({"status": "success", "item": support_request})


@admin_bp.route("/admin/api/support/<int:request_id>/ai-answer", methods=["POST"])
@login_required
@verified_user
@only_admin
def generate_support_ai_answer(request_id):
    data = AdminService.dashboard_data()
    support_request = next(
        (
            item
            for item in data["supportRequests"]
            if item["dbId"] == request_id
        ),
        None,
    )
    if not support_request:
        return jsonify({"status": "error", "message": "Support request not found"}), 404

    try:
        reply = AIService.answer_support_request(
            support_request["category"],
            support_request["message"],
        )
    except Exception as exc:
        print("Support AI answer error:", exc)
        return jsonify({"status": "error", "message": "AI service unavailable"}), 503

    return jsonify({"status": "success", "reply": reply})


@admin_bp.route("/admin/api/reports/<int:report_id>/review", methods=["POST"])
@login_required
@verified_user
@only_admin
def mark_report_reviewed(report_id):
    try:
        report = AdminService.mark_report_reviewed(report_id)
    except ValueError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 404

    return jsonify({"status": "success", "item": report})


@admin_bp.route("/admin/api/users/<int:user_id>/verify", methods=["POST"])
@login_required
@verified_user
@only_admin
def verify_user(user_id):
    try:
        user = AdminService.verify_user(user_id)
    except ValueError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400

    return jsonify({"status": "success", "item": user})


@admin_bp.route("/admin/api/users/<int:user_id>/approve-pro", methods=["POST"])
@login_required
@verified_user
@only_admin
def approve_pro(user_id):
    try:
        user = AdminService.approve_pro(user_id)
    except ValueError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400

    return jsonify({"status": "success", "item": user})


@admin_bp.route("/admin/api/users/<int:user_id>/reject-pro", methods=["POST"])
@login_required
@verified_user
@only_admin
def reject_pro(user_id):
    try:
        user = AdminService.reject_pro(user_id)
    except ValueError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400

    return jsonify({"status": "success", "item": user})


@admin_bp.route("/admin/api/users/<int:user_id>/warning", methods=["POST"])
@login_required
@verified_user
@only_admin
def create_warning(user_id):
    try:
        user = AdminService.create_warning(user_id)
    except ValueError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400

    return jsonify({"status": "success", "item": user})


@admin_bp.route("/admin/api/users/<int:user_id>/block", methods=["POST"])
@login_required
@verified_user
@only_admin
def block_user(user_id):
    try:
        user = AdminService.block_user(user_id)
    except ValueError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400

    return jsonify({"status": "success", "item": user})


@admin_bp.route("/admin/api/users/<int:user_id>/unblock", methods=["POST"])
@login_required
@verified_user
@only_admin
def unblock_user(user_id):
    try:
        user = AdminService.unblock_user(user_id)
    except ValueError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400

    return jsonify({"status": "success", "item": user})
