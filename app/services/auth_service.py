from flask import current_app, url_for
from itsdangerous import URLSafeTimedSerializer
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db
from app.models.users import UserData
from app.services.email_service import EmailService
def get_serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"])


class AuthService:

    @staticmethod
    def username_exists(username):
        return db.session.execute(
            db.select(UserData).where(UserData.username == username)
        ).scalar()

    @staticmethod
    def email_exists(email):
        return db.session.execute(
            db.select(UserData).where(UserData.email == email)
        ).scalar()

    @staticmethod
    def create_user(name, username, email, phone, birth_date, password):

        user = UserData(
            name=name,
            username=username,
            email=email,
            birth_date=birth_date,
            number=phone,
            password=generate_password_hash(
                password, method="pbkdf2:sha256", salt_length=8
            ),
        )

        db.session.add(user)
        db.session.commit()

        return user

    @staticmethod
    def authenticate(identifier, password):

        user = db.session.execute(
            db.select(UserData).where(
            (UserData.email == identifier) | (UserData.username == identifier)
            )
        ).scalar()

        if not user or not check_password_hash(user.password, password):
            return None

        return user

    @staticmethod
    def create_reset_token(user_id):
        serializer = get_serializer()
        return serializer.dumps(user_id, salt="password-reset-salt")

    @staticmethod
    def verify_reset_token(token):
        serializer = get_serializer()
        try:
            user_id = serializer.loads(token, salt="password-reset-salt", max_age=1200)
            return db.session.get(UserData, user_id)
        except Exception:
            return None

    @staticmethod
    def reset_password(user, new_password):
        user.password = generate_password_hash(
            new_password, method="pbkdf2:sha256", salt_length=8
        )
        db.session.commit()

    @staticmethod
    def send_email_verification(user):
        serializer = get_serializer()
        token = serializer.dumps(user.id, salt="email-verify-salt")

        verify_link = url_for(
            "auth.verify_email_with_token",
            token=token,
            _external=True,
        )

        return EmailService.send_link_email(user.email, verify_link, st=1)

    @staticmethod
    def verify_email_token(token):
        serializer = get_serializer()
        try:
            user_id = serializer.loads(
                token, salt="email-verify-salt", max_age=1200
            )
            return db.session.get(UserData, user_id)
        except Exception:
            return None
