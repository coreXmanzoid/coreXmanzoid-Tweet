import re
from app.extensions import db
from app.models.users import UserData


def mentions_parser(content: str):

    mentioned_usernames = [
        word[1:] for word in content.split() if word.startswith("@")
    ]

    users = (
        db.session.execute(
            db.select(UserData).where(UserData.username.in_(mentioned_usernames))
        )
        .scalars()
        .all()
    )

    mentioned_objects = [
        {"user_id": u.id, "username": u.username} for u in users
    ]

    return mentioned_objects