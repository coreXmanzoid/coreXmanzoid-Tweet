from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app.services.report_service import ReportService
from app.utils.subscription_manager import has_feature

report_bp = Blueprint("report", __name__)


@report_bp.route("/reports/posts", methods=["POST"])
@login_required
def create_post_report():
    if not has_feature(current_user, "support", "can_report_content"):
        return jsonify({
            "status": "error",
            "message": "Your plan does not allow reports.",
        }), 403

    data = request.get_json(silent=True) or {}

    try:
        post_id = int(data.get("post_id") or 0)
    except (TypeError, ValueError):
        post_id = 0

    try:
        report, created = ReportService.create_post_report(
            post_id=post_id,
            reporter_id=current_user.id,
            reason=data.get("category"),
            details=data.get("message"),
        )
    except ValueError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400

    message = (
        "Report submitted successfully."
        if created
        else "Your existing report was updated."
    )
    return jsonify({
        "status": "success",
        "message": message,
        "report_id": report.id,
    })
