from datetime import date
from copy import deepcopy
from flask_login import UserMixin
from sqlalchemy import Date, Integer, JSON, String
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db

DEFAULT_USER_SETTINGS = {
    "profile-info": {"bio": ""},
    "account-info": {"website": "", "about": ""},
    "privacy-setting": {
        "private_account": False,
        "show_birthdate": True,
        "show_bio": True,
        "show_status": True,
    },
    "notifications-setting": {
        "email_notifications": True,
        "push_notifications": True,
        "new_followers": True,
        "mentions": True,
        "likes_comments": True,
        "reposts": True,
    },
    "support": {"theme": "light"},
}


class UserData(UserMixin, db.Model):
    __tablename__ = "user_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    name: Mapped[str] = mapped_column(String, nullable=False)

    username: Mapped[str] = mapped_column(String, nullable=False, unique=True)

    profile_image_url: Mapped[str | None] = mapped_column(
        String, nullable=True, default=None
    )

    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)

    contact: Mapped[int] = mapped_column(Integer, nullable=False)

    password: Mapped[str] = mapped_column(String, nullable=False)

    fb_auth_token: Mapped[str | None] = mapped_column(
        String, nullable=True, default=None
    )

    liked_posts: Mapped[list] = mapped_column(
        MutableList.as_mutable(JSON), default=list
    )

    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    reposted_posts: Mapped[list] = mapped_column(
        MutableList.as_mutable(JSON), default=list
    )

    status: Mapped[str] = mapped_column(String, default="UNVERIFIED")

    setting: Mapped[dict] = mapped_column(
        MutableDict.as_mutable(JSON),
        default=lambda: deepcopy(DEFAULT_USER_SETTINGS),
        nullable=False,
    )

    def get_setting(self, section, key, default=None):
        return self.setting.get(section, {}).get(key, default)

    def set_setting(self, section, key, value):
        settings = dict(self.setting)  # create new dict

        if section not in settings:
            settings[section] = {}

        section_data = dict(settings[section])
        section_data[key] = value
        settings[section] = section_data

        self.setting = settings  # 🔥 reassign → triggers change
    # Relationships
    posts = relationship("Post", back_populates="user", cascade="all, delete-orphan")
    comments = relationship("Comments", back_populates="user", cascade="all, delete-orphan")
    support = relationship("Support", back_populates="user", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="user", cascade="all, delete-orphan")

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
        cascade="all, delete-orphan",  # optional but recommended
    )