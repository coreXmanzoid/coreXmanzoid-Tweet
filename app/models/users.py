from datetime import  date
from flask_login import UserMixin

from sqlalchemy import String, Integer, Boolean, Date, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.mutable import MutableList

from app.extensions import db


class UserData(UserMixin, db.Model):
    __tablename__ = "user_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    name: Mapped[str] = mapped_column(String, nullable=False)

    username: Mapped[str] = mapped_column(String, nullable=False, unique=True)

    profile_image_url: Mapped[str | None] = mapped_column(
        String, nullable=True, default=None
    )

    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)

    contact : Mapped[int] = mapped_column(Integer, nullable=False)

    password: Mapped[str] = mapped_column(String, nullable=False)

    fb_auth_token: Mapped[str | None] = mapped_column(String, nullable=True, default=None)

    liked_posts: Mapped[list] = mapped_column(
        MutableList.as_mutable(JSON), default=list
    )

    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    reposted_posts: Mapped[list] = mapped_column(
        MutableList.as_mutable(JSON), default=list
    )

    status: Mapped[str] = mapped_column(String, default="UnVerified")

    # Relationships
    posts = relationship("Post", back_populates="user")

    comments = relationship("Comments", back_populates="user")

    received_notifications = relationship(
        "Notification",
        foreign_keys="Notification.recipient_id",
        back_populates="recipient",
        cascade="all, delete-orphan",
    )

    sent_notifications = relationship(
        "Notification",
        foreign_keys="Notification.sender_id",
        back_populates="sender",
    )

    # USERS WHO FOLLOW THIS USER
    followers: Mapped[list["Follow"]] = relationship(
        "Follow",
        foreign_keys="Follow.following_id",
        back_populates="following",
        cascade="all, delete-orphan",
    )

    # USERS THIS USER IS FOLLOWING
    following: Mapped[list["Follow"]] = relationship(
        "Follow",
        foreign_keys="Follow.follower_id",
        back_populates="follower",
        cascade="all, delete-orphan",
    )