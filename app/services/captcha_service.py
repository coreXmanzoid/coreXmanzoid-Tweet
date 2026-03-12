import os
import requests

TURNSTILE_SECRET = os.getenv("CLOUDFARE_SECRET_KEY")


class CaptchaService:

    @staticmethod
    def verify_turnstile(token, ip):

        url = "https://challenges.cloudflare.com/turnstile/v0/siteverify"

        data = {
            "secret": TURNSTILE_SECRET,
            "response": token,
            "remoteip": ip,
        }

        r = requests.post(url, data=data)
        result = r.json()

        return result.get("success", False)