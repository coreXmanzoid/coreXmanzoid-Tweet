import re
from app.extensions import db
from app.models.users import UserData


def validate_username(username):
    """Validates a username based on specific criteria:
    - Must be between 3 and 20 characters long.
    - Can only contain letters, numbers, and underscores.
    - spaces are replaced with underscores.
    - Is case-insensitive (converted to lowercase).
    Args:
        username (str): The username to validate.
        Returns:
            bool: True if the username is valid, False otherwise.
    """
    username = username.lower().replace(" ", "_")
    if not username:
        return False
    if len(username) < 3 or len(username) > 20:
        return False
    if not re.match(r"^[a-zA-Z0-9_]+$", username):
        return False
    return True

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