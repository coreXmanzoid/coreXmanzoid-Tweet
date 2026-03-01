from smtplib import SMTP
from random import randint
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import re, os

load_dotenv()

EMAIL = str(os.getenv("EMAIL"))
PASSWORD = str(os.environ.get("PASSWORD"))


def validate_email(email):
    pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    return re.match(pattern, email) is not None


def sendLinkEmail(userEmail: str, resetLink: str, st: int) -> bool:
    """
    'False' if email sending fail and 'True' if success
    :param userEmail: Email where reset password link to be sent
    :type userEmail: str
    :param resetLink: Reset password link to be sent to user email
    :type resetLink: str
    :return: True if email sent successfully else False
    :rtype: bool
    """
    # Validate the email address format
    if not validate_email(userEmail):
        print("❌ Invalid email format")
        return False

    # Create the email message
    msg = MIMEMultipart("alternative")
    msg["From"] = EMAIL
    msg["To"] = userEmail
    msg["Subject"] = "Password Reset Link - coreXmanzoid Tweet" if st == 2 else "Verify Email - coreXmanzoid Tweet"

    button_text = "Reset Password" if st == 2 else "Verify Email"
    Email_message = "We received a request to reset your password for coreXmanzoid Tweet." if st == 2 else "Please verify your email address for coreXmanzoid Tweet."
    # Use HTML for better formatting
    html_content = f"""
    <html>
      <body>
        <p>Hello, This is Python Bot sending you this email.<br><br>
        {Email_message} <b>coreXmanzoid Tweet</b>.<br>
        If you made this request, please click the link below to {button_text}:<br><br>
        <a href="{resetLink}" 
        style="
            display: inline-block;
            background-color: #c7c0b1;
            color: #ffffff;
            font-size: 16px;
            font-weight: bold;
            text-decoration: none;
            text-align: center;
            padding: 10px 20px;
            border-radius: 40px;
            border: 1px solid #46423b;
            transition: background 0.3s;
            margin: 15px auto;
            max-width: 250px;   /* prevents it from being too wide on desktop */
            width: 80%;         /* scales nicely on mobile */
        "
        onmouseover="this.style.backgroundColor='#F94818';" 
        onmouseout="this.style.backgroundColor='#c7c0b1';"
        >
        {button_text}
        </a> <br><br>
        If you didn’t request a password reset, you can safely ignore this email — your data is safe.<br><br>
        <b>coreXmanzoid Development Team</b>
        </p>
      </body>
    </html>
    """

    # Attach the HTML body
    msg.attach(MIMEText(html_content, "html"))

    # Send the email
    try:
        with SMTP("smtp.gmail.com", 587) as connection:
            connection.starttls()
            connection.login(EMAIL, PASSWORD)
            response = connection.sendmail(EMAIL, userEmail, msg.as_string())
        print("✅ Email sent successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

    return False