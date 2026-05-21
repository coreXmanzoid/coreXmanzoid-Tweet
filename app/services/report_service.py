from sqlalchemy import select

from app.extensions import db
from app.models.posts import Post
from app.models.report_post import ReportPost


class ReportService:
    VALID_REASONS = {
        "Spam",
        "Harassment or Bullying",
        "Hate Speech",
        "Violence or Threats",
        "Adult or Sexual Content",
        "Graphic or Disturbing Content",
        "Fake Information",
        "Scam or Fraud",
        "Copyright Violation",
        "Privacy Violation",
        "Self-harm or Dangerous Content",
        "Impersonation",
        "Illegal Content",
        "Off-topic or Misleading",
        "Other",
    }

    @staticmethod
    def create_post_report(post_id, reporter_id, reason, details=None):
        post = db.session.get(Post, post_id)
        if not post:
            raise ValueError("Post not found.")

        normalized_reason = (reason or "").strip()
        if normalized_reason not in ReportService.VALID_REASONS:
            raise ValueError("Please select a report reason.")

        normalized_details = (details or "").strip() or None

        existing_report = db.session.scalars(
            select(ReportPost).where(
                ReportPost.post_id == post_id,
                ReportPost.reported_by == reporter_id,
                ReportPost.status == "pending",
            )
        ).first()

        if existing_report:
            existing_report.reason = normalized_reason
            existing_report.details = normalized_details
            db.session.commit()
            return existing_report, False

        report = ReportPost(
            post_id=post_id,
            reported_by=reporter_id,
            reason=normalized_reason,
            details=normalized_details,
        )
        db.session.add(report)
        db.session.commit()
        return report, True
