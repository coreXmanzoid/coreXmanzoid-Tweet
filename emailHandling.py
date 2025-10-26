from smtplib import SMTP
from random import randint
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os

load_dotenv()

EMAIL = str(os.getenv("EMAIL"))       # your sender email
PASSWORD = str(os.environ.get("PASSWORD"))      # Gmail App Password (not your main password)

def sendEmail(userEmail: str) -> str:
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
            connection.send_message(msg)
        print("✅ Email sent successfully!")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

    return OTP


def checkOTP(sentOTP, UserEnteredOTP) -> bool:
    if sentOTP == UserEnteredOTP:
        return True
    return False

# sendEmail("me.hammad163@gmail.com")