import os
from pathlib import Path

import firebase_admin
from dotenv import load_dotenv
from firebase_admin import credentials


BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

DEFAULT_FIREBASE_WEB_CONFIG = {
    "apiKey": "AIzaSyDjohzpCRhWTU1bMBqU3CXLlPiyfDSobgk",
    "authDomain": "corexmanzoid-twitter-7a86a.firebaseapp.com",
    "projectId": "corexmanzoid-twitter-7a86a",
    "storageBucket": "corexmanzoid-twitter-7a86a.firebasestorage.app",
    "messagingSenderId": "266928901713",
    "appId": "1:266928901713:web:b092a1071e9467deccf270",
    "measurementId": "G-5BXH7TMB3S",
}


def get_firebase_web_config():
    return {
        "apiKey": os.getenv("FIREBASE_API_KEY", DEFAULT_FIREBASE_WEB_CONFIG["apiKey"]),
        "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN", DEFAULT_FIREBASE_WEB_CONFIG["authDomain"]),
        "projectId": os.getenv("FIREBASE_PROJECT_ID", DEFAULT_FIREBASE_WEB_CONFIG["projectId"]),
        "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET", DEFAULT_FIREBASE_WEB_CONFIG["storageBucket"]),
        "messagingSenderId": os.getenv(
            "FIREBASE_MESSAGING_SENDER_ID",
            DEFAULT_FIREBASE_WEB_CONFIG["messagingSenderId"],
        ),
        "appId": os.getenv("FIREBASE_APP_ID", DEFAULT_FIREBASE_WEB_CONFIG["appId"]),
        "measurementId": os.getenv(
            "FIREBASE_MEASUREMENT_ID",
            DEFAULT_FIREBASE_WEB_CONFIG["measurementId"],
        ),
    }


def _candidate_service_account_paths():
    configured_path = (
        os.getenv("FIREBASE_SERVICE_ACCOUNT")
        or os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
        or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    )

    candidates = []
    seen = set()

    def add_candidate(value):
        if not value:
            return

        raw_path = Path(value).expanduser()
        path = raw_path if raw_path.is_absolute() else (BASE_DIR / raw_path).resolve()
        normalized = str(path)

        if normalized not in seen:
            seen.add(normalized)
            candidates.append(path)

    add_candidate(configured_path)
    add_candidate(BASE_DIR / "corexmanzoid-twitter-notify-firebase.json")
    add_candidate(BASE_DIR / "firebase-service-account.json")

    return candidates


def init_firebase():
    if firebase_admin._apps:
        return True, "initialized"

    service_account_candidates = _candidate_service_account_paths()
    service_account_path = next(
        (path for path in service_account_candidates if path.exists()),
        None,
    )

    if service_account_path is None:
        checked_paths = ", ".join(str(path) for path in service_account_candidates)
        return False, (
            "service account file not found. Set FIREBASE_SERVICE_ACCOUNT to an "
            f"absolute path on PythonAnywhere. Checked: {checked_paths}"
        )

    try:
        cred = credentials.Certificate(str(service_account_path))
        firebase_admin.initialize_app(cred)
    except Exception as exc:
        return False, (
            f"firebase init failed with {service_account_path}: {exc}"
        )

    return True, f"initialized using {service_account_path}"
