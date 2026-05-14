from datetime import datetime
from pathlib import Path

from flask import Blueprint, current_app, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models.payment import PaymentSubmission
from flask import Blueprint, jsonify, render_template, request
from flask_login import login_required, current_user

pricing_bp = Blueprint("pricing", __name__)

@pricing_bp.route("/pricing")
def pricing():
    user = current_user if current_user.is_authenticated else None
    return render_template("pricing.html", user=user)



ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}
MAX_FILE_BYTES = 5 * 1024 * 1024


def _allowed(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _upload_dir() -> Path:
    upload_dir = Path(current_app.instance_path) / "payment_screenshots"
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


@pricing_bp.route("/payment")
@login_required
def payment_page():
    """Render the Pro upgrade payment page."""
    if (current_user.status or "").upper() in {"PRO", "ENTERPRISE"}:
        return redirect(url_for("main.homepage"))

    return render_template("payment.html")


@pricing_bp.route("/payment/submit", methods=["POST"])
@login_required
def payment_submit():
    """Accept a payment verification form and store it for admin review."""
    full_name = request.form.get("full_name", "").strip()
    email = request.form.get("email", "").strip()
    plan = request.form.get("plan", "").strip()
    payment_method = request.form.get("payment_method", "").strip()
    transaction_id = request.form.get("transaction_id", "").strip()
    note = request.form.get("note", "").strip()

    errors = {}
    if not full_name:
        errors["full_name"] = "Full name is required."
    if not email or "@" not in email:
        errors["email"] = "Valid email is required."
    if not payment_method:
        errors["payment_method"] = "Payment method is required."
    if not transaction_id:
        errors["transaction_id"] = "Transaction ID is required."

    screenshot_file = request.files.get("screenshot")
    if not screenshot_file or screenshot_file.filename == "":
        errors["screenshot"] = "Payment screenshot is required."
    elif not _allowed(screenshot_file.filename):
        errors["screenshot"] = "Only PNG, JPG, JPEG, WEBP, and GIF images are accepted."
    elif screenshot_file.content_length and screenshot_file.content_length > MAX_FILE_BYTES:
        errors["screenshot"] = "File size must be under 5 MB."

    if errors:
        return jsonify({"status": "error", "message": "Validation failed.", "errors": errors}), 422

    filename = secure_filename(
        f"pay_{current_user.id}_{int(datetime.utcnow().timestamp())}_{screenshot_file.filename}"
    )
    save_path = _upload_dir() / filename

    try:
        screenshot_file.seek(0)
        data = screenshot_file.read()
        if len(data) > MAX_FILE_BYTES:
            return jsonify({"status": "error", "message": "File size exceeds 5 MB."}), 422
        save_path.write_bytes(data)
    except OSError:
        current_app.logger.exception("Screenshot save failed")
        return jsonify({"status": "error", "message": "File save failed."}), 500

    try:
        submission = PaymentSubmission(
            user_id=current_user.id,
            full_name=full_name,
            email=email.lower(),
            plan=plan or "pro_monthly",
            payment_method=payment_method,
            transaction_id=transaction_id,
            screenshot_path=filename,
            note=note or None,
            status="pending",
        )
        db.session.add(submission)
        if (current_user.status or "").upper() not in {"PRO", "ENTERPRISE", "BLOCKED"}:
            current_user.status = "PENDING_PRO"
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        save_path.unlink(missing_ok=True)
        return jsonify({
            "status": "error",
            "message": "This transaction ID has already been submitted.",
        }), 409
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Payment submission DB error")
        save_path.unlink(missing_ok=True)
        return jsonify({"status": "error", "message": "Database error. Please try again."}), 500

    return jsonify({
        "status": "success",
        "message": "Payment submitted for verification.",
        "submission_id": submission.id,
    })
