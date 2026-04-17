from datetime import date
from copy import deepcopy
from flask_login import UserMixin
from sqlalchemy import Date, Integer, JSON, String
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db

DEFAULT_USER_SETTINGS = {
    "profile-info": {"bio": ""},
    "account-info": {
        "website": "",
        "about": "",
        "warnings": 0,  # Track and block account on third warning.
    },
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
_MISSING = object()


def _split_path(*parts):
    path = []
    for part in parts:
        if part is None:
            continue
        if isinstance(part, str):
            path.extend(segment for segment in part.split(".") if segment)
        else:
            path.append(part)
    return path


def _get_nested(data, path, default=_MISSING):
    current = data
    for segment in path:
        if not isinstance(current, dict) or segment not in current:
            return default
        current = current[segment]
    return current


def _set_nested(data, path, value):
    current = data
    for segment in path[:-1]:
        next_value = current.get(segment)
        if not isinstance(next_value, dict):
            next_value = {}
            current[segment] = next_value
        current = next_value
    current[path[-1]] = value


def _delete_nested(data, path):
    if not path or not isinstance(data, dict):
        return False

    current = data
    parents = []

    for segment in path[:-1]:
        next_value = current.get(segment)
        if not isinstance(next_value, dict):
            return False
        parents.append((current, segment))
        current = next_value

    if path[-1] not in current:
        return False

    del current[path[-1]]

    for parent, segment in reversed(parents):
        child = parent.get(segment)
        if isinstance(child, dict) and not child:
            del parent[segment]
        else:
            break

    return True


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
        MutableDict.as_mutable(JSON), default=dict, nullable=False
    )

    def get_setting(self, section, key, default=None):
        path = _split_path(section, key)

        overrides = self.setting if isinstance(self.setting, dict) else {}

        value = _get_nested(overrides, path, _MISSING)
        if value is not _MISSING:
            return value

        default_value = _get_nested(DEFAULT_USER_SETTINGS, path, _MISSING)
        if default_value is not _MISSING:
            return default_value

        return default

    def set_setting(self, section, key, value):
        path = _split_path(section, key)
        if not path:
            raise ValueError("section and key must identify a setting path")

        if _get_nested(DEFAULT_USER_SETTINGS, path, _MISSING) is _MISSING:
            raise KeyError(f"Invalid setting path: {'.'.join(path)}")

        settings = deepcopy(self.setting) if isinstance(self.setting, dict) else {}
        default_value = _get_nested(DEFAULT_USER_SETTINGS, path, _MISSING)

        if value == default_value:
            _delete_nested(settings, path)
        else:
            _set_nested(settings, path, value)

        self.setting = settings
        
    # Relationships
    posts = relationship("Post", back_populates="user", cascade="all, delete-orphan")
    comments = relationship(
        "Comments", back_populates="user", cascade="all, delete-orphan"
    )
    support = relationship(
        "Support", back_populates="user", cascade="all, delete-orphan"
    )
    reports = relationship(
        "Report", back_populates="user", cascade="all, delete-orphan"
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
