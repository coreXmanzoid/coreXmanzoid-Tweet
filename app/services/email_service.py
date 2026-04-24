import logging
import os
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from smtplib import SMTP, SMTP_SSL

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BASE_DIR / ".env"
load_dotenv(ENV_PATH)

logger = logging.getLogger(__name__)


class EmailService:

    @staticmethod
    def _env_flag(name: str, default: bool) -> bool:
        value = os.getenv(name)
        if value is None:
            return default
        return value.strip().lower() in {"1", "true", "yes", "on"}

    @staticmethod
    def _get_config():
        sender_email = os.getenv("EMAIL") or os.getenv("SMTP_USERNAME")
        sender_password = (
            os.getenv("EMAIL_PASSWORD")
            or os.getenv("SMTP_PASSWORD")
            or os.getenv("PASSWORD")
        )

        return {
            "sender_email": sender_email,
            "sender_password": sender_password,
            "smtp_host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
            "smtp_port": int(os.getenv("SMTP_PORT", "587")),
            "use_tls": EmailService._env_flag("SMTP_USE_TLS", True),
            "use_ssl": EmailService._env_flag("SMTP_USE_SSL", False),
            "timeout": int(os.getenv("SMTP_TIMEOUT", "20")),
        }

    @staticmethod
    def validate_email(email: str) -> bool:
        pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
        return re.match(pattern, email) is not None

    @staticmethod
    def send_link_email(user_email: str, reset_link: str, st: int) -> bool:
        """
        st = 1 -> verify email
        st = 2 -> reset password
        """

        if not EmailService.validate_email(user_email):
            logger.warning("Invalid email format: %s", user_email)
            return False

        config = EmailService._get_config()
        sender_email = config["sender_email"]
        sender_password = config["sender_password"]

        missing = [
            name
            for name, value in (
                ("EMAIL or SMTP_USERNAME", sender_email),
                ("EMAIL_PASSWORD, SMTP_PASSWORD, or PASSWORD", sender_password),
            )
            if not value
        ]

        if missing:
            logger.error(
                "Email configuration missing: %s. On PythonAnywhere, make sure the "
                "project .env file exists at %s or define the variables in the WSGI file.",
                ", ".join(missing),
                ENV_PATH,
            )
            return False

        subject = (
            "Password Reset Link - coreXmanzoid Tweet"
            if st == 2
            else "Verify Email - coreXmanzoid Tweet"
        )

        button_text = "Reset Password" if st == 2 else "Verify Email"
        message_text = (
            "We received a request to reset your password."
            if st == 2
            else "Please verify your email address."
        )

        msg = MIMEMultipart("alternative")
        msg["From"] = sender_email
        msg["To"] = user_email
        msg["Subject"] = subject

        html_content = f"""
        <html>
        <body>
        <p>
        Hello,<br><br>

        {message_text} for <b>coreXmanzoid Tweet</b>.<br><br>

        <a href="{reset_link}"
        style="
            display:inline-block;
            background:#c7c0b1;
            color:white;
            padding:10px 20px;
            border-radius:40px;
            text-decoration:none;
        ">
        {button_text}
        </a>

        <br><br>
        The link will expire in 20 minutes.<br>
        If you did not request this, simply ignore this email.<br><br>

        <b>coreXmanzoid Development Team</b>
        </p>
        </body>
        </html>
        """

        msg.attach(MIMEText(html_content, "html"))

        try:
            smtp_class = SMTP_SSL if config["use_ssl"] else SMTP

            with smtp_class(
                config["smtp_host"],
                config["smtp_port"],
                timeout=config["timeout"],
            ) as connection:
                connection.ehlo()

                if config["use_tls"] and not config["use_ssl"]:
                    connection.starttls()
                    connection.ehlo()

                connection.login(sender_email, sender_password)
                connection.sendmail(sender_email, user_email, msg.as_string())

            logger.info("Email sent successfully to %s", user_email)
            return True

        except Exception:
            logger.exception(
                "Failed to send email to %s using %s:%s (TLS=%s, SSL=%s)",
                user_email,
                config["smtp_host"],
                config["smtp_port"],
                config["use_tls"],
                config["use_ssl"],
            )
            return False
