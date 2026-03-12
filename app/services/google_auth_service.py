import secrets
from werkzeug.security import generate_password_hash
from flask import current_app
from app.extensions import db
from app.models.users import UserData
from app.utils.username import build_unique_username


class GoogleAuthService:

    @staticmethod
    def get_or_create_user(user_info):

        email = (user_info or {}).get("email")
        if not email:
            return None

        name = user_info.get("name") or email.split("@")[0]

        user = db.session.execute(
            db.select(UserData).where(UserData.email == email)
        ).scalar()

        if user:
            return user

        base_username = user_info.get("given_name") or email.split("@")[0]

        user = UserData(
            name=name,
            username=build_unique_username(base_username),
            email=email,
            contact=0,
            password=generate_password_hash(secrets.token_urlsafe(32)),
            status="Verified",
        )

        db.session.add(user)
        db.session.commit()

        return user