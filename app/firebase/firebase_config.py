import os
from pathlib import Path

import firebase_admin
from dotenv import load_dotenv
from firebase_admin import credentials


BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")


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
