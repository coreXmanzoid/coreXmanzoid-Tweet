from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.utils.time_utils import utc_now


class PaymentSubmission(db.Model):
    __tablename__ = "payment_submissions"
    __table_args__ = (
        UniqueConstraint("transaction_id", name="uq_payment_transaction_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, db.ForeignKey("user_data.id"), nullable=False
    )
    full_name: Mapped[str] = mapped_column(String(160), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    plan: Mapped[str] = mapped_column(String(40), nullable=False, default="pro_monthly")
    payment_method: Mapped[str] = mapped_column(String(60), nullable=False)
    transaction_id: Mapped[str] = mapped_column(String(160), nullable=False)
    screenshot_path: Mapped[str] = mapped_column(String(255), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="pending")
    admin_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user = relationship("UserData", back_populates="payment_submissions")
