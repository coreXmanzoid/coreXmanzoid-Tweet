from flask import url_for

from app.extensions import db
from app.models.notifications import Notification
from app.models.payment import PaymentSubmission
from app.models.report_post import ReportPost
from app.models.report import Report
from app.models.support_requests import Support
from app.models.users import UserData
from app.utils.subscription_manager import normalize_plan
from app.utils.time_utils import utc_iso_from, utc_now


class AdminService:
    @staticmethod
    def dashboard_data():
        support_requests = db.session.scalars(
            db.select(Support).order_by(Support.created_at.desc(), Support.id.desc())
        ).all()
        reports = db.session.scalars(
            db.select(Report).order_by(Report.created_at.desc(), Report.id.desc())
        ).all()
        post_reports = db.session.scalars(
            db.select(ReportPost).order_by(ReportPost.created_at.desc(), ReportPost.id.desc())
        ).all()
        users = db.session.scalars(
            db.select(UserData).order_by(UserData.id.desc())
        ).all()
        payments = db.session.scalars(
            db.select(PaymentSubmission).order_by(
                PaymentSubmission.created_at.desc(), PaymentSubmission.id.desc()
            )
        ).all()

        return {
            "supportRequests": [
                AdminService._serialize_support_request(item)
                for item in support_requests
            ],
            "userReports": [AdminService._serialize_report(item) for item in reports],
            "postReports": [
                AdminService._serialize_post_report(item)
                for item in post_reports
            ],
            "managedUsers": [AdminService._serialize_user(item) for item in users],
            "paymentSubmissions": [
                AdminService._serialize_payment_submission(item) for item in payments
            ],
        }

    @staticmethod
    def save_support_reply(request_id, reply):
        support_request = db.session.get(Support, request_id)
        if not support_request:
            raise ValueError("Support request not found")

        support_request.admin_reply = reply
        support_request.updated_at = utc_now()
        db.session.commit()
        return AdminService._serialize_support_request(support_request)

    @staticmethod
    def mark_support_answered(request_id, reply=None):
        support_request = db.session.get(Support, request_id)
        if not support_request:
            raise ValueError("Support request not found")

        if reply is not None:
            support_request.admin_reply = reply

        support_request.status = "ANSWERED"
        support_request.updated_at = utc_now()
        db.session.commit()
        return AdminService._serialize_support_request(support_request)

    @staticmethod
    def mark_report_reviewed(report_id):
        report = db.session.get(Report, report_id)
        if not report:
            raise ValueError("Report not found")

        report.status = "REVIEWED"
        db.session.commit()
        return AdminService._serialize_report(report)

    @staticmethod
    def mark_post_report_reviewed(report_id):
        report = AdminService._get_post_report(report_id)
        report.status = "reviewed"
        report.admin_action = report.admin_action or "reviewed"
        report.reviewed_at = utc_now()
        db.session.commit()
        return AdminService._serialize_post_report(report)

    @staticmethod
    def remove_reported_post(report_id):
        report = AdminService._get_post_report(report_id)
        if not report.post:
            raise ValueError("Reported post not found")

        report.post.status = "REMOVED"
        report.status = "reviewed"
        report.admin_action = "post_removed"
        report.reviewed_at = utc_now()
        db.session.commit()
        return AdminService._serialize_post_report(report)

    @staticmethod
    def warn_reported_post_author(report_id):
        report = AdminService._get_post_report(report_id)
        if not report.post or not report.post.user:
            raise ValueError("Reported post author not found")

        user = report.post.user
        if user.status == "BLOCKED":
            raise ValueError("User is already blocked")

        warnings = int(user.get_setting("account-info", "warnings", 0) or 0) + 1
        user.set_setting("account-info", "warnings", warnings)

        if warnings >= 3:
            AdminService._remember_previous_status(user)
            user.status = "BLOCKED"

        db.session.add(Notification(
            recipient_id=user.id,
            sender_id=None,
            title="Moderation Warning",
            message="Your post was reviewed by moderation and a warning was added to your account.",
            type="moderation_warning",
            identifier=report.post_id,
        ))
        report.admin_action = "warning_sent"
        db.session.commit()
        return {
            "report": AdminService._serialize_post_report(report),
            "user": AdminService._serialize_user(user),
        }

    @staticmethod
    def verify_user(user_id):
        user = AdminService._get_user(user_id)
        if user.status == "BLOCKED":
            raise ValueError("Blocked users must be unblocked before verification")

        if user.status == "UNVERIFIED":
            user.status = "VERIFIED"
            db.session.commit()

        return AdminService._serialize_user(user)

    @staticmethod
    def approve_pro(user_id):
        user = AdminService._get_user(user_id)
        if user.status == "BLOCKED":
            raise ValueError("Blocked users cannot receive Pro access")

        user.subscription_plan = "pro"
        db.session.commit()
        return AdminService._serialize_user(user)

    @staticmethod
    def reject_pro(user_id):
        user = AdminService._get_user(user_id)
        if user.status == "BLOCKED":
            raise ValueError("Blocked users cannot be updated")

        if user.status == "PENDING_PRO":
            user.status = "VERIFIED"
            db.session.commit()

        return AdminService._serialize_user(user)

    @staticmethod
    def approve_payment(submission_id):
        submission = AdminService._get_payment_submission(submission_id)
        if (submission.status or "").lower() != "pending":
            raise ValueError("Only pending payment submissions can be approved")

        user = submission.user or AdminService._get_user(submission.user_id)
        if user.status == "BLOCKED":
            raise ValueError("Blocked users cannot receive Pro access")

        requested_plan = normalize_plan((submission.plan or "pro").split("_", 1)[0])
        user.subscription_plan = requested_plan if requested_plan != "free" else "pro"
        submission.status = "approved"
        submission.reviewed_at = utc_now()
        db.session.commit()
        return AdminService._serialize_payment_submission(submission)

    @staticmethod
    def reject_payment(submission_id, reason=None):
        submission = AdminService._get_payment_submission(submission_id)
        if (submission.status or "").lower() != "pending":
            raise ValueError("Only pending payment submissions can be rejected")

        user = submission.user
        if user and user.status == "PENDING_PRO":
            user.status = "VERIFIED"

        submission.status = "rejected"
        submission.admin_note = reason
        submission.reviewed_at = utc_now()
        db.session.commit()
        return AdminService._serialize_payment_submission(submission)

    @staticmethod
    def create_warning(user_id):
        user = AdminService._get_user(user_id)
        if user.status == "BLOCKED":
            raise ValueError("User is already blocked")

        warnings = int(user.get_setting("account-info", "warnings", 0) or 0) + 1
        user.set_setting("account-info", "warnings", warnings)

        if warnings >= 3:
            AdminService._remember_previous_status(user)
            user.status = "BLOCKED"

        db.session.commit()
        return AdminService._serialize_user(user)

    @staticmethod
    def block_user(user_id):
        user = AdminService._get_user(user_id)
        if user.status != "BLOCKED":
            AdminService._remember_previous_status(user)
            user.status = "BLOCKED"
            db.session.commit()

        return AdminService._serialize_user(user)

    @staticmethod
    def unblock_user(user_id):
        user = AdminService._get_user(user_id)
        if user.status == "BLOCKED":
            restored_status = user.get_setting(
                "account-info", "previous_status", "UNVERIFIED"
            )
            if restored_status == "BLOCKED":
                restored_status = "UNVERIFIED"

            user.status = restored_status
            user.set_setting("account-info", "previous_status", None)
            db.session.commit()

        return AdminService._serialize_user(user)

    @staticmethod
    def _get_user(user_id):
        user = db.session.get(UserData, user_id)
        if not user:
            raise ValueError("User not found")
        return user

    @staticmethod
    def _get_payment_submission(submission_id):
        submission = db.session.get(PaymentSubmission, submission_id)
        if not submission:
            raise ValueError("Payment submission not found")
        return submission

    @staticmethod
    def _get_post_report(report_id):
        report = db.session.get(ReportPost, report_id)
        if not report:
            raise ValueError("Post report not found")
        return report

    @staticmethod
    def _remember_previous_status(user):
        previous_status = user.status if user.status != "BLOCKED" else "UNVERIFIED"
        user.set_setting("account-info", "previous_status", previous_status)

    @staticmethod
    def _serialize_support_request(item):
        return {
            "id": f"SUP-{item.id:04d}",
            "dbId": item.id,
            "userId": f"USR-{item.user_id:04d}",
            "userDbId": item.user_id,
            "userName": item.user.name if item.user else "Unknown User",
            "category": item.category,
            "message": item.message,
            "status": AdminService._present_status(item.status),
            "timestamp": AdminService._format_timestamp(item.created_at),
            "adminReply": item.admin_reply or "",
        }

    @staticmethod
    def _serialize_report(item):
        return {
            "id": f"RPT-{item.id:04d}",
            "dbId": item.id,
            "userId": f"USR-{item.user_id:04d}",
            "userDbId": item.user_id,
            "userName": item.user.name if item.user else "Unknown User",
            "text": item.report_text,
            "status": AdminService._present_status(item.status),
            "timestamp": AdminService._format_timestamp(item.created_at),
        }

    @staticmethod
    def _serialize_post_report(item):
        post = item.post
        author = post.user if post else None
        reporter = item.reporter
        return {
            "id": f"PRP-{item.id:04d}",
            "dbId": item.id,
            "postId": f"PST-{item.post_id:04d}" if item.post_id else "PST-0000",
            "postDbId": item.post_id,
            "postContent": post.content if post else "Post unavailable",
            "postHashtags": post.hashtags if post and isinstance(post.hashtags, list) else [],
            "postStatus": AdminService._present_status(post.status if post else "unknown"),
            "postTimestamp": AdminService._format_timestamp(post.timestamp if post else None),
            "authorId": f"USR-{post.user_id:04d}" if post else "USR-0000",
            "authorDbId": post.user_id if post else None,
            "authorName": author.name if author else "Unknown User",
            "authorUsername": author.username if author else "",
            "authorWarnings": int(author.get_setting("account-info", "warnings", 0) or 0) if author else 0,
            "reporterId": f"USR-{item.reported_by:04d}",
            "reporterDbId": item.reported_by,
            "reporterName": reporter.name if reporter else "Unknown User",
            "reason": item.reason,
            "details": item.details or "",
            "status": AdminService._present_status(item.status),
            "adminAction": AdminService._present_status(item.admin_action),
            "adminNote": item.admin_note or "",
            "timestamp": AdminService._format_timestamp(item.created_at),
            "reviewedAt": AdminService._format_timestamp(item.reviewed_at),
        }

    @staticmethod
    def _serialize_user(user):
        status = (user.status or "UNVERIFIED").upper()
        blocked = status == "BLOCKED"
        pending_pro = status == "PENDING_PRO"
        pro = status == "PRO"
        enterprise = status == "ENTERPRISE"
        verified = status in {"VERIFIED", "PENDING_PRO", "PRO", "ENTERPRISE"}

        return {
            "id": f"USR-{user.id:04d}",
            "dbId": user.id,
            "name": user.name,
            "email": user.email,
            "verified": verified,
            "pendingPro": pending_pro,
            "pro": pro,
            "enterprise": enterprise,
            "plan": user.subscription_plan,
            "status": "Blocked" if blocked else "Deactivated" if status == "DEACTIVED" else "Active",
            "rawStatus": status,
            "warnings": int(user.get_setting("account-info", "warnings", 0) or 0),
            "profileUrl": url_for("profile.profile", id=user.id),
        }

    @staticmethod
    def _serialize_payment_submission(item):
        return {
            "id": f"PAY-{item.id:04d}",
            "dbId": item.id,
            "userId": f"USR-{item.user_id:04d}",
            "userDbId": item.user_id,
            "userName": item.user.name if item.user else "Unknown User",
            "fullName": item.full_name,
            "email": item.email,
            "plan": item.plan,
            "paymentMethod": item.payment_method,
            "transactionId": item.transaction_id,
            "screenshotUrl": url_for(
                "admin.payment_screenshot",
                filename=item.screenshot_path,
            ),
            "note": item.note or "",
            "status": AdminService._present_status(item.status),
            "adminNote": item.admin_note or "",
            "timestamp": AdminService._format_timestamp(item.created_at),
            "reviewedAt": AdminService._format_timestamp(item.reviewed_at),
        }

    @staticmethod
    def _present_status(value):
        normalized = (value or "").replace("_", " ").strip().title()
        return normalized or "Unknown"

    @staticmethod
    def _format_timestamp(value):
        if not value:
            return "-"
        return utc_iso_from(value)
