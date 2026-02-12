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

def sendEmail(userEmail: str) -> str:
    """
    '0000' if email sending fail and OTP if success
    
    :param userEmail: Email where OTP to be sent
    :type userEmail: str
    :return: OTP
    :rtype: str
    """
    # Validate the email address format
    if not validate_email(userEmail):
        print("❌ Invalid email format")
        return "0000"
    # Generate a 4-digit OTP
    OTP = str(randint(1000, 9999))
    # Create the email message
    msg = MIMEMultipart("alternative")
    msg["From"] = EMAIL
    msg["To"] = userEmail
    msg["Subject"] = "Email Verification - coreXmanzoid Tweet"

    # Use HTML for better formatting
    html_content = f"""
    <html>
      <body>
        <p>Hello, this is Python Bot sending you this email.<br><br>
        We are here to verify your email address for <b>coreXmanzoid Tweet</b>.<br>
        We're glad to see you on our site, but we need verification to create secure authentication between developers and users.<br><br>
        Enter the below OTP on the verification page:<br>
        <h2 style="color:blue;">C-{OTP}</h2><br>
        If you didn’t create an account, just ignore this email — your data is safe.<br><br>
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
        return OTP
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
    return "0000"


def checkOTP(sentOTP, UserEnteredOTP) -> bool:
    """
    :param sentOTP: The OTP sent to the user.
    :param UserEnteredOTP: The OTP entered by the user.
    :return: True if both OTP matched.
    :rtype: bool
    """
    if sentOTP == UserEnteredOTP:
        return True
    return False
