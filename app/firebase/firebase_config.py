import firebase_admin
from firebase_admin import credentials
import os
from dotenv import load_dotenv

load_dotenv()


def init_firebase():
    if firebase_admin._apps:
        return True, "initialized"

    service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT")

    if not service_account_path:
        if os.path.exists("corexmanzoid-twitter-notify-firebase.json"):
            service_account_path = "corexmanzoid-twitter-notify-firebase.json"
        else:
            service_account_path = "firebase-service-account.json"

    if not os.path.exists(service_account_path):
        return False, f"service account file not found: {service_account_path}"

    try:
        cred = credentials.Certificate(service_account_path)
        firebase_admin.initialize_app(cred)
    except Exception as exc:
        return False, f"firebase init failed: {exc}"

    return True, "initialized"