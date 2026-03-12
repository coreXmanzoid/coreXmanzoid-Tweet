import re
from app.extensions import db
from app.models.users import UserData


def build_unique_username(raw_value: str) -> str:
    base = re.sub(r"[^a-zA-Z0-9_]", "", (raw_value or "").replace(" ", "_")).lower()

    if not base:
        base = "user"

    username = base
    counter = 1

    while db.session.execute(
        db.select(UserData).where(UserData.username == username)
    ).scalar():
        username = f"{base}{counter}"
        counter += 1

    return username