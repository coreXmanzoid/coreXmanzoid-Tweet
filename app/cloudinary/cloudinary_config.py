import os
from pathlib import Path

import cloudinary
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BASE_DIR / ".env"

# PythonAnywhere often starts the WSGI process outside the project root.
# Load the project's .env explicitly so config is consistent with localhost.
load_dotenv(ENV_PATH)


def configure_cloudinary():
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME")
    api_key = os.getenv("CLOUDINARY_API_KEY")
    api_secret = os.getenv("CLOUDINARY_API_SECRET")
    api_proxy = os.getenv("CLOUDINARY_API_PROXY")

    missing = [
        name
        for name, value in (
            ("CLOUDINARY_CLOUD_NAME", cloud_name),
            ("CLOUDINARY_API_KEY", api_key),
            ("CLOUDINARY_API_SECRET", api_secret),
        )
        if not value
    ]

    if missing:
        raise RuntimeError(
            "Missing Cloudinary configuration: " + ", ".join(missing)
        )

    cloudinary.config(
        cloud_name=cloud_name,
        api_key=api_key,
        api_secret=api_secret,
        api_proxy=api_proxy,
        secure=True,
    )


configure_cloudinary()
