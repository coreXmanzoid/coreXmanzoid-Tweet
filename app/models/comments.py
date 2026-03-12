from sqlalchemy import String, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db

class Comments(db.Model):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    content: Mapped[str] = mapped_column(String, nullable=False)
    mentions: Mapped[JSON] = mapped_column(JSON, default=list)

    # on which post
    post_id: Mapped[int] = mapped_column(
        Integer, db.ForeignKey("posts.id"), nullable=False
    )

    # which user commented
    user_id: Mapped[int] = mapped_column(
        Integer, db.ForeignKey("user_data.id"), nullable=False
    )

    likes: Mapped[int] = mapped_column(Integer, default=0)

    post = relationship("Post", back_populates="comment_entries")
    user = relationship("UserData", back_populates="comments")
