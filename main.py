import os
from dotenv import load_dotenv
from flask_login import current_user
from app import create_app
from app.firebase.firebase_config import init_firebase
from app.utils.time_utils import utc_now


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
        "current_time" : utc_now(),
        "current_user" : current_user if current_user else None
    }


if __name__ == "__main__":
    app.run(debug=True)
