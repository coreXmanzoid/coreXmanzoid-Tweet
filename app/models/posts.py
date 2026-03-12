from datetime import datetime, UTC

from sqlalchemy import String, Integer, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db

class Post(db.Model):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    content: Mapped[str] = mapped_column(String, nullable=False)
    user_id: Mapped[int] = mapped_column(
        Integer, db.ForeignKey("user_data.id"), nullable=False
    )
    hashtags: Mapped[JSON] = mapped_column(JSON, default=list)
    mentions: Mapped[JSON] = mapped_column(JSON, default=list)

    timestamp: Mapped[datetime] = mapped_column(
        # Store UTC as naive to avoid offset-aware/naive mixing
        DateTime, nullable=False, default=lambda: datetime.now(UTC)
    )

    likes: Mapped[int] = mapped_column(Integer, default=0)
    comments: Mapped[int] = mapped_column(Integer, default=0)
    reposts: Mapped[int] = mapped_column(Integer, default=0)
    shares: Mapped[int] = mapped_column(Integer, default=0)

    user = relationship("UserData", back_populates="posts")
    comment_entries = relationship("Comments", back_populates="post")

