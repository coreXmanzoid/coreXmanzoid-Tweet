from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db

class Follow(db.Model):
    __tablename__ = "follows"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # who follows
    follower_id: Mapped[int] = mapped_column(
        Integer, db.ForeignKey("user_data.id"), nullable=False
    )

    # who is being followed
    following_id: Mapped[int] = mapped_column(
        Integer, db.ForeignKey("user_data.id"), nullable=False
    )

    # user who follows someone
    follower: Mapped["UserData"] = relationship(
        "UserData", foreign_keys=[follower_id], back_populates="following"
    )

    # user who is being followed
    following: Mapped["UserData"] = relationship(
        "UserData", foreign_keys=[following_id], back_populates="followers"
    )

