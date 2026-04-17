from datetime import UTC, datetime

from flask import url_for

from app.extensions import db
from app.models.report import Report
from app.models.support_requests import Support
from app.models.users import UserData


class AdminService:
    @staticmethod
    def dashboard_data():
        support_requests = db.session.scalars(
            db.select(Support).order_by(Support.created_at.desc(), Support.id.desc())
        ).all()
        reports = db.session.scalars(
            db.select(Report).order_by(Report.created_at.desc(), Report.id.desc())
        ).all()
        users = db.session.scalars(
            db.select(UserData).order_by(UserData.id.desc())
        ).all()

        return {
            "supportRequests": [
                AdminService._serialize_support_request(item)
                for item in support_requests
            ],
            "userReports": [AdminService._serialize_report(item) for item in reports],
            "managedUsers": [AdminService._serialize_user(item) for item in users],
        }

    @staticmethod
    def save_support_reply(request_id, reply):
        support_request = db.session.get(Support, request_id)
        if not support_request:
            raise ValueError("Support request not found")

        support_request.admin_reply = reply
        support_request.updated_at = datetime.now(UTC)
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
        support_request.updated_at = datetime.now(UTC)
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

        user.status = "PRO"
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
    def _serialize_user(user):
        status = (user.status or "UNVERIFIED").upper()
        blocked = status == "BLOCKED"
        pending_pro = status == "PENDING_PRO"
        pro = status == "PRO"
        verified = status in {"VERIFIED", "PENDING_PRO", "PRO"}

        return {
            "id": f"USR-{user.id:04d}",
            "dbId": user.id,
            "name": user.name,
            "email": user.email,
            "verified": verified,
            "pendingPro": pending_pro,
            "pro": pro,
            "status": "Blocked" if blocked else "Deactivated" if status == "DEACTIVED" else "Active",
            "rawStatus": status,
            "warnings": int(user.get_setting("account-info", "warnings", 0) or 0),
            "profileUrl": url_for("profile.profile", id=user.id),
        }

    @staticmethod
    def _present_status(value):
        normalized = (value or "").replace("_", " ").strip().title()
        return normalized or "Unknown"

    @staticmethod
    def _format_timestamp(value):
        if not value:
            return "-"
        return value.strftime("%b %d, %Y - %I:%M %p").replace(" 0", " ")
