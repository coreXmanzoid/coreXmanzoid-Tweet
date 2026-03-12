import os
from datetime import datetime, UTC
from dotenv import load_dotenv

from app import create_app
from app.firebase.firebase_config import init_firebase


load_dotenv()

app = create_app()

firebase_enabled, firebase_status = init_firebase()


@app.context_processor
def inject_runtime_config():
    return {
        "firebase_enabled": firebase_enabled,
        "firebase_status": firebase_status,
        "fcm_vapid_key": os.getenv("FCM_VAPID_KEY", ""),
        "firebase_api_key": os.getenv("FIREBASE_API_KEY", ""),
        "current_time" : datetime.now(UTC)
    }


if __name__ == "__main__":
    app.run(debug=True)
