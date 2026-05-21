from datetime import datetime

from sqlalchemy import (
    String,
    Integer,
    DateTime,
    ForeignKey,
    Text
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)

from app.extensions import db
from app.utils.time_utils import utc_now


class ReportPost(db.Model):
    __tablename__ = "report_posts"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    # Reported Post
    post_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("posts.id"),
        nullable=False
    )

    # User who reported
    reported_by: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("user_data.id"),
        nullable=False
    )

    # Reason selected from dropdown
    reason: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    # Optional user explanation
    details: Mapped[str] = mapped_column(
        Text,
        nullable=True
    )

    # Report status
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False
    )

    # Admin action
    admin_action: Mapped[str] = mapped_column(
        String(50),
        nullable=True
    )

    # Admin note
    admin_note: Mapped[str] = mapped_column(
        Text,
        nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False
    )

    reviewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Relationships
    post = relationship(
        "Post",
        backref="reports"
    )

    reporter = relationship(
        "UserData",
        foreign_keys=[reported_by]
    )