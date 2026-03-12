from smtplib import SMTP
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import re
import os

load_dotenv()

EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")


class EmailService:

    @staticmethod
    def validate_email(email: str) -> bool:
        pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
        return re.match(pattern, email) is not None

    @staticmethod
    def send_link_email(user_email: str, reset_link: str, st: int) -> bool:
        """
        st = 1 → verify email
        st = 2 → reset password
        """

        if not EmailService.validate_email(user_email):
            print("❌ Invalid email format")
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
        msg["From"] = EMAIL
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
        If you didn’t request this, Simplly ignore this email.<br><br>

        <b>coreXmanzoid Development Team</b>
        </p>
        </body>
        </html>
        """

        msg.attach(MIMEText(html_content, "html"))

        try:
            with SMTP("smtp.gmail.com", 587) as connection:
                connection.starttls()
                connection.login(EMAIL, PASSWORD)
                connection.sendmail(EMAIL, user_email, msg.as_string())

            print("✅ Email sent successfully")
            return True

        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            return False