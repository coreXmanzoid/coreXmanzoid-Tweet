from datetime import datetime

from sqlalchemy import String, Integer, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.utils.time_utils import utc_now



class Notification(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Who receives it
    recipient_id: Mapped[int] = mapped_column(
        Integer, db.ForeignKey("user_data.id"), nullable=False
    )

    sender_id: Mapped[int] = mapped_column(
        Integer, db.ForeignKey("user_data.id"), nullable=True
    )
    # Notification content
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(String, nullable=False)

    # Type of notification (like, comment, follow, etc.)
    type: Mapped[str] = mapped_column(String(50), nullable=True)

    identifier: Mapped[int] = mapped_column(
        Integer, nullable=True
    )  # e.g., post_id or comment_id related to the notification
    
    # Status
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    recipient = relationship(
        "UserData", foreign_keys=[recipient_id], back_populates="received_notifications"
    )
    sender = relationship(
        "UserData", foreign_keys=[sender_id], back_populates="sent_notifications"
    )
